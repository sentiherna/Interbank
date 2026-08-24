# Arqueologia: 03_validacion_clientes_unicos.py

- **Objetivo:** validar independencia entre Train/Validation/Test a nivel de cliente-mes.
- **Evidencia:** lineas 35-38 declaran TRAIN 202501-202507, VAL 202508-202509 y TEST 202510-202604; lineas 90-117 asignan conjunto por `cod_mes`; lineas 135-138 calculan intersecciones de clientes.
- **Entradas:** parquet S3 en linea 80 y columnas `cod_cli`, `cod_mes`, `target` (lineas 42, 113-117).
- **Salidas:** reporte HTML y resultados en `outputs_validacion` (lineas 51, 457).
- **Target/metricas:** calcula tasa target por conjunto; no demuestra ventana de 30 dias.
- **Hallazgo:** el script si implementa la particion disjunta declarada, pero su resultado ejecutado no esta disponible en Train; por tanto la ausencia de reporte impide confirmar cifras.
- **Dependencias:** pandas/numpy/awswrangler/S3 y credenciales externas.
- **Estado de evidencia:** PARCIAL para la logica; NO EVIDENCIADO para resultados ejecutados.