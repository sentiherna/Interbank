import click
import json
import pickle
import tarfile
import joblib
import os
import shap
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline

from nxaatk import BinaryClassificationPerformance

from utils import *


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

model_path = "/opt/ml/processing/model/model.tar.gz"
test_path = "/opt/ml/processing/test"
output_dir = "/opt/ml/processing/output"
headers_path = "/opt/ml/processing/feature_headers"
shap_path="/opt/ml/processing/train_sample"

headers = load_pickle(f"{headers_path}/feature_headers.pkl")

@click.command()
@click.option('--test-tag', type=str)
@click.option('--model-tag', type=str)
@click.option('--best-model-path', type=str)
@click.option('--shap-tag',type=str)
def main(test_tag, model_tag, best_model_path,shap_tag):
    logger.debug("Starting evaluation.")
    with tarfile.open(model_path) as tar:
        tar.extractall(path=".")
    logger.debug("Loading model.")
    model = joblib.load(open(model_tag, "rb"))
    
    logger.debug("Reading test data.")
    data = pd.read_csv(Path(test_path) / test_tag)
    id_cols = ['ID','PERIODO','DATE_MIN_CREACION_CI', 'DATE_MIN_CREACION_CO', 'FECHA_DE_ONBOARDING', 'UNIVERSO_TARGET_FECHA_ACTIVACION', 'TC_CLIENTES_FECHA_ACTIVACION','TARGET']
    
    data.columns = id_cols+headers
    #data.dropna(subset=data.columns[0], inplace=True)
    
    data = data.reset_index(drop = True)
    logger.debug("Printing data columns.")
    print(data.columns)
    
    
    y = data.TARGET.values
    
    ids = data[['PERIODO', 'ID','DATE_MIN_CREACION_CI', 'DATE_MIN_CREACION_CO', 'FECHA_DE_ONBOARDING', 'UNIVERSO_TARGET_FECHA_ACTIVACION', 'TC_CLIENTES_FECHA_ACTIVACION']]
    
    #ids.colums = [id_col, date_col]
    logger.info(f"data.columns: {data.columns}")
    logger.info(f"headers: {headers}")
    
    
    logger.info("Performing predictions against test data.")
    y_pred = model.predict_proba(data[headers])[:, 1]
    
    logger.debug("Calculating metrics.")
    testmetrics = metrics(y, y_pred)
    
    report_dict = {
        "binary_classification_metrics": {
            "accuracy": {
                "value": testmetrics['accuracy'],
                "standard_deviation": "NaN",
            },
            "auc": {
                "value": testmetrics['roc_auc'],
                "standard_deviation": "NaN"
            },
            "ks": {
                "value": testmetrics['ks'],
                "standard_deviation": "NaN"
            },
        },
    }

    logger.info("Classification report:\n{}".format(report_dict))
    
    to_json(report_dict, f"{output_dir}/evaluation/evaluation.json")
    
    ids['target'] = y
    ids['score'] = y_pred
    data['SCORE'] = y_pred
    
    ks_list = calcular_ks_por_periodo(ids, 'score', 'target', 'PERIODO')
    logger.info("KS por periodo test:\n{}".format(ks_list))
    
    #ids.to_csv(f"{output_dir}/pred/test_prediction.csv", index=False)
    data.to_csv(f"{output_dir}/pred/test_prediction.csv", index=False)
    
    
    bc = BinaryClassificationPerformance(y_true=y, y_score=y_pred)
    to_pkl(bc, f"{output_dir}/metrics/metrics_class.pkl")
     
    ## shap values 
    data = pd.read_csv(Path(shap_path) / shap_tag)
    
    df_predict = model[:-1].transform(data[headers])
    support = model.named_steps['feature_selection'].support_ 
    selected_col_names = np.array(model['preprocessor'].get_feature_names_out())[support]
    
    df_transformed = pd.DataFrame(data=df_predict, columns=selected_col_names, index=data.index)
    shap_model=model['model']
    
    features_cleaned = selected_col_names.tolist()
    
    lista_quitar = ['numerical__cnt_imputer__', 'numerical__remainder__', 'categorical__']
    
    for i in lista_quitar:
        features_cleaned = [feature.replace(i, '') for feature in features_cleaned]
    
    
    print(features_cleaned)
    
    df_transformed.columns = features_cleaned
    
    explainer = shap.TreeExplainer(shap_model, feature_names=features_cleaned)
    shap_values = explainer.shap_values(df_transformed)
    
    #ordenar la lista de variables por feature importance
    shap_values_df = pd.DataFrame(shap_values, columns=features_cleaned)
    feature_importance = shap_values_df.abs().mean().sort_values(ascending=False)

    sorted_features = feature_importance.index.tolist()
    
    #shap en 1 es mora
    shap.summary_plot(shap_values, df_transformed, max_display=40, show=False)

    to_pkl(sorted_features, Path(output_dir) / 'shap/features_selected_names.pkl')
    
    
    
    # Guardar el gráfico localmente
    local_path_plot = f"{output_dir}/shap/shap_summary_plot.png"
    plt.savefig(local_path_plot)
    
    shap.summary_plot(shap_values, df_transformed, plot_type="bar")
    local_path_bar = f"{output_dir}/shap/shap_summary_bar.png"
    plt.savefig(local_path_bar)
    
if __name__ == "__main__":
    main()
    
    

