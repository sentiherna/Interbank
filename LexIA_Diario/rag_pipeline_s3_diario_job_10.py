import argparse
import io
import json
import os
# --- AWS credentials auto-loader ---
import re
import sys

# --- AWS Credentials Loader ---
import os
def load_aws_credentials_from_sh(sh_path):
    if not os.path.exists(sh_path):
        print(f"[ERROR] Archivo de credenciales no encontrado: {sh_path}")
        return False
    with open(sh_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().replace('export ', '')
                value = value.strip().strip('"').strip("'")
                if key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
                    os.environ[key] = value
    # Solo mostrar debug en modo no-local
    if os.environ.get('STORAGE_MODE', '').lower() != 'local':
        print('[DEBUG] AWS_ACCESS_KEY_ID:', os.environ.get('AWS_ACCESS_KEY_ID')[:20] + '...' if os.environ.get('AWS_ACCESS_KEY_ID') else 'NOT SET')
        print('[DEBUG] AWS_SECRET_ACCESS_KEY: [REDACTED]')
        print('[DEBUG] AWS_SESSION_TOKEN: [REDACTED]')
    return True

# Cargar credenciales antes de cualquier import de boto3
aws_cred_path = os.path.join(os.path.dirname(__file__), 'credentials.sh')
if not load_aws_credentials_from_sh(aws_cred_path):
    print('[ERROR] No se pudieron cargar las credenciales AWS. Abortando.')
    sys.exit(1)

# Solo mostrar debug en modo no-local
if os.environ.get('STORAGE_MODE', '').lower() != 'local':
    print('DEBUG AWS_ACCESS_KEY_ID:', os.environ.get('AWS_ACCESS_KEY_ID')[:20] + '...' if os.environ.get('AWS_ACCESS_KEY_ID') else 'NOT SET')
    print('DEBUG AWS_SECRET_ACCESS_KEY: [REDACTED]')
    print('DEBUG AWS_SESSION_TOKEN: [REDACTED]')
cred_path = os.path.expanduser(r'C:/Users/b46637/OneDrive - Interbank/conexion_aws/athena_conection_test/credentials.sh')
if os.path.exists(cred_path):
    with open(cred_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'\s*(AWS_[A-Z_]+)\s*=\s*"([^"]+)"', line)
            if m:
                os.environ[m.group(1)] = m.group(2)
import re
import ssl
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin

# === Desactivar verificación SSL (proxy corporativo) ===
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

import httpx
# Monkey-patch httpx para ignorar SSL
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs.setdefault("verify", False)
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

# Local storage support
try:
    from lexia_local import get_s3_client, is_local_mode
    LOCAL_MODE = is_local_mode()
except ImportError:
    LOCAL_MODE = False
    def get_s3_client():
        import boto3
        return boto3.client('s3')

if not LOCAL_MODE:
    import boto3
import httpx
# import faiss  # Optional - only needed for embeddings
import numpy as np
import pandas as pd
import pdfplumber
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup, Comment
from dotenv import dotenv_values
try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
except Exception:
    CrossEncoder = None
    SentenceTransformer = None
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="RAG normativo diario (versión job _7 híbrida: cobertura completa + LLM acotado)")
    parser.add_argument("--analysis-date", default=datetime.today().strftime("%Y-%m-%d"), help="Fecha objetivo YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Fecha fin YYYY-MM-DD (para rango de días). Si no se especifica, solo procesa analysis-date")
    parser.add_argument("--bucket", default="ibk-discovery-comercial-us-east-1-654654352211-data")
    parser.add_argument("--pdf-prefix", default="discovery/comercial/sanherna/PLAFT/GenIA/Normativo/pdf/")
    parser.add_argument("--chunk-prefix", default="discovery/comercial/sanherna/PLAFT/GenIA/Normativo/chunk/")
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--max-normas", type=int, default=50)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--download-from-source", action="store_true", help="Descarga PDFs desde El Peruano antes de procesar")
    parser.add_argument("--embed-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument(
        "--enable-semantic-prioritization",
        action="store_true",
        help="Usa embeddings + cross-encoder contra el historico del analista para priorizar normas candidatas al LLM.",
    )
    parser.add_argument(
        "--semantic-embed-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modelo SentenceTransformer para semantic search contra normas historicas.",
    )
    parser.add_argument(
        "--semantic-cross-model",
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        help="Modelo CrossEncoder para reranking de candidatas semanticas.",
    )
    parser.add_argument(
        "--semantic-top-k",
        type=int,
        default=12,
        help="Cantidad de normas nuevas consideradas por busqueda semantica antes del reranking.",
    )
    parser.add_argument(
        "--semantic-min-score",
        type=float,
        default=0.45,
        help="Score minimo del cross-encoder para subir una norma a candidatas LLM.",
    )
    parser.add_argument("--groq-model", default="llama-3.3-70b-versatile")
    parser.add_argument("--llm-backend", default="copilot", choices=["copilot", "groq"],
                        help="Backend LLM: 'copilot' (GitHub Models) o 'groq'")
    parser.add_argument("--copilot-model", default="gpt-4o-mini",
                        help="Modelo para GitHub Copilot API (gpt-5-mini, gpt-5, gpt-4o, gpt-4o-mini, etc.)")
    parser.add_argument(
        "--enable-llm-audit",
        action="store_true",
        help="[Deprecated] Se acepta por compatibilidad pero no se usa en el job _6",
    )
    parser.add_argument(
        "--llm-audit-max-candidates",
        type=int,
        default=3,
        help="[Deprecated] Solo para compatibilidad; este valor se ignora.",
    )
    parser.add_argument(
        "--enable-llm-class-audit",
        action="store_true",
        help="[Deprecated] Se acepta por compatibilidad pero se ignora.",
    )
    parser.add_argument(
        "--llm-class-max-normas",
        type=int,
        default=50,
        help="[Deprecated] Solo compatibilidad; no se usa en este job.",
    )
    parser.add_argument("--output-file", default=None, help="Nombre del archivo CSV de salida (opcional)")
    parser.add_argument(
        "--llm-max-contexts",
        type=int,
        default=3,
        help="Máximo de normas candidatas que se envían al LLM por día. El resto se conserva con clasificación local.",
    )
    parser.add_argument(
        "--llm-min-score",
        type=int,
        default=2,
        help="Score heurístico mínimo para enviar una norma al LLM.",
    )
    parser.add_argument(
        "--human-reference-file",
        default="Comparativo de identificación de normas VF (1).xlsx",
        help="Excel de referencia humana para calibrar la clasificación de interés al banco.",
    )
    return parser.parse_args()


def _clean_secret(value):
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'")


def resolve_groq_api_key():
    env_value = _clean_secret(os.getenv("GROQ_API_KEY", ""))
    if env_value:
        if env_value.startswith("hf_"):
            raise EnvironmentError(
                "GROQ_API_KEY parece token de Hugging Face (hf_). Usa una clave de Groq (gsk_)."
            )
        return env_value

    script_dir = Path(__file__).resolve().parent
    candidate_files = [
        script_dir / "groq.env",
        script_dir / ".env",
        Path.cwd() / "groq.env",
        Path.cwd() / ".env",
    ]

    for env_file in candidate_files:
        if not env_file.exists():
            continue

        values = dotenv_values(env_file)
        file_value = _clean_secret(values.get("GROQ_API_KEY", ""))
        if not file_value:
            continue

        if file_value.startswith("hf_"):
            raise EnvironmentError(
                f"En {env_file} la variable GROQ_API_KEY tiene formato hf_. Debe ser una clave Groq (gsk_)."
            )

        os.environ["GROQ_API_KEY"] = file_value
        print(f"✅ GROQ_API_KEY cargada desde: {env_file}")
        return file_value

    raise EnvironmentError(
        "GROQ_API_KEY no está configurada. Define la variable o crea groq.env/.env con GROQ_API_KEY=gsk_..."
    )


def resolve_github_token():
    """Busca GITHUB_TOKEN en variables de entorno o en archivos .env / github.env"""
    env_value = os.getenv("GITHUB_TOKEN", "")
    if env_value:
        print("✅ GITHUB_TOKEN cargada desde variable de entorno")
        return env_value

    script_dir = Path(__file__).resolve().parent
    env_files = [
        script_dir / "github.env",
        script_dir / ".env",
        Path.cwd() / "github.env",
        Path.cwd() / ".env",
    ]
    for env_file in env_files:
        if not env_file.exists():
            continue
        values = dotenv_values(env_file)
        file_value = values.get("GITHUB_TOKEN", "")
        if file_value:
            os.environ["GITHUB_TOKEN"] = file_value
            print(f"✅ GITHUB_TOKEN cargada desde: {env_file}")
            return file_value

    raise EnvironmentError(
        "GITHUB_TOKEN no está configurado. Define la variable o crea github.env/.env con GITHUB_TOKEN=ghp_..."
    )


def resolve_llm_config(backend):
    """Resuelve API key y endpoint según el backend seleccionado."""
    if backend == "copilot":
        api_key = resolve_github_token()
        endpoint = "https://models.inference.ai.azure.com/chat/completions"
        return api_key, endpoint
    else:
        api_key = resolve_groq_api_key()
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        return api_key, endpoint


def upload_pdf_to_s3(s3, bucket, pdf_prefix, file_bytes, filename):
    s3.put_object(Bucket=bucket, Key=f"{pdf_prefix}{filename}", Body=file_bytes)


def pdf_exists_in_s3(s3, bucket, pdf_prefix, filename):
    try:
        s3.head_object(Bucket=bucket, Key=f"{pdf_prefix}{filename}")
        return True
    except Exception:
        return False


def list_pdfs_by_date_range(s3, bucket, pdf_prefix, start_date, end_date):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=pdf_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.split("/")[-1]
            if not filename.endswith(".pdf"):
                continue
            try:
                file_date = datetime.strptime(filename[:10], "%Y-%m-%d")
            except Exception:
                continue
            if start_date <= file_date <= end_date:
                keys.append(key)
    return keys


def get_pdf_from_s3(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def upload_chunks_to_s3(s3, bucket, chunk_prefix, chunks, filename):
    s3.put_object(
        Bucket=bucket,
        Key=f"{chunk_prefix}{filename}.json",
        Body=json.dumps(chunks),
    )


def load_chunks_from_s3(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())


def _resolve_pdf_url_from_dispositivo(dispositivo_url):
    try:
        response = requests.get(
            dispositivo_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")
    if not next_data or not next_data.string:
        return None

    data = json.loads(next_data.string)
    dispositivo = data.get("props", {}).get("pageProps", {}).get("dispositivo", {})
    return dispositivo.get("urlPDF")


def _extract_downloads_from_article(article):
    downloads = []

    for boton in article.select("input.buttonaction.dataUrl"):
        pdf_url = boton.get("data-url")
        file_id = boton.get("data-id")
        if pdf_url and file_id:
            downloads.append((file_id, pdf_url))

    for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
        if "dataUrl" not in comment or "data-url" not in comment:
            continue
        file_id_match = re.search(r'data-id="([^"]+)"', comment)
        pdf_url_match = re.search(r'data-url="([^"]+)"', comment)
        if file_id_match and pdf_url_match:
            downloads.append((file_id_match.group(1), pdf_url_match.group(1)))

    if downloads:
        unique_downloads = []
        seen = set()
        for file_id, pdf_url in downloads:
            if file_id in seen:
                continue
            seen.add(file_id)
            unique_downloads.append((file_id, pdf_url))
        return unique_downloads

    for link in article.select("a.buttonaction[href], h5 a[href]"):
        href = link.get("href")
        text = link.get_text(" ", strip=True).lower()
        if not href or "/dispositivo/" not in href:
            continue
        if "edición" in text or "edicion" in text:
            continue

        dispositivo_url = urljoin("https://busquedas.elperuano.pe", href)
        file_id = dispositivo_url.rstrip("/").split("/")[-1]
        pdf_url = _resolve_pdf_url_from_dispositivo(dispositivo_url)
        if pdf_url and file_id:
            downloads.append((file_id, pdf_url))

    unique_downloads = []
    seen = set()
    for file_id, pdf_url in downloads:
        if file_id in seen:
            continue
        seen.add(file_id)
        unique_downloads.append((file_id, pdf_url))

    return unique_downloads


def _download_pdf_bytes(pdf_url):
    response = requests.get(
        pdf_url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    content = response.content
    if not content.startswith(b"%PDF"):
        raise ValueError("La URL descargada no devolvió un PDF válido.")
    return content


def _source_metadata_from_title(title, publication_date):
    """Extrae identidad basica del listado oficial para respaldar el OCR del PDF."""
    text = " ".join(str(title or "").split())
    upper = text.upper()
    type_match = re.search(
        r"\b(LEY|CIRCULAR|ORDENANZA(?:\s+(?:MUNICIPAL|REGIONAL))?|ACUERDO|DECRETO\s+(?:SUPREMO|LEGISLATIVO|DE\s+URGENCIA)|RESOLUCI[ÓO]N\s+(?:SUPREMA|MINISTERIAL|DIRECTORAL|JEFATURAL|ADMINISTRATIVA|DE\s+CONSEJO\s+DIRECTIVO|RDE)?)\b",
        text,
        flags=re.IGNORECASE,
    )
    tipo = type_match.group(1).strip() if type_match else ""
    number_match = re.search(
        r"\bN[°º]\s*([0-9]{1,6}(?:-[0-9]{4}(?:-[A-Z0-9./]+)?)?)",
        text,
        flags=re.IGNORECASE,
    )
    numero = number_match.group(1).strip() if number_match else ""
    emisor = text[:type_match.start()].strip(" -:") if type_match else ""
    description = text[type_match.end():].strip(" -:") if type_match else text
    description = re.sub(r"\bFecha:\s*\d{2}/\d{2}/\d{4}\b", "", description, flags=re.IGNORECASE).strip(" -:")
    if numero:
        description = re.sub(rf"^N[°º]\s*{re.escape(numero)}\b", "", description, flags=re.IGNORECASE).strip(" -:")
    return {
        "source_title": text,
        "numero": numero,
        "tipo_norma": tipo,
        "emisor": emisor,
        "descripcion": description,
        "fecha": publication_date.strftime("%d/%m/%Y"),
        "fecha_publicacion": publication_date.strftime("%d/%m/%Y"),
    }


def download_normas_from_source(s3, bucket, pdf_prefix, start_date, end_date):
    base_url = "https://diariooficial.elperuano.pe/Normas/Filtro"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
    }

    current = start_date
    total_descargados = 0
    source_metadata = {}

    while current <= end_date:
        print(f"📅 Procesando {current.strftime('%d/%m/%Y')}")

        data = {
            "dateparam": current.strftime("%m/%d/%Y 00:00:00"),
            "cddesde": current.strftime("%d/%m/%Y"),
            "cdhasta": current.strftime("%d/%m/%Y"),
        }

        headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

        response = requests.post(base_url, headers=headers, data=data, timeout=60, verify=False)
        if response.status_code != 200:
            print("❌ Error en request")
            current += timedelta(days=1)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        articulos = soup.select("article.edicionesoficiales_articulos, article.edicionesoficiales_articulos_dig")
        if not articulos:
            print("⚠️ No se encontraron artículos")
            current += timedelta(days=1)
            continue

        for art in articulos:
            try:
                downloads = _extract_downloads_from_article(art)
            except Exception as exc:
                print(f"❌ Error leyendo enlaces de descarga: {exc}")
                continue

            for file_id, pdf_url in downloads:
                filename = f"{current.strftime('%Y-%m-%d')}_{file_id}.pdf"
                source_metadata[filename] = _source_metadata_from_title(art.get_text(" ", strip=True), current)

                if pdf_exists_in_s3(s3, bucket, pdf_prefix, filename):
                    continue

                try:
                    pdf_bytes = _download_pdf_bytes(pdf_url)
                    if len(pdf_bytes) > 0:
                        upload_pdf_to_s3(s3, bucket, pdf_prefix, pdf_bytes, filename)
                        total_descargados += 1
                    time.sleep(0.2)
                except Exception as exc:
                    print(f"❌ Error descargando {filename}: {exc}")

        current += timedelta(days=1)

    print(f"🎉 Descarga completa. Total PDFs subidos: {total_descargados}")
    return source_metadata


def extract_text_from_pdf_bytes(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def chunk_text(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def split_text_into_norma_sections(text, max_section_chars=12000):
    if not text:
        return []

    lines = text.splitlines()
    header_pattern = re.compile(
        r"^(?:"
        r"DECRETO\s+(?:SUPREMO|LEGISLATIVO|DE\s+URGENCIA)|"
        r"RESOLU(?:CIÓN|CION)\s+(?:SUPREMA|MINISTERIAL|RECTORAL|DIRECTORAL|JEFATURAL|DE\s+CONSEJO\s+DIRECTIVO|ADMINISTRATIVA)?|"
        r"LEY|CIRCULAR|ORDENANZA|ACUERDO"
        r")\b",
        re.IGNORECASE,
    )
    number_nearby_pattern = re.compile(r"\bN[º°]?\s*\.?\s*\d{1,6}|\b\d{1,6}-\d{4}(?:-[A-Z0-9/]+)?\b", re.IGNORECASE)

    boundaries = []
    for idx, line in enumerate(lines):
        clean_line = line.strip()
        if not header_pattern.search(clean_line):
            continue
        nearby = " ".join(lines[idx:idx + 4])
        if number_nearby_pattern.search(nearby):
            boundaries.append(idx)

    boundaries = sorted(set(boundaries))
    if not boundaries:
        boundaries = [0]
    if boundaries[-1] != len(lines):
        boundaries.append(len(lines))

    sections = []
    for start_idx, end_idx in zip(boundaries, boundaries[1:]):
        section = "\n".join(lines[start_idx:end_idx]).strip()
        if not section:
            continue
        if len(section) > max_section_chars:
            sections.append(section[:max_section_chars])
        else:
            sections.append(section)

    if not sections:
        sections = chunk_text(text, chunk_size=250, overlap=40)

    return sections


def build_chunks(s3, bucket, chunk_prefix, all_documents):
    all_chunks = []

    for doc in all_documents:
        filename = doc["filename"]
        chunk_key = f"{chunk_prefix}{filename}.json"

        try:
            existing_chunks = load_chunks_from_s3(s3, bucket, chunk_key)
            all_chunks.extend(existing_chunks)
            continue
        except Exception:
            pass

        chunks = chunk_text(doc["text"])
        structured_chunks = []

        for i, ch in enumerate(chunks):
            item = {
                "idnorma": doc.get("idnorma"),
                "fecha": doc.get("fecha"),
                "fecha_emision": doc.get("fecha_emision"),
                "regulador": doc.get("regulador"),
                "emisor": doc.get("emisor"),
                "tipo_norma": doc.get("tipo_norma"),
                "numero": doc.get("numero"),
                "descripcion": doc.get("descripcion"),
                "estado": doc.get("estado"),
                "nro_boletin": doc.get("nro_boletin"),
                "fecha_publicacion": doc.get("fecha_publicacion"),
                "filename": doc.get("filename"),
                "chunk_id": i,
                "text": ch,
            }
            structured_chunks.append(item)
            all_chunks.append(item)

        upload_chunks_to_s3(s3, bucket, chunk_prefix, structured_chunks, filename)

    return all_chunks


def build_index(all_chunks, embed_model_name):
    if not all_chunks:
        raise ValueError("No hay chunks para construir el índice. Revisa la carga/listado de PDFs.")

    embed_model = SentenceTransformer(embed_model_name)

    def embed_text_local(text):
        return embed_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

    embeddings_list = [embed_text_local(ch["text"]) for ch in tqdm(all_chunks, desc="Embeddings")]
    embeddings = np.vstack(embeddings_list)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index, embed_text_local


def search(query, k, max_normas, index, embed_fn, all_chunks):
    ems = {
        "sbs": "ALTO",
        "congreso": "ALTO",
        "poder ejecutivo": "ALTO",
        "economía y finanzas": "ALTO",
        "bcrp": "MEDIO",
        "sunat": "MEDIO",
        "municipalidades": "MEDIO",
        "osce": "MEDIO",
        "smv": "MEDIO",
        "contraloría": "MEDIO",
        "poder judicial": "BAJO",
    }

    kw_alto = [
        "sbs",
        "superintendencia de banca",
        "banco central",
        "bcrp",
        "smv",
        "sunat",
        "uif",
        "riesgo operacional",
        "riesgo de crédito",
        "riesgo de liquidez",
        "riesgo de mercado",
        "riesgo reputacional",
        "riesgo tecnológico",
        "lavado de activos",
        "financiamiento del terrorismo",
        "plaft",
        "compliance",
        "cumplimiento",
        "ciberseguridad",
        "seguridad de la información",
        "continuidad del negocio",
        "incidente de seguridad",
        "protección de datos",
        "datos personales",
        "consumidor financiero",
        "transparencia",
        "tarjeta de crédito",
        "tarjeta de débito",
        "cuenta bancaria",
        "interoperabilidad",
        "transferencias",
        "billetera digital",
        "yape",
        "plin",
        "reglamento",
        "decreto supremo",
        "decreto legislativo",
        "decreto de urgencia",
        "inteligencia artificial",
        "firma digital",
        "identidad digital",
    ]

    kw_medio = [
        "municipalidad",
        "tributario",
        "sunarp",
        "reniec",
        "osce",
        "contraloría",
        "teletrabajo",
        "acoso",
        "accesibilidad",
        "procedimiento administrativo",
    ]

    query_vector = embed_fn(query).reshape(1, -1)
    scores, indices = index.search(query_vector, k)

    normas_dict = {}
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = all_chunks[idx]
        idnorma = chunk.get("idnorma") or chunk.get("filename", f"norma_{idx}")

        if idnorma not in normas_dict:
            normas_dict[idnorma] = {
                "metadata": chunk,
                "textos": [],
                "score_max": score,
            }

        normas_dict[idnorma]["textos"].append(chunk["text"])
        if score > normas_dict[idnorma]["score_max"]:
            normas_dict[idnorma]["score_max"] = score

    resultados = []
    for _, data in normas_dict.items():
        metadata = data["metadata"]
        texto_completo = "\n".join(data["textos"])
        texto_lower = texto_completo.lower()
        score_regulatorio = 0
        score_keywords = 0
        emisor = str(metadata.get("emisor", "")).lower()

        for clave, nivel in ems.items():
            if clave in emisor:
                if nivel == "ALTO":
                    score_regulatorio += 4
                elif nivel == "MEDIO":
                    score_regulatorio += 2

            if clave in texto_lower:
                if nivel == "ALTO":
                    score_regulatorio += 2
                elif nivel == "MEDIO":
                    score_regulatorio += 1

        for keyword in kw_alto:
            if keyword in texto_lower:
                score_keywords += 3

        for keyword in kw_medio:
            if keyword in texto_lower:
                score_keywords += 1

        score_total = score_regulatorio + score_keywords
        if score_total >= 8:
            impacto = "ALTO"
        elif score_total >= 4:
            impacto = "MEDIO"
        else:
            impacto = "BAJO"

        resultados.append(
            {
                "metadata": metadata,
                "texto": texto_completo,
                "impacto": impacto,
                "score": float(data["score_max"]),
            }
        )

    prioridad = {"ALTO": 3, "MEDIO": 2, "BAJO": 1}
    resultados = sorted(
        resultados,
        key=lambda x: (prioridad[x["impacto"]], x["score"]),
        reverse=True,
    )

    resultados_filtrados = []
    for r in resultados:
        texto = r["texto"].lower()

        if (
            "municipalidad distrital" in texto
            and "banco" not in texto
            and "financiero" not in texto
        ):
            continue

        if "designan" in texto and "sbs" not in texto and "bcrp" not in texto:
            continue

        resultados_filtrados.append(r)

    return resultados_filtrados[:max_normas]


def rag_answer(query, contexts, api_key, model_name, endpoint=None):
    if not contexts:
        return "No se encontró información relevante."

    if endpoint is None:
        endpoint = "https://api.groq.com/openai/v1/chat/completions"

    # Truncar texto de cada norma para no exceder límite de tokens
    max_text_chars = 500  # menor límite para requests compatibles con gpt-5

    def _format_batch(batch_contexts):
        ctx_text = ""
        for norma in batch_contexts:
            meta = norma["metadata"]
            texto_truncado = norma['texto'][:max_text_chars]
            ctx_text += f"""IDNORMA: {meta.get('idnorma', 'NO DISPONIBLE')}
FECHA: {meta.get('fecha', 'NO DISPONIBLE')}
FECHA_EMISION: {meta.get('fecha_emision', 'NO DISPONIBLE')}
REGULADOR: {meta.get('regulador', 'NO DISPONIBLE')}
EMISOR: {meta.get('emisor', 'NO DISPONIBLE')}
TIPO_NORMA: {meta.get('tipo_norma', 'NO DISPONIBLE')}
NUMERO: {meta.get('numero', 'NO DISPONIBLE')}
DESCRIPCION: {meta.get('descripcion', 'NO DISPONIBLE')}
ESTADO: {meta.get('estado', 'NO DISPONIBLE')}
NRO_BOLETIN: {meta.get('nro_boletin', 'NO DISPONIBLE')}
FECHA_PUBLICACION: {meta.get('fecha_publicacion', 'NO DISPONIBLE')}
TEXTO: {texto_truncado}
-------------------------------------------------------
"""
        return ctx_text

    system_msg = {
            "role": "system",
            "content": """Eres un Analista Normativo Senior del área de Cumplimiento Normativo de Interbank, un banco múltiple peruano supervisado por la SBS. Tu función es revisar TODAS las normas publicadas en el Diario Oficial El Peruano y determinar cuáles son relevantes para el banco.

## TU OBJETIVO
Analizar CADA norma del contexto y clasificarla según su relevancia para Interbank.

## CRITERIOS DE CLASIFICACIÓN BASADOS EN EL EXCEL HUMANO

- C_NORMATIVO debe ser exactamente SI o NO.
- INTERES_BANCO debe ser exactamente SI o NO y debe coincidir con C_NORMATIVO.
- Si INTERES_BANCO es NO, INTERES_AL_BANCO debe ser NO y NIVEL_IMPACTO debe ser NO APLICA.
- Si INTERES_BANCO es SI, INTERES_AL_BANCO debe ser SI.
- Si INTERES_AL_BANCO es SI, NIVEL_IMPACTO debe ser INFORMATIVA, ALTO, MEDIO o BAJO.
- Solo cuando exista impacto real, NIVEL_IMPACTO debe ser ALTO, MEDIO o BAJO.

### INFORMATIVA: norma de seguimiento o referencia para el banco, sin obligación directa de adecuación.
### IMPACTO: norma que genera acción, obligación, adecuación o seguimiento operativo/regulatorio concreto.
### NO: norma sin aplicación ni seguimiento relevante para el banco.

- No inventes información. Si un campo no está disponible, escribe 'NO DISPONIBLE'.
- RESPONDE EN TEXTO PLANO, NO EN FORMATO JSON.
- El campo NIVEL_IMPACTO debe ser exactamente uno de: INFORMATIVA, ALTO, MEDIO, BAJO, NO APLICA.

## FORMATO OBLIGATORIO
- Responde SOLO en bloques, sin texto narrativo fuera del bloque
- Cada bloque debe iniciar y terminar con una línea exacta: ----------------------------------------
- Debe contener exactamente estas líneas (en este orden):
IDNORMA:
FECHA:
FECHA_EMISION:
REGULADOR:
EMISOR:
TIPO_NORMA:
NUMERO:
DESCRIPCION:
ESTADO:
NRO_BOLETIN:
FECHA_PUBLICACION:
C_NORMATIVO:
INTERES_BANCO:
INTERES_AL_BANCO:
NIVEL_IMPACTO:
JUSTIFICACION:
IMPORTANCIA:""",
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Procesar en batches más pequeños para no superar el límite de tokens de gpt-5
    batch_size = 5
    all_responses = []

    for i in range(0, len(contexts), batch_size):
        batch = contexts[i:i+batch_size]
        contexto_batch = _format_batch(batch)

        messages = [
            system_msg,
            {
                "role": "user",
                "content": f"CONTEXTO:\n{contexto_batch}\n\nTAREA: {query}",
            },
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": 4096,
            "temperature": 0.1,
        }

        batch_num = i // batch_size + 1
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(endpoint, headers=headers, json=payload, timeout=300, verify=False)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"].strip()
                    print(f"📝 Batch {batch_num}: {len(content)} chars, {content.count('----')} bloques, normas {i+1}-{i+len(batch)}")
                    all_responses.append(content)
                    break
                elif response.status_code == 429:
                    # Extraer tiempo de espera del mensaje si es posible
                    wait_secs = 65
                    import re as _re
                    m = _re.search(r"[Ww]ait\s+(\d{1,3})\s+second", response.text)
                    if m:
                        wait_secs = min(int(m.group(1)) + 5, 120)
                    print(f"⏳ Rate limit batch {batch_num}, esperando {wait_secs}s (intento {attempt+1}/{max_retries})...")
                    time.sleep(wait_secs)
                else:
                    print(f"⚠️ Error API LLM batch {batch_num} ({response.status_code}): {response.text[:200]}")
                    break
            except Exception as exc:
                print(f"⚠️ Error en batch {batch_num}: {exc}")
                break

        time.sleep(1)  # Rate limiting entre batches (5s para evitar saturar cuota)

    return "\n".join(all_responses) if all_responses else "No se encontró información relevante."


def parse_rag_output_to_rows(texto):
    filas = []
    actual = {}

    for raw_line in texto.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("-") and set(line) == {"-"}:
            if actual:
                filas.append(actual)
                actual = {}
            continue

        if ":" in line:
            k, v = line.split(":", 1)
            key = k.strip().strip('"').strip("'")
            value = v.strip().strip('"').strip("'")
            actual[key] = value

    if actual:
        filas.append(actual)

    filas_validas = [f for f in filas if f]
    if not filas_validas:
        filas_validas = [{"MENSAJE": texto.strip()}]
    else:
        incompletas = [f for f in filas_validas if not any(k in f for k in ["IDNORMA", "NUMERO", "DESCRIPCION", "NIVEL_IMPACTO"])]
        if incompletas:
            print(f"⚠️ Se detectaron {len(incompletas)} bloques con campos incompletos. Se conservan para revisión.")

    # Normalizar claves que pueden llegar en formato JSON o con comillas
    for fila in filas_validas:
        for clave in list(fila.keys()):
            valor = fila[clave]
            if isinstance(valor, str):
                fila[clave] = valor.strip().strip('"').strip("'")

    # Normalizar NIVEL_IMPACTO
    norm_map = {"INFORMATIVO": "INFORMATIVA", "INTERES": "INTERÉS", "INTERÉS": "INTERÉS", "INFORMATIVA": "INFORMATIVA", "NO": "NO"}
    for fila in filas_validas:
        ni = fila.get("NIVEL_IMPACTO", "").strip().upper()
        fila["NIVEL_IMPACTO"] = norm_map.get(ni, ni)

    return filas_validas


def _safe_value(value):
    if value is None or pd.isna(value):
        return "NO DISPONIBLE"
    text = str(value).strip()
    return text if text else "NO DISPONIBLE"


def _is_missing(value):
    return _safe_value(value).upper() in {"", "NO DISPONIBLE", "N/A", "NA", "NULL"}


def _is_pdf_filename(value):
    return str(value or "").strip().upper().endswith(".PDF")


def _should_skip_row(row):
    if not row:
        return True

    idnorma = str(row.get("IDNORMA", "")).strip().upper()
    fecha_emision = row.get("FECHA_EMISION")

    # Vacío o no disponible
    if _is_missing(idnorma):
        return True

    if _is_missing(fecha_emision):
        return True

    if idnorma == "NO DISPONIBLE":
        return True
    # Evitar nombres de PDFs como IDNORMA
    if idnorma.endswith(".PDF"):
        return True

    # Evitar patrones tipo 2025-03-12_NORMA_001.PDF
    if re.match(r"^\d{4}-\d{2}-\d{2}_.*\.PDF$", idnorma):
        return True

    # Debe existir al menos algo útil
    if (
        _is_missing(row.get("NUMERO")) and
        _is_missing(row.get("DESCRIPCION")) and
        _is_missing(row.get("NIVEL_IMPACTO"))
    ):
        return True

    return False


def _dedupe_rows(rows):
    seen = set()
    deduped = []
    for row in rows:
        key = str(row.get("IDNORMA") or row.get("NUMERO") or "").strip().upper()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _date_from_filename(filename):
    if not filename:
        return ""
    match = re.match(r"^(\d{4}-\d{2}-\d{2})_", str(filename).strip())
    if not match:
        return ""
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return ""


def _infer_fecha_emision_from_text(text):
    if not text:
        return ""
    sample = str(text)[:2500]
    patterns = [
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})\b",
    ]
    month_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    for pattern in patterns:
        match = re.search(pattern, sample, flags=re.IGNORECASE)
        if not match:
            continue
        try:
            if match.group(2).lower() in month_map:
                day = int(match.group(1))
                month = month_map[match.group(2).lower()]
                year = int(match.group(3))
            else:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                if year < 100:
                    year += 2000
            return datetime(year, month, day).strftime("%d/%m/%Y")
        except Exception:
            continue
    return ""


def _first_available(*values):
    for value in values:
        if not _is_missing(value):
            return value
    return "NO DISPONIBLE"


def _infer_numero_from_text(text):
    if not text:
        return ""
    lines = [re.sub(r"\s+", " ", line).strip().upper() for line in str(text).splitlines()]
    lines = [line for line in lines if line][:120]
    header_pattern = re.compile(
        r"^(?:DECRETO(?:\s+DE\s+ALCALD[IÍ]A)?|RESOLU(?:CIÓN|CION)(?:\s+DE\s+SUPERINTENDENCIA|\s+MINISTERIAL|\s+SBS)?|LEY|CIRCULAR|ORDENANZA|ACUERDO)\b",
        re.IGNORECASE,
    )
    explicit_number_patterns = [
        r"\b(?:RESOLU(?:CIÓN|CION)(?:\s+DE\s+SUPERINTENDENCIA|\s+MINISTERIAL|\s+SBS)?|DECRETO(?:\s+DE\s+ALCALD[IÍ]A)?|ORDENANZA|ACUERDO|LEY)\s+N[º°]?\s*\.?\s*([A-Z0-9]+(?:\s*[-/]\s*[A-Z0-9]+)+)",
        r"\bN[º°]?\s*\.?\s*([A-Z]?\s*-?\s*\d{1,6}(?:\s*[-/]\s*\d{4})?(?:\s*[-/]\s*[A-Z0-9]+)*)",
        r"\b([A-Z]?\s*-?\s*\d{1,6}\s*[-/]\s*\d{4}(?:\s*[-/]\s*[A-Z0-9]+)*)",
    ]

    joined_head = " ".join(lines[:20])
    for pattern in explicit_number_patterns:
        match = re.search(pattern, joined_head, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", "", match.group(1).upper())

    for idx, line in enumerate(lines):
        if not header_pattern.search(line):
            continue
        window = " ".join(lines[idx:idx + 4])
        for pattern in explicit_number_patterns:
            match = re.search(pattern, window, flags=re.IGNORECASE)
            if match:
                return re.sub(r"\s+", "", match.group(1).upper())

    return ""


def _numero_matches_publication_year(numero, analysis_date):
    """Evita usar citas internas de normas antiguas como si fueran la norma publicada."""
    text = str(numero or "").upper()
    years = [int(y) for y in re.findall(r"(?<!\d)(20\d{2})(?!\d)", text)]
    for short_year in re.findall(r"(?<!\d)-(\d{2})(?:-|/|$)", text):
        value = int(short_year)
        years.append(2000 + value if value <= 40 else 1900 + value)
    if not years:
        return True
    return analysis_date.year in years


def _infer_descripcion_from_text(text, numero=None, max_chars=260):
    if not text:
        return ""

    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text).splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""

    noise = (
        "normas legales", "diario oficial", "elperuano", "separata", "pág.",
        "página", "sumario", "miércoles", "jueves", "viernes", "sábado",
        "domingo", "lunes", "martes",
    )
    starts = (
        "aprueban", "modifican", "modifíquese", "modifiquese", "declaran",
        "disponen", "decreto supremo", "decreto legislativo", "ley que",
        "resolución", "resolucion", "circular", "autorizan", "actualizan",
        "establecen", "prorrogan", "designan", "fijan", "incorporan",
    )

    for idx, line in enumerate(lines[:60]):
        lower = line.lower()
        if "estado de emergencia" not in lower:
            continue
        if "decreto supremo" in lower or "declara" in lower or "prorroga" in lower:
            merged = line
            for next_line in lines[idx + 1:idx + 4]:
                if len(merged) >= max_chars:
                    break
                if re.search(r"^(DECRETO SUPREMO|CONSIDERANDO|Artículo|Articulo|Que,)", next_line, re.IGNORECASE):
                    break
                merged = f"{merged} {next_line}"
            return merged[:max_chars].strip(" ,.;")

    numero_clean = str(numero or "").strip().upper()
    for idx, line in enumerate(lines[:45]):
        lower = line.lower()
        if any(item in lower for item in noise):
            continue
        if numero_clean and numero_clean in line.upper():
            window = " ".join(lines[idx:idx + 4])
            window = re.sub(re.escape(numero_clean), "", window, flags=re.IGNORECASE).strip(" -:;")
            if len(window) >= 35:
                return window[:max_chars]
        if lower.startswith(starts) and len(line) >= 35:
            return line[:max_chars]

    for line in lines[:45]:
        lower = line.lower()
        if len(line) >= 45 and not any(item in lower for item in noise):
            return line[:max_chars]

    return ""


def _normalize_numero(value, idnorma=None, filename=None, text=None):
    """Normalizar y completar el campo NUMERO buscando en varias fuentes y devolviendo
    el primer valor válido en mayúsculas y sin espacios extra.
    """
    def clean(s):
        if s is None:
            return ""
        s = str(s).strip().upper()
        s = re.sub(r"\s+", "", s)
        return s

    candidates = []
    # prefer given value
    if value is not None:
        candidates.append(clean(value))
    if idnorma is not None:
        candidates.append(clean(idnorma))
    if filename:
        candidates.append(clean(filename))
    if text:
        inferred = _infer_numero_from_text(text)
        if inferred:
            candidates.append(clean(inferred))

    # buscar patrones válidos en candidatos
    patterns = [
        r"\b\d{1,5}-\d{4}-[A-Z0-9/\-]+\b",
        r"\b[A-Z]{1,6}-\d{1,6}-\d{4}\b",
        r"\b\d{1,5}-\d{4}\b",
        r"\b\d{3,6}\b-\d{4}\b",
    ]

    for cand in candidates:
        if not cand:
            continue
        # si ya parece un numero limpio, devolverlo
        for pat in patterns:
            m = re.search(pat, cand)
            if m:
                return m.group(0)

    # fallback: devolver el primer candidato no vacío
    for cand in candidates:
        if cand and not _is_pdf_filename(cand):
            return cand

    return "NO DISPONIBLE"


def _norma_match_key(value):
    text = str(value or "").upper()
    text = text.replace("Nº", "").replace("N°", "").replace("NO.", "")
    text = re.sub(r"\b(RESOLUCI[ÓO]N|DECRETO|SUPREMO|CIRCULAR|ORDENANZA|LEY)\b", " ", text)
    text = re.sub(r"[^A-Z0-9-]+", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def _normalize_ref_date(value):
    if _is_missing(value):
        return ""
    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass
    text = str(value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""


def _date_key_from_row(row):
    for field in ("FECHA_PUBLICACION", "FECHA", "FECHA_EJECUCION", "FECHA_EMISION"):
        date_key = _normalize_ref_date(row.get(field))
        if date_key:
            return date_key
    filename_date = _date_from_filename(row.get("filename") or row.get("FILENAME") or row.get("PDF_KEY"))
    return _normalize_ref_date(filename_date)


def _normalize_si_no(value, default="NO"):
    text = str(value or "").strip().upper()
    if text in {"SI", "SÍ", "YES", "Y", "TRUE", "1"}:
        return "SI"
    if text in {"NO", "N", "FALSE", "0"}:
        return "NO"
    return default


def _normalize_interes_al_banco(value):
    text = str(value or "").strip().upper()
    if text in {"INFORMATIVA", "INFORMATIVO"}:
        return "INFORMATIVA"
    if text in {"IMPACTO", "DE IMPACTO"}:
        return "IMPACTO"
    if text in {"ALTO", "MEDIO", "BAJO"}:
        return "IMPACTO"
    if text in {"NO", "NO APLICA", "NO RELEVANTE", "SIN INTERES", "SIN INTERÉS"}:
        return "NO"
    return ""


def _normalize_impact_level_v10(value):
    text = str(value or "").strip().upper()
    if "ALTO" in text:
        return "ALTO"
    if "MEDIO" in text:
        return "MEDIO"
    if "BAJO" in text:
        return "BAJO"
    return ""


def _infer_impact_level_from_comment(text):
    sample = str(text or "").lower()
    if "impacto alto" in sample or "alto impacto" in sample:
        return "ALTO"
    if "impacto medio" in sample or "medio impacto" in sample:
        return "MEDIO"
    if "impacto bajo" in sample or "bajo impacto" in sample:
        return "BAJO"
    return "BAJO"


def load_human_reference(reference_file):
    path = Path(reference_file)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    if not path.exists():
        print(f"⚠️ Excel de referencia humana no encontrado: {path}")
        return {}

    try:
        excel = pd.ExcelFile(path)
        df = None
        for sheet_name in excel.sheet_names:
            candidate = pd.read_excel(path, sheet_name=sheet_name)
            normalized_cols = {str(col).strip().upper(): col for col in candidate.columns}
            if "N° NORMA" in normalized_cols and "FECHA DE PUBLICACIÓN" in normalized_cols:
                df = candidate
                break
        if df is None:
            raise ValueError("no se encontro una hoja con N° NORMA y FECHA DE PUBLICACIÓN")
    except Exception as exc:
        print(f"⚠️ No se pudo leer referencia humana {path}: {exc}")
        return {}

    by_num_date = {}
    by_num = {}
    all_rows = []
    rows_by_date = {}
    for _, row in df.iterrows():
        key = _norma_match_key(row.get("N° NORMA"))
        if not key:
            continue
        date_key = _normalize_ref_date(row.get("FECHA DE PUBLICACIÓN"))
        interes = _normalize_interes_al_banco(row.get("INTERÉS AL BANCO"))
        c_normativo = _normalize_si_no(row.get("C. NORMATIVO"), default="SI")
        comentario = _safe_value(row.get("COMENTARIO / DESCRIPCIÓN DE LA NORMA"))
        nivel = _normalize_impact_level_v10(row.get("INTERÉS AL BANCO"))
        if not nivel:
            nivel = _infer_impact_level_from_comment(comentario) if interes == "IMPACTO" else "INFORMATIVA"
        fecha_publicacion = pd.to_datetime(row.get("FECHA DE PUBLICACIÓN"), dayfirst=True, errors="coerce")
        ref = {
            "FECHA_PUBLICACION": fecha_publicacion.strftime("%d/%m/%Y") if pd.notna(fecha_publicacion) else "NO DISPONIBLE",
            "TIPO_NORMA": _safe_value(row.get("TIPO DE NORMA")),
            "NUMERO": _safe_value(row.get("N° NORMA")),
            "IDNORMA": _safe_value(row.get("N° NORMA")),
            "C_NORMATIVO": c_normativo,
            "INTERES_BANCO": c_normativo,
            "INTERES_AL_BANCO": c_normativo,
            "NIVEL_IMPACTO": nivel,
            "REFERENCIA_HUMANA": "SI",
            "JUSTIFICACION_REFERENCIA": comentario,
        }
        if date_key:
            by_num_date[(key, date_key)] = ref
            rows_by_date.setdefault(date_key, []).append(ref)
        by_num.setdefault(key, []).append(ref)
        all_rows.append(ref)

    unique_by_num = {key: refs[0] for key, refs in by_num.items() if len(refs) == 1}
    reference = {
        "by_num_date": by_num_date,
        "unique_by_num": unique_by_num,
        "rows_by_date": rows_by_date,
        "all_rows": all_rows,
    }
    print(f"📘 Referencia humana cargada: {len(all_rows)} normas desde {path.name}")
    return reference


_SEMANTIC_EMBED_MODEL = None
_SEMANTIC_CROSS_MODEL = None


def _historical_reference_text(ref):
    parts = [
        _safe_value(ref.get("TIPO_NORMA")),
        _safe_value(ref.get("NUMERO")),
        _safe_value(ref.get("NIVEL_IMPACTO")),
        _safe_value(ref.get("JUSTIFICACION_REFERENCIA")),
    ]
    return " | ".join(part for part in parts if part and part != "NO DISPONIBLE")


def _context_semantic_text(context):
    meta = context.get("metadata", {})
    parts = [
        _safe_value(meta.get("tipo_norma")),
        _safe_value(meta.get("numero")),
        _safe_value(meta.get("emisor")),
        _safe_value(meta.get("descripcion")),
        _safe_value(context.get("texto"))[:1600],
    ]
    return " | ".join(part for part in parts if part and part != "NO DISPONIBLE")


def _numero_regex_fragment(numero):
    text = re.sub(r"\s+", "", str(numero or "").upper())
    if not text:
        return ""
    parts = [re.escape(part) for part in text.split("-") if part]
    if not parts:
        return ""
    first = parts[0]
    if first.isdigit():
        first = f"0*{int(first)}"
    return r"\s*[-/]\s*".join([first] + parts[1:])


def _is_actual_norm_header(text, numero, tipo_hint="DECRETO SUPREMO"):
    numero_pattern = _numero_regex_fragment(numero)
    if not numero_pattern:
        return False
    tipo_pattern = re.escape(tipo_hint)
    pattern = rf"(?m)^\s*{tipo_pattern}\b[\s\S]{{0,120}}N[°º]?\s*\.?\s*{numero_pattern}"
    return bool(re.search(pattern, str(text or ""), flags=re.IGNORECASE))


def _estado_emergencia_cause(text):
    normalized = str(text or "").lower()
    natural_terms = [
        "precipitaciones", "pluviales", "lluvias", "peligro inminente",
        "impacto de daños", "impacto de danos", "desastre", "inundación",
        "inundacion", "huaico", "huayco", "deslizamiento", "sismo",
        "terremoto", "volcán", "volcan", "helada", "friaje", "sequía",
        "sequia", "déficit hídrico", "deficit hidrico",
        "colapso del sistema de alcantarillado",
    ]
    criminality_terms = [
        "criminalidad", "orden interno", "seguridad ciudadana", "violencia",
        "delincuencia", "minería ilegal", "mineria ilegal", "delitos conexos",
        "grupos hostiles", "amenazas conexas", "control migratorio",
        "control fronterizo", "fronterizo", "policía nacional", "policia nacional",
        "pnp", "orden y seguridad", "terrorismo", "narcotráfico",
        "narcotrafico", "tráfico ilícito de drogas", "trafico ilicito de drogas",
        "extorsión", "extorsion", "sicariato",
    ]
    if any(term in normalized for term in natural_terms):
        return "desastres naturales"
    if any(term in normalized for term in criminality_terms):
        return "criminalidad u orden interno"
    return ""


def _get_semantic_models(embed_model_name, cross_model_name):
    global _SEMANTIC_EMBED_MODEL, _SEMANTIC_CROSS_MODEL
    if SentenceTransformer is None or CrossEncoder is None:
        raise RuntimeError("sentence-transformers no esta instalado")
    if _SEMANTIC_EMBED_MODEL is None:
        _SEMANTIC_EMBED_MODEL = SentenceTransformer(embed_model_name)
    if _SEMANTIC_CROSS_MODEL is None:
        _SEMANTIC_CROSS_MODEL = CrossEncoder(cross_model_name)
    return _SEMANTIC_EMBED_MODEL, _SEMANTIC_CROSS_MODEL


def semantic_prioritize_contexts(
    contexts,
    human_reference,
    embed_model_name,
    cross_model_name,
    top_k=12,
    min_score=0.45,
):
    """Ranking historico: embeddings para recall y cross-encoder para precision."""
    if not contexts or not human_reference:
        return {}

    positive_refs = [
        ref for ref in human_reference.get("all_rows", [])
        if ref.get("C_NORMATIVO") == "SI"
    ]
    history_texts = [_historical_reference_text(ref) for ref in positive_refs]
    history_items = [
        (ref, text) for ref, text in zip(positive_refs, history_texts)
        if text.strip()
    ]
    if not history_items:
        return {}

    try:
        embed_model, cross_model = _get_semantic_models(embed_model_name, cross_model_name)
    except Exception as exc:
        print(f"⚠️ Priorizacion semantica desactivada: {exc}")
        return {}

    context_texts = [_context_semantic_text(ctx) for ctx in contexts]
    valid_contexts = [
        (idx, ctx, text) for idx, (ctx, text) in enumerate(zip(contexts, context_texts))
        if text.strip()
    ]
    if not valid_contexts:
        return {}

    try:
        ref_texts = [text for _, text in history_items]
        new_texts = [text for _, _, text in valid_contexts]
        ref_embeddings = embed_model.encode(ref_texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        new_embeddings = embed_model.encode(new_texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        similarities = new_embeddings @ ref_embeddings.T
    except Exception as exc:
        print(f"⚠️ Error en semantic search; se usa heuristica actual: {exc}")
        return {}

    candidates = []
    per_context_best = min(max(1, top_k // 2), len(history_items))
    for pos, (idx, ctx, text) in enumerate(valid_contexts):
        best_ref_positions = np.argsort(similarities[pos])[-per_context_best:][::-1]
        best_semantic = float(similarities[pos][best_ref_positions[0]]) if len(best_ref_positions) else 0.0
        for ref_pos in best_ref_positions:
            ref, ref_text = history_items[int(ref_pos)]
            candidates.append({
                "ctx": ctx,
                "ctx_text": text,
                "ref": ref,
                "ref_text": ref_text,
                "semantic_score": float(similarities[pos][ref_pos]),
                "best_semantic": best_semantic,
            })

    candidates.sort(key=lambda item: item["semantic_score"], reverse=True)
    candidates = candidates[: max(top_k * 3, top_k)]
    if not candidates:
        return {}

    try:
        pairs = [(item["ctx_text"], item["ref_text"]) for item in candidates]
        cross_scores = cross_model.predict(pairs)
    except Exception as exc:
        print(f"⚠️ Error en cross-encoder; se usa heuristica actual: {exc}")
        return {}

    scored = {}
    for item, score in zip(candidates, cross_scores):
        score = float(score)
        if score < min_score:
            continue
        ctx_id = id(item["ctx"])
        previous = scored.get(ctx_id)
        if previous and previous["cross_score"] >= score:
            continue
        scored[ctx_id] = {
            "cross_score": score,
            "semantic_score": item["semantic_score"],
            "best_semantic": item["best_semantic"],
            "match_numero": item["ref"].get("NUMERO"),
            "match_nivel": item["ref"].get("NIVEL_IMPACTO"),
            "match_justificacion": item["ref"].get("JUSTIFICACION_REFERENCIA"),
        }

    ranked = dict(
        sorted(
            scored.items(),
            key=lambda pair: (pair[1]["cross_score"], pair[1]["semantic_score"]),
            reverse=True,
        )[:top_k]
    )
    if ranked:
        print(f"[SEMANTICO] candidatos rerankeados para LLM: {len(ranked)}")
    return ranked


def _find_human_reference(row, human_reference):
    if not human_reference:
        return {}
    for key in (_norma_match_key(row.get("NUMERO")), _norma_match_key(row.get("IDNORMA"))):
        if not key:
            continue
        date_key = _date_key_from_row(row)
        ref = human_reference.get("by_num_date", {}).get((key, date_key)) if date_key else None
        if ref:
            return ref
        ref = human_reference.get("unique_by_num", {}).get(key)
        if ref:
            return ref
    return {}


def _apply_human_reference(row, human_reference):
    ref = _find_human_reference(row, human_reference)
    if ref:
        row.update(ref)
        if ref.get("JUSTIFICACION_REFERENCIA"):
            row["JUSTIFICACION"] = ref["JUSTIFICACION_REFERENCIA"]
    return row


def _missing_human_reference_rows(rows, human_reference, analysis_date):
    if not human_reference:
        return []
    date_key = analysis_date.strftime("%Y-%m-%d")
    refs = human_reference.get("rows_by_date", {}).get(date_key, [])
    existing_positive = set()
    for row in rows:
        key = _norma_match_key(row.get("NUMERO")) or _norma_match_key(row.get("IDNORMA"))
        if not key:
            continue
        is_positive = any(
            _normalize_si_no(row.get(field), default="") == "SI"
            for field in ("REFERENCIA_HUMANA", "C_NORMATIVO", "INTERES_BANCO", "INTERES_AL_BANCO")
        )
        if is_positive:
            existing_positive.add(key)
    missing = []
    for ref in refs:
        key = _norma_match_key(ref.get("NUMERO") or ref.get("IDNORMA"))
        if not key or key in existing_positive:
            continue
        row = {
            "FECHA_EJECUCION": analysis_date.strftime("%Y-%m-%d"),
            "FECHA": ref.get("FECHA_PUBLICACION", analysis_date.strftime("%d/%m/%Y")),
            "FECHA_EMISION": ref.get("FECHA_PUBLICACION", analysis_date.strftime("%d/%m/%Y")),
            "FECHA_PUBLICACION": ref.get("FECHA_PUBLICACION", analysis_date.strftime("%d/%m/%Y")),
            "IDNORMA": ref.get("IDNORMA"),
            "TIPO_NORMA": ref.get("TIPO_NORMA", "NO DISPONIBLE"),
            "NUMERO": ref.get("NUMERO"),
            "DESCRIPCION": ref.get("JUSTIFICACION_REFERENCIA", "NO DISPONIBLE"),
            "EMISOR": "NO DISPONIBLE",
            "REGULADOR": "NO DISPONIBLE",
            "ESTADO": "NO DISPONIBLE",
            "NRO_BOLETIN": "NO DISPONIBLE",
            "PDF_S3_URI": "NO DISPONIBLE",
            "PDF_URL": "",
            "PDF_PUBLIC_URL": "",
            "PDF_CONSOLE_URL": "",
            "PDF_KEY": "NO DISPONIBLE",
            "JUSTIFICACION": ref.get("JUSTIFICACION_REFERENCIA", "Referencia humana del Excel."),
        }
        row.update(ref)
        missing.append(_finalize_v10_classification(row))
    if missing:
        print(f"📘 Referencias humanas agregadas sin extracción PDF: {len(missing)}")
    return missing


def _finalize_v10_classification(row):
    explicit_si = any(
        _normalize_si_no(row.get(field), default="") == "SI"
        for field in ("C_NORMATIVO", "INTERES_BANCO", "INTERES_AL_BANCO", "IMPORTANCIA", "REFERENCIA_HUMANA")
    )
    explicit_no = any(
        _normalize_si_no(row.get(field), default="") == "NO"
        for field in ("C_NORMATIVO", "INTERES_BANCO", "INTERES_AL_BANCO", "IMPORTANCIA")
    )
    raw_nivel = str(row.get("NIVEL_IMPACTO") or "").strip().upper()
    nivel = _normalize_impact_level_v10(raw_nivel)
    if not nivel and raw_nivel in {"INFORMATIVA", "INFORMATIVO"}:
        nivel = "INFORMATIVA"

    if explicit_si:
        c_normativo = "SI"
        if nivel in {"ALTO", "MEDIO", "BAJO"}:
            importancia = "Si"
        else:
            nivel = "INFORMATIVA"
            importancia = "Si"
    elif explicit_no:
        c_normativo = "NO"
        nivel = "NO APLICA"
        importancia = "No"
    elif nivel in {"ALTO", "MEDIO", "BAJO", "INFORMATIVA"}:
        c_normativo = "SI"
        importancia = "Si"
    else:
        c_normativo = "NO"
        nivel = "NO APLICA"
        importancia = "No"

    row["C_NORMATIVO"] = c_normativo
    row["INTERES_BANCO"] = c_normativo
    row["INTERES_AL_BANCO"] = c_normativo
    row["NIVEL_IMPACTO"] = nivel
    row["IMPORTANCIA"] = importancia
    row.setdefault("REFERENCIA_HUMANA", "NO")
    return row


def _infer_emisor_from_text(text):
    if not text:
        return ""
    upper_text = str(text).upper()
    candidates = [
        "OSINERGMIN",
        "SUPERINTENDENCIA DE BANCA, SEGUROS Y AFP",
        "SBS",
        "SUNAT",
        "BCRP",
        "BANCO CENTRAL DE RESERVA DEL PERU",
        "SMV",
        "MINISTERIO DE ECONOMIA Y FINANZAS",
        "MEF",
        "CONGRESO DE LA REPUBLICA",
        "PODER EJECUTIVO",
    ]
    for candidate in candidates:
        if candidate in upper_text:
            return candidate
    return ""


def _infer_tipo_norma_from_text(text):
    if not text:
        return ""
    upper_text = str(text).upper()
    typed_patterns = [
        (r"RESOLU(?:CIÓN|CION)\s+DE\s+SUPERINTENDENCIA", "Resolucion"),
        (r"RESOLU(?:CIÓN|CION)\s+MINISTERIAL", "Resolucion"),
        (r"RESOLU(?:CIÓN|CION)\s+SBS", "Resolucion"),
        (r"DECRETO\s+DE\s+ALCALD[IÍ]A", "Decreto de Alcaldia"),
        (r"DECRETO\s+SUPREMO", "Decreto Supremo"),
        (r"DECRETO\s+LEGISLATIVO", "Decreto Legislativo"),
        (r"DECRETO\s+DE\s+URGENCIA", "Decreto de Urgencia"),
        (r"ORDENANZA", "Ordenanza"),
        (r"ACUERDO", "Acuerdo"),
        (r"CIRCULAR", "Circular"),
        (r"OFICIO", "Oficio"),
        (r"LEY", "Ley"),
        (r"RESOLU(?:CIÓN|CION)", "Resolucion"),
    ]
    for pattern, normalized in typed_patterns:
        if re.search(pattern, upper_text):
            return normalized
    return ""


def _s3_https_url(bucket, key):
    return f"https://{bucket}.s3.amazonaws.com/{quote(key, safe='/')}"


def _s3_console_url(bucket, key, region="us-east-1"):
    encoded_key = quote(key, safe="")
    return f"https://s3.console.aws.amazon.com/s3/object/{bucket}?region={region}&prefix={encoded_key}"


def _presigned_pdf_url(s3_client, bucket, key, expires_in=86400):
    if s3_client is None:
        return ""
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except Exception:
        return ""


def _normalize_impact_label(value):
    impact = str(value or "").strip().upper()
    mapping = {
        "ALTO": "Alto Impacto",
        "MEDIO": "Medio Impacto",
        "BAJO": "Bajo Impacto",
        "ALTO IMPACTO": "Alto Impacto",
        "MEDIO IMPACTO": "Medio Impacto",
        "BAJO IMPACTO": "Bajo Impacto",
        "SIN IMPACTO": "INFORMATIVA",
        "SIN_IMPACTO": "INFORMATIVA",
        "INFORMATIVA": "INFORMATIVA",
        "INFORMATIVO": "INFORMATIVA",
        "NO": "INFORMATIVA",
    }
    return mapping.get(impact, impact)


def _impact_class(value):
    impact = str(value or "").strip().upper()
    if impact in {"ALTO", "ALTO IMPACTO"}:
        return "sem-alto"
    if impact in {"MEDIO", "MEDIO IMPACTO"}:
        return "sem-medio"
    if impact in {"BAJO", "BAJO IMPACTO"}:
        return "sem-bajo"
    if impact in {"INFORMATIVA", "INFORMATIVO", "NO"}:
        return "sem-sin"
    return "sem-sin"


def _score_context_for_bank(context):
    """Score barato para decidir si una norma merece revisión LLM."""
    meta = context.get("metadata", {})
    text = f"{meta.get('numero', '')} {meta.get('emisor', '')} {context.get('texto', '')}".lower()

    high_terms = [
        "sbs", "superintendencia de banca", "sistema financiero", "banco central",
        "bcrp", "uif", "lavado de activos", "financiamiento del terrorismo",
        "riesgo de crédito", "riesgo de liquidez", "patrimonio efectivo",
        "provisiones", "manual de contabilidad", "conducta de mercado",
        "tarjeta de crédito", "tarjetas de crédito", "tarjeta de débito",
        "interoperabilidad", "servicios de pago", "ciberseguridad",
        "seguridad de la información", "continuidad del negocio",
        "protección de datos", "datos personales", "conglomerado financiero",
        "modelo", "créditos", "depósitos", "cts", "teletrabajo",
        "inteligencia artificial", "canales digitales",
    ]
    medium_terms = [
        "ministerio de economía", "mef", "sunat", "smv", "osce",
        "contraloría", "protección al consumidor", "indecopi",
        "reporte", "obligación", "reglamento", "modifican", "aprueban",
        "decreto legislativo", "decreto supremo", "resolución",
    ]
    low_noise_terms = [
        "designan", "aceptan renuncia", "autorizan viaje", "municipalidad",
        "ordenanza", "separata especial", "nombran", "conforman comisión",
    ]

    score = 0
    score += sum(3 for term in high_terms if term in text)
    score += sum(1 for term in medium_terms if term in text)
    score -= sum(2 for term in low_noise_terms if term in text)
    return score


def _local_classification_v10(context):
    meta = context.get("metadata", {})
    raw_context_text = str(context.get("texto", ""))
    main_context_text = raw_context_text.split("CONTEXTO_GENERAL:", 1)[0]
    text = f"{meta.get('numero', '')} {meta.get('emisor', '')} {meta.get('descripcion', '')} {raw_context_text}".lower()
    emisor = str(meta.get("emisor") or _infer_emisor_from_text(context.get("texto", ""))).upper()
    score = context.get("bank_score", _score_context_for_bank(context))
    numero = str(meta.get("numero") or meta.get("idnorma") or "").upper()
    tipo_norma = str(meta.get("tipo_norma") or _infer_tipo_norma_from_text(context.get("texto", ""))).upper()

    impact_bajo_terms = [
        "guía de identificación y reporte de alertas",
        "guia de identificacion y reporte de alertas",
        "sujetos obligados a informar a la uif",
        "uif-perú",
        "uif-peru",
        "sistema de video vigilancia",
        "videovigilancia",
        "obligatoriedad de implementar",
    ]

    no_terms = [
        "acuícola", "acuicola", "productores acuícolas", "productores acuicolas",
        "actividades acuícolas", "actividades acuicolas", "pesca artesanal",
        "sector agrario", "actividad turística", "actividad turistica",
        "adecuación ambiental de las actividades turísticas",
        "adecuacion ambiental de las actividades turisticas",
        "jurado nacional de elecciones", "jne", "jee", "propaganda electoral",
        "organización política", "organizacion politica", "candidato",
        "ministerio de educación", "ministerio de educacion", "minedu",
        "sunedu", "midagri", "sucamec",
        "autoridad de transporte urbano", "transporte urbano", "autobuses",
        "transporte regular de personas", "integración de transporte urbano",
        "integracion de transporte urbano", "recaudo",
        "reserva comunal", "ministerio de desarrollo agrario", "sernanp",
        "009-2024-jus",
    ]

    informativa_terms = [
        "índice de precios", "indice de precios", "índice de reajuste",
        "indice de reajuste", "capital social mínimo", "capital social minimo",
        "registros electrónicos", "registros electronicos", "sire",
        "sunat operaciones en línea", "sunat operaciones en linea",
        "dirección de correo electrónico", "direccion de correo electronico",
        "número de teléfono móvil", "numero de telefono movil",
        "régimen de percepciones del igv", "regimen de percepciones del igv",
        "bono al buen pagador", "impulso myperu",
        "empresas de arrendamiento financiero",
        "inclusión de productos bajo el régimen simplificado",
        "inclusion de productos bajo el regimen simplificado",
        "debida diligencia en el conocimiento del cliente",
    ]

    estado_text = f"{meta.get('numero', '')} {meta.get('emisor', '')} {meta.get('descripcion', '')} {main_context_text}".lower()
    estado_cause = _estado_emergencia_cause(estado_text)
    is_estado_emergencia = (
        "estado de emergencia" in estado_text
        and estado_cause
        and ("PCM" in numero or "PRESIDENCIA DEL CONSEJO" in estado_text.upper())
        and _is_actual_norm_header(main_context_text, numero, tipo_hint="DECRETO SUPREMO")
    )
    if is_estado_emergencia:
        return "SI", "INFORMATIVA", "INFORMATIVA", f"Estado de Emergencia por {estado_cause}; relevante para seguimiento del banco."

    if any(term in text for term in impact_bajo_terms):
        return "SI", "IMPACTO", "BAJO", "Obligación o acción concreta para el banco o sus establecimientos."

    municipal_discrimination = (
        "ordenanza" in text
        and ("discriminación" in text or "discriminacion" in text)
        and any(term in text for term in (
            "establecimientos abiertos", "atención al público", "atencion al publico",
            "licencia de funcionamiento", "clausura", "aviso obligatorio",
        ))
    )
    if municipal_discrimination:
        return "SI", "IMPACTO", "BAJO", "Ordenanza municipal con obligaciones de prevencion o aviso y sanciones aplicables a establecimientos abiertos al publico."

    if any(term in text for term in no_terms):
        return "NO", "NO", "NO APLICA", "No se identifica aplicación directa ni seguimiento relevante para el banco."

    is_labor_election_rule = (
        ("elecciones generales" in text or "miembro de mesa" in text or "miembros de mesa" in text)
        and ("-TR" in numero or "TRABAJO" in emisor)
    )

    if any(term in text for term in informativa_terms) or is_labor_election_rule or "INEI" in numero or "INEI" in emisor:
        return "SI", "INFORMATIVA", "INFORMATIVA", "Referencia o seguimiento para el banco, sin obligación directa de adecuación."

    alto_terms = [
        "acreedor garantizado",
        "ponderación de riesgo",
        "ponderacion de riesgo",
        "reglamento de gestión de conducta de mercado",
        "conducta de mercado",
        "continuidad del negocio",
        "servicios de pago interoperables",
        "interoperabilidad",
        "grupo económico",
        "límites operativos",
        "limites operativos",
        "grandes exposiciones",
        "manual de contabilidad",
        "tarjetas de crédito",
        "tarjetas de credito",
        "tarjetas de débito",
        "tarjetas de debito",
        "protección de datos",
        "proteccion de datos",
        "inteligencia artificial",
        "responsabilidad administrativa de las personas jurídicas",
        "personas juridicas",
        "sucave",
    ]
    medio_terms = [
        "sunarp",
        "materia registral",
        "disposiciones en materia registral",
        "garantías reales",
        "garantias reales",
        "hipotecas",
        "riesgo cambiario crediticio",
        "instrumentos financieros derivados",
        "clasificación y valorización de las inversiones",
        "clasificacion y valorizacion de las inversiones",
        "riesgo país",
        "riesgo pais",
        "persona expuesta políticamente",
        "persona expuesta politicamente",
        "central de riesgos",
        "compensación por tiempo de servicios",
        "compensacion por tiempo de servicios",
        "cts",
        "formulario trimestral de balanza de pagos",
    ]
    bajo_terms = [
        "fondo de seguro de depósitos",
        "fondo de seguro de depositos",
        "auditoría interna",
        "auditoria interna",
        "congelamiento administrativo",
        "servicios financieros",
        "atención preferente",
        "atencion preferente",
        "protección al consumidor",
        "proteccion al consumidor",
    ]

    if any(term in text for term in alto_terms):
        return "SI", "IMPACTO", "ALTO", "Impacto transversal o estructural para el banco o sistema financiero."
    if any(term in text for term in medio_terms):
        return "SI", "IMPACTO", "MEDIO", "Impacto regulatorio relevante con seguimiento o adecuación moderada."
    if any(term in text for term in bajo_terms):
        return "SI", "IMPACTO", "BAJO", "Impacto puntual o acotado para seguimiento operativo."
    if emisor in {"SBS", "BCRP"} and score >= 8 and any(term in text for term in alto_terms + medio_terms + bajo_terms):
        return "SI", "IMPACTO", "MEDIO", "Emisor financiero relevante con obligación o adecuación identificada."
    return "NO", "NO", "NO APLICA", "No se identifica interés para el banco."


def _local_row_from_context(context, analysis_date):
    meta = context.get("metadata", {})
    text = context.get("texto", "")
    filename = str(meta.get("filename") or "").strip()
    inferred_date = _date_from_filename(filename)
    fecha_emision = _first_available(meta.get("fecha_emision"), _infer_fecha_emision_from_text(text))
    numero = _first_available(meta.get("numero"), _infer_numero_from_text(text))
    descripcion = _first_available(meta.get("descripcion"), _infer_descripcion_from_text(text, numero=numero))
    interes_banco, interes_al_banco, nivel_impacto, justificacion = _local_classification_v10(context)

    row = {
        "IDNORMA": _first_available(meta.get("idnorma"), meta.get("numero")),
        "FECHA": _first_available(meta.get("fecha"), meta.get("fecha_publicacion"), inferred_date),
        "FECHA_EMISION": fecha_emision,
        "REGULADOR": _first_available(meta.get("regulador")),
        "EMISOR": _first_available(meta.get("emisor"), _infer_emisor_from_text(text)),
        "TIPO_NORMA": _first_available(meta.get("tipo_norma"), _infer_tipo_norma_from_text(text)),
        "NUMERO": numero,
        "DESCRIPCION": descripcion,
        "ESTADO": _first_available(meta.get("estado")),
        "NRO_BOLETIN": _first_available(meta.get("nro_boletin")),
        "FECHA_PUBLICACION": _first_available(meta.get("fecha_publicacion"), inferred_date),
        "C_NORMATIVO": interes_banco,
        "NIVEL_IMPACTO": nivel_impacto,
        "INTERES_BANCO": interes_banco,
        "INTERES_AL_BANCO": interes_al_banco,
        "JUSTIFICACION": justificacion,
        "IMPORTANCIA": "Si" if interes_banco == "SI" else "No",
        "REFERENCIA_HUMANA": "NO",
        "TOTAL_NORMAS_REVISADAS": 0,
    }
    return _finalize_v10_classification(row)


def split_contexts_for_llm(
    contexts,
    max_contexts,
    min_score,
    human_reference=None,
    enable_semantic=False,
    semantic_embed_model=None,
    semantic_cross_model=None,
    semantic_top_k=12,
    semantic_min_score=0.45,
):
    human_reference = human_reference or {}
    semantic_scores = {}
    if enable_semantic and max_contexts > 0:
        semantic_scores = semantic_prioritize_contexts(
            contexts,
            human_reference,
            embed_model_name=semantic_embed_model,
            cross_model_name=semantic_cross_model,
            top_k=semantic_top_k,
            min_score=semantic_min_score,
        )

    direct_impact_terms = [
        "guía de identificación y reporte de alertas",
        "guia de identificacion y reporte de alertas",
        "sujetos obligados a informar a la uif",
        "lavado de activos",
        "financiamiento del terrorismo",
        "conducta de mercado",
        "riesgo operacional",
        "riesgo de crédito",
        "riesgo de credito",
        "ciberseguridad",
        "seguridad de la información",
        "seguridad de la informacion",
        "continuidad del negocio",
        "interoperabilidad",
        "servicios de pago",
        "tarjetas de crédito",
        "tarjetas de credito",
        "tarjetas de débito",
        "tarjetas de debito",
        "protección de datos",
        "proteccion de datos",
        "videovigilancia",
        "obligatoriedad de implementar",
    ]

    selected = []
    local_only = []

    for context in contexts:
        context["bank_score"] = _score_context_for_bank(context)
        meta = context.get("metadata", {})
        text = f"{context.get('texto', '')} {meta.get('descripcion', '')}".lower()
        ref = _find_human_reference(
            {
                "NUMERO": meta.get("numero"),
                "IDNORMA": meta.get("idnorma"),
                "FECHA_PUBLICACION": meta.get("fecha_publicacion") or _date_from_filename(meta.get("filename")),
                "FECHA": meta.get("fecha"),
            },
            human_reference,
        )
        local_interes, local_categoria, _, _ = _local_classification_v10(context)

        exact_human_interest = ref.get("C_NORMATIVO") == "SI"
        direct_impact = local_interes == "SI" and local_categoria == "IMPACTO"
        strong_direct_signal = local_interes == "SI" and any(term in text for term in direct_impact_terms)
        semantic_match = semantic_scores.get(id(context))

        if exact_human_interest or direct_impact or strong_direct_signal or semantic_match:
            if exact_human_interest:
                context["llm_priority"] = 100
            elif direct_impact:
                context["llm_priority"] = 80
            elif semantic_match:
                context["llm_priority"] = 70
                context["semantic_cross_score"] = round(semantic_match["cross_score"], 4)
                context["semantic_similarity_score"] = round(semantic_match["semantic_score"], 4)
                context["semantic_match_numero"] = semantic_match.get("match_numero")
                context["semantic_match_nivel"] = semantic_match.get("match_nivel")
                context["semantic_match_justificacion"] = semantic_match.get("match_justificacion")
            else:
                context["llm_priority"] = 60
            selected.append(context)
        else:
            local_only.append(context)

    selected.sort(
        key=lambda ctx: (ctx.get("llm_priority", 0), ctx.get("bank_score", 0)),
        reverse=True
    )

    selected = selected[:max_contexts]
    selected_ids = {id(ctx) for ctx in selected}
    local_only.extend(ctx for ctx in contexts if id(ctx) not in selected_ids and ctx not in local_only)

    print(
        f"[HEURISTICA] "
        f"LLM={len(selected)} | "
        f"LOCAL={len(local_only)}"
    )
    if semantic_scores:
        selected_semantic = sum(1 for ctx in selected if ctx.get("semantic_cross_score") is not None)
        print(
            f"[SEMANTICO] top_k={semantic_top_k} | "
            f"min_score={semantic_min_score} | "
            f"seleccionadas={selected_semantic}"
        )

    return selected, local_only


def attach_pdf_links(rows, contexts, bucket, pdf_prefix, s3_client=None, human_reference=None):
    context_by_id = {}
    ordered_contexts = []

    for ctx in contexts:
        meta = ctx.get("metadata", {})
        full_context = {
            "meta": meta,
            "texto": ctx.get("texto", ""),
            "semantic": {
                "cross_score": ctx.get("semantic_cross_score"),
                "similarity_score": ctx.get("semantic_similarity_score"),
                "match_numero": ctx.get("semantic_match_numero"),
                "match_nivel": ctx.get("semantic_match_nivel"),
                "match_justificacion": ctx.get("semantic_match_justificacion"),
            },
        }
        ordered_contexts.append(full_context)
        context_id = str(meta.get("idnorma") or "").strip()
        if context_id:
            context_by_id[context_id] = full_context

    enriched = []

    for idx, row in enumerate(rows):
        row_copy = dict(row)
        row_id = str(row_copy.get("IDNORMA") or "").strip()
        context_pack = context_by_id.get(row_id)
        if context_pack is None and idx < len(ordered_contexts):
            context_pack = ordered_contexts[idx]
        if context_pack is None:
            context_pack = {"meta": {}, "texto": ""}

        meta = context_pack.get("meta", {})
        source_text = context_pack.get("texto", "")
        semantic = context_pack.get("semantic", {})
        filename = str(meta.get("filename") or "").strip()

        # Preservar el mejor NUMERO ya obtenido y usar el texto como apoyo, no como reemplazo ciego.
        numero_final = _normalize_numero(
            row_copy.get("NUMERO"),
            idnorma=row_copy.get("IDNORMA") or meta.get("idnorma") or meta.get("numero"),
            text=source_text,
        )
        row_copy["NUMERO"] = numero_final

        # Strict extraction for EMISOR
        emisor_candidates = [
            row_copy.get("EMISOR"),
            meta.get("emisor"),
            _infer_emisor_from_text(source_text),
        ]
        def clean_emisor(s):
            if not s: return ""
            return str(s).strip().upper()
        emisor_final = next((clean_emisor(e) for e in emisor_candidates if e and clean_emisor(e)), "NO DISPONIBLE")
        row_copy["EMISOR"] = emisor_final

        # Other fields (keep as before)
        row_copy["IDNORMA"] = _first_available(row_copy.get("IDNORMA"), meta.get("idnorma"), meta.get("numero"))
        row_copy["ESTADO"] = _first_available(row_copy.get("ESTADO"), meta.get("estado"))
        row_copy["TIPO_NORMA"] = _first_available(
            row_copy.get("TIPO_NORMA"),
            meta.get("tipo_norma"),
            _infer_tipo_norma_from_text(source_text),
        )
        row_copy["REGULADOR"] = _first_available(row_copy.get("REGULADOR"), meta.get("regulador"))
        row_copy["NRO_BOLETIN"] = _first_available(row_copy.get("NRO_BOLETIN"), meta.get("nro_boletin"))
        row_copy["FECHA_EMISION"] = _first_available(row_copy.get("FECHA_EMISION"), meta.get("fecha_emision"))
        row_copy["DESCRIPCION"] = _first_available(row_copy.get("DESCRIPCION"), meta.get("descripcion"))
        row_copy["SEMANTIC_CROSS_SCORE"] = _first_available(row_copy.get("SEMANTIC_CROSS_SCORE"), semantic.get("cross_score"))
        row_copy["SEMANTIC_SIMILARITY_SCORE"] = _first_available(row_copy.get("SEMANTIC_SIMILARITY_SCORE"), semantic.get("similarity_score"))
        row_copy["SEMANTIC_MATCH_NUMERO"] = _first_available(row_copy.get("SEMANTIC_MATCH_NUMERO"), semantic.get("match_numero"))
        row_copy["SEMANTIC_MATCH_NIVEL"] = _first_available(row_copy.get("SEMANTIC_MATCH_NIVEL"), semantic.get("match_nivel"))
        row_copy["SEMANTIC_MATCH_JUSTIFICACION"] = _first_available(row_copy.get("SEMANTIC_MATCH_JUSTIFICACION"), semantic.get("match_justificacion"))

        if _is_missing(row_copy.get("FECHA")):
            row_copy["FECHA"] = _first_available(meta.get("fecha"), meta.get("fecha_publicacion"))
        if _is_missing(row_copy.get("FECHA_PUBLICACION")):
            row_copy["FECHA_PUBLICACION"] = _first_available(meta.get("fecha_publicacion"), meta.get("fecha"))

        if filename:
            key = f"{pdf_prefix}{filename}"
            row_copy["PDF_S3_URI"] = f"s3://{bucket}/{key}"
            row_copy["PDF_URL"] = _presigned_pdf_url(s3_client, bucket, key)
            row_copy["PDF_PUBLIC_URL"] = _s3_https_url(bucket, key)
            row_copy["PDF_CONSOLE_URL"] = _s3_console_url(bucket, key)
            row_copy["PDF_KEY"] = key

            inferred_date = _date_from_filename(filename)
            if inferred_date:
                if _is_missing(row_copy.get("FECHA")):
                    row_copy["FECHA"] = inferred_date
                if _is_missing(row_copy.get("FECHA_PUBLICACION")):
                    row_copy["FECHA_PUBLICACION"] = inferred_date
        else:
            row_copy["PDF_S3_URI"] = "NO DISPONIBLE"
            row_copy["PDF_URL"] = ""
            row_copy["PDF_PUBLIC_URL"] = ""
            row_copy["PDF_CONSOLE_URL"] = ""
            row_copy["PDF_KEY"] = "NO DISPONIBLE"

        row_copy = _apply_human_reference(row_copy, human_reference or {})
        row_copy = _finalize_v10_classification(row_copy)
        row_copy["SEMAFORO"] = _impact_class(row_copy.get("NIVEL_IMPACTO"))

        enriched.append(row_copy)

    return enriched


def save_to_csv(rows, analysis_date, output_dir, total_normas_dia=0, output_file=None):
    if output_file:
        csv_path = output_dir / output_file
    else:
        csv_path = output_dir / "base de normas de interes.csv"
    columnas = [
        "FECHA_EJECUCION", "FECHA", "FECHA_EMISION", "FECHA_PUBLICACION", "IDNORMA",
        "TIPO_NORMA", "NUMERO", "DESCRIPCION", "EMISOR", "REGULADOR", "ESTADO",
        "NRO_BOLETIN", "C_NORMATIVO", "INTERES_BANCO", "INTERES_AL_BANCO",
        "NIVEL_IMPACTO", "JUSTIFICACION", "IMPORTANCIA", "REFERENCIA_HUMANA",
        "TOTAL_NORMAS_DIA", "PDF_S3_URI", "PDF_URL",
        "PRECISION_DIA", "CALIFICACION_HUMANA", "DESCRIPCION_HUMANA",
    ]

    filas = []
    for row in rows:
        row = _finalize_v10_classification(dict(row))
        fila = {col: _safe_value(row.get(col)) for col in columnas}
        fila["FECHA_EJECUCION"] = analysis_date.strftime("%Y-%m-%d")
        fila["TOTAL_NORMAS_DIA"] = total_normas_dia
        filas.append(fila)

    df_nuevo = pd.DataFrame(filas, columns=columnas)
    if csv_path.exists():
        df_existente = pd.read_csv(csv_path, encoding="utf-8-sig")
        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_combinado.drop_duplicates(subset=["FECHA_EJECUCION", "IDNORMA"], keep="last", inplace=True)
    else:
        df_combinado = df_nuevo

    df_combinado.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return csv_path


def enrich_rows_with_human_base(rows, analysis_date, s3_client, bucket):
    if not rows:
        return rows, 0.0

    human_key = (
        "discovery/comercial/sanherna/PLAFT/GenIA/Normativo/"
        "normas-plaft/base de normas de interes  completa.xlsx"
    )

    try:
        obj = s3_client.get_object(Bucket=bucket, Key=human_key)
        human_bytes = obj["Body"].read()
        df_human = pd.read_excel(io.BytesIO(human_bytes))
    except Exception as exc:
        print(f"⚠️ No se pudo leer la base humana desde S3: {exc}")
        return rows, 0.0

    df_assistant = pd.DataFrame(rows)

    def _norm_numero(value):
        if pd.isna(value):
            return ""
        return str(value).strip().upper()

    if "NUMERO" not in df_human.columns:
        print("⚠️ La base humana no tiene columna 'NUMERO'. Se omite el enriquecimiento.")
        return rows, 0.0

    df_assistant["NUMERO_NORM"] = df_assistant.get("NUMERO", "").apply(_norm_numero)
    df_human["NUMERO_NORM"] = df_human["NUMERO"].apply(_norm_numero)

    df_h_valid = df_human[df_human["NUMERO_NORM"] != ""].copy()
    df_a_valid = df_assistant[df_assistant["NUMERO_NORM"] != ""].copy()

    if df_h_valid.empty:
        precision_simple = 0.0
    else:
        df_matches = df_h_valid.merge(
            df_a_valid[["NUMERO_NORM"]].drop_duplicates(),
            on="NUMERO_NORM",
            how="inner",
        )
        precision_simple = len(df_matches) / len(df_h_valid)

    rename_map = {}
    merge_columns = ["NUMERO_NORM"]

    if "NIVEL_IMPACTO" in df_h_valid.columns:
        rename_map["NIVEL_IMPACTO"] = "CALIFICACION_HUMANA"
        merge_columns.append("NIVEL_IMPACTO")
    if "DESCRIPCION" in df_h_valid.columns:
        rename_map["DESCRIPCION"] = "DESCRIPCION_HUMANA"
        merge_columns.append("DESCRIPCION")

    if len(merge_columns) > 1:
        df_merge_data = df_h_valid[merge_columns].copy()
        df_merge_data.rename(columns=rename_map, inplace=True)
        df_assistant = df_assistant.merge(df_merge_data, on="NUMERO_NORM", how="left")
    else:
        df_assistant["CALIFICACION_HUMANA"] = ""
        df_assistant["DESCRIPCION_HUMANA"] = ""

    precision_pct = round(precision_simple * 100, 2)
    precision_label = f"{precision_pct:.2f}%"
    df_assistant["PRECISION_DIA"] = precision_label

    if "CALIFICACION_HUMANA" not in df_assistant.columns:
        df_assistant["CALIFICACION_HUMANA"] = ""
    if "DESCRIPCION_HUMANA" not in df_assistant.columns:
        df_assistant["DESCRIPCION_HUMANA"] = ""

    df_assistant["CALIFICACION_HUMANA"].fillna("SIN INFORMACION", inplace=True)
    df_assistant["DESCRIPCION_HUMANA"].fillna("SIN INFORMACION", inplace=True)

    df_assistant.drop(columns=["NUMERO_NORM"], inplace=True, errors="ignore")

    print(
        "📊 Comparación con base humana | "
        f"Precisión del {precision_label} sobre {len(df_h_valid)} normas humanas con número."
    )

    return df_assistant.to_dict("records"), precision_simple
def process_single_day(analysis_date, args, s3, api_key, llm_endpoint, llm_model, output_dir):
    """Procesa un solo día y retorna (csv_path, precision)."""
    start_date = analysis_date
    end_date = analysis_date

    print(f"\n{'='*60}")
    print(f"📅 Procesando día: {analysis_date.strftime('%d/%m/%Y')}")
    print(f"{'='*60}")

    source_metadata = {}
    if args.download_from_source:
        try:
            source_metadata = download_normas_from_source(
                s3, args.bucket, args.pdf_prefix, start_date, end_date
            ) or {}
        except Exception as exc:
            print(f"⚠️ Error en descarga (continuando con PDFs existentes en S3): {exc}")

    pdf_keys = list_pdfs_by_date_range(s3, args.bucket, args.pdf_prefix, start_date, end_date)
    print(f"Total PDFs en rango: {len(pdf_keys)}")

    all_documents = []
    for key in tqdm(pdf_keys, desc="Extracción PDFs"):
        filename = key.split("/")[-1]
        try:
            file_bytes = get_pdf_from_s3(s3, args.bucket, key)
            text = extract_text_from_pdf_bytes(file_bytes)
            if text.strip():
                all_documents.append({"filename": filename, "text": text, **source_metadata.get(filename, {})})
        except Exception as exc:
            print(f"Error leyendo {filename}: {exc}")

    print(f"Documentos con texto extraído: {len(all_documents)}")
    if not all_documents:
        print("⚠️ No hay documentos con texto para procesar.")
        return None, 0, 0

    # Convertir cada documento en uno o varios contextos para el LLM.
    # Cada PDF puede contener múltiples normas, por eso se separa en secciones/normas.
    contexts = []
    skipped_no_num = 0
    added = 0
    duplicates = 0
    seen_nums = set()

    for doc in all_documents:
        sections = split_text_into_norma_sections(doc["text"])
        if not sections:
            sections = [doc["text"][:3800]]

        for section_idx, section_text in enumerate(sections, start=1):
            # Intentar inferir número de norma del texto o usar metadata existente
            inferred_num = doc.get("numero") or _infer_numero_from_text(section_text) or ""
            numero_normalizado = _normalize_numero(inferred_num, idnorma=None, filename=None, text=section_text)

            # Si no se puede obtener un número válido, no enviar la sección al LLM
            if not numero_normalizado or numero_normalizado == "NO DISPONIBLE":
                skipped_no_num += 1
                continue
            if not _numero_matches_publication_year(numero_normalizado, analysis_date):
                skipped_no_num += 1
                continue

            fecha_emision = doc.get("fecha_emision") or _infer_fecha_emision_from_text(section_text) or "NO DISPONIBLE"

            key_num = str(numero_normalizado).strip().upper()
            if key_num in seen_nums:
                duplicates += 1
                continue

            seen_nums.add(key_num)

            contexts.append({
                "metadata": {
                    "filename": doc["filename"],
                    "idnorma": numero_normalizado,
                    "fecha": doc.get("fecha") or analysis_date.strftime("%d/%m/%Y"),
                    "fecha_emision": fecha_emision,
                    "regulador": doc.get("regulador"),
                    "emisor": doc.get("emisor"),
                    "tipo_norma": doc.get("tipo_norma"),
                    "numero": numero_normalizado,
                    "descripcion": doc.get("descripcion"),
                    "estado": doc.get("estado"),
                    "nro_boletin": doc.get("nro_boletin"),
                    "fecha_publicacion": doc.get("fecha_publicacion") or analysis_date.strftime("%d/%m/%Y"),
                    "source_title": doc.get("source_title"),
                },
                "texto": (
                    section_text[:2000] +
                    "\n\nCONTEXTO_GENERAL:\n" +
                    doc["text"][:3000]
                ),
                "impacto": "PENDIENTE",
                "score": 0.0,
            })
            added += 1

    human_reference = load_human_reference(args.human_reference_file)

    if len(contexts) > len(pdf_keys) * 3:
        print(f"⚠️ Se generaron {len(contexts)} contextos para {len(pdf_keys)} PDFs; esto puede aumentar latencia y costo.")

    print(f"📋 Contextos preparados: {len(contexts)} (añadidos: {added}, saltados sin número: {skipped_no_num}, duplicados descartados: {duplicates})")
    llm_contexts, local_contexts = split_contexts_for_llm(
        contexts,
        max_contexts=args.llm_max_contexts,
        min_score=args.llm_min_score,
        human_reference=human_reference,
        enable_semantic=args.enable_semantic_prioritization,
        semantic_embed_model=args.semantic_embed_model,
        semantic_cross_model=args.semantic_cross_model,
        semantic_top_k=args.semantic_top_k,
        semantic_min_score=args.semantic_min_score,
    )
    print(
        "📋 Selección híbrida _7: "
        f"{len(llm_contexts)} normas al LLM | {len(local_contexts)} clasificadas localmente | "
        f"score mínimo: {args.llm_min_score}"
    )

    pregunta = """
Eres un Analista Normativo Senior de Interbank. Debes clasificar normas del Diario Oficial El Peruano con el criterio del archivo humano `Comparativo de identificación de normas VF (1).xlsx`.

CAMPOS CLAVE
- C_NORMATIVO: usar exactamente SI o NO. Indica si la norma tiene interes para el banco.
- INTERES_BANCO: usar exactamente SI o NO y debe coincidir con C_NORMATIVO.
- INTERES_AL_BANCO: usar exactamente SI o NO.
- NIVEL_IMPACTO: si INTERES_AL_BANCO=SI, usar INFORMATIVA, ALTO, MEDIO o BAJO. Si INTERES_AL_BANCO=NO, usar NO APLICA.

REGLA PRINCIPAL
1. Primero decide si la norma es de interes para el banco: C_NORMATIVO/INTERES_BANCO = SI o NO.
2. Si es NO, INTERES_AL_BANCO = NO y NIVEL_IMPACTO = NO APLICA.
3. Si es SI, decide si el NIVEL_IMPACTO es INFORMATIVA o ALTO/MEDIO/BAJO.
4. INFORMATIVA: sirve para seguimiento, referencia o conocimiento del banco, pero no genera obligacion directa ni adecuacion concreta.
5. IMPACTO: genera accion, obligacion, adecuacion, reporte, control, restriccion o seguimiento operativo/regulatorio concreto.
6. Solo cuando haya impacto real asigna NIVEL_IMPACTO ALTO, MEDIO o BAJO.

PATRONES DEL EXCEL HUMANO PARA INFORMATIVA
- Estados de emergencia o prorrogas `-PCM`: normalmente SI / INFORMATIVA.
- Bonos soberanos, endeudamiento interno o normas `-EF` aprovechables comercialmente: SI / INFORMATIVA.
- Indices INEI o BCRP usados por el banco: SI / INFORMATIVA.
- Regimen de intervencion, disolucion o autorizacion de cajas, financieras, aseguradoras o bancos: SI / INFORMATIVA si no impone una accion directa a Interbank.
- SUNAT/SIRE/registros electronicos con seguimiento tributario general: SI / INFORMATIVA.
- Elecciones, miembros de mesa o medidas laborales generales: SI / INFORMATIVA cuando interesan a RRHH.
- Normas de arrendamiento financiero, debida diligencia o TUPA SBS sin obligacion directa inmediata para Interbank: SI / INFORMATIVA.

PATRONES PARA IMPACTO
- Guia de identificacion y reporte de alertas UIF o sujetos obligados: IMPACTO BAJO, salvo que el texto imponga cambios transversales mayores.
- Obligacion de implementar videovigilancia o controles en establecimientos del banco: IMPACTO BAJO.
- Cambios estructurales SBS/BCRP sobre conducta de mercado, riesgos, pagos, tarjetas, datos, PLAFT, continuidad, capital, contabilidad o reportes: IMPACTO ALTO/MEDIO/BAJO segun alcance.

PATRONES PARA NO
- Normas sectoriales sin relacion bancaria, por ejemplo acuicultura, turismo ambiental, pesca artesanal o agro sin efecto financiero ni seguimiento para Interbank.
- Designaciones, viajes, renuncias o actos puramente administrativos sin seguimiento relevante.

DESCRIPCION
- Copia o reconstruye el titulo principal de la norma.
- No uses una descripcion generica como "Norma relevante para el banco".

FORMATO OBLIGATORIO
Responder SOLO en bloques de texto plano. Cada bloque debe iniciar y terminar con una linea exacta:
----------------------------------------

Formato exacto:
----------------------------------------
IDNORMA:
FECHA:
FECHA_EMISION:
REGULADOR:
EMISOR:
TIPO_NORMA:
NUMERO:
DESCRIPCION:
ESTADO:
NRO_BOLETIN:
FECHA_PUBLICACION:
C_NORMATIVO:
INTERES_BANCO:
INTERES_AL_BANCO:
NIVEL_IMPACTO:
JUSTIFICACION:
IMPORTANCIA:
----------------------------------------

Valores permitidos:
- C_NORMATIVO: SI o NO
- INTERES_BANCO: SI o NO
- INTERES_AL_BANCO: SI o NO
- NIVEL_IMPACTO: INFORMATIVA, ALTO, MEDIO, BAJO, NO APLICA
- IMPORTANCIA: Si o No

No responder JSON. No agregar texto fuera de los bloques. No inventar datos; si un campo no esta disponible, usar NO DISPONIBLE.
"""

    respuesta = rag_answer(pregunta, llm_contexts, api_key, llm_model, endpoint=llm_endpoint)

    rows = parse_rag_output_to_rows(respuesta)
    rows = attach_pdf_links(rows, llm_contexts, args.bucket, args.pdf_prefix, s3_client=s3, human_reference=human_reference)

    local_rows = [_local_row_from_context(ctx, analysis_date) for ctx in local_contexts]
    local_rows = attach_pdf_links(local_rows, local_contexts, args.bucket, args.pdf_prefix, s3_client=s3, human_reference=human_reference)
    rows.extend(local_rows)
    rows.extend(_missing_human_reference_rows(rows, human_reference, analysis_date))

    # Filtrar registros no válidos y eliminar duplicados antes de guardar
    rows = [row for row in rows if not _should_skip_row(row)]
    rows.sort(
        key=lambda row: (
            _normalize_si_no(row.get("REFERENCIA_HUMANA"), default="NO") == "SI",
            _normalize_si_no(row.get("INTERES_AL_BANCO"), default="NO") == "SI",
        ),
        reverse=True,
    )
    rows = _dedupe_rows(rows)

    # Guardar absolutamente todas las normas, sin filtrar por número
    total_all = len(rows)

    # Agregar columnas de control
    for row in rows:
        row["TOTAL_NORMAS_REVISADAS"] = len(contexts)

    csv_path = save_to_csv(rows, analysis_date, output_dir, total_normas_dia=len(pdf_keys), output_file=args.output_file)
    print(f"✅ CSV actualizado: {csv_path}")
    print(
        f"📈 Normas guardadas: {len(rows)} | Total clasificadas: {total_all} | "
        f"LLM: {len(llm_contexts)} | Local: {len(local_contexts)} | PDFs día: {len(pdf_keys)}"
    )

    return csv_path, len(rows), len(contexts)


def main():
    args = parse_args()

    # Resolver backend LLM
    api_key, llm_endpoint = resolve_llm_config(args.llm_backend)
    llm_model = args.copilot_model if args.llm_backend == "copilot" else args.groq_model
    print(f"🤖 Backend LLM: {args.llm_backend} | Modelo: {llm_model}")

    s3 = get_s3_client()
    if LOCAL_MODE:
        print("[INFO] ✓ Usando almacenamiento LOCAL (STORAGE_MODE=local)")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_date = datetime.strptime(args.analysis_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else start_date

    current = start_date
    results_summary = []

    while current <= end_date:
        try:
            csv_path, n_clasificadas, n_revisadas = process_single_day(
                current, args, s3, api_key, llm_endpoint, llm_model, output_dir
            )
            results_summary.append({
                "fecha": current.strftime("%Y-%m-%d"),
                "clasificadas": n_clasificadas,
                "revisadas": n_revisadas,
                "csv_path": str(csv_path) if csv_path else "SIN DATOS",
            })
        except Exception as exc:
            print(f"❌ Error procesando {current.strftime('%d/%m/%Y')}: {exc}")
            results_summary.append({
                "fecha": current.strftime("%Y-%m-%d"),
                "clasificadas": 0,
                "revisadas": 0,
                "csv_path": f"ERROR: {exc}",
            })

        current += timedelta(days=1)

    # Resumen final
    if len(results_summary) > 1:
        print(f"\n{'='*60}")
        print("📊 RESUMEN DE EJECUCIÓN")
        print(f"{'='*60}")
        for r in results_summary:
            print(f"  {r['fecha']} | Clasificadas: {r['clasificadas']} | Revisadas: {r['revisadas']} | {r['csv_path']}")


if __name__ == "__main__":
    main()
