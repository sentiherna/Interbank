import os
import tarfile
from pathlib import Path
from io import StringIO
import pandas as pd
import joblib
import logging

from utils import load_pickle, download_s3_file



logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


HEADERS_PATH = os.environ.get("HEADERS_PATH")
logger.debug(HEADERS_PATH)
headers = load_pickle(download_s3_file(f"{HEADERS_PATH}/feature_headers.pkl"))

MODEL_VERSION = os.environ.get("MODEL_VERSION")


def input_fn(input_data, content_type):
    logger.debug(f"Reading input data from: {StringIO(input_data)}")
    if content_type == "text/csv":
        df = pd.read_csv(StringIO(input_data), header=None, index_col=False)
        logger.debug(f'Input data number of rows: {df.shape[0]}')
    else:
        raise ValueError("Tipo de contenido no soportado. Se esperaba 'text/csv'.")
    return df


def predict_fn(input_data, model):
    logger.debug("Generating inference")
    logger.debug(f"Headers: {headers}") 
    logger.debug(f"Columns: {input_data.columns}")
    logger.debug(f"{input_data.head()}")
    
    if len(input_data.columns) == len(headers):
        input_data.columns = headers
    else:
        raise ValueError(f"Error en el numero de features: se esperaban {len(headers)} y se recibieron {input_data.shape[1]}")
    y_hat = model.predict_proba(input_data)

    return   y_hat[:, 1]


def model_fn(model_dir):
    logger.debug("Deserialize fitted model")
    preprocessor = joblib.load(os.path.join(model_dir, "model.joblib"))
    return preprocessor