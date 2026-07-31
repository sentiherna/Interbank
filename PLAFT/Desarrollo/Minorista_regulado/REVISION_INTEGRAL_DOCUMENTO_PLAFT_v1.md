# Revisión integral de consistencia documental — PLAFT PJ Minorista v3.1

**Fecha:** 31 de julio de 2026  
**Base de contraste:** todos los archivos disponibles en `Minorista_regulado` al momento de la revisión.  
**Criterio:** una afirmación se considera *sustentada* solo cuando existe un artefacto disponible que la demuestra de forma directa y reproducible.

## Dictamen global

El documento **no está consistente con el paquete de archivos disponible** y no debe enviarse a Ubimia como versión final. Tiene una base documental útil —diccionario fuente, consultas, notebooks de construcción/EDA, preprocesamiento, HPO, validación y objeto del modelo—, pero mezcla resultados de distintas ejecuciones, cifras no soportadas, anexos ausentes y declaraciones de corrección que contradicen el código actual.

## Matriz por sección

| Sección | Estado | Resultado de la revisión |
|---|---|---|
| 1. Introducción y referencias | Parcial | El alcance BPE/PJ y XGBoost son coherentes. Las referencias nombran varios archivos que no están en la carpeta (`00.limpieza_datos.ipynb`, `11.PRE PROCESSING.ipynb`, `12.HPO.ipynb`, `13.VALIDACION_TOTAL.ipynb`, entre otros), mientras los existentes se llaman `0.limpieza_datos.ipynb` y `Train/1.PRE PROCESSING.ipynb`, etc. También se cita un informe Ubimia v3.0 que no está disponible. |
| 2. Contexto PLAFT | Parcial | El manual `MET-GeneracionAlertas_GestionRiesgos_LAFT.pdf` respalda la existencia de alertas automáticas/manuales y el marco PLAFT. No respalda por sí solo todas las reglas internas de clasificación “Con Riesgo/Falso Positivo” que presenta el texto. |
| 3. Arquitectura | Contradictorio | La arquitectura es plausible, pero declara 36 variables finales. En `Train/3.VALIDACION_TOTAL.ipynb` se cargan 33 columnas incluyendo `target`: ello equivale a 32 predictores. El documento usa también 32 y 37 en otras secciones. |
| 4. Target | Contradictorio | `Bases/Querys/model_target.sql` construye `target_m = 1` si `MAX(calificacion_monitoreo) = '1'` y 0 en otro caso. No usa las etiquetas textuales documentadas, no excluye explícitamente no clasificados ni contiene fechas de generación/clasificación. La unión se realiza por cliente y mismo mes. |
| 5. Dataset y muestreo | Contradictorio | El notebook `01.genera_base_train.ipynb` sí filtra BPE, separa hasta 202507/desde 202508 y toma 0.5% de casos sin alerta. Pero el texto pone 0.05% en dos lugares. La salida disponible registra 175.400 filas train, mientras el documento declara 854.321; la validación del notebook muestra 324.253 y test 1.509.824, no los rangos aproximados indicados. |
| 6. Integridad temporal | Contradictorio | La consulta disponible une variables y target en el mismo `cod_mes`; no hay fechas de corte ni una prueba disponible de no leakage. Además, `Train/preprocessing_1.py` usa validación 202508–202509 y test 202508–202604, por lo que ambos se solapan. No se encontró el script/reporte que el documento cita como evidencia de exclusividad de clientes. |
| 7. Variables predictoras | Parcial | `model_variables.sql` y `diccionario_variables.xlsx` sustentan la fuente `d_perm_aws.t_agg_alertas_plaft`, nombres, tipos y descripciones de variables fuente. El diccionario no deja trazabilidad completa de cada transformación/modelo final, dominio permitido ni orden del vector de producción. |
| 8. Preprocesamiento | Contradictorio | La sección afirma imputación diferenciada. El script ejecutable `Train/preprocessing_1.py` aplica primero `df.fillna(0)` a todo el dataframe; luego convierte una lista a numérico y completa esos nulos con la media. No se encontraron los CSV/notebook de evidencia citados. |
| 9. Selección de variables | Contradictorio | Existe EDA y LightGBM en `02.bivariados+EDA_train+seleccion_variables.ipynb`; sin embargo, su salida muestra 34 variables analizadas, 31 tras filtros y 29 que acumulan 99% de importancia. El notebook usa correlación 0.70, no 0.90, y entrena LightGBM directo, no validación cruzada 5-fold. El documento declara 305→32, 32/36/37 y criterios que no se reproducen con el artefacto disponible. |
| 10. Desarrollo del modelo | Parcial | XGBoost, `scale_pos_weight=494`, AUC y early stopping están sustentados por `Train/2.HPO.ipynb`, `Train/hpo.txt` y `Train/metricas_train.txt`. No está sustentado el tamaño train de 854.321 ni “~457 rounds”; `hpo.txt` muestra `num_round=780`. El objeto está en formato XGBoost comprimido, no como `modelo_xgboost_final.pkl` citado. |
| 11. HPO | Parcial | HPO de SageMaker y el objetivo `validation:auc` existen. Los valores finales no coinciden: el documento declara eta 0.0708, subsample 0.8163, colsample 0.8449, gamma 5.3742 y 457 rounds; `Train/hpo.txt` reporta eta 0.013463, subsample 0.989020, colsample 0.889042, gamma 6.320260 y 780 rounds. Faltan el CSV de 50 ejecuciones y logs citados. |
| 12. Calibración | No verificable | El documento declara Isotonic Regression como análisis teórico no productivo, pero no se encuentran `3.calibracion_modelo.py` ni `07_calibracion_y_validacion.ipynb`. Las cifras de pre/post calibración no tienen evidencia disponible. |
| 13. Evaluación | Parcial / contradictorio | `Train/3.VALIDACION_TOTAL.ipynb` calcula Gini, tablas por quintil y una función Top-K. Se observa Gini mensual promedio 0.9192 y, para 202508 con un umbral fijo, precisión 0.1142 y recall 0.2437. No están disponibles las tablas fuente que soporten todos los AUC, KS, Top 20%, lift y valores por mes del documento. Tampoco puede llamarse OOT independiente al test por el solapamiento detectado. |
| 14. Interpretabilidad | Parcial | Hay SHAP para XGBoost en `Train/3.VALIDACION_TOTAL.ipynb` y LightGBM para importancia en EDA. No está el HTML de SHAP ni el CSV de importancias mencionados; el ranking/porcentajes del documento no son reproducibles desde el paquete. |
| 15. Implementación | No verificable | No hay pipeline, endpoint, especificación de integración, contrato de entrada/salida ni evidencia de despliegue productivo. Esta sección debe describirse como diseño propuesto, no implementación vigente. |
| 16. Monitoreo y gobierno | No verificable | No hay jobs, dashboards, umbrales aprobados, reportes de monitoreo, evidencia de reentrenamiento ni aprobaciones. Debe trasladarse a plan de monitoreo propuesto. |
| 17. Conclusiones | Contradictorio | No puede concluir “técnicamente validado”, “documentación completada” o “listo para producción”. Persisten inconsistencias materiales de target, muestras, selección, parámetros, evaluación y anexos. |

## Hallazgos transversales comprobados

1. **Porcentaje sin alerta inconsistente:** 0.05% en secciones 1.3 y 5.1; 0.5% en 5.5 y en el notebook (`porcentaje_sin_alerta = 0.005`).
2. **Variables finales inconsistentes:** 36 en arquitectura y dataset, 37 como objeto de producción y 32 en selección/conclusiones. El notebook de validación usa 32 predictores (33 columnas con target).
3. **Tamaño de muestras inconsistente:** documento: train 854.321; salida EDA/validación disponible: train 175.400, validation 324.253, test 1.509.824.
4. **Particiones inconsistentes:** documento: test octubre 2025–abril 2026; código de preprocesamiento: test agosto 2025–abril 2026. La validación es agosto–septiembre 2025 en ambos.
5. **HPO inconsistente:** parámetros y rounds de sección 11.4 no coinciden con `Train/hpo.txt`.
6. **Imputación inconsistente:** documento describe reglas diferenciadas; código aplica cero global antes de cualquier otro tratamiento.
7. **Target/horizonte no demostrados:** no hay ventana de 30 días ni campos de fecha de clasificación en la query disponible.
8. **Anexos faltantes:** no existen los scripts, CSV, HTML, notebooks y matriz que el propio documento usa como evidencia.

## Archivos que sí sirven como evidencia

| Artefacto | Qué respalda | Limitación |
|---|---|---|
| `MET-GeneracionAlertas_GestionRiesgos_LAFT.pdf` | Marco de generación de alertas automáticas/manuales. | No prueba target, muestras ni modelo. |
| `diccionario_variables.xlsx` | Tabla fuente, nombres, tipos y descripciones de variables iniciales. | No contiene el diccionario formal completo del modelo final. |
| `Bases/Querys/model_target.sql` | Lógica actualmente documentada para target. | Expone la falta de ventana de 30 días/corte temporal. |
| `Bases/Querys/model_variables.sql` | Fuente, BPE, transformaciones y variables candidatas. | No identifica de forma inequívoca el vector final/versión de producción. |
| `01.genera_base_train.ipynb` | Muestreo 0.5%, corte train/test y algunos conteos. | No coincide con cifras del documento; no crea validación independiente visible. |
| `02.bivariados+EDA_train+seleccion_variables.ipynb` | EDA, correlación y LightGBM. | Resultado 34→31→29 no coincide con metodología escrita. |
| `Train/preprocessing_1.py` | Preprocesamiento y periodos usados en SageMaker. | Contradice la imputación/independencia declaradas. |
| `Train/2.HPO.ipynb`, `Train/hpo.txt`, `Train/metricas_train.txt` | HPO y configuración/entrenamiento XGBoost. | Parámetros no coinciden con sección 11.4. |
| `Train/3.VALIDACION_TOTAL.ipynb` | Carga de objeto, Gini, quintiles, Top-K y SHAP. | No aporta todas las métricas documentadas y refleja solapamiento de conjuntos. |

## Anexos/referencias del documento no disponibles

- `02_validacion_integridad_temporal.py`, `Validación_Integridad_Temporal.txt`.
- `03_validacion_clientes_unicos.py`, `cliente_distribucion_por_conjunto.csv`, `Independencia_Conjuntos_Train_Val_Test.html`.
- `Análisis_Sensibilidad_Proporción_Sin_Alerta.ipynb`.
- `Diccionario_Variables_Formal.xlsx`, `Variables_Finales_32_LightGBM.csv`.
- `01_Missing_PreImputacion.csv`, `02_Estadisticos_PostImputacion.csv`, `03_Outliers_Detectados.csv`, `01_resumen_estadistico.csv`.
- `2.entrenamiento_modelo.py`, `05_entrenamiento_xgboost.ipynb`, `sagemaker_hpo_results.csv`, `06_hpo_analisis.ipynb`.
- `3.calibracion_modelo.py`, `07_calibracion_y_validacion.ipynb`.
- `resultados/SHAP_Feature_Importance.html` y `trazabilidad/Matriz_Documentacion_Modelo.xlsx`.

## Conclusión operativa

La documentación debe reconstruirse a partir de una única ejecución congelada y trazable. Mientras ello no ocurra, puede remitirse a Ubimia únicamente como **borrador sujeto a remediación**, acompañado de una matriz de hallazgos abierta; no como respuesta de cierre ni como evidencia de idoneidad para producción.
