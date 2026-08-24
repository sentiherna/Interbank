# Arqueologia: 04_reportes_preprocesamiento.py

- **Objetivo:** producir reportes de faltantes y preprocesamiento.
- **Evidencia:** lineas 71-81 fijan periodos; lineas 192-194 separan Train/Validation/Test; lineas 256-263 muestran imputacion por tipo (cero, mediana y `SIN_INFO`); lineas 293-305 incorporan importancias SHAP desde CSV.
- **Entradas:** parquet S3 (lineas 142-143), diccionario/variables e `importancia_variables.csv` (lineas 297-299).
- **Salidas:** descripciones/reportes de preprocesamiento; rutas de salida deben verificarse en ejecucion.
- **Target/modelo/HPO:** no entrena modelo ni prueba metricas finales.
- **Validacion:** reporta faltantes por conjunto, no prueba por si solo leakage ni calidad predictiva.
- **Ambiguedades:** depende de datos S3, credenciales y archivos auxiliares externos.