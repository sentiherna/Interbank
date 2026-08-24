"""
Módulo de evaluación para modelo de scoring de riesgo.
Genera métricas y predicciones sobre el conjunto de test.
"""
import argparse
import logging
import os
import json
import pandas as pd
import pickle
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, 
    recall_score, f1_score, confusion_matrix, classification_report
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model(model_path: str):
    """Carga el modelo desde S3."""
    logger.info(f"Cargando modelo desde {model_path}")
    
    # Copiar desde S3
    os.system(f"aws s3 cp {model_path} /tmp/model.pkl")
    
    # Cargar modelo
    with open('/tmp/model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    logger.info("Modelo cargado exitosamente")
    return model


def load_test_data(test_path: str) -> tuple:
    """Carga datos de test desde S3."""
    logger.info(f"Cargando datos de test desde {test_path}")
    
    df = pd.read_csv(test_path)
    
    # Separar features y target
    feature_columns = [
        'edad', 'antiguedad_meses', 'saldo_promedio_90d', 
        'cant_productos', 'dias_ultimo_movimiento', 
        'ratio_utilizacion_credito', 'cant_cuotas_atrasadas',
        'segmento_encoded'
    ]
    
    X_test = df[feature_columns]
    y_test = df['default_90d']
    
    logger.info(f"Test data cargado: {X_test.shape[0]} filas")
    
    return X_test, y_test


def generate_predictions(model, X_test):
    """Genera predicciones de probabilidad y clase."""
    logger.info("Generando predicciones")
    
    # Probabilidades de clase positiva (default)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Clase predicha con umbral 0.5 por defecto
    y_pred = model.predict(X_test)
    
    # Flag de riesgo alto (umbral 0.6)
    riesgo_alto = (y_pred_proba >= 0.6).astype(int)
    
    logger.info(f"Predicciones generadas: {len(y_pred)} registros")
    logger.info(f"Distribución riesgo_alto - 0: {(riesgo_alto==0).sum()}, 1: {(riesgo_alto==1).sum()}")
    
    return y_pred, y_pred_proba, riesgo_alto


def calculate_metrics(y_test, y_pred, y_pred_proba):
    """Calcula métricas de evaluación."""
    logger.info("Calculando métricas de evaluación")
    
    metrics = {
        'auc_roc': float(roc_auc_score(y_test, y_pred_proba)),
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1_score': float(f1_score(y_test, y_pred, zero_division=0))
    }
    
    # Matriz de confusión
    cm = confusion_matrix(y_test, y_pred)
    metrics['confusion_matrix'] = {
        'true_negatives': int(cm[0, 0]),
        'false_positives': int(cm[0, 1]),
        'false_negatives': int(cm[1, 0]),
        'true_positives': int(cm[1, 1])
    }
    
    # Log de métricas
    logger.info(f"AUC-ROC: {metrics['auc_roc']:.4f}")
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
    
    # Classification report
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred))
    
    return metrics


def save_metrics(metrics: dict, metrics_output_path: str):
    """Guarda métricas en formato JSON."""
    logger.info(f"Guardando métricas en {metrics_output_path}")
    
    # Guardar localmente
    with open('/tmp/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Copiar a S3
    os.system(f"aws s3 cp /tmp/metrics.json {metrics_output_path}")
    
    logger.info("Métricas guardadas exitosamente")


def save_predictions(X_test, y_test, y_pred_proba, riesgo_alto, predictions_output_path: str):
    """Guarda predicciones detalladas."""
    logger.info(f"Guardando predicciones en {predictions_output_path}")
    
    # Crear DataFrame con predicciones
    predictions_df = pd.DataFrame({
        'default_90d_real': y_test.values,
        'score_riesgo': y_pred_proba,
        'riesgo_alto': riesgo_alto
    })
    
    # Agregar features para análisis
    for col in X_test.columns:
        predictions_df[col] = X_test[col].values
    
    # Guardar localmente
    predictions_df.to_csv('/tmp/predictions.csv', index=False)
    
    # Copiar a S3
    os.system(f"aws s3 cp /tmp/predictions.csv {predictions_output_path}")
    
    logger.info(f"Predicciones guardadas: {len(predictions_df)} registros")


def evaluate(model_path: str, test_path: str, metrics_output_path: str, predictions_output_path: str):
    """
    Función principal de evaluación.
    
    Args:
        model_path: Ruta S3 del modelo entrenado
        test_path: Ruta S3 de los datos de test
        metrics_output_path: Ruta S3 para guardar métricas
        predictions_output_path: Ruta S3 para guardar predicciones
    """
    logger.info("Iniciando evaluación")
    
    # Cargar modelo
    model = load_model(model_path)
    
    # Cargar datos de test
    X_test, y_test = load_test_data(test_path)
    
    # Generar predicciones
    y_pred, y_pred_proba, riesgo_alto = generate_predictions(model, X_test)
    
    # Calcular métricas
    metrics = calculate_metrics(y_test, y_pred, y_pred_proba)
    
    # Guardar métricas
    save_metrics(metrics, metrics_output_path)
    
    # Guardar predicciones
    save_predictions(X_test, y_test, y_pred_proba, riesgo_alto, predictions_output_path)
    
    logger.info("Evaluación completada")
    
    # Retornar métricas para el pipeline
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', type=str, required=True)
    parser.add_argument('--test-path', type=str, required=True)
    parser.add_argument('--metrics-output-path', type=str, required=True)
    parser.add_argument('--predictions-output-path', type=str, required=True)
    
    args = parser.parse_args()
    
    evaluate(
        model_path=args.model_path,
        test_path=args.test_path,
        metrics_output_path=args.metrics_output_path,
        predictions_output_path=args.predictions_output_path
    )
