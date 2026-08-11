"""
preprocessing_1.py
==================
Script de preprocesamiento para el modelo PLAFT PJ Minorista v2.
Replica EXACTAMENTE las transformaciones definidas en 01.genera_base_train.ipynb:

  8.2  Imputación diferenciada por tipo de variable
  8.4  Label Encoding ordenado por tasa de positividad (Nulo=0, Bajo=1, Medio=2, Alto=3)
  8.6  Winsorización automática de outliers (p1/p99 si >5% fuera de rango)
  +    Cast de tipos finales (cnt_alerta_hist → float64, mto_fact_declarado_sunat → numeric)
  +    Selección de columnas según selected_columns.csv (26 variables del modelo v2)
"""

import os
import subprocess
import sys
import time


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

DIR_DATA    = "/opt/ml/processing/input/data"
DIR_COLUMNS = "/opt/ml/processing/input/Columns"
DIR_ARTIFACTS = "/opt/ml/processing/input/artifacts"  # encoding_maps.json + percentil_limits.json
DIR_TRAIN   = "/opt/ml/processing/train"
DIR_VAL     = "/opt/ml/processing/val"
DIR_TEST    = "/opt/ml/processing/test"
DIR_HEADERS = "/opt/ml/processing/headers"

DATA_FILE    = "data_pn_total_expandido_new_v1.parquet"
COLUMNS_FILE = "selected_columns.csv"

# Columnas de identificación/control que NO son features del modelo
COLS_IDS = ["cod_mes", "key_value", "cod_cli", "tipo_alerta_n2", "trx_riesgo_cliente"]

# Columnas a eliminar antes del preprocesamiento
COLS_DROP_ALWAYS = ["fec_constitucion", "codmes_lag1"]

# Particiones temporales (alineadas con el notebook)
MESES_TRAIN = ["202501", "202502", "202503", "202504", "202505", "202506", "202507"]
MESES_VAL   = ["202508", "202509"]
MESES_TEST  = ["202508", "202509", "202510", "202511", "202512",
               "202601", "202602", "202603", "202604"]


# ══════════════════════════════════════════════════════════════════════════════
# 1. LECTURA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

def leer_datos(meses: list) -> "pd.DataFrame":
    """Lee el parquet y filtra los meses indicados."""
    import dask.dataframe as dd

    path = os.path.join(DIR_DATA, DATA_FILE)
    print(f"[LeerDatos] Leyendo: {path}")
    df = dd.read_parquet(path).compute()

    if "cod_mes" not in df.columns:
        raise ValueError("⚠  Columna 'cod_mes' no encontrada.")

    df["cod_mes"] = df["cod_mes"].astype(str)
    df = df[df["cod_mes"].isin(meses)].reset_index(drop=True)
    print(f"[LeerDatos] {len(df):,} registros | meses={meses}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2. LIMPIEZA INICIAL
# ══════════════════════════════════════════════════════════════════════════════

def limpieza_inicial(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    - Renombra target_m → target
    - Elimina duplicados por key_value + cod_mes
    - Elimina fec_constitucion, codmes_lag1
    - tipo_alerta_n2 → str
    - cnt_alerta_hist → float64
    - mto_fact_declarado_sunat → numeric
    Celdas del notebook: dc757167, e273824e, b63d2cb2, 391d288f,
                         5ad3743f, e28fcf11, c01b7f46
    """
    import pandas as pd

    if "target_m" in df.columns and "target" not in df.columns:
        df = df.rename(columns={"target_m": "target"})

    if "target" in df.columns:
        df = df[["target"] + [c for c in df.columns if c != "target"]]

    if "key_value" in df.columns and "cod_mes" in df.columns:
        antes = len(df)
        df = df.drop_duplicates(subset=["key_value", "cod_mes"], keep="first")
        print(f"[Limpieza] Duplicados eliminados: {antes - len(df):,}")

    df = df.drop(columns=COLS_DROP_ALWAYS, errors="ignore")

    if "tipo_alerta_n2" in df.columns:
        df["tipo_alerta_n2"] = df["tipo_alerta_n2"].astype(str)

    if "cnt_alerta_hist" in df.columns:
        df["cnt_alerta_hist"] = df["cnt_alerta_hist"].astype("float64")

    if "mto_fact_declarado_sunat" in df.columns:
        df["mto_fact_declarado_sunat"] = pd.to_numeric(
            df["mto_fact_declarado_sunat"], errors="coerce"
        )

    return df


# ══════════════════════════════════════════════════════════════════════════════
# 3. IMPUTACIÓN DIFERENCIADA  (sección 8.2 del notebook)
# ══════════════════════════════════════════════════════════════════════════════

def imputar(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Estrategia diferenciada por tipo de variable:
      cnt_trx_*, imp_trx_*, max_trx_*, avg_trx_*  → 0
      rat_*, ratio_*, share_*, gap_*               → mediana
      cnt_meses_sin*, flg_vrcn_*                   → -1
      num_antiguedad                               → mediana
      flg_* restantes                              → 0
      Int32                                        → 0 → int64
      boolean                                      → False
      object / string                              → "SIN_INFO"
      resto numéricas                              → mediana
    """
    import numpy as np

    cols_transac  = [c for c in df.columns if c.startswith(("cnt_trx_", "imp_trx_", "max_trx_", "avg_trx_"))]
    cols_ratios   = [c for c in df.columns if c.startswith(("rat_", "ratio_", "share_", "gap_"))]
    cols_variacion= [c for c in df.columns if c.startswith(("cnt_meses_sin", "flg_vrcn_"))]
    cols_flag     = [c for c in df.columns if c.startswith("flg_") and c not in cols_variacion]

    df[cols_transac]   = df[cols_transac].fillna(0)
    for col in cols_ratios:
        df[col] = df[col].fillna(df[col].median())
    df[cols_variacion] = df[cols_variacion].fillna(-1)
    if "num_antiguedad" in df.columns:
        df["num_antiguedad"] = df["num_antiguedad"].fillna(df["num_antiguedad"].median())
    df[cols_flag] = df[cols_flag].fillna(0)

    int32_cols = df.select_dtypes(include=["Int32"]).columns
    df[int32_cols] = df[int32_cols].fillna(0).astype("int64")

    bool_cols = df.select_dtypes(include=["boolean"]).columns
    df[bool_cols] = df[bool_cols].fillna(False)

    cols_cat = df.select_dtypes(include=["object", "string"]).columns.tolist()
    df[cols_cat] = df[cols_cat].fillna("SIN_INFO")

    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    print(f"[Imputación] Completada — nulos restantes: {df.isnull().sum().sum()}")
    print(f"  transaccionales={len(cols_transac)}, ratios={len(cols_ratios)}, "
          f"variacion={len(cols_variacion)}, flags={len(cols_flag)}, cat={len(cols_cat)}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 4. LABEL ENCODING ORDENADO POR TASA DE POSITIVIDAD  (sección 8.4 del notebook)
# ══════════════════════════════════════════════════════════════════════════════

def label_encode(df: "pd.DataFrame",
                 encoding_maps: dict = None,
                 fit: bool = True):
    """
    Escala ordinal basada en tasa de positividad del target:
        SIN_INFO=0 / Bajo=1 / Medio=2 / Alto=3

    fit=True  → calcula mapas desde df (solo TRAIN).
    fit=False → aplica mapas precalculados (VAL / TEST).

    Excluye siempre: key_value, cod_cli, tipo_alerta_n2,
                     trx_riesgo_cliente, desc_provincia, desc_departamento
    """
    import numpy as np

    EXCLUIR = {"key_value", "cod_cli", "tipo_alerta_n2",
               "trx_riesgo_cliente", "desc_provincia", "desc_departamento"}
    TARGET_COL = "target"

    cols_cat = [c for c in df.select_dtypes(include=["object", "string"]).columns
                if c != TARGET_COL and c not in EXCLUIR]

    if fit:
        encoding_maps = {}
        for col in cols_cat:
            tasa = (
                df.groupby(col)[TARGET_COL]
                .agg(count="count", pos_rate="mean")
                .reset_index()
                .sort_values("pos_rate")
            )
            n = len(tasa)
            if n >= 3:
                t1, t2 = int(np.floor(n / 3)), int(np.floor(2 * n / 3))
                bajo  = tasa.iloc[:t1][col].tolist()
                medio = tasa.iloc[t1:t2][col].tolist()
                alto  = tasa.iloc[t2:][col].tolist()
            elif n == 2:
                bajo, medio, alto = [tasa.iloc[0][col]], [], [tasa.iloc[1][col]]
            else:
                bajo, medio, alto = tasa[col].tolist(), [], []

            mapa = {"SIN_INFO": 0}
            for v in bajo:  mapa[v] = 1
            for v in medio: mapa[v] = 2
            for v in alto:  mapa[v] = 3
            encoding_maps[col] = mapa
            print(f"[Encoding] ✓ {col:<40} cats={n} | bajo={len(bajo)}, "
                  f"medio={len(medio)}, alto={len(alto)}")

    for col in cols_cat:
        if col in (encoding_maps or {}):
            df[col] = df[col].map(encoding_maps[col]).fillna(0).astype(int)

    print(f"[Encoding] Completado — {len(cols_cat)} variables codificadas")
    return df, encoding_maps


# ══════════════════════════════════════════════════════════════════════════════
# 5. WINSORIZACIÓN DE OUTLIERS  (sección 8.6 del notebook)
# ══════════════════════════════════════════════════════════════════════════════

def winsorizacion(df: "pd.DataFrame",
                  percentil_limits: dict = None,
                  fit: bool = True):
    """
    Variables con >5% de registros fuera del rango [p1, p99] son winsorizadas.
    fit=True  → calcula límites desde TRAIN.
    fit=False → aplica límites precalculados.
    """
    import numpy as np

    TARGET_COL = "target"
    cols_num = [c for c in df.select_dtypes(include=[np.number]).columns
                if c != TARGET_COL]

    if fit:
        percentil_limits = {}
        winsorizadas = []
        for col in cols_num:
            p1  = df[col].quantile(0.01)
            p99 = df[col].quantile(0.99)
            if ((df[col] < p1) | (df[col] > p99)).mean() * 100 > 5:
                percentil_limits[col] = (p1, p99)
                winsorizadas.append(col)
        print(f"[Winsorización] Variables con outliers >5%: {len(winsorizadas)}")
        for c in winsorizadas:
            print(f"  → {c}")

    for col, (p1, p99) in (percentil_limits or {}).items():
        if col in df.columns:
            df[col] = df[col].clip(lower=p1, upper=p99)

    return df, percentil_limits


# ══════════════════════════════════════════════════════════════════════════════
# 6. SELECCIÓN DE VARIABLES FINALES
# ══════════════════════════════════════════════════════════════════════════════

def seleccionar_columnas(df: "pd.DataFrame") -> "pd.DataFrame":
    """Lee selected_columns.csv y recorta el DataFrame a esas columnas + target."""
    import pandas as pd

    path_cols = os.path.join(DIR_COLUMNS, COLUMNS_FILE)
    columnas = pd.read_csv(path_cols, header=None)[0].tolist()

    if "target" not in columnas:
        columnas = ["target"] + columnas

    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        print(f"[SeleccionarColumnas] ⚠  No encontradas: {faltantes}")

    cols_ok = [c for c in columnas if c in df.columns]
    print(f"[SeleccionarColumnas] {len(cols_ok)} columnas seleccionadas")
    return df[cols_ok]


# ══════════════════════════════════════════════════════════════════════════════
# 6b. GUARDAR / CARGAR ARTEFACTOS (encoding_maps + percentil_limits)
# ══════════════════════════════════════════════════════════════════════════════

def guardar_artefactos(encoding_maps: dict, percentil_limits: dict) -> None:
    """Guarda los artefactos de preprocesamiento calculados en TRAIN como JSON."""
    import json
    os.makedirs(DIR_ARTIFACTS, exist_ok=True)
    fp_enc  = os.path.join(DIR_ARTIFACTS, "encoding_maps.json")
    fp_wins = os.path.join(DIR_ARTIFACTS, "percentil_limits.json")
    with open(fp_enc,  "w", encoding="utf-8") as f:
        json.dump(encoding_maps,   f, ensure_ascii=False, indent=2)
    with open(fp_wins, "w", encoding="utf-8") as f:
        json.dump(percentil_limits, f, ensure_ascii=False, indent=2)
    print(f"[Artefactos] encoding_maps.json    → {len(encoding_maps)} variables")
    print(f"[Artefactos] percentil_limits.json → {len(percentil_limits)} variables")


def cargar_artefactos() -> tuple:
    """Carga los artefactos desde DIR_ARTIFACTS (para VAL/TEST en producción)."""
    import json
    fp_enc  = os.path.join(DIR_ARTIFACTS, "encoding_maps.json")
    fp_wins = os.path.join(DIR_ARTIFACTS, "percentil_limits.json")
    with open(fp_enc,  "r", encoding="utf-8") as f:
        encoding_maps = json.load(f)
    with open(fp_wins, "r", encoding="utf-8") as f:
        raw = json.load(f)
        percentil_limits = {k: tuple(v) for k, v in raw.items()}
    print(f"[Artefactos] Cargados — encoding: {len(encoding_maps)}, wins: {len(percentil_limits)}")
    return encoding_maps, percentil_limits


# ══════════════════════════════════════════════════════════════════════════════
# 7. PIPELINE COMPLETO
# ══════════════════════════════════════════════════════════════════════════════

def pipeline(df: "pd.DataFrame",
             encoding_maps: dict = None,
             percentil_limits: dict = None,
             fit: bool = True):
    t0 = time.time()
    df = limpieza_inicial(df)
    df = imputar(df)
    df, encoding_maps    = label_encode(df, encoding_maps, fit=fit)
    df, percentil_limits = winsorizacion(df, percentil_limits, fit=fit)
    df = seleccionar_columnas(df)
    print(f"[Pipeline] {(time.time()-t0)/60:.2f} min | shape={df.shape}")
    return df, encoding_maps, percentil_limits


# ══════════════════════════════════════════════════════════════════════════════
# 8. MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.23.5",   "-q"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas==1.5.1",   "-q"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "toolz",           "-q"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dask==2.11.0",    "-q"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fsspec",          "-q"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow==10.0.0", "-q"])

    import pandas as pd
    import numpy as np
    import dask.dataframe as dd

    for d in [DIR_TRAIN, DIR_VAL, DIR_TEST, DIR_HEADERS]:
        os.makedirs(d, exist_ok=True)

    # ── TRAIN ────────────────────────────────────────────────────────────────
    print("\n" + "="*65 + "\nTRAIN\n" + "="*65)
    df_raw_train = leer_datos(MESES_TRAIN)
    extras_train = df_raw_train[[c for c in COLS_IDS if c in df_raw_train.columns]].copy()
    df_train, encoding_maps, percentil_limits = pipeline(df_raw_train, fit=True)

    # Guardar artefactos calculados en TRAIN para reutilizar en VAL/TEST/Inferencia
    guardar_artefactos(encoding_maps, percentil_limits)

    # ── VALIDACIÓN ───────────────────────────────────────────────────────────
    print("\n" + "="*65 + "\nVALIDACIÓN\n" + "="*65)
    df_raw_val = leer_datos(MESES_VAL)
    extras_val = df_raw_val[[c for c in COLS_IDS if c in df_raw_val.columns]].copy()
    df_val, _, _ = pipeline(df_raw_val, encoding_maps, percentil_limits, fit=False)

    # ── TEST ─────────────────────────────────────────────────────────────────
    print("\n" + "="*65 + "\nTEST\n" + "="*65)
    df_raw_test = leer_datos(MESES_TEST)
    extras_test = df_raw_test[[c for c in COLS_IDS if c in df_raw_test.columns]].copy()
    df_test, _, _ = pipeline(df_raw_test, encoding_maps, percentil_limits, fit=False)

    # ── HEADERS ──────────────────────────────────────────────────────────────
    df_headers = df_train.dtypes.to_frame("dtypes").reset_index()
    df_headers.columns = ["variables", "dtypes"]

    # ── GUARDAR ──────────────────────────────────────────────────────────────
    df_train.to_csv(  os.path.join(DIR_TRAIN,   "train_total.csv"),      header=False, index=False)
    df_val.to_csv(    os.path.join(DIR_VAL,     "validation_total.csv"), header=False, index=False)
    df_test.to_csv(   os.path.join(DIR_TEST,    "test_total.csv"),       header=False, index=False)
    df_headers.to_csv(os.path.join(DIR_HEADERS, "headers_total.csv"),    index=False)
    extras_val.to_csv( os.path.join(DIR_VAL,  "extras_validation_total.csv"), index=False)
    extras_test.to_csv(os.path.join(DIR_TEST, "extras_test_total.csv"),        index=False)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  PREPROCESAMIENTO COMPLETADO ✅                          ║
╠══════════════════════════════════════════════════════════╣
║  Train  : {df_train.shape[0]:>8,} filas × {df_train.shape[1]:>3} cols               ║
║  Val    : {df_val.shape[0]:>8,} filas × {df_val.shape[1]:>3} cols               ║
║  Test   : {df_test.shape[0]:>8,} filas × {df_test.shape[1]:>3} cols               ║
╠══════════════════════════════════════════════════════════╣
║  Transformaciones aplicadas:                             ║
║    ✓ Imputación diferenciada por tipo (8.2)              ║
║    ✓ Label Encoding ordenado por positividad (8.4)       ║
║    ✓ Winsorización p1/p99 si outliers >5%% (8.6)        ║
║    ✓ Cast cnt_alerta_hist → float64                      ║
║    ✓ Cast mto_fact_declarado_sunat → numeric             ║
║    ✓ Selección 26 variables del modelo v2                ║
╚══════════════════════════════════════════════════════════╝
""")

    