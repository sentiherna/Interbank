"""
Módulo de preprocesamiento para modelo de scoring de riesgo.
Realiza imputación, encoding y scaling de features.
"""
import argparse
import logging
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data(input_path: str) -> pd.DataFrame:
    """Carga datos desde S3."""
    logger.info(f"Cargando datos desde {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def impute_nulls(df: pd.DataFrame, numeric_features: list) -> pd.DataFrame:
    """Imputa valores nulos con la mediana para features numéricas."""
    logger.info("Imputando valores nulos con mediana")
    df_copy = df.copy()
    
    for feature in numeric_features:
        if feature in df_copy.columns:
            median_value = df_copy[feature].median()
            nulls_count = df_copy[feature].isnull().sum()
            if nulls_count > 0:
                logger.info(f"Imputando {nulls_count} nulos en {feature} con mediana {median_value}")
                df_copy[feature].fillna(median_value, inplace=True)
    
    return df_copy


def encode_segmento(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica la variable categórica segmento."""
    logger.info("Codificando variable segmento")
    df_copy = df.copy()
    
    segmento_mapping = {
        'RETAIL': 0,
        'PYME': 1,
        'CORPORATIVO': 2
    }
    
    df_copy['segmento_encoded'] = df_copy['segmento'].map(segmento_mapping)
    # Valores nulos asignados a RETAIL (0)
    nulls_count = df_copy['segmento_encoded'].isnull().sum()
    if nulls_count > 0:
        logger.info(f"Asignando {nulls_count} valores nulos de segmento a RETAIL (0)")
        df_copy['segmento_encoded'].fillna(0, inplace=True)
    
    df_copy['segmento_encoded'] = df_copy['segmento_encoded'].astype(int)
    
    return df_copy


def scale_features(df: pd.DataFrame, feature_columns: list, scaler=None, fit: bool = True):
    """Aplica StandardScaler a las features."""
    logger.info("Aplicando StandardScaler")
    df_copy = df.copy()
    
    if fit:
        scaler = StandardScaler()
        df_copy[feature_columns] = scaler.fit_transform(df_copy[feature_columns])
        logger.info("Scaler entrenado y aplicado")
    else:
        if scaler is None:
            raise ValueError("Se debe proporcionar un scaler cuando fit=False")
        df_copy[feature_columns] = scaler.transform(df_copy[feature_columns])
        logger.info("Scaler aplicado (sin fit)")
    
    return df_copy, scaler


def preprocess(input_path: str, output_path: str, scaler_output_path: str, mode: str = 'train'):
    """
    Función principal de preprocesamiento.
    
    Args:
        input_path: Ruta S3 del archivo CSV de entrada
        output_path: Ruta S3 para guardar datos procesados
        scaler_output_path: Ruta S3 para guardar el scaler
        mode: 'train' para entrenar scaler, 'inference' para aplicar scaler existente
    """
    logger.info(f"Iniciando preprocesamiento en modo {mode}")
    
    # Cargar datos
    df = load_data(input_path)
    
    # Definir features numéricas
    numeric_features = [
        'edad', 'antiguedad_meses', 'saldo_promedio_90d', 
        'cant_productos', 'dias_ultimo_movimiento', 
        'ratio_utilizacion_credito', 'cant_cuotas_atrasadas'
    ]
    
    # Imputación
    df = impute_nulls(df, numeric_features)
    
    # Encoding de segmento
    df = encode_segmento(df)
    
    # Features finales para scaling
    feature_columns = numeric_features + ['segmento_encoded']
    
    # Scaling
    if mode == 'train':
        df, scaler = scale_features(df, feature_columns, fit=True)
        # Guardar scaler
        logger.info(f"Guardando scaler en {scaler_output_path}")
        with open('/tmp/scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        # Copiar a S3
        os.system(f"aws s3 cp /tmp/scaler.pkl {scaler_output_path}")
    else:
        # Cargar scaler existente
        logger.info(f"Cargando scaler desde {scaler_output_path}")
        os.system(f"aws s3 cp {scaler_output_path} /tmp/scaler.pkl")
        with open('/tmp/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        df, _ = scale_features(df, feature_columns, scaler=scaler, fit=False)
    
    # Guardar datos procesados
    logger.info(f"Guardando datos procesados en {output_path}")
    df.to_csv('/tmp/processed_data.csv', index=False)
    os.system(f"aws s3 cp /tmp/processed_data.csv {output_path}")
    
    logger.info("Preprocesamiento completado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, required=True)
    parser.add_argument('--output-path', type=str, required=True)
    parser.add_argument('--scaler-output-path', type=str, required=True)
    parser.add_argument('--mode', type=str, default='train', choices=['train', 'inference'])
    
    args = parser.parse_args()
    
    preprocess(
        input_path=args.input_path,
        output_path=args.output_path,
        scaler_output_path=args.scaler_output_path,
        mode=args.mode
    )
