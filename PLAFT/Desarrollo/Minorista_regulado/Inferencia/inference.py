import sys
import subprocess
import argparse
import datetime
import glob
import warnings

# Reduce ruido de deprecaciones en la imagen base (dask/pyarrow viejos).
warnings.simplefilter("ignore", FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Mean of empty slice")

import pandas as pd
import numpy as np
import dask.dataframe as dd
import tarfile
import os

# La validación que generó los scores de referencia usa XGBoost 1.7.6.
subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost==1.7.6", "-q"])

import xgboost as xgb
import pytz

if xgb.__version__ != "1.7.6":
    raise RuntimeError(f"Versión XGBoost no compatible: {xgb.__version__}. Se requiere 1.7.6.")

# ======================== RUTAS DE ENTRADA ==============================
DIR_DATA      = "/opt/ml/processing/input/data"
DIR_MODELS    = "/opt/ml/processing/input/models"
DIR_RENAME    = "/opt/ml/processing/input/rename"
DIR_ARTIFACTS = "/opt/ml/processing/input/artifacts"
ENCODING_MAPS_FILE = "encoding_maps.json"

# ======================== RUTAS DE SALIDA ===============================
DIR_RESULTS = "/opt/ml/processing/output/results"

# ======================== LISTA DE VARIABLES ============================
COLS_IDS = ["cod_mes", "key_value","cod_cli","tipo_alerta_n2"]
COLS_CONTROL = ["trx_riesgo_cliente"]
COLS_POST = ["key_value", "tipo_alerta_n2", "cod_mes"]

COLS_VARS = [  # VARIABLES FINALES del TRAIN (selected_columns.csv sin target)
    "cnt_trx_cargostot_3m",
    "mto_pas_soles",
    "rat_pastot_x_ingtot_6m",
    "cnt_trx_abonospromtot_3m",
    "imp_trx_abonosefect_6m",
    "num_antiguedad",
    "imp_trx_cargosefe_6m",
    "ratio_cargos_1m_vs_6m",
    "cnt_meses_sinegresos_12m",
    "cnt_alerta_hist",
    "rat_trx_abonosefectot_3m",
    "avg_trx_cargostot_3m",
    "rat_mntcrgsefetot_1m",
    "rat_trx_abonosefectot_1m",
    "rat_cntros_x_cnttrxegr_3m",
    "share_cp_egresos",
    "mto_del_ext_12m",
    "rat_ing_ext_x_ing_tot_12m",
    "max_mto_cpegrmen_12m",
    "avg_cpmenegr_12m",
    "mto_al_ext_12m",
    "ratio_egresos_exterior",
    "cnt_ros_hist",
    "cnt_trx_sinenv_alext_12m",
    "flg_alerta_12m",
    "flg_vrcn_abonos_5m_1m",
    "avg_cp_men_ing_12m",
    "cnt_noticias",
    "share_cp_ingresos",
    "mto_fact_declarado_sunat",
    "cod_ubigeo_cd",
    "cod_sectorista_id",
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


def _safe_fill_median(series: pd.Series, default_value: float = 0.0) -> pd.Series:
    """Fill NaN with median, or with default when a column is fully null."""
    non_null = series.dropna()
    if non_null.empty:
        median_value = default_value
    else:
        median_value = non_null.median()
    return series.fillna(median_value)


def apply_feature_mappings(df: pd.DataFrame) -> pd.DataFrame:
    """Apply categorical mappings fitted during training."""
    import json

    maps_path = os.path.join(DIR_ARTIFACTS, ENCODING_MAPS_FILE)
    if not os.path.exists(maps_path):
        raise FileNotFoundError(
            f"No se encontró {maps_path}. "
            "Monte MODEL/artifacts_v2 en la entrada artifacts."
        )

    with open(maps_path, "r", encoding="utf-8") as file:
        feature_maps = json.load(file)

    for column, mapping in feature_maps.items():
        if column not in df.columns or column not in COLS_VARS:
            continue
        raw_values = df[column].fillna("SIN_INFO").astype(str)
        mapped_values = raw_values.map(mapping)
        unknown_count = int(mapped_values.isna().sum())
        if unknown_count:
            print(f"WARN: {column} tiene {unknown_count:,} valores no mapeados; se asignan a 0.")
        df[column] = mapped_values.fillna(0).astype("float32")

    return df


def _build_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features required by the model when they are missing."""
    def _first_existing(options):
        for col in options:
            if col in df.columns:
                return col
        return None

    if "share_cp_ingresos" not in df.columns:
        num_col = _first_existing(["avg_cp_men_ing_12m", "avg_cpmening_12m", "avg_cp_men_ing_6m"])
        den_col = _first_existing(["imp_trx_abonosefect_6m", "imp_trx_abonostot_6m", "imp_trx_abonosefect_12m"])
        if num_col and den_col:
            den = pd.to_numeric(df[den_col], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df[num_col], errors="coerce")
            df["share_cp_ingresos"] = num / den

    if "ratio_egresos_exterior" not in df.columns:
        num_col = _first_existing(["mto_al_ext_12m", "mto_alext_12m"])
        den_col = _first_existing(["imp_trx_cargosefe_12m", "imp_trx_cargostot_12m", "imp_trx_cargosefe_6m"])
        if num_col and den_col:
            den = pd.to_numeric(df[den_col], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df[num_col], errors="coerce")
            df["ratio_egresos_exterior"] = num / den

    if "rat_pastot_x_ingtot_6m" not in df.columns:
        num_col = _first_existing(["mto_pas_soles"])
        den_col = _first_existing(["imp_trx_abonostot_6m", "imp_trx_abonosefect_6m", "avg_cp_men_ing_12m"])
        if num_col and den_col:
            den = pd.to_numeric(df[den_col], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df[num_col], errors="coerce")
            df["rat_pastot_x_ingtot_6m"] = num / den

    if "rat_cntros_x_cnttrxegr_3m" not in df.columns:
        if {"cnt_ros_hist", "cnt_trx_cargostot_3m"}.issubset(df.columns):
            den = pd.to_numeric(df["cnt_trx_cargostot_3m"], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df["cnt_ros_hist"], errors="coerce")
            df["rat_cntros_x_cnttrxegr_3m"] = num / den

    if "rat_ing_ext_x_ing_tot_12m" not in df.columns:
        num_col = _first_existing(["mto_del_ext_12m"])
        den_col = _first_existing(["imp_trx_abonostot_12m", "imp_trx_abonosefect_6m"])
        if num_col and den_col:
            den = pd.to_numeric(df[den_col], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df[num_col], errors="coerce")
            df["rat_ing_ext_x_ing_tot_12m"] = num / den

    if "ratio_cargos_1m_vs_6m" not in df.columns:
        num_col = _first_existing(["imp_trx_cargostot_1m", "imp_trx_cargosefe_1m"])
        den_col = _first_existing(["avg_trx_cargostot_6m", "imp_trx_cargostot_6m", "imp_trx_cargosefe_6m"])
        if num_col and den_col:
            den = pd.to_numeric(df[den_col], errors="coerce").replace(0, np.nan)
            num = pd.to_numeric(df[num_col], errors="coerce")
            df["ratio_cargos_1m_vs_6m"] = num / den

    # Si por estructura de fuente no se pueden derivar, crear como 0 para estabilidad.
    for col in [
        "share_cp_ingresos",
        "ratio_egresos_exterior",
        "rat_pastot_x_ingtot_6m",
        "rat_cntros_x_cnttrxegr_3m",
        "rat_ing_ext_x_ing_tot_12m",
        "ratio_cargos_1m_vs_6m",
    ]:
        if col not in df.columns:
            df[col] = 0.0

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

    df = apply_feature_mappings(df)

    if "mto_fact_declarado_sunat" in df.columns:
        df["mto_fact_declarado_sunat"] = pd.to_numeric(
            df["mto_fact_declarado_sunat"], errors="coerce"
        )

    df = _build_derived_features(df)

    # ── Imputación diferenciada (sección 8.2 del notebook) ─────────────────
    cols_transac   = [c for c in df.columns if c.startswith(("cnt_trx_", "imp_trx_", "max_trx_", "avg_trx_"))]
    cols_ratios    = [c for c in df.columns if c.startswith(("rat_", "ratio_", "share_", "gap_"))]
    cols_variacion = [c for c in df.columns if c.startswith(("cnt_meses_sin", "flg_vrcn_"))]
    cols_flag      = [c for c in df.columns if c.startswith("flg_") and c not in cols_variacion]

    df[cols_transac]   = df[cols_transac].fillna(0)
    for col in cols_ratios:
        df[col] = _safe_fill_median(df[col], default_value=0.0)
    df[cols_variacion] = df[cols_variacion].fillna(-1)
    if "num_antiguedad" in df.columns:
        df["num_antiguedad"] = _safe_fill_median(df["num_antiguedad"], default_value=0.0)
    df[cols_flag] = df[cols_flag].fillna(0)

    int32_cols = df.select_dtypes(include=["Int32"]).columns
    df[int32_cols] = df[int32_cols].fillna(0).astype("int64")

    bool_cols = df.select_dtypes(include=["boolean"]).columns
    df[bool_cols] = df[bool_cols].fillna(False)

    cols_cat_str = df.select_dtypes(include=["object", "string"]).columns.tolist()
    df[cols_cat_str] = df[cols_cat_str].fillna("SIN_INFO")

    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isnull().sum() > 0:
            df[col] = _safe_fill_median(df[col], default_value=0.0)

    # ── Winsorización con límites del TRAIN, si el artefacto está disponible ─
    fp_wins = os.path.join(DIR_ARTIFACTS, "percentil_limits.json")
    if os.path.exists(fp_wins):
        import json

        with open(fp_wins, "r", encoding="utf-8") as file:
            percentil_limits = json.load(file)
        for col, (p1, p99) in percentil_limits.items():
            if col in df.columns:
                df[col] = df[col].clip(lower=p1, upper=p99)
    else:
        print("WARN: percentil_limits.json no disponible; no se aplicará winsorización.")

    return df


def inference_fn(dir_models: str, df: pd.DataFrame, cols_vars: list) -> pd.DataFrame:
    model_tar_path = f"{dir_models}/model.tar.gz"
    extract_path = f"{dir_models}/model"

    with tarfile.open(model_tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path)

    model_path = os.path.join(extract_path, "xgboost-model")
    model = xgb.Booster()
    model.load_model(model_path)

    missing_cols = [c for c in cols_vars if c not in df.columns]
    if missing_cols:
        raise ValueError(
            "Columnas requeridas por el modelo ausentes en inferencia: "
            f"{missing_cols}. Revise Inference.sql antes de puntuar."
        )

    zero_share = (df[cols_vars].isna().mean() * 100).sort_values(ascending=False)
    print("Top 10 variables con mayor %NA antes de imputar:")
    print(zero_share.head(10).round(2).to_string())

    for col in cols_vars:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[cols_vars] = df[cols_vars].replace([np.inf, -np.inf], np.nan).fillna(0)

    dmatrix = xgb.DMatrix(df[cols_vars])
    scores = model.predict(dmatrix)
    df["puntuacion"] = scores
    print(
        "Score stats -> "
        f"min={df['puntuacion'].min():.6f}, "
        f"p25={df['puntuacion'].quantile(0.25):.6f}, "
        f"p50={df['puntuacion'].quantile(0.50):.6f}, "
        f"p75={df['puntuacion'].quantile(0.75):.6f}, "
        f"max={df['puntuacion'].max():.6f}"
    )
    return df


def postprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("puntuacion", ascending=False).drop_duplicates("cod_cli")
    df["orden"] = df["puntuacion"].rank(method="first", ascending=False).astype(int)

    df["tipo_alerta_n2"] = df["tipo_alerta_n2"].astype(str)

    # ── Umbral nueva alerta ─────────────────────────────────────────────
    UMBRAL_NUEVA_ALERTA = 0.99296

    df["grupo_corte_nueva_alerta"] = (
        (df["puntuacion"] >= UMBRAL_NUEVA_ALERTA)
        & (df["tipo_alerta_n2"] == "0")
    ).astype(int)

    # ── Quintiles de riesgo, referencia: 202508 ─────────────────────────
    # Cohorte de validación: alertas AUTOMATICA con riesgo distinto de A.
    cortes = [
        -float("inf"),
        0.224,   # P5 | P4
        0.690,   # P4 | P3
        0.892,   # P3 | P2
        0.977,   # P2 | P1
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
