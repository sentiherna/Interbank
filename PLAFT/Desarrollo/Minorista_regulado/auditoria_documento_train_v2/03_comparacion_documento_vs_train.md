# Comparacion documento vs Train

## Dictamen ejecutivo

**Dictamen: PARCIAL, con hallazgos criticos abiertos.** El paquete contiene evidencia de preprocesamiento diferenciado, seleccion/EDA, HPO XGBoost, validacion por mes/quintiles/Top-K y SHAP. Sin embargo, no es posible afirmar consistencia documental completa: `preprocessing_1.py` solapa Validation y Test, mientras `03_validacion_clientes_unicos.py` declara periodos disjuntos; el horizonte de 30 dias no esta implementado de forma demostrable; y varias cifras, artefactos de salida y resultados oficiales no estan vinculados a una ejecucion congelada.

La auditoria automatica contra GitHub Models no se pudo ejecutar porque el endpoint devolvio HTTP 410 (`github_models_retirement_brownout`). Este informe es una auditoria local basada en texto extraible del PDF y codigo/estructura de Train inspeccionados directamente.

## Matriz de trazabilidad

| ID | Pagina/seccion | Requisito declarado | Estado | Evidencia en Train | Hallazgo/accion |
|---|---|---|---|---|---|
| R-001 | p. 5, 21, 30, 53 | Vector final de variables consistente | PARCIAL | `3.VALIDACION_TOTAL.ipynb`, celdas 17, 23, 65-67; `preprocessing_1.py`, lineas 269-276 | Existe seleccion de columnas, pero falta un manifiesto unico que ate lista, version y modelo oficial.
| R-002 | p. 15 | No hay traslape temporal | NO CUMPLE | `preprocessing_1.py`, lineas 42-45; `03_validacion_clientes_unicos.py`, lineas 35-38 | El primer archivo incluye 202508-202509 en Val y Test; corregir y ejecutar prueba.
| R-003 | Seccion target | Horizonte de clasificacion de 30 dias | NO EVIDENCIADO | No hay referencia verificable a fecha de generacion/clasificacion en los artefactos citados | Implementar o aportar query con ventana y fechas.
| R-004 | Seccion datos | Fuente/unidad declaradas | PARCIAL | `preprocessing_1.py`, lineas 52-64; `03_validacion_clientes_unicos.py`, lineas 42, 80, 113-117 | Se observan parquet, `cod_mes`, `cod_cli`; falta resultado congelado y contrato de datos.
| R-005 | Seccion muestreo | Proporcion y tamanos declarados | PARCIAL | `01.genera_base_train.ipynb`, celda 1; `preprocessing_1.py`, lineas 359-376 | Hay logica de muestreo/periodos, pero no todos los conteos oficiales persistidos.
| R-006 | Seccion preprocesamiento | Imputacion diferenciada | CUMPLE | `preprocessing_1.py`, lineas 122-156; `04_reportes_preprocesamiento.py`, lineas 256-263 | La logica esta explicitamente diferenciada; falta validar que coincide exactamente con el texto del PDF.
| R-007 | Seccion variables | Seleccion segun metodologia | PARCIAL | `02.bivariados+EDA_train+seleccion_variables.ipynb`, funciones de correlacion; `preprocessing_1.py`, lineas 269-276 | Hay flujo tecnico, pero no se demuestra univocamente el vector/version declarado.
| R-008 | p. 27-29, 31-33 | Algoritmos LightGBM/XGBoost | PARCIAL | `02.bivariados+EDA_train+seleccion_variables.ipynb`; `2.HPO.ipynb`; `3.VALIDACION_TOTAL.ipynb`, celdas 17, 23 | Ambos aparecen, pero falta separar formalmente modelo exploratorio y oficial.
| R-009 | Seccion HPO | Hiperparametros finales y rounds | PARCIAL | `2.HPO.ipynb`; `Train/hpo.txt`; `Train/metricas_train+hpo.txt` | Hay evidencia de HPO, no una ejecucion oficial identificada por hash/fecha.
| R-010 | p. 27-29, 34, 37-40, 42-44, 46-47 | Metricas declaradas | PARCIAL | `3.VALIDACION_TOTAL.ipynb`, celdas 19-20, 28-63 | Se calculan Gini, quintiles, Top-K y umbrales; faltan salidas persistidas que demuestren cada cifra del PDF.
| R-011 | Seccion validacion | Validacion temporal/cliente/mes | PARCIAL | `03_validacion_clientes_unicos.py`, lineas 90-143; `3.VALIDACION_TOTAL.ipynb`, celdas 28-63 | Logica existe, pero los resultados y la contradiccion de periodos impiden cierre.
| R-012 | p. 30-31, 47-48, 50-51, 53 | SHAP/importancias coincidentes | PARCIAL | `3.VALIDACION_TOTAL.ipynb`, celdas 65-67; `04_reportes_preprocesamiento.py`, lineas 293-305 | Calculo/exportacion evidenciados; no se prueba que CSV y tabla del PDF sean la misma ejecucion.
| R-013 | Seccion calibracion | Estado de calibracion | NO EVIDENCIADO | No se encontro script/notebook de calibracion dentro de Train | Declarar explicitamente no implementado o aportar artefacto.
| R-014 | Implementacion/gobierno | Integracion, monitoreo y aprobaciones | NO EVIDENCIADO | Artefactos revisados son de entrenamiento/validacion; no hay jobs/reportes de gobierno | Separar diseño documental de evidencia de implementacion.
| R-015 | p. 54 | Conclusiones de validacion/produccion | NO CUMPLE | Contradiccion de periodos en `preprocessing_1.py`, lineas 42-45; ausencia de resultados congelados | No sostener “listo para produccion” hasta resolver R-002, R-003, R-009-R-014.

## Hallazgos criticos

1. **Particiones contradictorias:** `preprocessing_1.py` asigna 202508 y 202509 simultaneamente a Validation y Test (lineas 42-45). El script `03_validacion_clientes_unicos.py` declara Test desde 202510 (lineas 35-38). Debe existir una sola fuente de verdad y una ejecucion de la prueba.
2. **Horizonte de 30 dias no evidenciado:** no se localizo en los artefactos evaluados una fecha de generacion y otra de clasificacion que implemente la ventana.
3. **Modelo oficial no congelado:** HPO, entrenamiento, metricas y SHAP no estan ligados en Train a un hash, semilla, fecha, version de dependencias y salida oficial unica.
4. **Resultados no persistidos completamente:** los notebooks calculan resultados, pero varias tablas/cifras del documento no tienen CSV/HTML ejecutado asociado en Train.

## Evidencia faltante

- Query o script que implemente y pruebe la ventana target de 30 dias.
- Correccion y ejecucion de la particion temporal disjunta.
- Registro de ejecucion oficial: fecha, semilla, dependencias, hiperparametros, hash del modelo y datasets.
- Salidas persistidas de conteos por conjunto, metricas por mes, Top-K, SHAP y validacion de clientes.
- Artefacto de calibracion o declaracion formal de no implementacion.
- Evidencia de integracion, monitoreo, aprobacion y gobierno si el documento los presenta como existentes.

## Inventario de referencias

| Archivo revisado | IDs de requisitos que evidencia |
|---|---|
| `0.limpieza_datos.ipynb` | R-004, R-006 |
| `01.genera_base_train.ipynb` | R-005 |
| `02.bivariados+EDA_train+seleccion_variables.ipynb` | R-007, R-008 |
| `03.bivariados+EDA_test.ipynb` | R-010, R-011 |
| `03_validacion_clientes_unicos.py` | R-002, R-004, R-005, R-011 |
| `04_reportes_preprocesamiento.py` | R-004, R-006, R-012 |
| `1.PRE PROCESSING.ipynb` | R-004, R-006 |
| `2.HPO.ipynb` | R-008, R-009 |
| `3.VALIDACION_TOTAL.ipynb` | R-001, R-008, R-010, R-011, R-012 |
| `preprocessing_1.py` | R-001, R-002, R-004, R-006, R-007 |

**Alcance:** se inventariaron recursivamente todos los `.ipynb` y `.py` bajo `Train`; los archivos auxiliares no pertenecen al inventario formal de artefactos solicitado, aunque se consideraron cuando eran referenciados por el codigo.