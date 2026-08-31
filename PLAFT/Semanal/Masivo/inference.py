''' Inferencia del modelo A Masivo — PLAFT '''

import sys
import subprocess
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'xgboost==1.6.2'])
# pylint: disable=E0401,C0411,C0413
import numpy as np
np.float = float

import argparse
import datetime
import pickle
import os
import tarfile
import pytz
import pandas as pd
import xgboost as xgb

from utils.utils import read_data
from utils.utils import metrics_stability
# pylint: disable=E0401,C0411,C0413

# RUTAS DE ENTRADA =================================================================================

DIR_DATA   = '/opt/ml/processing/input/data'
DIR_MODELS = '/opt/ml/processing/input/models'
DIR_RENAME = '/opt/ml/processing/input/rename'

# RUTAS DE SALIDA ==================================================================================

DIR_RESULTS = '/opt/ml/processing/output/results'

# LISTA DE VARIABLES ===============================================================================

COLS_IDS = ["cuc_num", "cod_mes", "subsegmento", "key_value"]

SUBSEGMENTOS_MASIVO = ['Masivo']

COLS_VARS = [
    "concentracion_dia_max",
    "n_canales_distintos",
    "monto_max_soles",
    "monto_debitos_soles",
    "ratio_debito_credito",
    "fe_ratio_salidas_entradas",
    "n_trx_otros",
    "monto_transferencias_soles",
    "imp_trx_abonosefect_12m",
    "n_trx_mismo_cliente",
    "n_trx_app",
    "fe_velocidad_rotacion",
    "cnt_trx_abonosefect_12m",
    "n_trx_efectivo",
    "imp_trx_cargosefe_12m",
    "monto_efectivo_soles",
    "fe_ratio_efectivo_vs_total",
    "flg_vrcn_abonos_5m_1m",
    "imp_trx_cargostot_1m",
    "td_avg_monto_1h",
    "td_monto_total",
    "fe_zscore_cargos",
    "rat_trx_mntabnsefetot_6m",
    "cnt_trx_cargostot_12m",
    "cnt_trx_abonostot_12m",
    "td_gap_promedio",
    "num_antiguedad",
    "cnt_dif_abn_crgsefe_6m",
    "monto_total_dolares",
    "monto_promedio_dolares",
    "mto_dif_abn_crgsefe_6m",
    "n_trx_pagos",
    "tc_total_monto_mes",
    "flg_activo",
]

COLS_CAT = {"global": []}

COLS_CONT = {"global": list(COLS_VARS) + ["prob_model"]}

COLS_NULL = {col: 0.0 for col in COLS_VARS}

COLS_DTYPES = {col: "float32" for col in COLS_VARS}
COLS_DTYPES.update({"cuc_num": "string", "cod_mes": "string", "subsegmento": "string"})

COLS_OUTPUT_CONFIG = {
    'directa':      {'prefix': '',      'cols': []},
    'imputada':     {'prefix': 'impt_', 'cols': []},
    'transformada': {'prefix': 'trf_',  'cols': []},
    'woe':          {'prefix': 'woe_',  'cols': []},
    'shap':         {'prefix': 'shap_', 'cols': []},
}

# PUNTOS DE CORTE DE QUINTILES =====================================================================
# Umbrales fijos sobre prob_model para asignar grupo_calibracion.
# Derivados como promedio de los percentiles 20/40/60/80 de los 3 primeros meses de test.
# G1 = mayor riesgo (prob_model > QUINTIL_BINS[3]) … G5 = menor riesgo (prob_model ≤ QUINTIL_BINS[0]).

QUINTIL_BINS = [0.4606, 0.8541, 0.9368, 0.9827]

# PREPROCESAR LOS DATOS DE ENTRADA =================================================================


def preprocessing_fn(df: pd.DataFrame,
                     cols_null: dict,
                     cols_dtypes: dict) -> pd.DataFrame:
    '''
    Preprocesa los datos de entrada.
    ### Parametros
    - df: Datos de entrada cargados.
    - cols_null: Valores para rellenar nulos: {'col1': 0.0, 'col2': -999.0}
    - cols_dtypes: Tipos de datos de las columnas: {'col1': int, 'col2': float}
    ### Retorna
    - df: Datos preprocesados.
    - df_null: Copia de los datos antes de la imputacion (para metricas de estabilidad).
    '''

    df = df[df['subsegmento'].isin(SUBSEGMENTOS_MASIVO)].copy()
    print(f"Registros Masivo: {len(df):,}")

    df_null = df.copy()

    vars_numeric = [c for c in COLS_VARS if c in df.columns]
    for col in vars_numeric:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    if vars_numeric:
        df[vars_numeric] = df[vars_numeric].replace([np.inf, -np.inf], np.nan)

    for col, fill_val in cols_null.items():
        if col in df.columns:
            df[col] = df[col].fillna(fill_val)

    for col, dtype_tag in cols_dtypes.items():
        if col not in df.columns:
            continue
        try:
            if dtype_tag == "string":
                df[col] = df[col].astype(str)
            else:
                df[col] = df[col].astype(dtype_tag)
        except Exception:
            pass

    return df, df_null

# HACER LA INFERENCIA DEL MODELO ===================================================================


def inference_fn(dir_models: str,
                 df: pd.DataFrame,
                 cols_vars: list) -> pd.DataFrame:
    '''
    Hace la inferencia del modelo.
    ### Parametros
    - dir_models: Carpeta con el modelo entrenado.
    - df: Datos preprocesados.
    - cols_vars: Columnas que son variables del modelo.
    ### Retorna
    - df: Datos con la prediccion del modelo.
    '''

    model = None
    model_source = None

    # 1) Prioriza artefacto pickle directo (modelo historico)
    pkl_candidates = [
        'modelo_modA_masivo.pkl',
        'model.pkl',
        'model.joblib',
    ]
    for filename in pkl_candidates:
        pkl_path = os.path.join(dir_models, filename)
        if os.path.exists(pkl_path):
            with open(pkl_path, 'rb') as f:
                model = pickle.load(f)
            model_source = pkl_path
            break

    # 2) Fallback a artefacto SageMaker (model.tar.gz -> xgboost-model)
    if model is None:
        tar_path = os.path.join(dir_models, 'model.tar.gz')
        if os.path.exists(tar_path):
            extract_path = os.path.join(dir_models, 'model')
            os.makedirs(extract_path, exist_ok=True)
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(path=extract_path)

            xgb_model_path = os.path.join(extract_path, 'xgboost-model')
            if os.path.exists(xgb_model_path):
                booster = xgb.Booster()
                booster.load_model(xgb_model_path)
                model = booster
                model_source = xgb_model_path

    if model is None:
        available_files = []
        if os.path.exists(dir_models):
            available_files = sorted(os.listdir(dir_models))
        raise FileNotFoundError(
            f'No se encontro modelo compatible en {dir_models}. '
            f'Se esperaba alguno de {pkl_candidates} o model.tar.gz. '
            f'Contenido encontrado: {available_files}'
        )

    print(f'Modelo cargado desde: {model_source}')

    missing_cols = [c for c in cols_vars if c not in df.columns]
    if missing_cols:
        print(f"WARN: columnas faltantes (se imputan con 0): {missing_cols}")
        for c in missing_cols:
            df[c] = 0.0

    X = df[cols_vars].replace([np.inf, -np.inf], np.nan)

    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X)[:, 1]
    elif isinstance(model, xgb.Booster):
        probs = model.predict(xgb.DMatrix(X))
    elif hasattr(model, 'predict'):
        probs = model.predict(X)
    else:
        raise TypeError('El modelo cargado no soporta predict_proba ni predict.')

    df["prob_model"] = np.asarray(probs, dtype=float)
    df["score"] = (df["prob_model"] * 1000).round().astype("int32")

    # Quintiles: puntos de corte fijos sobre prob_model (ver QUINTIL_BINS).
    df['score_quintil'] = pd.cut(
        df['prob_model'],
        bins=[-float('inf')] + QUINTIL_BINS + [float('inf')],
        labels=['G5', 'G4', 'G3', 'G2', 'G1'],
        right=True,
        include_lowest=True,
    )

    print(f"Quintiles asignados: {df['score_quintil'].notna().sum():,} registros")
    return df

# POSTPROCESAR LA INFERENCIA DEL MODELO ============================================================


def postprocessing_fn(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Postprocesa la inferencia del modelo.
    ### Parametros
    - df: Datos con la prediccion del modelo.
    ### Retorna
    - df: Datos postprocesados.
    '''

    return df

# FORMATEAR LOS DATOS DE SALIDA ====================================================================


def output_fn(df: pd.DataFrame,
              output_cols_config: dict) -> pd.DataFrame:
    '''
    Formatea los datos de salida.
    ### Parametros
    - df: Datos postprocesados con la prediccion del modelo.
    - output_cols_config: Configuracion de columnas de salida adicionales.
    ### Retorna
    - df_output: Datos formateados de salida.
    '''

    datetime_now = datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    df_output = pd.DataFrame()
    df_output['cod_mes'] = df['cod_mes']
    df_output['fec_dia'] = ''
    df_output['cod_tip_doc'] = ''
    df_output['key_value'] = df['key_value']
    df_output['cod_cli'] = df['cuc_num']
    df_output['prob_model'] = df['prob_model']
    df_output['puntuacion'] = df['score'].astype('int32')
    df_output['modelo'] = ''
    df_output['ts_carga'] = datetime_now
    df_output['grupo_ejec'] = ''
    df_output['segmento'] = df['subsegmento']
    df_output['orden'] = ''
    df_output['grupo_calibracion'] = df['score_quintil']
    df_output['prob_modelo_cal'] = np.nan
    df_output['puntuacion_cal'] = np.nan
    df_output['extra_01'] = ''
    df_output['extra_02'] = ''
    df_output['extra_03'] = ''
    df_output['extra_04'] = ''
    df_output['extra_05'] = ''

    for group_cfg in output_cols_config.values():
        prefix = group_cfg.get('prefix', '')
        for col_var in group_cfg.get('cols', []):
            output_col = f'{prefix}{col_var}' if prefix else col_var
            df_output[output_col] = df[col_var]

    return df_output

# FUNCION PRINCIPAL ================================================================================


def main(args: argparse.Namespace) -> None:
    ''' Funcion principal '''

    model = args.model
    table_score = args.table_score
    partition = args.partition

    df = read_data(DIR_DATA, DIR_RENAME)

    df, df_null = preprocessing_fn(df, COLS_NULL, COLS_DTYPES)

    df = inference_fn(DIR_MODELS, df, COLS_VARS)
    df = postprocessing_fn(df)
    df_output = output_fn(df, COLS_OUTPUT_CONFIG)
    df_output['modelo'] = model

    path = f'{DIR_RESULTS}/{table_score}_{partition}.txt'
    df_output.to_csv(path, index=False, sep='|')
    print(f"Salida completa: {path}")

    extra_cols = [
        f"{group_cfg.get('prefix', '')}{col}"
        for group_cfg in COLS_OUTPUT_CONFIG.values()
        for col in group_cfg.get('cols', [])
    ]
    path = f'{DIR_RESULTS}/{table_score}_tdt_{partition}.txt'
    df_output.drop(extra_cols, axis=1).to_csv(path, index=False, sep='|')
    print(f"Salida TDT: {path}")

    var_segmentos = ''
    df_null['prob_model'] = df_output['prob_model'].values
    df_metrics = metrics_stability(df_null, COLS_CAT, COLS_CONT, var_segmentos)

    path = f'{DIR_RESULTS}/t_est_{model}_rsk_{partition}.txt'
    df_metrics.to_csv(path, index=False, sep='|')
    print(f"Metricas de estabilidad: {path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str)
    parser.add_argument('--table-score', type=str)
    parser.add_argument('--partition', type=str)
    main(parser.parse_args())
