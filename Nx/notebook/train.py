import click
import json
import pickle
import joblib
import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import make_scorer, accuracy_score, roc_auc_score
from sklearn.model_selection import cross_validate
from nxaatk import get_pipeline, CustomTimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.compose import ColumnTransformer
from utils import *  # Asegúrate de que utils tenga las funciones necesarias

from IPython.display import clear_output
clear_output()
import matplotlib.dates as mdates

from sagemaker_containers.beta.framework import encoders, worker
from io import StringIO
import datetime as dt

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

@click.command()
@click.option('--target-col', type=str)
@click.option('--date-col', type=str)
@click.option('--overfit-alpha', type=int, default=10)
@click.option('--train-dir', envvar="SM_CHANNEL_TRAIN")
@click.option('--train-tag', envvar="SM_CHANNEL_TRAIN_TAG")
@click.option('--val-dir', envvar="SM_CHANNEL_VAL")
@click.option('--model-dir', envvar="SM_MODEL_DIR")
@click.option('--val-tag', envvar="SM_CHANNEL_VAL_TAG")
@click.option('--output-dir', envvar="SM_OUTPUT_DATA_DIR")
@click.option('--featselect-perc', type=float, default=100)
@click.option('--reg-alpha', type=float, default=0.0)
@click.option('--colsample-bylevel',type=float,default=1)
@click.option('--colsample-bytree',type=float,default=1)
@click.option('--learning-rate',type=float, default=0.3)
@click.option('--gamma',type=float, default=0)
@click.option('--reg-lambda',type=float, default=1)
@click.option('--max-delta-step', type=int, default=0)
@click.option('--max-depth', type=int, default=6)
@click.option('--min-child-weight',type=float, default=1)
@click.option('--subsample' ,type=float, default=1)
@click.option('--n-estimators', type=int, default=100)
def main(train_dir, train_tag, val_dir, val_tag, model_dir, output_dir,date_col,target_col, featselect_perc, overfit_alpha, **model_kwargs):
    ##read data
    data_train = pd.read_csv(Path(train_dir) / train_tag)
    data_val = pd.read_csv(Path(val_dir) / val_tag)

    # Eliminar la transformación de las variables y el pipeline de preprocesamiento

    ## Separar el target de las variables
    y_train = data_train.pop(target_col)
    y_val = data_val.pop(target_col)

    # Crear el modelo de clasificación
    model = XGBClassifier(objective='binary:logistic', random_state=42, **model_kwargs)

    # Entrenamiento del modelo con los datos de entrenamiento (sin transformación de características)
    model.fit(data_train, y_train)
    
    # Predicción y métricas en el conjunto de entrenamiento
    y_pred_train = model.predict_proba(data_train)[:, 1]
    train_metrics = {
        'accuracy': accuracy_score(y_train, model.predict(data_train)),
        'roc_auc': roc_auc_score(y_train, y_pred_train)
    }
    log_step_metrics(train_metrics, 'train', logger)
    
    # Predicción y métricas en el conjunto de validación
    y_pred_val = model.predict_proba(data_val)[:, 1]
    val_metrics = {
        'accuracy': accuracy_score(y_val, model.predict(data_val)),
        'roc_auc': roc_auc_score(y_val, y_pred_val)
    }
    log_step_metrics(val_metrics, 'val', logger)
    
    # Guardar el modelo
    joblib.dump(model, Path(model_dir) / 'model.joblib')
    logger.debug("Saved model")

if __name__ == '__main__':
    main()
