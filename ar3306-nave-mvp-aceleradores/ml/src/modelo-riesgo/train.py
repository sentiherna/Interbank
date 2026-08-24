"""
Módulo de entrenamiento para modelo de scoring de riesgo.
Entrena un GradientBoostingClassifier con hiperparámetros fijos.
"""
import argparse
import logging
import os
import pandas as pd
import pickle
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_processed_data(input_path: str) -> pd.DataFrame:
    """Carga datos preprocesados desde S3."""
    logger.info(f"Cargando datos procesados desde {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def prepare_train_data(df: pd.DataFrame, test_size: float = 0.2):
    """Prepara datos de entrenamiento y test."""
    logger.info("Preparando datos de train/test")
    
    # Features a utilizar
    feature_columns = [
        'edad', 'antiguedad_meses', 'saldo_promedio_90d', 
        'cant_productos', 'dias_ultimo_movimiento', 
        'ratio_utilizacion_credito', 'cant_cuotas_atrasadas',
        'segmento_encoded'
    ]
    
    X = df[feature_columns]
    y = df['default_90d']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    logger.info(f"Train set: {X_train.shape[0]} filas")
    logger.info(f"Test set: {X_test.shape[0]} filas")
    logger.info(f"Distribución target en train - Clase 0: {(y_train==0).sum()}, Clase 1: {(y_train==1).sum()}")
    
    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train):
    """
    Entrena el modelo GradientBoostingClassifier con hiperparámetros fijos.
    
    Hiperparámetros definidos según exploración de diciembre 2023.
    No modificar sin consultar al equipo de riesgo.
    """
    logger.info("Entrenando modelo GradientBoostingClassifier")
    
    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    logger.info("Modelo entrenado exitosamente")
    
    return model


def save_model(model, model_output_path: str):
    """Guarda el modelo serializado en S3."""
    logger.info(f"Guardando modelo en {model_output_path}")
    
    # Guardar localmente
    with open('/tmp/model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Copiar a S3
    os.system(f"aws s3 cp /tmp/model.pkl {model_output_path}")
    
    logger.info("Modelo guardado exitosamente")


def save_test_data(X_test, y_test, test_output_path: str):
    """Guarda datos de test para evaluación posterior."""
    logger.info(f"Guardando datos de test en {test_output_path}")
    
    # Combinar features y target
    test_df = X_test.copy()
    test_df['default_90d'] = y_test.values
    
    # Guardar localmente
    test_df.to_csv('/tmp/test_data.csv', index=False)
    
    # Copiar a S3
    os.system(f"aws s3 cp /tmp/test_data.csv {test_output_path}")
    
    logger.info("Datos de test guardados exitosamente")


def train(input_path: str, model_output_path: str, test_output_path: str):
    """
    Función principal de entrenamiento.
    
    Args:
        input_path: Ruta S3 del archivo CSV preprocesado
        model_output_path: Ruta S3 para guardar el modelo
        test_output_path: Ruta S3 para guardar datos de test
    """
    logger.info("Iniciando entrenamiento")
    
    # Cargar datos preprocesados
    df = load_processed_data(input_path)
    
    # Preparar train/test
    X_train, X_test, y_train, y_test = prepare_train_data(df)
    
    # Entrenar modelo
    model = train_model(X_train, y_train)
    
    # Guardar modelo
    save_model(model, model_output_path)
    
    # Guardar datos de test
    save_test_data(X_test, y_test, test_output_path)
    
    logger.info("Entrenamiento completado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, required=True)
    parser.add_argument('--model-output-path', type=str, required=True)
    parser.add_argument('--test-output-path', type=str, required=True)
    
    args = parser.parse_args()
    
    train(
        input_path=args.input_path,
        model_output_path=args.model_output_path,
        test_output_path=args.test_output_path
    )
