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
import glob

# ======================== RUTAS DE ENTRADA ==============================
DIR_DATA = "/opt/ml/processing/input/data"
DIR_MODELS = "/opt/ml/processing/input/models"
DIR_RENAME = "/opt/ml/processing/input/rename"

# ======================== RUTAS DE SALIDA ===============================
DIR_RESULTS = "/opt/ml/processing/output/results"

# ======================== LISTA DE VARIABLES ============================
COLS_IDS = ["cod_mes", "key_value","cod_cli","tipo_alerta_n2"]
COLS_CONTROL = ["trx_riesgo_cliente"]
COLS_POST = ["key_value", "tipo_alerta_n2", "cod_mes"]

COLS_VARS = [  # Features del modelo (completos)
   'mto_pas_soles',
 'imp_trx_abonosefect_6m',
 'imp_trx_cargosefe_6m',
 'avg_trx_cargostot_3m',
 'cnt_trx_cargostot_3m',
 'cnt_trx_abonospromtot_3m',
 'rat_trx_abonosefectot_1m',
 'rat_trx_abonosefectot_3m',
 'rat_trx_abonosefectot_9m',
 'rat_mntcrgsefetot_1m',
 'num_antiguedad',
 'cnt_meses_sinegresos_12m',
 'cod_ubigeo_cd',
 'cod_sectorista_id',
 'flg_vrcn_abonos_5m_1m',
 'flg_vrcn_efe_cargos_5m_1m',
 'mto_fact_declarado_sunat',
 'avg_cp_men_ing_12m',
 'avg_cpmenegr_12m',
 'max_mto_cpegrmen_12m',
 'cnt_trx_sinenv_alext_12m',
 'mto_al_ext_12m',
 'mto_del_ext_12m',
 'cnt_noticias',
 'flg_alerta_12m',
 'cnt_alerta_hist',
 'cnt_ros_hist',
 'ratio_abonos_1m_vs_6m',
 'ratio_cargos_1m_vs_6m',
 'share_cp_egresos',
 'share_cp_ingresos',
 'ros_por_trx_3m',
 'ingresos_vs_facturacion',
 'pasivo_vs_ingresos',
 'ratio_egresos_exterior',
 'ratio_ingresos_exterior',
]

# ======================== FUNCIONES DE UTILIDAD =========================




def read_data(dir_data):
    import glob

    cols_needed = list(set(COLS_IDS + COLS_CONTROL + COLS_VARS))

    csv_files = glob.glob(f"{dir_data}/*.csv")

    if len(csv_files) > 0:
        df = pd.read_csv(csv_files[0], usecols=cols_needed)
    else:
        path = f"{dir_data}/*"
        df = dd.read_parquet(
            path,
            columns=cols_needed,
            engine="pyarrow"
        ).compute().reset_index(drop=True)

    return df


#def read_data(dir_data):
#    try:
#        path = glob.glob(f"{dir_data}/*.csv")[0]
#        df = pd.read_csv(path)
#    except:
#        path = f"{dir_data}/*"
#        df = dd.read_parquet(path).compute().reset_index(drop=True)
#    return df


def preprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.fillna(0)

   # categorical_nominal = ["rgn", "grupo_final"]
   # for col in categorical_nominal:
    #    df[col] = df[col].astype("category").cat.codes

    categorical_columns = [
      "mto_fact_declarado_sunat", "cod_ubigeo_cd", "cod_sectorista_id"]

    for col in categorical_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df[categorical_columns] = df[categorical_columns].fillna(df[categorical_columns].mean())

 #   df["ingreso_bruto"] = df["ingreso_bruto"].combine_first(df["ing_brt"])

    # df.drop(columns=["ing_brt"], inplace=True)

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

    df["grupo_corte_nueva_alerta"] = (
        (df["puntuacion"] >0.992137148976326)
        & (df["tipo_alerta_n2"] == "0")
    ).astype(int)

    cortes = [
        -float("inf"),
       0.746,
       0.909,
       0.963,
       0.987,
        float("inf")
    ]
    etiquetas = [5, 4, 3, 2, 1]

    df["grupo_alerta"] = pd.cut(
        df["puntuacion"],
        bins=cortes,
        labels=etiquetas,
        include_lowest=True
    ).astype(int)

    nombres_grupo = {
        1: "P1",
        2: "P2",
        3: "P3",
        4: "P4",
        5: "P5"
    }

    df["grupo_alerta_desc"] = (
        df["grupo_alerta"]
        .map(nombres_grupo)
    )
    return df


def output_fn(df: pd.DataFrame, cols_control: list = None) -> pd.DataFrame:
    datetime_now = datetime.datetime.now(pytz.timezone("America/Lima")).strftime("%Y%m%d")

    df_output = pd.DataFrame()
    df_output["cod_mes"] = df["cod_mes"]
    df_output["cod_tip_doc"] = df["cod_tip_doc"]
    df_output["key_value"] = df["key_value"]
    df_output["cod_cli"] = df["cod_cli"]
    df_output["prob_model"] = ""
    df_output["puntuacion"] = df["puntuacion"]
    df_output["modelo"] = "plaft_pj_minorista"
    df_output["ts_carga"] = datetime_now
    df_output["grupo_ejec"] = df["grupo_alerta_desc"]
    df_output["segmento"] = ""
    df_output["orden"] = df["orden"]
    df_output["extra_01"] = df["tipo_alerta_n2"]
    df_output["extra_02"] = df["trx_riesgo_cliente"]
    df_output["extra_03"] = df["grupo_corte_nueva_alerta"]
    df_output["extra_04"] = ""
    df_output["extra_05"] = ""

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
