#!/usr/bin/env python3
"""Corrida diaria LexIA: ejecuta pipeline, resume el día y envía email."""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import subprocess
import sys
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output_batch"
REPORT_DIR = BASE_DIR / "reportes_diarios"
LOG_DIR = BASE_DIR / "logs"
DEFAULT_REFERENCE = BASE_DIR / "config" / "Comparativo de identificación de normas VF (1).xlsx"
DEFAULT_REFERENCE_DRIVE_URL = "https://docs.google.com/spreadsheets/d/1vO3fQfZqCtDX8HuHjmEuf7Z4guSfIbSv/edit?gid=1405822604#gid=1405822604"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().replace("export ", "")
        value = value.strip().strip('"').strip("'").strip()
        os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corrida diaria LexIA Normativo")
    parser.add_argument("--date", help="Fecha a procesar YYYY-MM-DD. Default: hoy.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--reference-file", default=str(DEFAULT_REFERENCE))
    parser.add_argument("--reference-drive-url", default=os.getenv("REFERENCE_DRIVE_URL", DEFAULT_REFERENCE_DRIVE_URL))
    parser.add_argument("--no-sync-reference", action="store_true", help="No intenta actualizar el Excel historico desde Drive.")
    parser.add_argument("--llm-backend", default="copilot", choices=["copilot", "groq"])
    parser.add_argument("--copilot-model", default="gpt-4o")
    parser.add_argument("--llm-max-contexts", type=int, default=3)
    parser.add_argument("--llm-min-score", type=int, default=2)
    parser.add_argument("--disable-semantic-prioritization", action="store_true", help="Desactiva embeddings + cross-encoder para priorizar candidatas al LLM.")
    parser.add_argument("--semantic-embed-model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--semantic-cross-model", default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    parser.add_argument("--semantic-top-k", type=int, default=12)
    parser.add_argument("--semantic-min-score", type=float, default=0.45)
    parser.add_argument("--no-download", action="store_true", help="No descargar PDFs desde El Peruano.")
    parser.add_argument("--no-email", action="store_true", help="No enviar email.")
    parser.add_argument("--force", action="store_true", help="Reprocesar aunque exista el CSV del día.")
    parser.add_argument("--skip-pipeline", action="store_true", help="No correr el pipeline; usa el CSV existente para armar/enviar reporte.")
    parser.add_argument(
        "--no-backfill-previous",
        action="store_true",
        help="No revisa ni reprocesa publicaciones extraordinarias tardias del dia anterior.",
    )
    return parser.parse_args()


def target_date(value: str | None) -> date:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return date.today()


def norm_si_no(value: object) -> str:
    text = str(value or "").strip().upper()
    return "SI" if text in {"SI", "SÍ", "YES", "Y", "TRUE", "1"} else "NO"


def norm_numero(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).upper().strip()
    text = text.replace("Nº", "").replace("N°", "").replace("NO.", "")
    text = re.sub(r"\b(RESOLUCI[ÓO]N|DECRETO|SUPREMO|CIRCULAR|ORDENANZA|LEY)\b", " ", text)
    text = re.sub(r"[^A-Z0-9-]+", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def norm_nivel(value: object) -> str:
    text = str(value or "").strip().upper()
    if "ALTO" in text:
        return "ALTO"
    if "MEDIO" in text:
        return "MEDIO"
    if "BAJO" in text:
        return "BAJO"
    if text in {"INFORMATIVA", "INFORMATIVO"}:
        return "INFORMATIVA"
    return "NO APLICA"


def extract_drive_file_id(url_or_id: str) -> str:
    text = (url_or_id or "").strip()
    if not text:
        return ""
    if "/" not in text and "http" not in text:
        return text
    parsed = urlparse(text)
    match = re.search(r"/d/([^/]+)", parsed.path)
    if match:
        return match.group(1)
    query_id = parse_qs(parsed.query).get("id", [""])[0]
    return query_id


def sync_reference_from_drive(reference_file: Path, drive_url: str | None) -> bool:
    file_id = extract_drive_file_id(drive_url or "")
    if not file_id:
        return False

    urls = [
        f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    ]

    tmp_path = reference_file.with_suffix(".download.xlsx")
    for url in urls:
        try:
            response = requests.get(url, timeout=60, allow_redirects=True)
        except requests.RequestException as exc:
            print(f"⚠️ No se pudo consultar Drive: {exc}")
            continue

        content_type = response.headers.get("content-type", "")
        content = response.content
        if response.status_code == 200 and content.startswith(b"PK"):
            tmp_path.write_bytes(content)
            # Validacion minima: debe abrir como Excel y contener las columnas esperadas.
            excel = pd.ExcelFile(tmp_path)
            found = False
            for sheet in excel.sheet_names:
                sample = pd.read_excel(tmp_path, sheet_name=sheet, nrows=5)
                cols = {str(c).strip().upper() for c in sample.columns}
                if {"N° NORMA", "FECHA DE PUBLICACIÓN"}.issubset(cols):
                    found = True
                    break
            if not found:
                tmp_path.unlink(missing_ok=True)
                print("⚠️ El archivo descargado desde Drive no tiene las columnas esperadas; se usa la copia local.")
                return False

            reference_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.replace(reference_file)
            print(f"✅ Referencia del analista actualizada desde Drive: {reference_file}")
            return True

        print(
            "⚠️ Drive no entregó un XLSX descargable "
            f"(status={response.status_code}, content-type={content_type})."
        )

    tmp_path.unlink(missing_ok=True)
    if reference_file.exists():
        print(f"ℹ️ Se usa la referencia local existente: {reference_file}")
    else:
        print(f"⚠️ No se pudo sincronizar Drive y no existe referencia local: {reference_file}")
    return False


def run_pipeline(args: argparse.Namespace, run_date: date, csv_path: Path) -> None:
    if csv_path.exists() and args.force:
        csv_path.unlink()

    cmd = [
        sys.executable,
        str(BASE_DIR / "rag_pipeline_s3_diario_job_10.py"),
        "--analysis-date",
        run_date.strftime("%Y-%m-%d"),
        "--output-dir",
        str(csv_path.parent),
        "--llm-backend",
        args.llm_backend,
        "--copilot-model",
        args.copilot_model,
        "--llm-max-contexts",
        str(args.llm_max_contexts),
        "--llm-min-score",
        str(args.llm_min_score),
        "--output-file",
        csv_path.name,
    ]
    if not args.disable_semantic_prioritization:
        cmd.extend([
            "--enable-semantic-prioritization",
            "--semantic-embed-model",
            args.semantic_embed_model,
            "--semantic-cross-model",
            args.semantic_cross_model,
            "--semantic-top-k",
            str(args.semantic_top_k),
            "--semantic-min-score",
            str(args.semantic_min_score),
        ])
    if not args.no_download:
        cmd.append("--download-from-source")
    if args.reference_file:
        cmd.extend(["--human-reference-file", args.reference_file])

    env = os.environ.copy()
    env.setdefault("STORAGE_MODE", "local")

    print("Ejecutando:", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=BASE_DIR, env=env, check=True)


def clone_args(args: argparse.Namespace, **updates: object) -> argparse.Namespace:
    values = vars(args).copy()
    values.update(updates)
    return argparse.Namespace(**values)


def load_human_for_date(reference_file: Path, run_date: date) -> pd.DataFrame:
    if not reference_file.exists():
        return pd.DataFrame()
    excel = pd.ExcelFile(reference_file)
    data = None
    for sheet in excel.sheet_names:
        tmp = pd.read_excel(reference_file, sheet_name=sheet)
        cols = {str(c).strip().upper(): c for c in tmp.columns}
        if "N° NORMA" in cols and "FECHA DE PUBLICACIÓN" in cols:
            data = tmp.copy()
            break
    if data is None:
        return pd.DataFrame()
    data["FECHA_NORM"] = pd.to_datetime(data["FECHA DE PUBLICACIÓN"], errors="coerce", dayfirst=True).dt.date
    data = data[data["FECHA_NORM"].eq(run_date)].copy()
    if data.empty:
        return data
    data["NUMERO_NORM"] = data["N° NORMA"].map(norm_numero)
    data["HUM_POSITIVO"] = data["C. NORMATIVO"].map(norm_si_no).eq("SI")
    data["HUM_NIVEL"] = data["INTERÉS AL BANCO"].map(norm_nivel)
    data["KEY"] = data["FECHA_NORM"].astype(str) + "|" + data["NUMERO_NORM"]
    return data


def daily_metrics(df: pd.DataFrame, human: pd.DataFrame, comparison_date: date) -> dict[str, object]:
    # Sin filas del analista para la fecha no hay base para llamar "FP" a una alerta.
    # La validacion queda pendiente hasta que el Excel reciba la revision del dia.
    if human.empty:
        return {
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "precision": None,
            "recall": None,
            "f1": None,
            "analyst_count": 0,
            "analyst_rows": 0,
            "pred_count": 0,
            "comparison_available": False,
        }

    if df.empty:
        pred = pd.DataFrame(columns=["KEY", "PRED_POSITIVO"])
    else:
        pred = df.copy()
        pred["FECHA_NORM"] = comparison_date
        pred["NUMERO_NORM"] = pred["NUMERO"].map(norm_numero)
        pred["PRED_POSITIVO"] = pred["INTERES_AL_BANCO"].map(norm_si_no).eq("SI")
        pred["PRED_NIVEL"] = pred["NIVEL_IMPACTO"].map(norm_nivel)
        pred["KEY"] = pred["FECHA_NORM"].astype(str) + "|" + pred["NUMERO_NORM"]
        pred = pred.groupby("KEY", as_index=False).agg(PRED_POSITIVO=("PRED_POSITIVO", "max"))

    hum = human[human.get("HUM_POSITIVO", False)].copy() if not human.empty else pd.DataFrame(columns=["KEY"])
    pred_pos = set(pred[pred["PRED_POSITIVO"]]["KEY"]) if not pred.empty else set()
    hum_pos = set(hum["KEY"]) if not hum.empty else set()
    tp = len(pred_pos & hum_pos)
    fp = len(pred_pos - hum_pos)
    fn = len(hum_pos - pred_pos)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and (precision + recall) else None
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "analyst_count": len(hum_pos),
        "analyst_rows": len(human),
        "pred_count": len(pred_pos),
        "comparison_available": True,
    }


def first_text(row: pd.Series, columns: list[str]) -> str:
    for col in columns:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    return ""


def comparison_details(pred_df: pd.DataFrame, analyst_df: pd.DataFrame, comparison_date: date) -> dict[str, pd.DataFrame]:
    pred_by_key: dict[str, pd.Series] = {}
    analyst_by_key: dict[str, pd.Series] = {}

    if analyst_df.empty:
        columns = [
            "RESULTADO", "FECHA_COMPARACION", "NUMERO", "TIPO_NORMA", "NIVEL_IA", "NIVEL_ANALISTA",
            "DESCRIPCION_IA", "DESCRIPCION_ANALISTA", "JUSTIFICACION_IA", "REFERENCIA_ANALISTA",
        ]
        empty = pd.DataFrame(columns=columns)
        return {"aciertos": empty.copy(), "falsos_positivos": empty.copy(), "falsos_negativos": empty.copy(), "retroalimentacion": empty.copy()}

    if not pred_df.empty:
        pred = pred_df.copy()
        pred["NUMERO_NORM"] = pred["NUMERO"].map(norm_numero)
        pred["PRED_POSITIVO"] = pred["INTERES_AL_BANCO"].map(norm_si_no).eq("SI")
        pred["KEY"] = comparison_date.strftime("%Y-%m-%d") + "|" + pred["NUMERO_NORM"]
        for _, row in pred[pred["PRED_POSITIVO"]].iterrows():
            pred_by_key.setdefault(row["KEY"], row)

    if not analyst_df.empty:
        analyst = analyst_df[analyst_df["HUM_POSITIVO"]].copy()
        for _, row in analyst.iterrows():
            analyst_by_key.setdefault(row["KEY"], row)

    tp_keys = sorted(pred_by_key.keys() & analyst_by_key.keys())
    fp_keys = sorted(pred_by_key.keys() - analyst_by_key.keys())
    fn_keys = sorted(analyst_by_key.keys() - pred_by_key.keys())

    def pred_payload(key: str, result: str, analyst_row: pd.Series | None = None) -> dict[str, object]:
        row = pred_by_key[key]
        return {
            "RESULTADO": result,
            "FECHA_COMPARACION": comparison_date.strftime("%Y-%m-%d"),
            "NUMERO": first_text(row, ["NUMERO", "IDNORMA"]),
            "TIPO_NORMA": first_text(row, ["TIPO_NORMA"]),
            "NIVEL_IA": first_text(row, ["NIVEL_IMPACTO"]),
            "NIVEL_ANALISTA": first_text(analyst_row, ["HUM_NIVEL", "INTERÉS AL BANCO"]) if analyst_row is not None else "",
            "DESCRIPCION_IA": first_text(row, ["DESCRIPCION", "JUSTIFICACION"]),
            "DESCRIPCION_ANALISTA": first_text(analyst_row, ["COMENTARIO / DESCRIPCIÓN DE LA NORMA"]) if analyst_row is not None else "",
            "JUSTIFICACION_IA": first_text(row, ["JUSTIFICACION"]),
            "REFERENCIA_ANALISTA": first_text(row, ["REFERENCIA_HUMANA"]),
        }

    def analyst_payload(key: str, result: str) -> dict[str, object]:
        row = analyst_by_key[key]
        return {
            "RESULTADO": result,
            "FECHA_COMPARACION": comparison_date.strftime("%Y-%m-%d"),
            "NUMERO": first_text(row, ["N° NORMA"]),
            "TIPO_NORMA": first_text(row, ["TIPO DE NORMA"]),
            "NIVEL_IA": "",
            "NIVEL_ANALISTA": first_text(row, ["HUM_NIVEL", "INTERÉS AL BANCO"]),
            "DESCRIPCION_IA": "",
            "DESCRIPCION_ANALISTA": first_text(row, ["COMENTARIO / DESCRIPCIÓN DE LA NORMA"]),
            "JUSTIFICACION_IA": "",
            "REFERENCIA_ANALISTA": "SI",
        }

    aciertos = [pred_payload(key, "TP", analyst_by_key[key]) for key in tp_keys]
    falsos_positivos = [pred_payload(key, "FP") for key in fp_keys]
    falsos_negativos = [analyst_payload(key, "FN") for key in fn_keys]

    columns = [
        "RESULTADO",
        "FECHA_COMPARACION",
        "NUMERO",
        "TIPO_NORMA",
        "NIVEL_IA",
        "NIVEL_ANALISTA",
        "DESCRIPCION_IA",
        "DESCRIPCION_ANALISTA",
        "JUSTIFICACION_IA",
        "REFERENCIA_ANALISTA",
    ]
    return {
        "aciertos": pd.DataFrame(aciertos, columns=columns),
        "falsos_positivos": pd.DataFrame(falsos_positivos, columns=columns),
        "falsos_negativos": pd.DataFrame(falsos_negativos, columns=columns),
        "retroalimentacion": pd.DataFrame(falsos_positivos + falsos_negativos, columns=columns),
    }


def parse_date_series(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce", dayfirst=True)
    missing = parsed.isna()
    if missing.any():
        parsed_alt = pd.to_datetime(values[missing], errors="coerce")
        parsed.loc[missing] = parsed_alt
    return parsed.dt.date


def filter_report_rows(df: pd.DataFrame, run_date: date) -> tuple[pd.DataFrame, int]:
    """Conserva filas publicadas el dia procesado; FECHA_EMISION queda como dato informativo."""
    required_cols = ["FECHA", "FECHA_PUBLICACION"]
    if df.empty or any(col not in df.columns for col in required_cols):
        return df.copy(), 0

    keep = pd.Series(True, index=df.index)
    for col in required_cols:
        keep &= parse_date_series(df[col]).eq(run_date)

    filtered = df[keep].copy()
    if not filtered.empty:
        identity = filtered.apply(_identity_review, axis=1, result_type="expand")
        filtered["IDENTIDAD_CONFIABLE"] = identity["IDENTIDAD_CONFIABLE"].values
        filtered["OBS_IDENTIDAD"] = identity["OBS_IDENTIDAD"].values
    return filtered, int((~keep).sum())


def _identity_review(row: pd.Series) -> dict[str, str]:
    numero = str(row.get("NUMERO") or "").strip().upper()
    tipo = str(row.get("TIPO_NORMA") or "").strip().upper()
    descripcion = str(row.get("DESCRIPCION") or "").strip().upper()

    observations = []
    if not numero or numero == "NO DISPONIBLE":
        observations.append("Numero no disponible")
    digits_only = bool(re.fullmatch(r"\d+", numero))
    if digits_only and len(numero) < 4:
        observations.append("Numero demasiado corto")
    if digits_only and "DECRETO" in tipo:
        observations.append("Numero numerico simple con tipo decreto")
    if "LEY" in tipo and re.match(r"^(RESOLU(?:CIÓN|CION)|DECRETO|ORDENANZA|ACUERDO)\b", descripcion):
        observations.append("Tipo ley no coincide con descripcion")
    if "DECRETO" in tipo and re.match(r"^(RESOLU(?:CIÓN|CION)|LEY|ORDENANZA|ACUERDO)\b", descripcion):
        observations.append("Tipo decreto no coincide con descripcion")
    if "RESOLU" in tipo and re.match(r"^(LEY|DECRETO|ORDENANZA|ACUERDO)\b", descripcion):
        observations.append("Tipo resolucion no coincide con descripcion")
    if digits_only and "QUE, LA LEY" in descripcion:
        observations.append("Posible cita interna de ley")

    return {
        "IDENTIDAD_CONFIABLE": "NO" if observations else "SI",
        "OBS_IDENTIDAD": "; ".join(observations) if observations else "",
    }


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def html_table(df: pd.DataFrame, columns: list[str], max_rows: int = 30) -> str:
    if df.empty:
        return "<p>No hay normas para mostrar.</p>"
    show = df[[c for c in columns if c in df.columns]].head(max_rows).copy()
    headers = "".join(f"<th>{escape(c)}</th>" for c in show.columns)
    rows = []
    for _, row in show.iterrows():
        rows.append("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in row) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def fetch_source_manifest(run_date: date) -> pd.DataFrame:
    url = "https://diariooficial.elperuano.pe/Normas/Filtro"
    data = {
        "dateparam": run_date.strftime("%m/%d/%Y 00:00:00"),
        "cddesde": run_date.strftime("%d/%m/%Y"),
        "cdhasta": run_date.strftime("%d/%m/%Y"),
    }
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
    }
    try:
        response = requests.post(url, headers=headers, data=data, timeout=60, verify=False)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"⚠️ No se pudo obtener manifiesto de El Peruano: {exc}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.edicionesoficiales_articulos, article.edicionesoficiales_articulos_dig")
    rows = []
    for idx, article in enumerate(articles, start=1):
        text = " ".join(article.get_text(" ", strip=True).split())
        title = re.sub(r"\s*Descarga individual.*$", "", text, flags=re.IGNORECASE).strip()
        rows.append({
            "ORDEN": idx,
            "FECHA_PUBLICACION": run_date.strftime("%d/%m/%Y"),
            "TITULO_FUENTE": title,
        })
    return pd.DataFrame(rows)


def normalize_manifest_title(value: object) -> str:
    text = str(value or "").upper()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9ÁÉÍÓÚÜÑ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def numero_match_key(value: object) -> str:
    normalized = norm_numero(value)
    if not normalized:
        return ""
    match = re.match(r"^([A-Z]*\d+)-(\d{4})", normalized)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    parts = [part for part in normalized.split("-") if part]
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return normalized


def extract_manifest_numero(title: object) -> str:
    text = str(title or "")
    patterns = [
        r"\bRESOLUCI(?:ÓN|ON)\s+SBS\s+N[°º]?\s*([A-Z0-9./-]+)",
        r"\bRESOLUCI(?:ÓN|ON)\s+MINISTERIAL\s+N[°º]?\s*([A-Z0-9./-]+)",
        r"\b(?:RESOLUCIÓN|RESOLUCION|DECRETO(?:S)?(?:\s+SUPREMO|\s+DE\s+ALCALD[IÍ]A)?|ORDENANZA(?:\s+(?:MUNICIPAL|REGIONAL))?|ACUERDO|CIRCULAR)\s+N[°º]?\s*([A-Z0-9./-]+)",
        r"\bLEY\s+N[°º]?\s*([A-Z0-9./-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return str(match.group(1)).strip()
    return ""


def extract_manifest_tipo(title: object) -> str:
    text = str(title or "").upper()
    mappings = [
        (r"DECRETOS\s+DE\s+ALCALD[IÍ]A", "Decreto de Alcaldia"),
        (r"DECRETO\s+DE\s+ALCALD[IÍ]A", "Decreto de Alcaldia"),
        (r"DECRETO\s+SUPREMO", "Decreto Supremo"),
        (r"RESOLUCIÓN\s+SBS|RESOLUCION\s+SBS", "Resolucion"),
        (r"RESOLUCIÓN|RESOLUCION", "Resolucion"),
        (r"ORDENANZA", "Ordenanza"),
        (r"ACUERDO", "Acuerdo"),
        (r"CIRCULAR", "Circular"),
        (r"LEY", "Ley"),
    ]
    for pattern, tipo in mappings:
        if re.search(pattern, text):
            return tipo
    return "NO DISPONIBLE"


def extract_manifest_descripcion(title: object) -> str:
    text = " ".join(str(title or "").split())
    match = re.search(r"Fecha:\s*\d{2}/\d{2}/\d{4}\s+(?:Edición Extraordinaria\s+)?(.+)$", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def extract_manifest_emisor(title: object) -> str:
    text = " ".join(str(title or "").split())
    patterns = [
        r"^(.*?)\s+DECRETO\s+SUPREMO",
        r"^(.*?)\s+DECRETO\s+DE\s+ALCALD[IÍ]A",
        r"^(.*?)\s+RESOLUCIÓN",
        r"^(.*?)\s+RESOLUCION",
        r"^(.*?)\s+LEY\s+N",
        r"^(.*?)\s+ACUERDO\s+N",
        r"^(.*?)\s+CIRCULAR\s+N",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "NO DISPONIBLE"


def classify_manifest_publication(title: object) -> dict[str, str] | None:
    text = " ".join(str(title or "").split())
    upper = text.upper()
    numero = extract_manifest_numero(text)
    tipo = extract_manifest_tipo(text)
    descripcion = extract_manifest_descripcion(text)
    emisor = extract_manifest_emisor(text)

    if "ESTADO DE EMERGENCIA" in upper and "PCM" in upper:
        return {
            "NUMERO": numero or "NO DISPONIBLE",
            "TIPO_NORMA": tipo,
            "DESCRIPCION": descripcion,
            "EMISOR": emisor,
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": "INFORMATIVA",
            "JUSTIFICACION": "Estado de emergencia o prórroga relevante para seguimiento del banco.",
            "IMPORTANCIA": "Si",
        }

    if "SUNARP" in upper and ("CERTIFICADO LITERAL" in upper or "PARTIDA REGISTRAL" in upper or "FIRMA DIGITAL INSTITUCIONAL" in upper):
        return {
            "NUMERO": numero or "NO DISPONIBLE",
            "TIPO_NORMA": tipo,
            "DESCRIPCION": descripcion,
            "EMISOR": emisor,
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": "MEDIO",
            "JUSTIFICACION": "Disposición registral SUNARP con impacto operativo en validaciones, formalización de garantías y documentación.",
            "IMPORTANCIA": "Si",
        }

    if "INDECOPI" in upper and "DESIGNAN ASESOR DE LA PRESIDENCIA EJECUTIVA" in upper:
        return None

    if "RESOLUCIÓN SBS" in upper or "RESOLUCION SBS" in upper:
        if "CONDUCTA DE MERCADO" in upper or "COMISIONES Y GASTOS" in upper:
            return {
                "NUMERO": numero or "NO DISPONIBLE",
                "TIPO_NORMA": tipo,
                "DESCRIPCION": descripcion,
                "EMISOR": "SBS",
                "INTERES_AL_BANCO": "SI",
                "NIVEL_IMPACTO": "ALTO",
                "JUSTIFICACION": "Cambio estructural SBS sobre conducta de mercado/comisiones con impacto alto para el banco.",
                "IMPORTANCIA": "Si",
            }
        if "CONSULTA PÚBLICA" in upper or "CONSULTA PUBLICA" in upper or "PROYECTO NORMATIVO" in upper:
            return {
                "NUMERO": numero or "NO DISPONIBLE",
                "TIPO_NORMA": tipo,
                "DESCRIPCION": descripcion,
                "EMISOR": "SBS",
                "INTERES_AL_BANCO": "SI",
                "NIVEL_IMPACTO": "INFORMATIVA",
                "JUSTIFICACION": "Consulta pública SBS de proyecto normativo; requiere seguimiento regulatorio, sin obligación directa inmediata para el banco.",
                "IMPORTANCIA": "Si",
            }
        if "CLASIFICACIÓN DE EMPRESAS DEL SISTEMA FINANCIERO" in upper or "CLASIFICACION DE EMPRESAS DEL SISTEMA FINANCIERO" in upper:
            return {
                "NUMERO": numero or "NO DISPONIBLE",
                "TIPO_NORMA": tipo,
                "DESCRIPCION": descripcion,
                "EMISOR": "SBS",
                "INTERES_AL_BANCO": "SI",
                "NIVEL_IMPACTO": "MEDIO",
                "JUSTIFICACION": "Modificación SBS aplicable al sistema financiero; requiere revisar nuevas obligaciones, clasificación y eventuales adecuaciones.",
                "IMPORTANCIA": "Si",
            }

    if (
        "BANCO CENTRAL DE RESERVA" in upper
        and "CIRCULAR" in upper
        and ("BANCOS DEL EXTERIOR DE PRIMERA CATEGORÍA" in upper or "BANCOS DEL EXTERIOR DE PRIMERA CATEGORIA" in upper)
    ):
        return {
            "NUMERO": numero or "NO DISPONIBLE",
            "TIPO_NORMA": "Circular",
            "DESCRIPCION": descripcion,
            "EMISOR": "BCRP",
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": "INFORMATIVA",
            "JUSTIFICACION": "Circular BCRP sobre lista de bancos del exterior de primera categoría; el histórico del analista la trata como seguimiento informativo para el banco.",
            "IMPORTANCIA": "Si",
        }

    if (
        "LEY" in upper
        and (
            "DESCANSO SENTADO" in upper
            or "ALTERNANCIA DE LA POSTURA" in upper
            or "SEGURIDAD Y SALUD EN EL TRABAJO" in upper
        )
    ):
        return {
            "NUMERO": numero or "NO DISPONIBLE",
            "TIPO_NORMA": "Ley",
            "DESCRIPCION": descripcion,
            "EMISOR": emisor,
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": "MEDIO",
            "JUSTIFICACION": "Norma laboral general aplicable a centros de trabajo; puede requerir adecuaciones de SST, mobiliario, reglamento interno y controles operativos.",
            "IMPORTANCIA": "Si",
        }

    if (
        "ORDENANZA" in upper
        and ("DISCRIMINACIÓN" in upper or "DISCRIMINACION" in upper)
        and any(term in upper for term in ("ESTABLECIMIENTOS ABIERTOS", "ATENCIÓN AL PÚBLICO", "ATENCION AL PUBLICO", "LICENCIA DE FUNCIONAMIENTO", "CLAUSURA", "AVISO OBLIGATORIO"))
    ):
        return {
            "NUMERO": numero or "NO DISPONIBLE",
            "TIPO_NORMA": "Ordenanza",
            "DESCRIPCION": descripcion,
            "EMISOR": emisor,
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": "BAJO",
            "JUSTIFICACION": "Ordenanza municipal aplicable a establecimientos abiertos al publico; exige medidas de prevencion o aviso y contempla sanciones con alcance territorial acotado.",
            "IMPORTANCIA": "Si",
        }

    return None


def manifest_interest_keys(source_manifest: pd.DataFrame) -> set[str]:
    keys: set[str] = set()
    if source_manifest.empty:
        return keys
    for _, row in source_manifest.iterrows():
        classification = classify_manifest_publication(row.get("TITULO_FUENTE", ""))
        if not classification:
            continue
        numero = classification.get("NUMERO", "")
        for candidate in (norm_numero(numero), numero_match_key(numero)):
            if candidate:
                keys.add(candidate)
    return keys


def prune_low_confidence_interest_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    interes = result.get("INTERES_AL_BANCO", pd.Series(index=result.index, dtype=object)).map(norm_si_no)
    identidad = result.get("IDENTIDAD_CONFIABLE", pd.Series(index=result.index, dtype=object)).astype(str).str.upper()
    obs = result.get("OBS_IDENTIDAD", pd.Series(index=result.index, dtype=object)).astype(str)

    low_conf_mask = (
        interes.eq("SI")
        & identidad.eq("NO")
        & ~obs.str.contains("manifiesto de el peruano", case=False, na=False)
        & obs.str.contains(
            "Numero demasiado corto|Numero numerico simple con tipo decreto|Tipo decreto no coincide con descripcion|Tipo resolucion no coincide con descripcion",
            case=False,
            na=False,
            regex=True,
        )
    )

    if low_conf_mask.any():
        result.loc[low_conf_mask, "C_NORMATIVO"] = "NO"
        result.loc[low_conf_mask, "INTERES_BANCO"] = "NO"
        result.loc[low_conf_mask, "INTERES_AL_BANCO"] = "NO"
        result.loc[low_conf_mask, "NIVEL_IMPACTO"] = "NO APLICA"
        result.loc[low_conf_mask, "JUSTIFICACION"] = "Descartada en reporte por identidad inconsistente; requiere validación adicional del documento fuente."
        result.loc[low_conf_mask, "IMPORTANCIA"] = "No"

    return result


def prune_interest_without_manifest_support(df: pd.DataFrame, source_manifest: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    manifest_keys = manifest_interest_keys(source_manifest)
    if not manifest_keys:
        return df

    result = df.copy()
    interes = result.get("INTERES_AL_BANCO", pd.Series(index=result.index, dtype=object)).map(norm_si_no)
    emisor = result.get("EMISOR", pd.Series(index=result.index, dtype=object)).astype(str).str.strip().str.upper()
    descripcion = result.get("DESCRIPCION", pd.Series(index=result.index, dtype=object)).astype(str)
    numero_norm = result.get("NUMERO", pd.Series(index=result.index, dtype=object)).map(norm_numero)
    numero_key = result.get("NUMERO", pd.Series(index=result.index, dtype=object)).map(numero_match_key)
    obs = result.get("OBS_IDENTIDAD", pd.Series(index=result.index, dtype=object)).astype(str)

    has_manifest_support = numero_norm.isin(manifest_keys) | numero_key.isin(manifest_keys)
    noisy_desc = descripcion.str.contains(
        r"^Que,|^RESOLUCI(?:ÓN|ON)\s+MINISTERIAL\s|CONTEXTO_GENERAL|N° \.|EL CONCEJO MUNICIPAL|Artículo|Articulo|Informe N°",
        case=False,
        na=False,
        regex=True,
    )
    weak_emisor = emisor.isin({"", "NO DISPONIBLE", "NAN", "PODER EJECUTIVO"})
    rescued = obs.str.contains("manifiesto de el peruano", case=False, na=False)

    drop_mask = interes.eq("SI") & ~has_manifest_support & weak_emisor & noisy_desc & ~rescued
    if drop_mask.any():
        result.loc[drop_mask, "C_NORMATIVO"] = "NO"
        result.loc[drop_mask, "INTERES_BANCO"] = "NO"
        result.loc[drop_mask, "INTERES_AL_BANCO"] = "NO"
        result.loc[drop_mask, "NIVEL_IMPACTO"] = "NO APLICA"
        result.loc[drop_mask, "JUSTIFICACION"] = "Descartada en reporte por OCR inconsistente sin respaldo suficiente en el manifiesto oficial."
        result.loc[drop_mask, "IMPORTANCIA"] = "No"

    generic_exec_mask = (
        interes.eq("SI")
        & emisor.eq("PODER EJECUTIVO")
        & descripcion.str.contains(r"^RESOLUCI(?:ÓN|ON)\s+MINISTERIAL", case=False, na=False, regex=True)
        & ~has_manifest_support
    )
    if generic_exec_mask.any():
        result.loc[generic_exec_mask, "C_NORMATIVO"] = "NO"
        result.loc[generic_exec_mask, "INTERES_BANCO"] = "NO"
        result.loc[generic_exec_mask, "INTERES_AL_BANCO"] = "NO"
        result.loc[generic_exec_mask, "NIVEL_IMPACTO"] = "NO APLICA"
        result.loc[generic_exec_mask, "JUSTIFICACION"] = "Descartada en reporte por referencia genérica del Poder Ejecutivo sin sustento suficiente en el manifiesto oficial."
        result.loc[generic_exec_mask, "IMPORTANCIA"] = "No"

    return result


def augment_with_source_manifest(df: pd.DataFrame, source_manifest: pd.DataFrame, run_date: date) -> tuple[pd.DataFrame, int, int]:
    if source_manifest.empty:
        return df.copy(), 0, 0

    result = df.copy()
    added = 0
    updated = 0
    normalized_numeros = set(result.get("NUMERO", pd.Series(dtype=str)).map(norm_numero)) if not result.empty else set()

    for _, manifest_row in source_manifest.iterrows():
        title = manifest_row.get("TITULO_FUENTE", "")
        classification = classify_manifest_publication(title)
        if not classification:
            continue

        numero = classification["NUMERO"]
        numero_key = norm_numero(numero)
        if not numero_key:
            continue

        mask = result["NUMERO"].map(norm_numero).eq(numero_key) if not result.empty and "NUMERO" in result.columns else pd.Series(False, index=result.index)
        if not mask.any() and not result.empty and "NUMERO" in result.columns:
            manifest_match_key = numero_match_key(numero)
            if manifest_match_key:
                mask = result["NUMERO"].map(numero_match_key).eq(manifest_match_key)

        if mask.any():
            idx = result[mask].index[0]
            existing_desc = str(result.at[idx, "DESCRIPCION"] or "")
            existing_emisor = str(result.at[idx, "EMISOR"] or "").strip().upper()
            existing_numero = str(result.at[idx, "NUMERO"] or "")
            degraded_existing = (
                existing_emisor in {"", "NO DISPONIBLE", "NAN", "PODER EJECUTIVO"}
                or "CONTEXTO_GENERAL" in existing_desc.upper()
                or existing_desc.upper().startswith("QUE,")
                or "INFORME N°" in existing_desc.upper()
                or norm_numero(existing_numero) != norm_numero(classification["NUMERO"])
            )
            if norm_si_no(result.at[idx, "INTERES_AL_BANCO"]) != "SI" or norm_nivel(result.at[idx, "NIVEL_IMPACTO"]) == "NO APLICA" or degraded_existing:
                result.at[idx, "NUMERO"] = classification["NUMERO"]
                result.at[idx, "IDNORMA"] = classification["NUMERO"]
                result.at[idx, "TIPO_NORMA"] = classification["TIPO_NORMA"]
                result.at[idx, "DESCRIPCION"] = classification["DESCRIPCION"]
                result.at[idx, "EMISOR"] = classification["EMISOR"]
                result.at[idx, "C_NORMATIVO"] = "SI"
                result.at[idx, "INTERES_BANCO"] = "SI"
                result.at[idx, "INTERES_AL_BANCO"] = "SI"
                result.at[idx, "NIVEL_IMPACTO"] = classification["NIVEL_IMPACTO"]
                result.at[idx, "JUSTIFICACION"] = classification["JUSTIFICACION"]
                result.at[idx, "IMPORTANCIA"] = classification["IMPORTANCIA"]
                result.at[idx, "IDENTIDAD_CONFIABLE"] = "SI"
                result.at[idx, "OBS_IDENTIDAD"] = "Actualizada desde el manifiesto de El Peruano"
                updated += 1
            continue

        row = {
            "FECHA_EJECUCION": run_date.strftime("%Y-%m-%d"),
            "FECHA": run_date.strftime("%d/%m/%Y"),
            "FECHA_EMISION": run_date.strftime("%d/%m/%Y"),
            "FECHA_PUBLICACION": run_date.strftime("%d/%m/%Y"),
            "IDNORMA": numero,
            "TIPO_NORMA": classification["TIPO_NORMA"],
            "NUMERO": numero,
            "DESCRIPCION": classification["DESCRIPCION"],
            "EMISOR": classification["EMISOR"],
            "REGULADOR": "NO DISPONIBLE",
            "ESTADO": "NO DISPONIBLE",
            "NRO_BOLETIN": "NO DISPONIBLE",
            "C_NORMATIVO": "SI",
            "INTERES_BANCO": "SI",
            "INTERES_AL_BANCO": "SI",
            "NIVEL_IMPACTO": classification["NIVEL_IMPACTO"],
            "JUSTIFICACION": classification["JUSTIFICACION"],
            "IMPORTANCIA": classification["IMPORTANCIA"],
            "REFERENCIA_HUMANA": "NO",
            "IDENTIDAD_CONFIABLE": "SI",
            "OBS_IDENTIDAD": "Recuperada desde el manifiesto de El Peruano",
            "PDF_S3_URI": "NO DISPONIBLE",
            "PDF_URL": "NO DISPONIBLE",
            "PRECISION_DIA": "NO DISPONIBLE",
            "CALIFICACION_HUMANA": "NO DISPONIBLE",
            "DESCRIPCION_HUMANA": "NO DISPONIBLE",
        }
        result = pd.concat([result, pd.DataFrame([row])], ignore_index=True)
        normalized_numeros.add(numero_key)
        added += 1

    return result, added, updated


def dedupe_report_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "NUMERO" not in df.columns:
        return df

    result = df.copy()
    result["_NUMERO_KEY"] = result["NUMERO"].map(numero_match_key)
    result["_INTERES_SCORE"] = result.get("INTERES_AL_BANCO", pd.Series(index=result.index, dtype=object)).map(norm_si_no).eq("SI").astype(int)
    result["_IMPACTO_SCORE"] = result.get("NIVEL_IMPACTO", pd.Series(index=result.index, dtype=object)).map(norm_nivel).map(
        {"ALTO": 4, "MEDIO": 3, "BAJO": 2, "INFORMATIVA": 1, "NO APLICA": 0}
    ).fillna(0)
    result["_IDENTIDAD_SCORE"] = result.get("IDENTIDAD_CONFIABLE", pd.Series(index=result.index, dtype=object)).astype(str).str.upper().eq("SI").astype(int)
    result["_OBS_SCORE"] = result.get("OBS_IDENTIDAD", pd.Series(index=result.index, dtype=object)).astype(str).str.contains("manifiesto de el peruano", case=False, na=False).astype(int)
    result["_DESC_LEN"] = result.get("DESCRIPCION", pd.Series(index=result.index, dtype=object)).astype(str).str.len()
    result = result.sort_values(
        by=["_NUMERO_KEY", "_INTERES_SCORE", "_IMPACTO_SCORE", "_IDENTIDAD_SCORE", "_OBS_SCORE", "_DESC_LEN"],
        ascending=[True, False, False, False, False, False],
        kind="stable",
    )
    deduped = result.drop_duplicates(subset=["_NUMERO_KEY"], keep="first").copy()
    return deduped.drop(columns=["_NUMERO_KEY", "_INTERES_SCORE", "_IMPACTO_SCORE", "_IDENTIDAD_SCORE", "_OBS_SCORE", "_DESC_LEN"], errors="ignore")


def load_report_source_manifest(report_date: date) -> pd.DataFrame:
    xlsx_path = REPORT_DIR / f"lexia_diario_{report_date:%Y%m%d}.xlsx"
    if not xlsx_path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(xlsx_path, sheet_name="publicadas_fuente")
    except Exception as exc:
        print(f"⚠️ No se pudo leer publicadas_fuente de {xlsx_path.name}: {exc}")
        return pd.DataFrame()


def detect_missing_publications(current_manifest: pd.DataFrame, previous_manifest: pd.DataFrame) -> pd.DataFrame:
    if current_manifest.empty:
        return pd.DataFrame(columns=["ORDEN", "FECHA_PUBLICACION", "TITULO_FUENTE"])
    if previous_manifest.empty or "TITULO_FUENTE" not in previous_manifest.columns:
        missing = current_manifest.copy()
        missing["MOTIVO_BACKFILL"] = "Sin manifiesto previo guardado"
        return missing

    previous_keys = set(previous_manifest["TITULO_FUENTE"].map(normalize_manifest_title))
    current = current_manifest.copy()
    current["MANIFEST_KEY"] = current["TITULO_FUENTE"].map(normalize_manifest_title)
    missing = current[~current["MANIFEST_KEY"].isin(previous_keys)].copy()
    if missing.empty:
        return pd.DataFrame(columns=["ORDEN", "FECHA_PUBLICACION", "TITULO_FUENTE", "MOTIVO_BACKFILL"])
    missing["MOTIVO_BACKFILL"] = "Publicacion detectada despues del reporte previo"
    return missing.drop(columns=["MANIFEST_KEY"], errors="ignore")


def backfill_trace_path(run_date: date) -> Path:
    return REPORT_DIR / f"extraordinarias_prev_{run_date:%Y%m%d}.csv"


def load_backfill_trace(run_date: date) -> pd.DataFrame:
    path = backfill_trace_path(run_date)
    if not path.exists():
        return pd.DataFrame(columns=["ORDEN", "FECHA_PUBLICACION", "TITULO_FUENTE", "MOTIVO_BACKFILL"])
    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"⚠️ No se pudo leer trazabilidad de extraordinarias {path.name}: {exc}")
        return pd.DataFrame(columns=["ORDEN", "FECHA_PUBLICACION", "TITULO_FUENTE", "MOTIVO_BACKFILL"])


def save_backfill_trace(run_date: date, missing: pd.DataFrame) -> None:
    if missing.empty:
        return
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    missing.to_csv(backfill_trace_path(run_date), index=False, encoding="utf-8-sig")


def backfill_previous_day_if_needed(
    args: argparse.Namespace,
    run_date: date,
    reference_file: Path,
) -> dict[str, object]:
    previous_date = run_date - timedelta(days=1)
    current_manifest = fetch_source_manifest(previous_date)
    previous_manifest = load_report_source_manifest(previous_date)
    missing = detect_missing_publications(current_manifest, previous_manifest)
    info: dict[str, object] = {
        "date": previous_date.strftime("%Y-%m-%d"),
        "checked": True,
        "rerun": False,
        "current_count": len(current_manifest),
        "previous_count": len(previous_manifest),
        "missing_count": len(missing),
        "missing": missing,
        "display_missing": missing,
        "display_missing_count": len(missing),
        "trace_loaded": False,
        "reason": "",
    }
    if len(missing):
        save_backfill_trace(run_date, missing)
    else:
        trace = load_backfill_trace(run_date)
        if not trace.empty:
            info["display_missing"] = trace
            info["display_missing_count"] = len(trace)
            info["trace_loaded"] = True

    previous_csv = Path(args.output_dir) / f"normas_{previous_date:%Y-%m-%d}.csv"
    should_rerun = bool(len(missing)) or not previous_csv.exists()
    if not should_rerun:
        info["reason"] = "Sin publicaciones nuevas del dia anterior."
        print(
            f"ℹ️ Backfill {previous_date:%Y-%m-%d}: sin extraordinarias nuevas "
            f"({len(current_manifest)} publicadas)."
        )
        return info

    if args.no_download:
        info["reason"] = "Se detectaron publicaciones nuevas, pero --no-download impide reprocesar desde fuente."
        print(f"⚠️ Backfill {previous_date:%Y-%m-%d}: {info['reason']}")
        return info

    print(
        f"🔁 Backfill {previous_date:%Y-%m-%d}: "
        f"{len(missing)} publicaciones nuevas/no incluidas. Reprocesando dia anterior..."
    )
    backfill_args = clone_args(args, force=True, skip_pipeline=False, reference_file=str(reference_file))
    run_pipeline(backfill_args, previous_date, previous_csv)
    build_reports(previous_csv, reference_file, previous_date, backfill_info=None)
    info["rerun"] = True
    info["reason"] = "Dia anterior reprocesado antes de armar la comparativa."
    return info


def build_reports(
    csv_path: Path,
    reference_file: Path,
    run_date: date,
    backfill_info: dict[str, object] | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame()
    df, excluded_same_emission = filter_report_rows(raw_df, run_date)
    source_manifest = fetch_source_manifest(run_date)
    df, manifest_added, manifest_updated = augment_with_source_manifest(df, source_manifest, run_date)
    if not df.empty:
        existing_obs = df.get("OBS_IDENTIDAD", pd.Series(index=df.index, dtype=object)).astype(str)
        identity = df.apply(_identity_review, axis=1, result_type="expand")
        df["IDENTIDAD_CONFIABLE"] = identity["IDENTIDAD_CONFIABLE"].values
        df["OBS_IDENTIDAD"] = identity["OBS_IDENTIDAD"].values
        rescued_mask = existing_obs.str.contains("manifiesto de el peruano", case=False, na=False)
        df.loc[rescued_mask, "IDENTIDAD_CONFIABLE"] = "SI"
        df.loc[rescued_mask, "OBS_IDENTIDAD"] = existing_obs[rescued_mask].values
    df = prune_low_confidence_interest_rows(df)
    df = prune_interest_without_manifest_support(df, source_manifest)
    df = dedupe_report_rows(df)

    comparison_date = run_date - timedelta(days=1)
    comparison_csv = csv_path.parent / f"normas_{comparison_date:%Y-%m-%d}.csv"
    comparison_df = pd.read_csv(comparison_csv) if comparison_csv.exists() else pd.DataFrame()
    comparison_human = load_human_for_date(reference_file, comparison_date)
    metrics = daily_metrics(comparison_df, comparison_human, comparison_date)
    details = comparison_details(comparison_df, comparison_human, comparison_date)
    reference_updated_at = (
        datetime.fromtimestamp(reference_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if reference_file.exists() else "NO DISPONIBLE"
    )

    if not df.empty:
        si = df[df["INTERES_AL_BANCO"].map(norm_si_no).eq("SI")].copy()
        if "REFERENCIA_HUMANA" in si.columns:
            si["REFERENCIA_ANALISTA"] = si["REFERENCIA_HUMANA"]
        no_count = int(df["INTERES_AL_BANCO"].map(norm_si_no).eq("NO").sum())
        levels = si["NIVEL_IMPACTO"].map(norm_nivel).value_counts().to_dict()
    else:
        si = pd.DataFrame()
        no_count = 0
        levels = {}
    backfill_info = backfill_info or {}
    backfill_missing = backfill_info.get("display_missing")
    if not isinstance(backfill_missing, pd.DataFrame):
        backfill_missing = pd.DataFrame(columns=["ORDEN", "FECHA_PUBLICACION", "TITULO_FUENTE", "MOTIVO_BACKFILL"])
    backfill_date = str(backfill_info.get("date") or comparison_date.strftime("%Y-%m-%d"))
    display_missing_count = int(backfill_info.get("display_missing_count", len(backfill_missing)) or 0)
    trace_note = ""
    if backfill_info.get("trace_loaded"):
        trace_note = " Lista conservada desde la ultima deteccion para mantener trazabilidad."
    backfill_status = (
        f"Dia revisado: {escape(backfill_date)} | "
        f"Publicadas actuales: {backfill_info.get('current_count', 'N/A')} | "
        f"Publicadas en reporte previo: {backfill_info.get('previous_count', 'N/A')} | "
        f"Nuevas/no incluidas en esta corrida: {backfill_info.get('missing_count', 0)} | "
        f"Mostradas por trazabilidad: {display_missing_count} | "
        f"Reprocesado: {'SI' if backfill_info.get('rerun') else 'NO'}"
    )

    html_path = REPORT_DIR / f"lexia_diario_{run_date:%Y%m%d}.html"
    xlsx_path = REPORT_DIR / f"lexia_diario_{run_date:%Y%m%d}.xlsx"
    report_csv_path = REPORT_DIR / f"normas_reporte_{run_date:%Y%m%d}.csv"

    css = """
    <style>
      body{font-family:Arial,sans-serif;color:#1d1d1d}
      .kpis{display:flex;gap:12px;flex-wrap:wrap}
      .kpi{border:1px solid #d9e2ef;border-left:6px solid #00BE50;border-radius:10px;padding:10px 14px;min-width:150px}
      .kpi b{font-size:24px;color:#1F4592}
      table{border-collapse:collapse;width:100%;font-size:12px}
      th,td{border:1px solid #d9e2ef;padding:6px;text-align:left;vertical-align:top}
      th{background:#eef3fb;color:#1F4592}
    </style>
    """
    body = f"""
    <html><head><meta charset="utf-8">{css}</head><body>
      <h1>LexIA Normativo Diario - {run_date:%Y-%m-%d}</h1>
      <div class="kpis">
        <div class="kpi">Publicadas fuente<br><b>{len(source_manifest) if not source_manifest.empty else 'N/A'}</b></div>
        <div class="kpi">Procesadas IA<br><b>{len(df)}</b></div>
        <div class="kpi">Interés banco<br><b>{len(si)}</b></div>
        <div class="kpi">No interés<br><b>{no_count}</b></div>
        <div class="kpi">Referencia analista<br><b>{int(df.get('REFERENCIA_HUMANA', pd.Series(dtype=str)).astype(str).str.upper().eq('SI').sum()) if not df.empty else 0}</b></div>
      </div>
      <h2>Resumen operativo</h2>
      <p>El Excel del analista se usa como referencia historica para detectar similitudes y reforzar la seleccion de candidatas al LLM. Copia local consultada: {escape(reference_updated_at)}. Las normas listadas corresponden a publicaciones del dia {run_date:%Y-%m-%d}. Se excluyeron {excluded_same_emission} filas parseadas porque FECHA o FECHA_PUBLICACION no coincidian con el dia procesado. FECHA_EMISION se informa como dato, pero no se usa para excluir publicaciones. Las posibles inconsistencias de nombre o numero se marcan en OBS_IDENTIDAD, sin ocultar la norma.</p>
      <p><b>Publicadas fuente</b> es el total de publicaciones detectadas en El Peruano para el dia. <b>Procesadas IA</b> es el total de normas que el pipeline pudo convertir en registros normativos validos para clasificar, con numero y fecha de publicacion consistentes. La diferencia suele corresponder a paginas generales, textos sin numero normativo estable, duplicados o bloques que se descargan como PDF pero no forman una norma individual clasificable.</p>
      <p>Rescate desde manifiesto de fuente: añadidas {manifest_added} | actualizadas {manifest_updated}.</p>
      <h2>Publicadas en El Peruano</h2>
      {html_table(source_manifest, ['ORDEN','FECHA_PUBLICACION','TITULO_FUENTE'], max_rows=60)}
      <h2>Revision de extraordinarias del dia anterior</h2>
      <p>{backfill_status}. {escape(str(backfill_info.get('reason') or ''))}{escape(trace_note)}</p>
      {html_table(backfill_missing, ['ORDEN','FECHA_PUBLICACION','TITULO_FUENTE','MOTIVO_BACKFILL'], max_rows=30)}
      <h2>Niveles de impacto detectados</h2>
      <p>{escape(str(levels))}</p>
      <h2>Normas de interés para el banco</h2>
      {html_table(si, ['NUMERO','TIPO_NORMA','NIVEL_IMPACTO','REFERENCIA_ANALISTA','IDENTIDAD_CONFIABLE','OBS_IDENTIDAD','DESCRIPCION','JUSTIFICACION'])}
      <h2>Normas revisadas del día</h2>
      {html_table(df, ['NUMERO','TIPO_NORMA','INTERES_AL_BANCO','NIVEL_IMPACTO','IDENTIDAD_CONFIABLE','OBS_IDENTIDAD','DESCRIPCION'], max_rows=50)}
      <h2>Comparativa con Excel analista</h2>
      <p>La comparativa se calcula con el dia anterior ({comparison_date:%Y-%m-%d}), porque la validacion del analista llega con rezago. CSV IA usado para contraste: {escape(comparison_csv.name if comparison_csv.exists() else 'no disponible')}.</p>
      <p>{'Comparativa pendiente: el Excel aun no tiene filas del analista para esa fecha; no se calculan TP, FP, FN ni metricas.' if not metrics['comparison_available'] else f"Filas analista: {metrics['analyst_rows']} | Analista SI: {metrics['analyst_count']} | Alertas IA SI: {metrics['pred_count']} | TP: {metrics['tp']} | FP: {metrics['fp']} | FN: {metrics['fn']} | Recall: {pct(metrics['recall'])} | Precision: {pct(metrics['precision'])}"}</p>
      <h3>Aciertos</h3>
      {html_table(details['aciertos'], ['NUMERO','TIPO_NORMA','NIVEL_IA','NIVEL_ANALISTA','DESCRIPCION_ANALISTA','DESCRIPCION_IA'], max_rows=20)}
      <h3>Alertas IA no marcadas por analista</h3>
      {html_table(details['falsos_positivos'], ['NUMERO','TIPO_NORMA','NIVEL_IA','DESCRIPCION_IA','JUSTIFICACION_IA'], max_rows=20)}
      <h3>Normas del analista no detectadas por IA</h3>
      {html_table(details['falsos_negativos'], ['NUMERO','TIPO_NORMA','NIVEL_ANALISTA','DESCRIPCION_ANALISTA'], max_rows=20)}
    </body></html>
    """
    html_path.write_text(body, encoding="utf-8")
    df.to_csv(report_csv_path, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(xlsx_path) as writer:
        df.to_excel(writer, sheet_name="normas_dia", index=False)
        source_manifest.to_excel(writer, sheet_name="publicadas_fuente", index=False)
        backfill_missing.to_excel(writer, sheet_name="extraordinarias_prev", index=False)
        si.to_excel(writer, sheet_name="interes_banco", index=False)
        raw_df.to_excel(writer, sheet_name="normas_dia_raw", index=False)
        comparison_human.to_excel(writer, sheet_name="referencia_analista_prev", index=False)
        comparison_df.to_excel(writer, sheet_name="ia_prev", index=False)
        details["aciertos"].to_excel(writer, sheet_name="aciertos", index=False)
        details["falsos_positivos"].to_excel(writer, sheet_name="falsos_positivos", index=False)
        details["falsos_negativos"].to_excel(writer, sheet_name="falsos_negativos", index=False)
        details["retroalimentacion"].to_excel(writer, sheet_name="retroalimentacion", index=False)
        pd.DataFrame([metrics]).to_excel(writer, sheet_name="metricas_dia", index=False)

    metrics.update({
        "total_rows": len(df),
        "source_rows": len(source_manifest) if not source_manifest.empty else None,
        "raw_total_rows": len(raw_df),
        "interest_rows": len(si),
        "no_rows": no_count,
        "levels": levels,
        "manifest_added": manifest_added,
        "manifest_updated": manifest_updated,
        "comparison_date": comparison_date.strftime("%Y-%m-%d"),
        "reference_updated_at": reference_updated_at,
        "excluded_same_emission": excluded_same_emission,
        "backfill_previous_date": backfill_date,
        "backfill_missing_count": int(backfill_info.get("missing_count", 0) or 0),
        "backfill_display_count": display_missing_count,
        "backfill_rerun": bool(backfill_info.get("rerun")),
    })
    return html_path, xlsx_path, report_csv_path, metrics


def add_attachment(msg: EmailMessage, path: Path, subtype: str) -> None:
    if path.exists():
        msg.add_attachment(path.read_bytes(), maintype="application", subtype=subtype, filename=path.name)


def send_email(run_date: date, html_path: Path, xlsx_path: Path, csv_path: Path, metrics: dict[str, object]) -> None:
    to_email = os.getenv("REPORT_EMAIL_TO")
    if not to_email:
        print("REPORT_EMAIL_TO no configurado; no se envía email.")
        return
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", smtp_user)
    if not smtp_user or not smtp_password or not from_email:
        raise RuntimeError("Faltan SMTP_USER, SMTP_PASSWORD o SMTP_FROM/SMTP_USER")

    msg = EmailMessage()
    msg["Subject"] = f"LexIA Normativo Diario - {run_date:%Y-%m-%d}"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        f"Reporte LexIA {run_date:%Y-%m-%d}. "
        f"Publicadas fuente: {metrics.get('source_rows') or 'N/A'} | "
        f"Procesadas IA: {metrics['total_rows']} | Interés banco: {metrics['interest_rows']}"
    )
    msg.add_alternative(html_path.read_text(encoding="utf-8"), subtype="html")
    add_attachment(msg, xlsx_path, "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    add_attachment(msg, csv_path, "octet-stream")

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)
    print(f"Email enviado a: {to_email}")


def main() -> int:
    load_env_file(BASE_DIR / "config" / ".env_email")
    load_env_file(BASE_DIR / "config" / "reference.env")
    load_env_file(BASE_DIR / "config" / "github.env")
    load_env_file(BASE_DIR / "config" / "groq.env")

    args = parse_args()
    run_date = target_date(args.date)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    reference_file = Path(args.reference_file)

    if not args.no_sync_reference:
        sync_reference_from_drive(reference_file, args.reference_drive_url)

    backfill_info = None
    if not args.no_backfill_previous:
        backfill_info = backfill_previous_day_if_needed(args, run_date, reference_file)

    csv_path = Path(args.output_dir) / f"normas_{run_date:%Y-%m-%d}.csv"
    if args.skip_pipeline:
        if not csv_path.exists():
            raise FileNotFoundError(f"No existe el CSV para --skip-pipeline: {csv_path}")
        print(f"Usando CSV existente: {csv_path}", flush=True)
    else:
        run_pipeline(args, run_date, csv_path)
    html_path, xlsx_path, report_csv_path, metrics = build_reports(
        csv_path,
        reference_file,
        run_date,
        backfill_info=backfill_info,
    )
    print(f"Reporte HTML: {html_path}")
    print(f"Reporte Excel: {xlsx_path}")
    print(f"CSV reporte: {report_csv_path}")
    print(f"Métricas: {metrics}")
    if not args.no_email:
        send_email(run_date, html_path, xlsx_path, report_csv_path, metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
