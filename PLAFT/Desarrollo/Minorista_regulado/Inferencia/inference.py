import sys
import subprocess
import argparse
import datetime
import pandas as pd
import numpy as np
import dask.dataframe as dd
import tarfile
import os
import xgboost as xgb
import pytz

# ======================== RUTAS DE ENTRADA ==============================
DIR_DATA      = "/opt/ml/processing/input/data"
DIR_MODELS    = "/opt/ml/processing/input/models"
DIR_RENAME    = "/opt/ml/processing/input/rename"
DIR_ARTIFACTS = "/opt/ml/processing/input/artifacts"  # encoding_maps.json + percentil_limits.json

# ======================== RUTAS DE SALIDA ===============================
DIR_RESULTS = "/opt/ml/processing/output/results"

# ======================== LISTA DE VARIABLES ============================
COLS_IDS = ["cod_mes", "key_value","cod_cli","tipo_alerta_n2"]
COLS_CONTROL = ["trx_riesgo_cliente"]
COLS_POST = ["key_value", "tipo_alerta_n2", "cod_mes"]

COLS_VARS = [  # VARIABLES_FINALES_MODELO v2 – 26 features (ordenadas por importancia)
    'cod_ubigeo_cd',            # importancia=10.5376%
    'cnt_trx_cargostot_3m',     # importancia=9.8065%
    'mto_pas_soles',            # importancia=9.4462%
    'cnt_trx_abonospromtot_3m', # importancia=8.7688%
    'imp_trx_abonosefect_6m',   # importancia=7.2957%
    'imp_trx_cargosefe_6m',     # importancia=5.8602%
    'rat_trx_abonosefectot_3m', # importancia=4.9247%
    'cnt_meses_sinegresos_12m', # importancia=4.8011%
    'mto_fact_declarado_sunat', # importancia=4.6183%
    'num_antiguedad',           # importancia=4.6075%
    'rat_mntcrgsefetot_1m',     # importancia=3.4839%
    'avg_trx_cargostot_3m',     # importancia=3.3763%
    'cnt_alerta_hist',          # importancia=3.3495%
    'mto_del_ext_12m',          # importancia=2.8387%
    'cod_sectorista_id',        # importancia=2.7957%
    'avg_cpmenegr_12m',         # importancia=2.2903%
    'share_cp_egresos',         # importancia=1.6075%  [avg_cpmenegr_12m / imp_trx_cargosefe_6m]
    'cnt_ros_hist',             # importancia=1.5269%
    'ratio_egresos_exterior',   # importancia=1.2688%  [mto_al_ext_12m / imp_trx_cargosefe_12m]
    'mto_al_ext_12m',           # importancia=1.1882%
    'avg_cp_men_ing_12m',       # importancia=1.1559%
    'flg_alerta_12m',           # importancia=1.0430%
    'flg_vrcn_abonos_5m_1m',    # importancia=0.9516%
    'share_cp_ingresos',        # importancia=0.7634%  [avg_cp_men_ing_12m / imp_trx_abonosefect_6m]
    'cnt_noticias',             # importancia=0.6613%
    'cnt_trx_sinenv_alext_12m', # importancia=0.5161%
]

# ======================== FUNCIONES DE UTILIDAD =========================


def read_data(dir_data):
    try:
        path = glob.glob(f"{dir_data}/*.csv")[0]
        df = pd.read_csv(path)
    except:
        path = f"{dir_data}/*"
        df = dd.read_parquet(path).compute().reset_index(drop=True)
    return df


def preprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    # ── Limpieza inicial ────────────────────────────────────────────────────
    if "target_m" in df.columns and "target" not in df.columns:
        df = df.rename(columns={"target_m": "target"})

    if "key_value" in df.columns and "cod_mes" in df.columns:
        df = df.drop_duplicates(subset=["key_value", "cod_mes"], keep="first")

    df = df.drop(columns=["fec_constitucion", "codmes_lag1"], errors="ignore")

    if "tipo_alerta_n2" in df.columns:
        df["tipo_alerta_n2"] = df["tipo_alerta_n2"].astype(str)

    if "cnt_alerta_hist" in df.columns:
        df["cnt_alerta_hist"] = df["cnt_alerta_hist"].astype("float64")

    if "mto_fact_declarado_sunat" in df.columns:
        df["mto_fact_declarado_sunat"] = pd.to_numeric(
            df["mto_fact_declarado_sunat"], errors="coerce"
        )

    # ── Imputación diferenciada (sección 8.2 del notebook) ─────────────────
    cols_transac   = [c for c in df.columns if c.startswith(("cnt_trx_", "imp_trx_", "max_trx_", "avg_trx_"))]
    cols_ratios    = [c for c in df.columns if c.startswith(("rat_", "ratio_", "share_", "gap_"))]
    cols_variacion = [c for c in df.columns if c.startswith(("cnt_meses_sin", "flg_vrcn_"))]
    cols_flag      = [c for c in df.columns if c.startswith("flg_") and c not in cols_variacion]

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

    cols_cat_str = df.select_dtypes(include=["object", "string"]).columns.tolist()
    df[cols_cat_str] = df[cols_cat_str].fillna("SIN_INFO")

    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # ── Label Encoding ordenado por tasa de positividad (sección 8.4) ──────
    # Cargar mapas calculados en TRAIN desde artefactos guardados
    import json

    EXCLUIR_ENCODE = {
        "key_value", "cod_cli", "tipo_alerta_n2",
        "trx_riesgo_cliente", "desc_provincia", "desc_departamento",
    }
    TARGET_COL = "target"

    fp_enc = os.path.join(DIR_ARTIFACTS, "encoding_maps.json")
    if os.path.exists(fp_enc):
        with open(fp_enc, "r", encoding="utf-8") as f:
            encoding_maps = json.load(f)

        cols_cat_encode = [
            c for c in df.select_dtypes(include=["object", "string"]).columns
            if c != TARGET_COL and c not in EXCLUIR_ENCODE
        ]
        for col in cols_cat_encode:
            if col in encoding_maps:
                df[col] = df[col].map(encoding_maps[col]).fillna(0).astype(int)
            else:
                # Variable no vista en train → 0 (categoría nula)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    else:
        # Fallback si no hay artefacto: convertir a numérico
        cols_cat_encode = [
            c for c in df.select_dtypes(include=["object", "string"]).columns
            if c != TARGET_COL and c not in EXCLUIR_ENCODE
        ]
        for col in cols_cat_encode:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ── Winsorización con límites del TRAIN (sección 8.6) ───────────────────
    fp_wins = os.path.join(DIR_ARTIFACTS, "percentil_limits.json")
    if os.path.exists(fp_wins):
        with open(fp_wins, "r", encoding="utf-8") as f:
            percentil_limits = json.load(f)
        for col, (p1, p99) in percentil_limits.items():
            if col in df.columns:
                df[col] = df[col].clip(lower=p1, upper=p99)

    return df


def inference_fn(dir_models: str, df: pd.DataFrame, cols_vars: list) -> pd.DataFrame:
    model_tar_path = f"{dir_models}/model.tar.gz"
    extract_path = f"{dir_models}/model"

    with tarfile.open(model_tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path)

    model_path = os.path.join(extract_path, "xgboost-model")
    model = xgb.Booster()
    model.load_model(model_path)

    dmatrix = xgb.DMatrix(df[cols_vars])
    scores = model.predict(dmatrix)
    df["puntuacion"] = scores
    return df


def postprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("puntuacion", ascending=False).drop_duplicates("cod_cli")
    df["orden"] = df["puntuacion"].rank(method="first", ascending=False).astype(int)

    df["tipo_alerta_n2"] = df["tipo_alerta_n2"].astype(str)

    # ── Umbral nueva alerta ─────────────────────────────────────────────
    UMBRAL_NUEVA_ALERTA = 0.992137148976326

    df["grupo_corte_nueva_alerta"] = (
        (df["puntuacion"] > UMBRAL_NUEVA_ALERTA)
        & (df["tipo_alerta_n2"] == "0")
    ).astype(int)

    # ── Quintiles de riesgo (P1=menor riesgo, P5=mayor riesgo) ──────────
    cortes = [
        -float("inf"),
        0.746,   # P1 | P2
        0.909,   # P2 | P3
        0.963,   # P3 | P4
        0.987,   # P4 | P5
        float("inf")
    ]
    etiquetas = [5, 4, 3, 2, 1]

    df["grupo_alerta"] = pd.cut(
        df["puntuacion"],
        bins=cortes,
        labels=etiquetas,
        include_lowest=True
    ).astype(int)

    nombres_grupo = {1: "P1", 2: "P2", 3: "P3", 4: "P4", 5: "P5"}
    df["grupo_alerta_desc"] = df["grupo_alerta"].map(nombres_grupo)

    return df


def output_fn(df: pd.DataFrame, cols_control: list = None) -> pd.DataFrame:
    datetime_now = datetime.datetime.now(pytz.timezone("America/Lima")).strftime("%Y%m%d")

    df_output = pd.DataFrame()
    df_output["codmes"] = df["cod_mes"]
    df_output["num_documento"] = df["key_value"]
    df_output["codunico"] = df["cod_cli"]
    df_output["modelo"] = "plaft_pj_minorista"
    df_output["fec_replica"] = datetime_now
    df_output["grupo_alerta"] = df["grupo_alerta_desc"]
    df_output["grupo_corte_nueva_alerta"] = (df["grupo_corte_nueva_alerta"])
    df_output["score"] = df["puntuacion"]
    df_output["orden"] = df["orden"]
    df_output["variable1"] = df["tipo_alerta_n2"]
    df_output["variable2"] = df["trx_riesgo_cliente"]
    df_output["variable3"] = ""

    return df_output, None


# ======================== MAIN ==========================================


def main(args: argparse.Namespace) -> None:
    model = args.model
    table_score = args.table_score
    partition = args.partition

    df = read_data(DIR_DATA)
    df = preprocessing_fn(df)
    df = inference_fn(DIR_MODELS, df, COLS_VARS)
    df = postprocessing_fn(df)
    df_output, _ = output_fn(df, COLS_CONTROL)

    path = f"{DIR_RESULTS}/{table_score}_{partition}.txt"
    df_output.to_csv(path, index=False, sep="|")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--table-score", type=str, required=True)
    parser.add_argument("--partition", type=str, required=True)
    main(parser.parse_args())
