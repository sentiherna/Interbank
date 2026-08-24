# Arqueologia: preprocessing_1.py

- **Objetivo:** pipeline de preprocesamiento para Train/Validation/Test.
- **Evidencia:** lineas 42-45 declaran `MESES_TRAIN` 202501-202507, `MESES_VAL` 202508-202509 y `MESES_TEST` comienza tambien en 202508; lineas 52-64 leen parquet y filtran meses; lineas 86-94 renombran target y eliminan duplicados.
- **Preprocesamiento:** lineas 122-156 imputan transaccionales con 0, variaciones con -1, numericas con mediana, flags con 0, booleanas con False y categoricas con `SIN_INFO`; lineas 170-220 hacen encoding con mapas ajustados en Train; lineas 232-269 hacen winsorizacion y seleccion de columnas.
- **Artefactos/salidas:** lineas 298-306 guardan/cargan mapas; lineas 383-388 escriben CSV de Train/Validation/Test.
- **Hallazgo critico:** Test y Validation se solapan en 202508-202509 segun lineas 42-45, contradiciendo `03_validacion_clientes_unicos.py`.
- **Dependencias:** dask/pandas y parquet; rutas SageMaker `/opt/ml`.
- **Estado:** PARCIAL para preprocesamiento; NO CUMPLE para particion temporal disjunta de este script.