# Reporte final de auditoria del modelo PLAFT

**Dictamen final: NO CONSISTENTE**

Documento: `C:\Users\b46637\OneDrive - Interbank\PLAFT\Interbank\PLAFT\Desarrollo\Minorista_regulado\Documentacion\Documento_Metodologico_PLAFT_PJ_Minorista_Formato_Modelo_v2.pdf`  
Train: `C:\Users\b46637\OneDrive - Interbank\PLAFT\Interbank\PLAFT\Desarrollo\Minorista_regulado\Train`  
PDF: 55 paginas con texto extraible.  
Artefactos evaluados: 10 notebooks/scripts.

## Resumen

La documentacion se considera consistente unicamente cuando todos los requisitos verificables tienen estado `CUMPLE` o `NO APLICA`. El resultado actual es **NO CONSISTENTE** porque existen contradicciones y evidencia faltante.

| Estado | Cantidad |
|---|---:|
| CUMPLE | 2 |
| PARCIAL | 8 |
| NO CUMPLE | 2 |
| NO EVIDENCIADO | 3 |
| NO APLICA | 0 |

## Matriz de trazabilidad

| ID | Requisito | Estado | Pagina/seccion PDF | Evidencia en Train | Accion |
|---|---|---|---|---|---|
| R-001 | Vector final de variables | **PARCIAL** | p. 3, 5, 6, 7, 13, 14, 15, 16 | `0.limpieza_datos.ipynb` (celda 16); `0.limpieza_datos.ipynb` (celda 17); `0.limpieza_datos.ipynb` (celda 18); `0.limpieza_datos.ipynb` (celda 22); `0.limpieza_datos.ipynb` (celda 23) | Aportar un vector final versionado y unico. |
| R-002 | Train/validacion/test sin traslape temporal | **NO CUMPLE** | p. 15 | `03_validacion_clientes_unicos.py` (linea 36); `03_validacion_clientes_unicos.py` (linea 37); `03_validacion_clientes_unicos.py` (linea 38); `03_validacion_clientes_unicos.py` (linea 91); `03_validacion_clientes_unicos.py` (linea 93) | Corregir periodos contradictorios y ejecutar una prueba de disjuncion. |
| R-003 | Target con horizonte de 30 dias | **NO EVIDENCIADO** | p. 2, 8, 52 | `0.limpieza_datos.ipynb` (celda 6); `0.limpieza_datos.ipynb` (celda 25); `01.genera_base_train.ipynb` (celda 5) | Aportar fechas y la logica que implemente la ventana de 30 dias. |
| R-004 | Fuente y unidad de analisis | **PARCIAL** | seccion de datos | `0.limpieza_datos.ipynb` (celda 3); `01.genera_base_train.ipynb` (celda 4); `01.genera_base_train.ipynb` (celda 5); `01.genera_base_train.ipynb` (celda 6); `01.genera_base_train.ipynb` (celda 9) | Versionar fuente, esquema y contrato de entrada. |
| R-005 | Muestreo y tamanos de muestra | **PARCIAL** | seccion de muestreo | `0.limpieza_datos.ipynb` (celda 3); `0.limpieza_datos.ipynb` (celda 7); `0.limpieza_datos.ipynb` (celda 16); `0.limpieza_datos.ipynb` (celda 17); `0.limpieza_datos.ipynb` (celda 18) | Persistir conteos y vincularlos con la ejecucion oficial. |
| R-006 | Imputacion diferenciada | **CUMPLE** | p. 22, 24, 53 | `0.limpieza_datos.ipynb` (celda 9); `0.limpieza_datos.ipynb` (celda 10); `0.limpieza_datos.ipynb` (celda 12); `0.limpieza_datos.ipynb` (celda 17); `0.limpieza_datos.ipynb` (celda 19) | Comparar cada regla con el texto exacto del documento. |
| R-007 | Seleccion de variables | **PARCIAL** | p. 3, 5, 25, 27, 48, 53 | `0.limpieza_datos.ipynb` (celda 6); `0.limpieza_datos.ipynb` (celda 13); `0.limpieza_datos.ipynb` (celda 18); `0.limpieza_datos.ipynb` (celda 22); `0.limpieza_datos.ipynb` (celda 25) | Documentar filtros, conteos y archivo final reproducible. |
| R-008 | Algoritmo declarado | **CUMPLE** | p. 2, 3, 5, 27, 28, 29, 31, 32 | `0.limpieza_datos.ipynb` (celda 2); `0.limpieza_datos.ipynb` (celda 46); `0.limpieza_datos.ipynb` (celda 64); `0.limpieza_datos.ipynb` (celda 66); `0.limpieza_datos.ipynb` (celda 71) | Separar modelo exploratorio y modelo oficial. |
| R-009 | Hiperparametros finales | **PARCIAL** | seccion HPO | `0.limpieza_datos.ipynb` (celda 6); `0.limpieza_datos.ipynb` (celda 21); `0.limpieza_datos.ipynb` (celda 22); `0.limpieza_datos.ipynb` (celda 46); `0.limpieza_datos.ipynb` (celda 66) | Congelar parametros, semilla, fecha, dependencias y hash. |
| R-010 | Metricas declaradas | **PARCIAL** | p. 2, 3, 27, 28, 29, 31, 34, 37 | `0.limpieza_datos.ipynb` (celda 46); `0.limpieza_datos.ipynb` (celda 47); `0.limpieza_datos.ipynb` (celda 49); `0.limpieza_datos.ipynb` (celda 50); `0.limpieza_datos.ipynb` (celda 53) | Persistir metricas por conjunto y mes. |
| R-011 | Validaciones temporal/cliente/mes | **PARCIAL** | seccion validacion | `0.limpieza_datos.ipynb` (celda 49); `0.limpieza_datos.ipynb` (celda 55); `0.limpieza_datos.ipynb` (celda 56); `0.limpieza_datos.ipynb` (celda 75); `0.limpieza_datos.ipynb` (celda 76) | Ejecutar y guardar reportes de independencia y validacion. |
| R-012 | SHAP e importancias | **PARCIAL** | p. 2, 3, 27, 28, 29, 30, 31, 32 | `0.limpieza_datos.ipynb` (celda 7); `0.limpieza_datos.ipynb` (celda 16); `0.limpieza_datos.ipynb` (celda 17); `0.limpieza_datos.ipynb` (celda 18); `0.limpieza_datos.ipynb` (celda 22) | Vincular salidas de importancias con la ejecucion oficial. |
| R-013 | Calibracion | **NO EVIDENCIADO** | seccion calibracion | No se encontro evidencia en Train. | Declarar formalmente no implementada o aportar resultados. |
| R-014 | Gobierno, integracion y monitoreo | **NO EVIDENCIADO** | secciones de implementacion/gobierno | `01.genera_base_train.ipynb` (celda 5) | No presentar diseño como evidencia de implementacion. |
| R-015 | Conclusiones de consistencia | **NO CUMPLE** | conclusiones del documento | Depende de los hallazgos anteriores; target: `0.limpieza_datos.ipynb` (celda 6); `0.limpieza_datos.ipynb` (celda 13); `0.limpieza_datos.ipynb` (celda 16); `0.limpieza_datos.ipynb` (celda 17); `0.limpieza_datos.ipynb` (celda 18). | No declarar la documentacion consistente hasta cerrar los hallazgos. |

## Hallazgos criticos

1. `preprocessing_1.py` declara `202508` y `202509` tanto en Validation como en Test.
2. No se evidencio una ventana target de 30 dias mediante fechas de generacion y clasificacion.
3. No existe una ejecucion oficial unica vinculada a hash, dataset, dependencias, semilla, metricas e hiperparametros.
4. Los notebooks calculan metricas, pero eso no prueba que las cifras del PDF correspondan a la misma ejecucion.

## Inventario de artefactos

- `0.limpieza_datos.ipynb`
- `01.genera_base_train.ipynb`
- `02.bivariados+EDA_train+seleccion_variables.ipynb`
- `03.bivariados+EDA_test.ipynb`
- `03_validacion_clientes_unicos.py`
- `04_reportes_preprocesamiento.py`
- `1.PRE PROCESSING.ipynb`
- `2.HPO.ipynb`
- `3.VALIDACION_TOTAL.ipynb`
- `preprocessing_1.py`

## Conclusion

La documentacion **NO ES CONSISTENTE** con los archivos evaluados. Deben resolverse los hallazgos criticos y volver a ejecutar este auditor antes de declarar el modelo listo para produccion.
