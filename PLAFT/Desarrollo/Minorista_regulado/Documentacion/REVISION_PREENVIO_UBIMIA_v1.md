# Revisión preenvío a Ubimia — Modelo PLAFT PJ Minorista

**Fecha de revisión:** 31 de julio de 2026  
**Documentos revisados:** `DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v3.txt`, `Documento_Metodologico_PLAFT_PJ_Minorista_Formato_Modelo_v3.docx`, consultas SQL, notebooks, preprocesamiento, artefacto de modelo y dos informes de Ubimia disponibles en esta carpeta.  
**Dictamen:** **NO APTO PARA REMISIÓN COMO DOCUMENTO METODOLÓGICO FINAL NI PARA DECLARAR EL MODELO LISTO PARA PRODUCCIÓN.**

## Motivo del dictamen

La versión 3.1 contiene afirmaciones de corrección y evidencia que no están respaldadas por los artefactos entregados. En particular, las consultas y el código disponible contradicen afirmaciones sobre separación temporal, independencia de los conjuntos y tratamiento de faltantes. Enviar el documento tal como está expondría a Interbank a una observación por inconsistencia documental y por cierre indebido de hallazgos de Ubimia.

Este dictamen no invalida el objetivo de negocio ni el uso de XGBoost; delimita lo que puede sostenerse con la evidencia disponible.

## Hallazgos que impiden el envío final

| Prioridad | Hallazgo verificable | Evidencia disponible | Implicación | Acción mínima para cierre |
|---|---|---|---|---|
| Crítica | No se demuestra una ventana de target de 30 días ni la precedencia de variables respecto del target. | `Bases/Querys/model_target.sql` une `a.cod_mes = b.periodo_alerta`; no selecciona fechas de generación/clasificación ni impone una ventana de 30 días. | No es posible afirmar prevención de leakage ni el significado documentado del horizonte. | Corregir la extracción con fechas de corte, conservar evidencia de ejecución y reentrenar/reevaluar. |
| Crítica | Validación y test se solapan temporalmente. | `Train/preprocessing_1.py`: validación = 202508–202509; test = 202508–202604. | La validación no es independiente del test. | Redefinir particiones disjuntas; regenerar bases, modelo y métricas. |
| Alta | El tratamiento de faltantes implementado no es diferenciado. | `Train/preprocessing_1.py`, función `TratamientoDF`: `df.fillna(0)`. | Contradice la sección 8.2 de v3.1 y el hallazgo metodológico de Ubimia. | Implementar reglas por variable, ajustar pruebas y documentar porcentaje/resultado por variable. |
| Alta | No hay trazabilidad cerrada entre variables documentadas y objeto oficial. | El documento alterna 36, 37 y 32 variables; `Train/model.tar.gz` no trae manifiesto/archivo de columnas; faltan los anexos citados. | No se puede certificar que el modelo documentado sea el que se utilizaría en producción. | Generar manifiesto versionado: hash del artefacto, lista ordenada de variables, tipos, transformaciones y parámetros. |
| Alta | Métricas operativas y discrepancias de alertas automáticas no están cerradas. | Ubimia reporta diferencias materiales en 202512 y 202601; v3.1 propone causas, pero no contiene base, script ni análisis reproducible que las confirme. | No corresponde atribuir la diferencia a tamaño muestral/volatilidad como conclusión. | Reproducir con base congelada, definición exacta del filtro productivo y conciliación de cada mes. |
| Media | La muestra y sus cifras no son consistentes ni plenamente evidenciadas. | v3.1 usa 0.05% en alcance/población y 0.5% en la metodología; incluye valores aproximados y archivos de respaldo inexistentes. | La población, la tasa de positivos y el balanceo no son auditables. | Publicar tabla única con conteos exactos, tasa positiva, periodos y criterio de inclusión/exclusión. |
| Media | Se afirma calibración independiente/corregida, a la vez que se declara no implementada; scripts citados no existen. | Sección 12 de v3.1; no están `3.calibracion_modelo.py` ni `07_calibracion_y_validacion.ipynb`. | Debe eliminarse toda afirmación de calibración ejecutada/corregida. | Declarar "no aplicada/no evaluada con evidencia disponible" o aportar artefactos y resultados reproducibles. |
| Media | No se dispone de todos los anexos invocados. | No se encuentran: `02_validacion_integridad_temporal.py`, `03_validacion_clientes_unicos.py`, `Análisis_Sensibilidad_Proporción_Sin_Alerta.ipynb`, `Variables_Finales_32_LightGBM.csv`, `01_resumen_estadistico.csv` y otros. | El documento no es autocontenido ni reproducible. | Adjuntar anexos, controlarlos por versión y referenciarlos desde un índice de evidencias. |

## Correcciones editoriales obligatorias en v3.1

Estas afirmaciones deben retirarse o reemplazarse por una declaración de limitación mientras no exista evidencia reproducible:

1. "Listo para implementación en producción" y las marcas de aprobación/cierre de la sección 17.
2. "No existe traslape entre Train, Validation y Test" y cualquier afirmación de separación a nivel cliente no sustentada por un reporte entregado.
3. "Mitigaciones implementadas" y "se verifica" en la sección 6.2.
4. La descripción de imputación diferenciada de la sección 8.2.
5. La calibración "implementada/corregida" y las métricas teóricas de la sección 12.
6. Las explicaciones causales de la discrepancia diciembre 2025–enero 2026 en la sección 13.7.
7. Los conteos, porcentajes, importancias y decisiones de selección que no cuenten con archivo de salida o notebook reproducible adjunto.

También debe unificarse una sola definición para: población objetivo, unidad de análisis, proporción de clientes sin alerta, periodos de cada conjunto, número de variables finales, universo productivo y versión/hash del modelo.

## Paquete que sí debe enviarse una vez cerrado

1. Documento metodológico corregido, con control de versiones, responsables y aprobaciones.
2. Respuesta a cada observación de Ubimia: estado, decisión, evidencia y referencia exacta al anexo.
3. Diccionario formal de variables: nombre, definición, tipo, fuente, dominio, ventana temporal, transformación, faltantes y condición de uso.
4. Consultas SQL parametrizadas y sus salidas congeladas: población, target, train, validación y test.
5. Evidencia de no leakage y de exclusividad de clientes entre conjuntos.
6. Código versionado de preprocesamiento, selección, entrenamiento, HPO, evaluación y calibración (si aplica), más requisitos de ejecución.
7. Artefacto oficial de producción con hash SHA-256 y manifiesto de variables/hiperparámetros.
8. Tabla de resultados reproducible, global y sobre el universo productivo; incluir precisión, recall y lift Top-K definidos con el volumen operativo real.
9. Conciliación de las diferencias de diciembre de 2025 y enero de 2026 frente a la réplica de Ubimia.

## Texto sugerido para comunicar el estado a los responsables internos

> La revisión de la versión 3.1 identificó que varios hallazgos de Ubimia figuran como corregidos en el documento, pero no están soportados por los artefactos de desarrollo disponibles. Para preservar la trazabilidad y no emitir declaraciones no verificables, el documento no debe remitirse como versión final hasta completar las acciones indicadas. Una vez generados los anexos y reejecutadas las validaciones, se emitirá una versión metodológica final con matriz de cierre y control de versiones.

## Fuentes revisadas

- `Ubimia - Interbank - Réplica - Resultados validación modelo PLAFT (v2.0).pdf`
- `Ubimia - Interbank - Réplica - Informe de validación modelo PLAFT (v1.0).seguro.pdf`
- `DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v3.txt` y su DOCX equivalente v3.1
- `Bases/Querys/model_target.sql` y `Bases/Querys/model_variables.sql`
- `01.genera_base_train.ipynb`
- `Train/preprocessing_1.py`, `Train/hpo.txt`, `Train/metricas_train.txt` y `Train/model.tar.gz`
