import argparse
import ast
import os
import json
from io import StringIO
import logging
import pickle
from urllib.parse import urlparse

import boto3
import pandas as pd

output_path = "/opt/ml/processing"

s3 = boto3.client("s3")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())  

def calcular_media_y_moda(dataframe):
    medias = dataframe.select_dtypes(include='number').mean()
    modas = dataframe.select_dtypes(exclude='number').mode().iloc[0]

    orden_columnas = dataframe.columns
    resultado = pd.concat([medias, modas])
    resultado = resultado[orden_columnas]

    return resultado

def parse_s3_uri(s3_uri):
    # Parse the S3 URI
    parsed_uri = urlparse(s3_uri)

    # Verificar si el esquema es 's3'
    if parsed_uri.scheme != 's3':
        raise ValueError("El URI proporcionado no es un URI de S3 válido")

    # Extraer el nombre del bucket y el prefijo
    bucket = parsed_uri.netloc
    prefix = parsed_uri.path.lstrip('/')

    return bucket, prefix

def dump_pickle(data, file):
    with open(file, 'wb') as f:
        pickle.dump(data, f)

def list_files(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for obj in response["Contents"]:
        if obj["Key"].endswith(".csv"):
            yield obj["Key"]

def read_csv_from_s3(bucket, key):
    csv_obj = s3.get_object(Bucket=bucket, Key=key)
    body = csv_obj["Body"]
    csv_string = body.read().decode("utf-8")

    df = pd.read_csv(StringIO(csv_string))
    return df

def save_csv_to_s3(df, bucket, key):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_resource = boto3.resource("s3")
    s3_resource.Object(bucket, key).put(Body=csv_buffer.getvalue())

def main(input_uri, step_periods, n_sample):
    logger.debug("Starting preprocessing.")
    
    bucket, prefix = parse_s3_uri(input_uri)
    keys = list(list_files(bucket, prefix))
    logger.debug(f"List of dataset:  {list(keys)}")

    for step, period_list in step_periods.items():
        step_keys = [key for key in keys if any(key.endswith(f"{period}/features.csv") for period in period_list)]
        
        logger.info(f"Reading {step} data")
        dfs = [read_csv_from_s3(bucket, key) for key in step_keys]
        df = pd.concat(dfs).reset_index(drop=True)
        
        logger.debug(df.columns.tolist())

        id_columns = ['DOCUMENTO']  # Aseguramos que 'DOCUMENTO' es la columna ID
        target_column = 'TARGET'
        date_column = 'MES_CORRIDA'

        # Actualizar feature_columns para excluir solo las columnas que realmente deseas
        feature_columns = [c for c in df.columns if c not in id_columns + [target_column, date_column]]

        # Eliminar columnas de tipo objeto que podrían estar causando problemas (por ejemplo, cadenas)
        df = df.select_dtypes(exclude=['object'])

        # Eliminar la columna ID (DOCUMENTO) y la columna de fecha (MES_CORRIDA)
        df = df.drop(columns=id_columns + [date_column], errors='ignore')

        # No se eliminan columnas, simplemente se utiliza df tal como está.
        target = df.pop(target_column)

        logger.info(f"Writing out {step} datasets to {output_path}/{step}")
        
        if step == 'test':  # Para TEST guardo sin headers por el TRANSFORM STEP con IDs
            df = pd.concat([target, df], axis=1)
            logger.info(f"{step} datasets has {df.shape[0]} rows and {df.shape[1]} columns")
            logger.debug(f"Dataset columns: {df.columns}")
            df.to_csv(f"{output_path}/{step}/" + f"{step}_features.csv", index=False, header=True)
            
        elif step == 'train':  # TRAIN Y VAL SIN IDS
            df = pd.concat([target, df], axis=1)
            logger.info(f"{step} datasets has {df.shape[0]} rows and {df.shape[1]} columns")
            logger.debug(f"Dataset columns: {df.columns}")
            df.to_csv(f"{output_path}/{step}/" + f"{step}_features.csv", index=False, header=True)
            df.sample(n=n_sample, random_state=42).to_csv(f"{output_path}/{step}_sample/" + f"{step}_sample_features.csv", index=False, header=True)
            baseline = calcular_media_y_moda(df[[c for c in df.columns if c != target_column]])
            baseline.to_csv(f"{output_path}/shap_baseline/" + f"baseline.csv", index=False)
            
        else:  # TRAIN Y VAL SIN IDS
            df = pd.concat([target, df], axis=1)
            logger.info(f"{step} datasets has {df.shape[0]} rows and {df.shape[1]} columns")
            logger.debug(f"Dataset columns: {df.columns}")
            df.to_csv(f"{output_path}/{step}/" + f"{step}_features.csv", index=False, header=True)
            
        if step == list(step_periods.keys())[0]:  # GUARDO EL FEATURE NAME
            dump_pickle(
                [c for c in df.columns.tolist() if c not in [target_column, id_columns, date_column]],
                f"{output_path}/feature_headers/feature_headers.pkl"
            )
            
    logger.debug("Preprocessing is completed.")
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-uri", type=str, default="")
    parser.add_argument("--step-periods", type=json.loads)
    parser.add_argument("--n_shap_sample", type=int, default=1000)

    args = parser.parse_args()

    main(args.input_uri, args.step_periods, args.n_shap_sample)

