"""
04_reportes_preprocesamiento.py
================================
Modelo PLAFT PJ Minorista — Reportes de calidad de preprocesamiento

Genera:
  outputs_preprocesamiento/
    01_Missing_PreImputacion.csv       → % de nulos por variable antes de imputación
    02_Estadisticos_PostImputacion.csv → estadísticos descriptivos post-imputación
    03_Outliers_Detectados.csv         → variables con outliers (percentiles 1/99)

Uso:
    python 04_reportes_preprocesamiento.py

Requisitos:
    pip install pandas awswrangler boto3

Autor  : Data Science — División Analítica
Versión: 1.0  (04/08/2026)
Ref.   : DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v2.1.txt §8
"""

import os
import re
import sys
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────

# Variables finales del modelo (32) — nomenclatura dataset
VARIABLES_MODELO = [
    "cnt_trx_cargostot_3m",
    "imp_trx_abonosefect_6m",
    "cnt_alerta_hist",
    "imp_trx_cargosefe_6m",
    "rat_pastot_x_ingtot_6m",
    "mto_del_ext_12m",
    "num_antiguedad",
    "mto_pas_soles",
    "cnt_meses_sinegresos_12m",
    "rat_abonos_1m_vs_6m",
    "rat_mntcrgsefetot_1m",
    "ratio_cargos_1m_vs_6m",
    "rat_ing_tot_x_factura_6m",
    "cnt_trx_abonospromtot_3m",
    "mto_fact_declarado_sunat",
    "rat_cntros_x_cnttrxegr_3m",
    "rat_ing_ext_x_ing_tot_12m",
    "cod_ubigeo_cd",
    "cnt_noticias",
    "cnt_ros_hist",
    "avg_cpmenegr_12m",
    "max_mto_cpegrmen_12m",
    "cod_sectorista_id",
    "avg_trx_cargostot_3m",
    "share_cp_ingresos",
    "mto_al_ext_12m",
    "rat_trx_abonosefectot_3m",
    "flg_alerta_12m",
    "share_cp_egresos",
    "ratio_egresos_exterior",
    "cnt_trx_sinenv_alext_12m",
    "avg_cp_men_ing_12m",
]

# Periodos del universo completo
PERIODOS_TODOS = [
    202501, 202502, 202503, 202504, 202505, 202506, 202507,
    202508, 202509,
    202510, 202511, 202512, 202601, 202602, 202603, 202604,
]

PERIODOS_TRAIN = [202501, 202502, 202503, 202504, 202505, 202506, 202507]

COL_CLI = "cod_cli"
COL_MES = "cod_mes"
COL_TGT = "target"

# Reglas de imputación por tipo de variable (§8.2 del documento metodológico)
# Formato: prefijo_o_nombre → estrategia
REGLAS_IMPUTACION = {
    # Transaccionales → 0
    "cnt_trx_":      "0 (sin actividad)",
    "imp_trx_":      "0 (sin actividad)",
    "avg_trx_":      "0 (sin actividad)",
    # Ratios → mediana por segmento
    "rat_":          "mediana por segmento",
    "ratio_":        "mediana por segmento",
    "share_":        "mediana por segmento",
    # Flags/variación → 0
    "flg_":          "0 (ausencia = No)",
    # Montos externos → 0
    "mto_":          "0 (sin actividad)",
    # Conteos históricos → 0
    "cnt_":          "0 (sin actividad)",
    # Antigüedad → mediana población
    "num_antiguedad":"mediana de la población (últimas 12 meses)",
    # Geográfico/sector → 'SIN_INFO'
    "cod_ubigeo_cd": "SIN_INFO",
    "cod_sectorista_id": "SIN_INFO",
}

UMBRAL_MISSING_ELIMINAR = 20.0   # % de nulos para marcar como eliminable
UMBRAL_OUTLIER_CAP      = 99.0   # percentil superior para Winsorización
UMBRAL_OUTLIER_FLOOR    = 1.0    # percentil inferior

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "outputs_preprocesamiento")

# ────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ────────────────────────────────────────────────────────────────────────────

def _cargar_datos() -> pd.DataFrame:
    try:
        import awswrangler as wr
        import boto3

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

        BUCKET       = "ibk-discovery-comercial-us-east-1-654654352211-data"
        MODEL_PREFIX = "discovery/comercial/sanherna/PLAFT/PJ/MINORISTA"
        S3_PATH      = f"s3://{BUCKET}/{MODEL_PREFIX}/DATA_INFERENCIA/data_pn_total_expandido_new_v1.parquet"

        session = boto3.Session(region_name="us-east-1")
        print(f"  Cargando parquet: {S3_PATH}")
        df = wr.s3.read_parquet(path=S3_PATH, boto3_session=session)
        print(f"  ✓ Shape: {df.shape}")
        return df

    except Exception as exc:
        print(f"  ✗ Error cargando S3: {exc}")
        sys.exit(1)


def _resolver_estrategia(var: str) -> str:
    """Devuelve la estrategia de imputación para una variable."""
    if var in REGLAS_IMPUTACION:
        return REGLAS_IMPUTACION[var]
    for prefijo, estrategia in REGLAS_IMPUTACION.items():
        if var.startswith(prefijo):
            return estrategia
    return "mediana por segmento"


# ────────────────────────────────────────────────────────────────────────────
# REPORTE 1 — MISSING PRE-IMPUTACIÓN
# ────────────────────────────────────────────────────────────────────────────

def generar_missing_pre(df: pd.DataFrame, variables: list, output_dir: str) -> str:
    """
    01_Missing_PreImputacion.csv
    Calcula % de nulos por variable ANTES de cualquier imputación.
    Separa por conjunto (TRAIN / VALIDATION / TEST / TOTAL).
    """
    print("\n[REPORTE 1] Missing pre-imputación...")

    def _missing_conjunto(sub: pd.DataFrame, label: str) -> pd.DataFrame:
        existentes = [v for v in variables if v in sub.columns]
        total      = len(sub)
        rows = []
        for v in variables:
            if v not in sub.columns:
                rows.append({"variable": v, "conjunto": label,
                             "total_registros": total, "missing_count": total,
                             "missing_pct": 100.0, "en_dataset": "NO"})
                continue
            mc  = int(sub[v].isnull().sum())
            pct = round(100 * mc / total, 4) if total > 0 else 0.0
            rows.append({"variable": v, "conjunto": label,
                         "total_registros": total, "missing_count": mc,
                         "missing_pct": pct, "en_dataset": "SI"})
        return pd.DataFrame(rows)

    df[COL_MES] = df[COL_MES].astype(int)

    train = df[df[COL_MES].isin(PERIODOS_TRAIN)]
    val   = df[df[COL_MES].isin([202508, 202509])]
    test  = df[df[COL_MES].isin([202510,202511,202512,202601,202602,202603,202604])]

    partes = [
        _missing_conjunto(train, "TRAIN"),
        _missing_conjunto(val,   "VALIDATION"),
        _missing_conjunto(test,  "TEST"),
        _missing_conjunto(df,    "TOTAL"),
    ]
    resultado = pd.concat(partes, ignore_index=True)

    # Agregar columnas adicionales útiles
    resultado["estrategia_imputacion"] = resultado["variable"].apply(_resolver_estrategia)
    resultado["decision"] = resultado["missing_pct"].apply(
        lambda x: f"ELIMINAR (>{UMBRAL_MISSING_ELIMINAR}%)" if x > UMBRAL_MISSING_ELIMINAR
                  else ("REVISAR (5-20%)" if x > 5 else "OK (<5%)")
    )

    # Pivotear para tener una fila por variable con columnas por conjunto
    pivot = (
        resultado[resultado["conjunto"] != "TOTAL"]
        .pivot_table(index="variable", columns="conjunto",
                     values="missing_pct", aggfunc="first")
        .reset_index()
    )
    pivot.columns.name = None
    total_col = resultado[resultado["conjunto"] == "TOTAL"][["variable", "missing_pct",
                                                              "missing_count", "total_registros",
                                                              "estrategia_imputacion", "decision",
                                                              "en_dataset"]]
    pivot = pivot.merge(total_col, on="variable", how="left")
    pivot = pivot.sort_values("missing_pct", ascending=False).reset_index(drop=True)
    pivot.rename(columns={"missing_pct": "missing_pct_TOTAL",
                           "missing_count": "missing_count_TOTAL",
                           "total_registros": "total_registros_TOTAL"}, inplace=True)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "01_Missing_PreImputacion.csv")
    pivot.to_csv(path, index=False, encoding="utf-8-sig")

    n_ok      = (pivot["missing_pct_TOTAL"] == 0).sum()
    n_revisar = ((pivot["missing_pct_TOTAL"] > 0) & (pivot["missing_pct_TOTAL"] <= UMBRAL_MISSING_ELIMINAR)).sum()
    n_eliminar= (pivot["missing_pct_TOTAL"] > UMBRAL_MISSING_ELIMINAR).sum()
    print(f"  Variables sin missing : {n_ok}")
    print(f"  Variables con missing : {n_revisar}  (0–{UMBRAL_MISSING_ELIMINAR}%)")
    print(f"  Variables a evaluar   : {n_eliminar}  (>{UMBRAL_MISSING_ELIMINAR}%)")
    print(f"  ✓ Guardado: {path}")
    return path


# ────────────────────────────────────────────────────────────────────────────
# REPORTE 2 — ESTADÍSTICOS POST-IMPUTACIÓN
# ────────────────────────────────────────────────────────────────────────────

def _imputar(df: pd.DataFrame, variables: list) -> pd.DataFrame:
    """Aplica imputación según reglas de §8.2 (solo para el reporte estadístico)."""
    df = df.copy()
    for v in variables:
        if v not in df.columns:
            df[v] = 0.0
            continue
        estrategia = _resolver_estrategia(v)
        if "0 (sin" in estrategia or "0 (au" in estrategia:
            df[v] = pd.to_numeric(df[v], errors="coerce").fillna(0)
        elif "mediana" in estrategia:
            med = pd.to_numeric(df[v], errors="coerce").median()
            df[v] = pd.to_numeric(df[v], errors="coerce").fillna(med if pd.notna(med) else 0)
        elif "SIN_INFO" in estrategia:
            df[v] = df[v].fillna("SIN_INFO")
        else:
            df[v] = pd.to_numeric(df[v], errors="coerce").fillna(0)
    return df


def generar_estadisticos_post(df: pd.DataFrame, variables: list, output_dir: str) -> str:
    """
    02_Estadisticos_PostImputacion.csv
    Estadísticos descriptivos DESPUÉS de aplicar imputación.
    Solo variables numéricas del modelo.
    """
    print("\n[REPORTE 2] Estadísticos post-imputación...")

    df[COL_MES] = df[COL_MES].astype(int)
    df_train    = df[df[COL_MES].isin(PERIODOS_TRAIN)].copy()
    df_imputado = _imputar(df_train, variables)

    vars_num = [v for v in variables
                if v in df_imputado.columns
                and pd.api.types.is_numeric_dtype(df_imputado[v])]

    desc = df_imputado[vars_num].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    desc.index.name = "variable"
    desc = desc.reset_index()

    # Añadir columnas extra
    desc["zeros_pct"]      = [(df_imputado[v] == 0).mean() * 100 for v in desc["variable"]]
    desc["skewness"]       = [df_imputado[v].skew()  for v in desc["variable"]]
    desc["kurtosis"]       = [df_imputado[v].kurt()  for v in desc["variable"]]
    desc["missing_post"]   = [df_imputado[v].isnull().sum() for v in desc["variable"]]
    desc["estrategia"]     = [_resolver_estrategia(v) for v in desc["variable"]]
    desc["importancia_shap"]= [None] * len(desc)

    # Unir importancias SHAP desde importancia_variables.csv si existe
    imp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "Train", "importancia_variables.csv")
    if os.path.exists(imp_path):
        df_imp = pd.read_csv(imp_path, sep=";")
        df_imp.columns = [c.strip() for c in df_imp.columns]
        imp_map = dict(zip(df_imp["Variable"], df_imp["Importancia"]))
        desc["importancia_shap"] = desc["variable"].map(imp_map)

    # Ordenar por importancia SHAP descendente
    desc = desc.sort_values("importancia_shap", ascending=False,
                            na_position="last").reset_index(drop=True)

    # Redondear
    num_cols = desc.select_dtypes(include=[np.number]).columns
    desc[num_cols] = desc[num_cols].round(6)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "02_Estadisticos_PostImputacion.csv")
    desc.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"  Variables analizadas  : {len(desc)}")
    print(f"  Nulos post-imputación : {desc['missing_post'].sum()}")
    print(f"  ✓ Guardado: {path}")
    return path


# ────────────────────────────────────────────────────────────────────────────
# REPORTE 3 — OUTLIERS DETECTADOS
# ────────────────────────────────────────────────────────────────────────────

def generar_outliers(df: pd.DataFrame, variables: list, output_dir: str) -> str:
    """
    03_Outliers_Detectados.csv
    Detecta outliers usando percentiles 1% y 99%.
    Reporta por variable: límites, cantidad de valores fuera, % afectado
    y recomendación (mantener / winsorizar).
    """
    print("\n[REPORTE 3] Detección de outliers...")

    df[COL_MES] = df[COL_MES].astype(int)
    df_train    = df[df[COL_MES].isin(PERIODOS_TRAIN)].copy()
    df_imputado = _imputar(df_train, variables)

    vars_num = [v for v in variables
                if v in df_imputado.columns
                and pd.api.types.is_numeric_dtype(df_imputado[v])]

    rows = []
    for v in vars_num:
        serie  = df_imputado[v].dropna()
        n      = len(serie)
        if n == 0:
            continue

        p01  = float(serie.quantile(UMBRAL_OUTLIER_FLOOR / 100))
        p99  = float(serie.quantile(UMBRAL_OUTLIER_CAP   / 100))
        p50  = float(serie.median())
        mean = float(serie.mean())
        std  = float(serie.std())
        iqr  = float(serie.quantile(0.75) - serie.quantile(0.25))

        n_bajo  = int((serie < p01).sum())
        n_alto  = int((serie > p99).sum())
        n_total = n_bajo + n_alto
        pct     = round(100 * n_total / n, 4) if n > 0 else 0.0

        # Magnitud del outlier: ratio (max-p99)/std
        vmax  = float(serie.max())
        vmin  = float(serie.min())
        ratio_alto = round((vmax - p99) / std, 2) if std > 0 else 0.0
        ratio_bajo = round((p01 - vmin) / std, 2) if std > 0 else 0.0

        if pct == 0:
            recomendacion = "OK — sin outliers detectados"
        elif pct < 0.5:
            recomendacion = "MANTENER — outliers marginales (<0.5%)"
        elif ratio_alto > 10 or ratio_bajo > 10:
            recomendacion = f"WINSORIZAR — valores extremos (ratio>{max(ratio_alto, ratio_bajo):.1f}σ)"
        else:
            recomendacion = "REVISAR — evaluar impacto en modelo"

        rows.append({
            "variable"          : v,
            "n_total"           : n,
            "media"             : round(mean, 4),
            "mediana"           : round(p50, 4),
            "std"               : round(std, 4),
            "iqr"               : round(iqr, 4),
            "min"               : round(vmin, 4),
            "p01"               : round(p01, 4),
            "p99"               : round(p99, 4),
            "max"               : round(vmax, 4),
            "n_bajo_p01"        : n_bajo,
            "n_alto_p99"        : n_alto,
            "n_outliers_total"  : n_total,
            "pct_outliers"      : pct,
            "ratio_extremo_alto": ratio_alto,
            "ratio_extremo_bajo": ratio_bajo,
            "recomendacion"     : recomendacion,
            "estrategia_imp"    : _resolver_estrategia(v),
        })

    resultado = pd.DataFrame(rows).sort_values("pct_outliers", ascending=False).reset_index(drop=True)

    # Unir importancias
    imp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "Train", "importancia_variables.csv")
    if os.path.exists(imp_path):
        df_imp = pd.read_csv(imp_path, sep=";")
        df_imp.columns = [c.strip() for c in df_imp.columns]
        imp_map = dict(zip(df_imp["Variable"], df_imp["Importancia"]))
        resultado["importancia_shap"] = resultado["variable"].map(imp_map)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "03_Outliers_Detectados.csv")
    resultado.to_csv(path, index=False, encoding="utf-8-sig")

    n_ok        = (resultado["pct_outliers"] == 0).sum()
    n_winsorizar= resultado["recomendacion"].str.startswith("WINSORIZAR").sum()
    n_revisar   = resultado["recomendacion"].str.startswith("REVISAR").sum()
    n_mantener  = resultado["recomendacion"].str.startswith("MANTENER").sum()
    print(f"  Variables sin outliers: {n_ok}")
    print(f"  Mantener              : {n_mantener}")
    print(f"  Revisar               : {n_revisar}")
    print(f"  Winsorizar            : {n_winsorizar}")
    print(f"  ✓ Guardado: {path}")
    return path


# ────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ────────────────────────────────────────────────────────────────────────────

def main(df: pd.DataFrame = None):
    print("=" * 65)
    print("04_reportes_preprocesamiento.py  v1.0")
    print("Modelo PLAFT PJ Minorista — Reportes §8 del doc. metodológico")
    print(f"Fecha ejecución: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    if df is None:
        df = _cargar_datos()

    # Convertir a numérico todas las variables del modelo que existan
    for v in VARIABLES_MODELO:
        if v in df.columns and v not in ("cod_ubigeo_cd", "cod_sectorista_id"):
            df[v] = pd.to_numeric(df[v], errors="coerce")

    path1 = generar_missing_pre(df,       VARIABLES_MODELO, OUTPUT_DIR)
    path2 = generar_estadisticos_post(df, VARIABLES_MODELO, OUTPUT_DIR)
    path3 = generar_outliers(df,          VARIABLES_MODELO, OUTPUT_DIR)

    print("\n" + "=" * 65)
    print("RESUMEN — Artefactos generados:")
    print(f"  → {path1}")
    print(f"  → {path2}")
    print(f"  → {path3}")
    print(f"\nCarpeta: {OUTPUT_DIR}")
    print("=" * 65)
    return path1, path2, path3


if __name__ == "__main__":
    main()
