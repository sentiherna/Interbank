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
from sklearn.preprocessing import LabelEncoder
import pickle
import glob

# ======================== RUTAS DE ENTRADA ==============================
DIR_DATA = "/opt/ml/processing/input/data"
DIR_MODELS = "/opt/ml/processing/input/models"

# ======================== RUTAS DE SALIDA ===============================
DIR_RESULTS = "/opt/ml/processing/output/results"

# ======================== LISTA DE VARIABLES ============================
COLS_IDS = ['key_value', 'cod_mes', 'tipo_alerta_n2','trx_riesgo_cliente']
COLS_CONTROL = ["tipo_alerta_n2"]

COLS_VARS = [
 'alertas_por_antiguedad',
'cnt_meses_siningresos_12m',
'cnt_trx_cargostot_3m',
'imp_trx_abonosefect_6m',
'grupo_final',
'cnt_alerta_hist',
'mto_pas_soles',
'pasivo_vs_ingresos',
'imp_trx_cargosefe_6m',
'rat_trx_abonosefectot_9m',
'ind_lin_ing_tcr_ibk',
'sow_svep1actallsfm01',
'edad',
'cod_ubigeo_cd',
'cnt_trx_abonospromtot_3m',
'ratio_cargos_1m_vs_6m',
'cnt_meses_sinegresos_12m',
'ratio_abonos_1m_vs_6m',
'cre_pct_salvig_tc_rccsf_m03',
'var_usotcrrstsf03m',
'lvl_edu',
'cod_rsg_pep',
'desc_departamento',
'flg_pep',
'ctd_camptot06m',
'desc_provincia',
'num_antiguedad',
'cre_saltot_tc_rccsf_m02',
'prm_camptot06m',
'avg_trx_cargostot_3m',
'ros_por_trx_3m',
'prm_usotcrrstsf03m',
'atm_frec',
'sow_lnep1tcrallsfm01',
'prom_salvig_pp_rccsf_06m',
'cre_salvig_tc_rccsf_m02',
'atm_monto',
'var_lintcrrstsf03m',
'rec_camptot06m',
'bpi_trx_mon_min',
'max_camptot06m',
'rat_trx_abonosefectot_3m',
'flg_alerta_12m',
'atm_recen',
'cnt_trx_sinenv_alext_12m',

]

# ======================== UTILIDADES ===================================


def read_data(dir_data):
    try:
        path = glob.glob(f"{dir_data}/*.csv")[0]
        df = pd.read_csv(path)
    except:
        path = f"{dir_data}/*"
        df = dd.read_parquet(path).compute().reset_index(drop=True)
    return df


def preprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.fillna(0)

    categoricas = [
        "cod_nacionalidad", "cod_sectorista_id", "rgn", "grupo_final", "desc_provincia", "desc_departamento","cod_ciiu_v4","flg_activo_pep","tip_lvledu","lvl_edu"
    ]

    for c in categoricas:
        if c in df.columns:
            le = LabelEncoder()
            df[c] = le.fit_transform(df[c].astype(str))

    return df


# ======================== MODELOS ======================================


def load_model(model_tar_path, extract_path):
    with tarfile.open(model_tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path)

    model_path = os.path.join(extract_path, "xgboost-model")
    model = xgb.Booster()
    model.load_model(model_path)
    return model


def score_with_model(df, model, cols_vars):
    dmatrix = xgb.DMatrix(df[cols_vars])
    return model.predict(dmatrix)


#def inference_fn(dir_models: str, df: pd.DataFrame, cols_vars: list) -> pd.DataFrame:

    # Split por tipo_alerta_n2 (ya encodeado, pero SIN_INFO quedó como string antes)
#    df_con_alerta = df[df["tipo_alerta_n2"] != "SIN_INFO"].copy()
 #   df_sin_info = df[df["tipo_alerta_n2"] == "SIN_INFO"].copy()

    # Cargar modelos
 #   model_con_alerta = load_model(
  #      f"{dir_models}/con_alerta/model.tar.gz", f"{dir_models}/con_alerta_extracted"
  #  )

   # model_sin_info = load_model(
   #     f"{dir_models}/sin_alerta/model.tar.gz", f"{dir_models}/sin_info_extracted"
   # )

    # Inferencia
   # if len(df_con_alerta) > 0:
   #     df_con_alerta["puntuacion"] = score_with_model(df_con_alerta, model_con_alerta, cols_vars)

    #if len(df_sin_info) > 0:
      #  df_sin_info["puntuacion"] = score_with_model(df_sin_info, model_sin_info, cols_vars)

    # Unir
   # df_final = pd.concat([df_con_alerta, df_sin_info], axis=0)

    #return df_final

def load_model(model_tar_path, extract_path):
    with tarfile.open(model_tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path)

    model_path = os.path.join(extract_path, "xgboost-model")
    model = xgb.Booster()
    model.load_model(model_path)
    return model


def score_with_model(df, model, cols_vars):
    dmatrix = xgb.DMatrix(df[cols_vars])
    return model.predict(dmatrix)


def inference_fn(dir_models: str, df: pd.DataFrame, cols_vars: list) -> pd.DataFrame:

    # Cargar modelo único (sin_info)
    model = load_model(
        f"{dir_models}/model.tar.gz", f"{dir_models}/sin_info_extracted"
    )

    # Inferencia sobre todo el DataFrame
    df["puntuacion"] = score_with_model(df, model, cols_vars)

    return df
    


# ======================== POSTPROCESS ==================================


def postprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    df = (
        df.sort_values("puntuacion", ascending=False)
        .drop_duplicates("cod_cli")
        .reset_index(drop=True)
    )

    df["orden"] = df["puntuacion"].rank(method="first", ascending=False).astype(int)

    df["grupo_corte_nueva_alerta"] = (
        (df["puntuacion"] > 0.9646596312522888) & (df["tipo_alerta_n2"] == "SIN_INFO")
    ).astype(int)

    cortes = [-float("inf"),0.321 ,0.681, 0.88,0.958, float("inf")]
    etiquetas = [5,4, 3, 2, 1]

    df["grupo_alerta"] = pd.cut(
        df["puntuacion"], bins=cortes, labels=etiquetas, include_lowest=True
    ).astype(int)

    nombres_grupo = {1: "P1", 2: "P2", 3: "P3", 4: "P4",5: "P5"}
    df["grupo_alerta_desc"] = df["grupo_alerta"].map(nombres_grupo)

    return df


def output_fn(df: pd.DataFrame) -> pd.DataFrame:
    datetime_now = datetime.datetime.now(pytz.timezone("America/Lima")).strftime("%Y%m%d")

    df_output = pd.DataFrame()
    df_output["codmes"] = df["cod_mes"]
    df_output["num_documento"] = df["key_value"]
    df_output["codunico"] = df["cod_cli"]
    df_output["modelo"] = "plaft_pj_minorista"
    df_output["fec_replica"] = datetime_now
    df_output["grupo_alerta"] = df["grupo_alerta_desc"]
    df_output["grupo_corte_nueva_alerta"] = df["grupo_corte_nueva_alerta"]
    df_output["score"] = df["puntuacion"]
    df_output["orden"] = df["orden"]
    df_output["variable1"] = df["tipo_alerta_n2"]
    df_output["variable2"] = ""
    df_output["variable3"] = ""

    return df_output


# ======================== MAIN ==========================================


def main(args: argparse.Namespace) -> None:
    df = read_data(DIR_DATA)
    df = preprocessing_fn(df)
    df = inference_fn(DIR_MODELS, df, COLS_VARS)
    df = postprocessing_fn(df)
    df_output = output_fn(df)

    path = f"{DIR_RESULTS}/{args.table_score}_{args.partition}.txt"
    df_output.to_csv(path, index=False, sep="|")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--table-score", type=str, required=True)
    parser.add_argument("--partition", type=str, required=True)
    main(parser.parse_args())
