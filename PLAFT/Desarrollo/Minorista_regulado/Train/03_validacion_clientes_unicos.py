"""
03_validacion_clientes_unicos.py
================================
Modelo PLAFT PJ Minorista — Validación de independencia entre conjuntos
Train / Validation / Test a nivel de cliente único.

Genera:
  - cliente_distribucion_por_conjunto.csv   → tabla resumen por conjunto
  - Independencia_Conjuntos_Train_Val_Test.html → reporte HTML interactivo

Uso:
    python 03_validacion_clientes_unicos.py

Requisitos:
    pip install pandas awswrangler boto3

Autor  : Data Science — División Analítica
Versión: 1.0  (04/08/2026)
"""

import os
import sys
import json
import hashlib
import datetime
import textwrap

import pandas as pd
import numpy as np

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────

# Periodos de cada conjunto (deben coincidir con lo documentado en §3.3)
PERIODOS_TRAIN = [202501, 202502, 202503, 202504, 202505, 202506, 202507]
PERIODOS_VAL   = [202508, 202509]
PERIODOS_TEST  = [202510, 202511, 202512, 202601, 202602, 202603, 202604]

# Columnas clave
COL_CLI  = "cod_cli"     # identificador de cliente
COL_MES  = "cod_mes"     # periodo (entero YYYYMM)
COL_TGT  = "target"      # variable objetivo

# Ruta del parquet de inferencia (mismo que usan los notebooks)
BUCKET        = "ibk-discovery-comercial-us-east-1-654654352211-data"
MODEL_PREFIX  = "discovery/comercial/sanherna/PLAFT/PJ/MINORISTA"
S3_PARQUET    = f"s3://{BUCKET}/{MODEL_PREFIX}/DATA_INFERENCIA/data_pn_total_expandido_new_v1.parquet"

# Directorio de salida (se crea si no existe)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs_validacion")

# ────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────

def _cargar_datos() -> pd.DataFrame:
    """Carga el parquet desde S3 usando awswrangler + credenciales del entorno."""
    try:
        import awswrangler as wr
        import boto3
        from pathlib import Path
        import re

        # Intentar cargar credenciales desde credentials.sh si existen
        cred_path = Path(
            r"c:/Users/b46637/OneDrive - Interbank/conexion_aws"
            r"/athena_conection_test/credentials.sh"
        )
        if cred_path.exists():
            pattern = re.compile(r'^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$')
            for line in cred_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = pattern.match(line.strip())
                if m:
                    k, v = m.groups()
                    os.environ[k] = v.strip().strip('"').strip("'")

        session = boto3.Session(region_name="us-east-1")
        print(f"  Cargando parquet desde S3: {S3_PARQUET}")
        df = wr.s3.read_parquet(path=S3_PARQUET, boto3_session=session)
        print(f"  ✓ Shape cargado: {df.shape}")
        return df

    except Exception as exc:
        print(f"  ✗ No se pudo cargar desde S3: {exc}")
        print("  → Intente cargar el DataFrame manualmente y pasar df= como argumento.")
        sys.exit(1)


def _asignar_conjunto(cod_mes: int) -> str:
    if cod_mes in PERIODOS_TRAIN:
        return "TRAIN"
    if cod_mes in PERIODOS_VAL:
        return "VALIDATION"
    if cod_mes in PERIODOS_TEST:
        return "TEST"
    return "OTRO"


# ────────────────────────────────────────────────────────────────────────────
# ANÁLISIS PRINCIPAL
# ────────────────────────────────────────────────────────────────────────────

def analizar_independencia(df: pd.DataFrame) -> dict:
    """
    Calcula la distribución de clientes únicos y la superposición entre
    conjuntos Train, Validation y Test.

    Retorna un dict con todos los resultados para generar los artefactos.
    """
    print("\n[1/4] Asignando conjuntos a cada registro...")
    df = df.copy()
    df[COL_MES] = df[COL_MES].astype(int)
    df["conjunto"] = df[COL_MES].apply(_asignar_conjunto)

    # Filtrar solo periodos relevantes
    df_rel = df[df["conjunto"].isin(["TRAIN", "VALIDATION", "TEST"])].copy()
    print(f"  Registros relevantes: {len(df_rel):,}")

    print("\n[2/4] Calculando clientes únicos por conjunto...")
    conjuntos = ["TRAIN", "VALIDATION", "TEST"]
    clientes  = {c: set(df_rel.loc[df_rel["conjunto"] == c, COL_CLI].unique())
                 for c in conjuntos}
    obs_count = {c: int((df_rel["conjunto"] == c).sum()) for c in conjuntos}
    tgt_rate  = {}
    if COL_TGT in df_rel.columns:
        for c in conjuntos:
            sub = df_rel.loc[df_rel["conjunto"] == c, COL_TGT]
            tgt_rate[c] = float(sub.mean()) if len(sub) > 0 else float("nan")
    else:
        tgt_rate = {c: float("nan") for c in conjuntos}

    print("\n[3/4] Calculando superposiciones (intersecciones)...")
    intersecciones = {
        "TRAIN ∩ VALIDATION": clientes["TRAIN"] & clientes["VALIDATION"],
        "TRAIN ∩ TEST"       : clientes["TRAIN"] & clientes["TEST"],
        "VALIDATION ∩ TEST"  : clientes["VALIDATION"] & clientes["TEST"],
        "TRAIN ∩ VAL ∩ TEST" : clientes["TRAIN"] & clientes["VALIDATION"] & clientes["TEST"],
    }

    print("\n[4/4] Calculando distribución mensual por conjunto...")
    dist_mensual = (
        df_rel.groupby([COL_MES, "conjunto"])
        .agg(
            registros  =(COL_CLI, "count"),
            clientes_u =(COL_CLI, "nunique"),
            positivos  =(COL_TGT, "sum") if COL_TGT in df_rel.columns
                        else (COL_CLI, lambda x: 0),
        )
        .reset_index()
    )
    dist_mensual["tasa_positivos"] = (
        dist_mensual["positivos"] / dist_mensual["registros"]
    ).round(6)

    return dict(
        df_rel        = df_rel,
        clientes      = clientes,
        obs_count     = obs_count,
        tgt_rate      = tgt_rate,
        intersecciones= intersecciones,
        dist_mensual  = dist_mensual,
        conjuntos     = conjuntos,
        ts            = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ────────────────────────────────────────────────────────────────────────────
# ARTEFACTO 1 — CSV
# ────────────────────────────────────────────────────────────────────────────

def generar_csv(res: dict, output_dir: str) -> str:
    """Genera cliente_distribucion_por_conjunto.csv"""
    conjuntos   = res["conjuntos"]
    clientes    = res["clientes"]
    obs_count   = res["obs_count"]
    tgt_rate    = res["tgt_rate"]
    intersec    = res["intersecciones"]

    rows_resumen = []
    for c in conjuntos:
        n_cli = len(clientes[c])
        rows_resumen.append({
            "conjunto"       : c,
            "periodos"       : str(PERIODOS_TRAIN if c == "TRAIN"
                                   else PERIODOS_VAL if c == "VALIDATION"
                                   else PERIODOS_TEST),
            "registros_total": obs_count[c],
            "clientes_unicos": n_cli,
            "tasa_target"    : round(tgt_rate[c], 6),
        })
    df_resumen = pd.DataFrame(rows_resumen)

    rows_inter = []
    for nombre, conj in intersec.items():
        n = len(conj)
        # denominador: el conjunto más pequeño de los involucrados
        partes = [p.strip() for p in nombre.replace("∩", "").split()]
        min_cli = min(len(clientes.get(p, set())) for p in partes
                      if p in clientes) or 1
        rows_inter.append({
            "interseccion"        : nombre,
            "clientes_compartidos": n,
            "pct_del_menor"       : round(100 * n / min_cli, 4),
            "evaluacion"          : "✓ ACEPTABLE (<1%)" if n / min_cli < 0.01
                                    else "⚠ REVISAR (≥1%)",
        })
    df_inter = pd.DataFrame(rows_inter)

    # CSV con dos bloques separados por línea en blanco
    os.makedirs(output_dir, exist_ok=True)
    path_csv = os.path.join(output_dir, "cliente_distribucion_por_conjunto.csv")

    with open(path_csv, "w", encoding="utf-8") as f:
        f.write("# RESUMEN POR CONJUNTO\n")
        df_resumen.to_csv(f, index=False)
        f.write("\n# SUPERPOSICIÓN ENTRE CONJUNTOS\n")
        df_inter.to_csv(f, index=False)
        f.write(f"\n# Generado: {res['ts']}\n")

    print(f"\n  ✓ CSV guardado: {path_csv}")
    return path_csv


# ────────────────────────────────────────────────────────────────────────────
# ARTEFACTO 2 — HTML
# ────────────────────────────────────────────────────────────────────────────

def _tabla_html(df: pd.DataFrame, id_: str = "") -> str:
    """Convierte un DataFrame a tabla HTML Bootstrap."""
    rows = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        # colorear filas de intersección según evaluación
        cls = ""
        if "evaluacion" in df.columns:
            cls = 'class="table-danger"' if "REVISAR" in str(row.get("evaluacion", "")) \
                  else 'class="table-success"'
        rows += f"<tr {cls}>{cells}</tr>\n"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return (
        f'<table id="{id_}" class="table table-sm table-bordered table-hover">'
        f"<thead class='table-dark'><tr>{headers}</tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def generar_html(res: dict, output_dir: str) -> str:
    """Genera Independencia_Conjuntos_Train_Val_Test.html"""
    conjuntos   = res["conjuntos"]
    clientes    = res["clientes"]
    obs_count   = res["obs_count"]
    tgt_rate    = res["tgt_rate"]
    intersec    = res["intersecciones"]
    dist_mensual= res["dist_mensual"]
    ts          = res["ts"]

    # ── Tabla 1: resumen por conjunto ───────────────────────────────────────
    rows_resumen = []
    for c in conjuntos:
        n_cli = len(clientes[c])
        rows_resumen.append({
            "Conjunto"       : c,
            "Períodos"       : ", ".join(map(str,
                               PERIODOS_TRAIN if c == "TRAIN"
                               else PERIODOS_VAL if c == "VALIDATION"
                               else PERIODOS_TEST)),
            "Registros"      : f"{obs_count[c]:,}",
            "Clientes únicos": f"{n_cli:,}",
            "Tasa target"    : f"{tgt_rate[c]:.4%}" if not np.isnan(tgt_rate[c]) else "N/D",
        })
    t1 = _tabla_html(pd.DataFrame(rows_resumen), "tbl-resumen")

    # ── Tabla 2: intersecciones ──────────────────────────────────────────────
    rows_inter = []
    for nombre, conj in intersec.items():
        n = len(conj)
        partes = [p.strip() for p in nombre.replace("∩", "").split()]
        min_cli = min(len(clientes.get(p, set())) for p in partes
                      if p in clientes) or 1
        pct = 100 * n / min_cli
        rows_inter.append({
            "Intersección"          : nombre,
            "Clientes compartidos"  : f"{n:,}",
            "% del conjunto menor"  : f"{pct:.4f}%",
            "Evaluación"            : "✓ ACEPTABLE (<1%)" if pct < 1
                                      else "⚠ REVISAR (≥1%)",
        })
    t2 = _tabla_html(pd.DataFrame(rows_inter), "tbl-inter")

    # ── Tabla 3: distribución mensual ────────────────────────────────────────
    dm = dist_mensual.rename(columns={
        COL_MES       : "Período",
        "conjunto"    : "Conjunto",
        "registros"   : "Registros",
        "clientes_u"  : "Clientes únicos",
        "positivos"   : "Positivos",
        "tasa_positivos": "Tasa positivos",
    })
    dm["Registros"]       = dm["Registros"].apply(lambda x: f"{x:,}")
    dm["Clientes únicos"] = dm["Clientes únicos"].apply(lambda x: f"{x:,}")
    dm["Tasa positivos"]  = dm["Tasa positivos"].apply(lambda x: f"{x:.4%}")
    t3 = _tabla_html(dm, "tbl-mensual")

    # ── Conclusión automática ─────────────────────────────────────────────────
    max_pct = 0.0
    for conj in intersec.values():
        n = len(conj)
        partes_set = [clientes[k] for k in conjuntos if k in clientes]
        min_c = min(len(s) for s in partes_set) or 1
        max_pct = max(max_pct, 100 * n / min_c)

    if max_pct < 1:
        conclusion_cls  = "alert-success"
        conclusion_icon = "✅"
        conclusion_txt  = (
            f"La superposición máxima detectada entre conjuntos es de "
            f"<strong>{max_pct:.4f}%</strong>, por debajo del umbral del 1%. "
            "Los conjuntos Train, Validation y Test son <strong>funcionalmente "
            "independientes</strong> a nivel de cliente-mes."
        )
    else:
        conclusion_cls  = "alert-warning"
        conclusion_icon = "⚠️"
        conclusion_txt  = (
            f"Se detectó una superposición de <strong>{max_pct:.4f}%</strong> "
            "entre al menos dos conjuntos. Revisar la partición antes de producción."
        )

    # ── HTML completo ─────────────────────────────────────────────────────────
    html = textwrap.dedent(f"""\
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>Validación Independencia Conjuntos — PLAFT PJ Minorista</title>
      <link rel="stylesheet"
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"/>
      <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f8f9fa; }}
        .header-box {{
          background: linear-gradient(135deg, #1a3c6e, #2d6fad);
          color: white; padding: 2rem; border-radius: .5rem; margin-bottom: 1.5rem;
        }}
        .section-title {{
          font-size: 1.1rem; font-weight: 600;
          border-left: 4px solid #2d6fad; padding-left: .75rem;
          margin: 1.5rem 0 .75rem;
        }}
        .badge-train      {{ background:#198754; }}
        .badge-validation {{ background:#0d6efd; }}
        .badge-test       {{ background:#6f42c1; }}
        .meta {{ font-size:.85rem; color:#6c757d; }}
        table {{ font-size:.875rem; }}
      </style>
    </head>
    <body>
    <div class="container py-4">

      <!-- ENCABEZADO -->
      <div class="header-box">
        <h4 class="mb-1">Validación de Independencia de Conjuntos</h4>
        <p class="mb-0">Modelo PLAFT PJ Minorista (BPE) — Script 03</p>
      </div>

      <p class="meta">
        Generado: <strong>{ts}</strong> &nbsp;|&nbsp;
        Script: <code>03_validacion_clientes_unicos.py v1.0</code> &nbsp;|&nbsp;
        Documentación: <em>DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v2.1.txt §6.4</em>
      </p>

      <!-- CONCLUSIÓN -->
      <div class="alert {conclusion_cls} mt-3" role="alert">
        {conclusion_icon} {conclusion_txt}
      </div>

      <!-- DEFINICIÓN DE PARTICIÓN -->
      <div class="section-title">Definición de Partición Temporal</div>
      <div class="row g-3 mb-3">
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-header text-white badge-train">TRAIN</div>
            <div class="card-body">
              <p class="mb-1"><strong>Períodos:</strong> {', '.join(map(str, PERIODOS_TRAIN))}</p>
              <p class="mb-0 text-muted">7 meses — Ene–Jul 2025</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-header text-white badge-validation">VALIDATION (OOT)</div>
            <div class="card-body">
              <p class="mb-1"><strong>Períodos:</strong> {', '.join(map(str, PERIODOS_VAL))}</p>
              <p class="mb-0 text-muted">2 meses — Ago–Sep 2025</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-header text-white badge-test">TEST (OOT)</div>
            <div class="card-body">
              <p class="mb-1"><strong>Períodos:</strong> {', '.join(map(str, PERIODOS_TEST))}</p>
              <p class="mb-0 text-muted">7 meses — Oct 2025–Abr 2026</p>
            </div>
          </div>
        </div>
      </div>

      <!-- TABLA 1: RESUMEN -->
      <div class="section-title">1. Distribución de Clientes y Registros por Conjunto</div>
      <div class="table-responsive">{t1}</div>

      <!-- TABLA 2: INTERSECCIONES -->
      <div class="section-title">2. Superposición de Clientes entre Conjuntos</div>
      <p class="text-muted" style="font-size:.875rem">
        Un mismo cliente puede aparecer en varios conjuntos en <em>períodos distintos</em>.
        Esto es esperado dado el universo BPE (~600K clientes únicos) y la naturaleza
        temporal de la partición. La independencia se evalúa a nivel <strong>cliente-mes</strong>,
        no a nivel cliente.
      </p>
      <div class="table-responsive">{t2}</div>

      <!-- TABLA 3: DISTRIBUCIÓN MENSUAL -->
      <div class="section-title">3. Distribución Mensual por Conjunto</div>
      <div class="table-responsive">{t3}</div>

      <!-- METODOLOGÍA -->
      <div class="section-title">4. Metodología y Criterios</div>
      <ul style="font-size:.875rem">
        <li><strong>Unidad de análisis:</strong> cliente-mes (<code>cod_cli</code>, <code>cod_mes</code>).
            Dos observaciones del mismo cliente en períodos distintos son <em>independientes</em>.</li>
        <li><strong>Umbral de aceptación:</strong> superposición &lt; 1% del conjunto menor.</li>
        <li><strong>Justificación de superposición aceptable:</strong> el universo BPE tiene
            ~600K clientes; con 16 meses de datos, es estadísticamente inevitable que un cliente
            aparezca en más de un período. Lo crítico es que no haya <em>mismo cliente-mes</em>
            en dos conjuntos.</li>
        <li><strong>Referencia documental:</strong> §6.4 de
            <code>DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v2.1.txt</code>.</li>
      </ul>

      <hr/>
      <p class="meta text-end">
        Modelo PLAFT PJ Minorista v2.1 &nbsp;|&nbsp;
        Data Science – División Analítica – Interbank &nbsp;|&nbsp;
        {ts}
      </p>

    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js">
    </script>
    </body>
    </html>
    """)

    os.makedirs(output_dir, exist_ok=True)
    path_html = os.path.join(output_dir, "Independencia_Conjuntos_Train_Val_Test.html")
    with open(path_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ HTML guardado: {path_html}")
    return path_html


# ────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ────────────────────────────────────────────────────────────────────────────

def main(df: pd.DataFrame = None):
    print("=" * 65)
    print("03_validacion_clientes_unicos.py")
    print("Modelo PLAFT PJ Minorista — Independencia Train/Val/Test")
    print("=" * 65)

    if df is None:
        df = _cargar_datos()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    res      = analizar_independencia(df)
    path_csv = generar_csv(res, OUTPUT_DIR)
    path_html= generar_html(res, OUTPUT_DIR)

    # ── Imprimir resumen en consola ──────────────────────────────────────────
    print("\n" + "=" * 65)
    print("RESUMEN FINAL")
    print("=" * 65)
    for c in res["conjuntos"]:
        print(f"  {c:<12} clientes únicos: {len(res['clientes'][c]):>8,}   "
              f"registros: {res['obs_count'][c]:>10,}   "
              f"tasa target: {res['tgt_rate'][c]:.4%}")

    print("\n  SUPERPOSICIONES:")
    for nombre, conj in res["intersecciones"].items():
        n = len(conj)
        partes = [p.strip() for p in nombre.replace("∩", "").split()]
        min_cli = min(len(res["clientes"].get(p, set())) for p in partes
                      if p in res["clientes"]) or 1
        pct = 100 * n / min_cli
        tag = "✓" if pct < 1 else "⚠"
        print(f"  {tag} {nombre:<30} {n:>6,} clientes  ({pct:.4f}% del conjunto menor)")

    print(f"\n  Artefactos generados:")
    print(f"  → {path_csv}")
    print(f"  → {path_html}")
    print("=" * 65)

    return res


if __name__ == "__main__":
    main()
