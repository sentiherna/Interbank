import os
import subprocess
import sys
import pickle
import time
from sklearn.model_selection import train_test_split
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

def process_data(df, target_1, sample=False, cols_Exclude=[]):
    df.drop(cols_Exclude, axis=1, inplace=True) 

    columns = df.columns
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='ignore', downcast='float')
        
    if sample:
        df_pos = df[df[target_1] != 0]
        df_pos.reset_index(drop=True, inplace=True)
        df_neg = df.drop(df_pos.index)
        df_neg = df_neg.sample(frac=0.3, random_state=999)
        df_neg.reset_index(drop=True, inplace=True)
        df = pd.concat([df_pos, df_neg])
        df.reset_index(drop=True, inplace=True)
        
    return df

def LecturaDatos(meses, cols_Exclude=[]):
    df_path = '/opt/ml/processing/input/data_pn_total_expandido_new_v1.parquet'
    print(f"Leyendo datos desde {df_path}")
    df = dd.read_parquet(df_path).compute()

    if 'cod_mes' not in df.columns:
        raise ValueError("⚠️ No se encontró la columna 'cod_mes' en el DataFrame.") 

    df['cod_mes'] = df['cod_mes'].astype(str)

    df = df[df['cod_mes'].isin(meses)]
    print(f"✅ Filtrado: {len(df):,} registros correspondientes a los meses {meses}")

    df = process_data(df, 'target', False, cols_Exclude)
    return df

def TratamientoDF(df, train=1):
    print("======Tratamiento")
    start_time = time.time()



    DIR_COLUMNS = '/opt/ml/processing/input/Columns'

    path_columns = f'{DIR_COLUMNS}/selected_columns.csv'
    columnas = pd.read_csv(path_columns, header=None)
    list_var = columnas[0].tolist()
    df = df[list_var]    

    print("--- %s min ---" % ((time.time() - start_time)/60))
    print("======Fin Tratamiento")
    return df


if __name__ == '__main__':

    # install libraries
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.19.5"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas==1.1.5"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "toolz"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dask==2021.7.2"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fsspec"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "category_encoders==2.3.0"])

    import pandas as pd
    import numpy as np
    import dask.dataframe as dd
    from category_encoders import target_encoder

    meses = ['202501','202502','202503','202504','202505','202506','202507']
    df = LecturaDatos(meses, cols_Exclude=[])

    # Guardamos extras solo las columnas indicadas
    extras = df[['cod_mes', 'key_value', 'tipo_alerta_n2','cod_cli','trx_riesgo_cliente']].copy()

    # Tratamiento para modelo (solo variables de entrenamiento)
    df_modelo = TratamientoDF(df.copy(), train=1)

 # =============================================================
    # 3) validación
    # =============================================================
    meses_val = ['202508','202509']
    df_val_raw = LecturaDatos(meses_val, cols_Exclude=[])

    extras_val = df_val_raw[['cod_mes','key_value', 'tipo_alerta_n2','cod_cli','trx_riesgo_cliente']].copy()
    df_val = TratamientoDF(df_val_raw.copy(), train=1)  # solo variables para modelo



    # Split 33% para validación
    #df_train, df_val, extras_train, extras_val = train_test_split(
    #    df_modelo, extras, test_size=0.33, random_state=123, shuffle=True
    #)

    # =============================================================
    # 3) Test
    # =============================================================
    test_meses = ['202508','202509','202510','202511','202512','202601','202602','202603','202604']
    df_test_raw = LecturaDatos(test_meses, cols_Exclude=[])

    extras_test = df_test_raw[['cod_mes','key_value', 'tipo_alerta_n2','cod_cli','trx_riesgo_cliente']].copy()
    df_test = TratamientoDF(df_test_raw.copy(), train=1)  # solo variables para modelo

    # =============================================================
    # 4) Headers del modelo
    # =============================================================
    df_headers = df_modelo.dtypes.to_frame("dtypes").reset_index()
    df_headers.columns = ["variables","dtypes"]

    # =============================================================
    # 5) Guardado
    # =============================================================
    headers_path = '/opt/ml/processing/headers/headers_total.csv'
    train_path = '/opt/ml/processing/train/train_total.csv'
    val_path = '/opt/ml/processing/val/validation_total.csv'
    test_path = '/opt/ml/processing/test/test_total.csv'

    df_modelo.to_csv(train_path, header=False, index=False)
    df_val.to_csv(val_path, header=False, index=False)
    df_test.to_csv(test_path, header=False, index=False)
    df_headers.to_csv(headers_path, index=False)

    # Extras
    extras_val.to_csv('/opt/ml/processing/val/extras_validation_total.csv', index=False)
    extras_test.to_csv('/opt/ml/processing/test/extras_test_total.csv', index=False)

    print("✅ Train, Validation, Test y Headers generados correctamente.")

    