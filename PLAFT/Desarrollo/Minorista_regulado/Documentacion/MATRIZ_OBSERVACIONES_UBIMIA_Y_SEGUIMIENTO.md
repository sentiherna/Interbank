# Matriz de observaciones de Ubimia y seguimiento de remediación

**Modelo:** PLAFT Persona Jurídica Minorista — subsegmento BPE  
**Fecha de consolidación:** 13 de agosto de 2026  
**Documento final contrastado:** `Documentacion/Documento_Metodologico_PLAFT_PJ_Minorista_Formato_Modelo_v3.docx` (Versión 3.1, estado “Incorpora cambios metodológicos”, fecha indicada: julio 2026).  
**Propósito:** dejar trazabilidad de todas las observaciones formuladas por Ubimia, la respuesta incorporada en el documento final y el estado verificable con los artefactos disponibles en `Minorista_regulado`.

## 1. Criterio de estado

- **Cerrada:** la corrección está documentada y existe evidencia reproducible disponible.
- **Parcial:** existe una corrección documental o código preparado, pero falta evidencia ejecutada, consistencia entre artefactos o una parte de la recomendación.
- **Abierta:** la observación continúa contradicha por el documento, el código o los resultados disponibles.
- **No verificable:** se afirma una corrección, pero no existe el artefacto necesario para comprobarla.

La matriz consolida observaciones repetidas en los informes de Ubimia para evitar duplicarlas, pero conserva todas las recomendaciones materiales. Las conclusiones de estado se basan en los archivos disponibles a la fecha de consolidación; no equivalen por sí solas a una aprobación de Ubimia.

## 2. Resumen ejecutivo

El documento final incorporó mejoras visibles: descripción de métricas Top-K y Lift, explicación de `scale_pos_weight`, descripción del proceso de selección, mención del subsegmento BPE, aclaración textual del horizonte de 30 días, periodos documentales disjuntos, estrategias diferenciadas de imputación y referencias a scripts para validar independencia y calidad de preprocesamiento.

Sin embargo, no se puede declarar el cierre total de las observaciones. La implementación del target no demuestra la ventana de 30 días; el documento acepta clientes compartidos entre conjuntos; la calibración continúa asociada a validation; la selección alterna 36, 32 y 37 variables; la etapa 1 presenta una aritmética inconsistente; y siguen sin estar disponibles varias salidas y anexos que el documento cita como evidencia.

## 2.1 Contraste directo con el documento final

| Aspecto | Lo que declara el DOCX final | Conclusión al contrastar artefactos |
|---|---|---|
| Versión y estado | Versión 3.1; “Incorpora cambios metodológicos”. | Es el documento final entregado por el usuario, pero no contiene un control de cambios completo ni hash del modelo oficial. |
| Población | PJ Minorista, subsegmento BPE, con alertas y 0.5% de clientes sin alerta. | La definición está más clara, pero el valor 0.5% contradice otras cifras históricas y no está respaldado por sensibilidad ejecutada. |
| Horizonte | 30 días entre generación y clasificación de la alerta. | Está explicado en el texto, pero `model_target.sql` no implementa fechas ni la ventana. |
| Particiones | Train 202501–202507, Validation 202508–202509, Test 202510–202604. | Coincide con `03_validacion_clientes_unicos.py`, pero contradice `preprocessing_1.py`, que conserva Test desde 202508. |
| Independencia | Declara clientes compartidos y los considera aceptables a nivel cliente-mes. | No cierra la recomendación de Ubimia de separar clientes; además, las cifras no tienen CSV/HTML ejecutado disponible. |
| Variables finales | La arquitectura y dataset declaran 36; la selección y tabla por categoría declaran 32; compara con modelo de producción de 37. | El objeto oficial y el documento siguen sin estar alineados. |
| Preprocesamiento | Describe imputación diferenciada y reportes de missing/outliers. | `preprocessing_1.py` contiene reglas diferenciadas y `04_reportes_preprocesamiento.py` genera reportes, pero las salidas no están entregadas. |
| Calibración | Validation se usa para optimización y calibración; en otra sección se indica que no está en producción. | No demuestra calibración independiente; la observación de Ubimia permanece abierta. |
| Selección | Declara 187 iniciales, 305 después de transformaciones y una reducción hasta 32/36 variables. | La secuencia no es reproducible: la etapa 1 dice 187 - 80 = 245 y las cifras mezclan universos. |
| Performance | Incluye AUC, Gini, KS, precisión/recall Top-K y Lift. | Atiende la recomendación documental, pero no resuelve la conciliación del universo de alertas automáticas en 202512 y 202601. |

## 3. Observaciones originales de Ubimia

### 3.1 Revisión documental

| ID | Observación de Ubimia | Recomendación de Ubimia | Tratamiento en el nuevo documento/artefactos | Estado verificable |
|---|---|---|---|---|
| U01 | No existe un diccionario formal de variables. Los archivos disponibles no cubren de forma completa nombre, descripción, tipo, fuente y dominio. | Elaborar un diccionario formal con nombre, definición, tipo, fuente y valores permitidos. | Existe `diccionario_variables.xlsx`, `Variables_Finales_32_LightGBM.csv` y una lista de variables en `04_reportes_preprocesamiento.py`, pero no un diccionario formal completo del vector final con transformaciones, dominio, ventana y orden de producción. | **Parcial** |
| U02 | La población objetivo se define de forma ambigua y no siempre se indica la proporción de clientes sin alerta incorporada como clase negativa. | Estandarizar la definición de población objetivo en todo el documento. | Las revisiones posteriores describen el alcance BPE y la inclusión de clientes sin alerta, pero siguen existiendo valores contradictorios para la proporción sin alerta. | **Parcial** |
| U03 | La definición de la clase negativa no es consistente: se alternan “Falso Positivo” y clientes sin alerta. | Unificar la definición de la clase negativa. | `model_target.sql` construye `target_m` con la clasificación de monitoreo y no contiene una especificación completa de las categorías documentadas ni de los no clasificados. | **Abierta** |
| U04 | Se declara un horizonte de evaluación de 30 días sin explicar qué significa ni cómo se implementa. | Explicar el horizonte y demostrarlo en la extracción del target. | El documento posterior lo describe, pero la query disponible une por periodo (`cod_mes = periodo_alerta`) y no usa fecha de generación, fecha de clasificación ni una ventana de 30 días. | **Abierta** |
| U05 | No se documentan los tamaños de las muestras por etapa ni sus tasas de positivos. Además, hay contradicciones en los periodos de train, validation y test. | Reportar conteos y tasas exactas y corregir los periodos. | `03_validacion_clientes_unicos.py` define Train 202501–202507, Validation 202508–202509 y Test 202510–202604. `preprocessing_1.py` todavía usa Test desde 202508. Los conteos y tasas no están publicados como salida ejecutada en la carpeta. | **Abierta** |
| U06 | El análisis estadístico de variables categóricas no es adecuado cuando se aplican medidas de dispersión numéricas. | Complementar con tablas de frecuencia. | `04_reportes_preprocesamiento.py` incorpora reportes de calidad y estadísticos para las variables del modelo, pero no hay salidas ejecutadas disponibles que permitan verificar las tablas de frecuencia solicitadas. | **Parcial** |
| U07 | No se indica que la población corresponde al subsegmento BPE. | Incluir expresamente BPE en el documento metodológico. | Las revisiones posteriores y los scripts identifican el modelo como PLAFT PJ Minorista BPE. | **Cerrada documentalmente; validar en versión final** |
| U08 | No se detalla la creación y el procesamiento de las variables explicativas. | Documentar fuentes, transformaciones y procesamiento. | `model_variables.sql`, `preprocessing_1.py` y `04_reportes_preprocesamiento.py` aportan parte de la trazabilidad. Aún no existe un manifiesto único que relacione cada variable final con fuente, transformación, imputación y orden. | **Parcial** |
| U09 | No se documentan las variables eliminadas, los criterios por etapa ni la reducción de 305 a 36 variables. | Detallar selección, variables descartadas y justificar umbrales de nulos y correlación. | La v2 incorpora un proceso de selección por etapas y umbrales; los artefactos disponibles muestran otras cifras (por ejemplo, 187/34/31/29/32) y no permiten reproducir de forma inequívoca la ruta 305→36. | **Parcial** |
| U10 | La calibración se describe sin detallar técnica, muestra ni tamaño de clases. | Detallar técnica y muestra; aclarar el balanceo antes y después. | La v2 aclara que la calibración no está implementada en producción. No existen los scripts/notebooks de calibración citados ni una evaluación reproducible de una muestra independiente. | **Parcial** |
| U11 | Falta documentar aspectos del balanceo y del uso de `scale_pos_weight=494`, incluyendo por qué se usa tras el balanceo y por qué no se usan `lambda` y `alpha`. | Justificar `scale_pos_weight` y los criterios de regularización. | La v2 añade una explicación de `scale_pos_weight` y sus niveles. No se encontró evidencia completa de búsqueda/decisión para `lambda` y `alpha`, ni una tabla única de clases antes y después del balanceo. | **Parcial** |
| U12 | No se incluyen todas las métricas relevantes para un modelo de priorización: precisión Top-K, recall Top-K y Lift en train, validation y universo operativo. | Incorporar estas métricas y reportarlas también en alertas automáticas. | La v2 incorpora precisión, recall y Lift Top-K. Las métricas del universo operativo y su conciliación con la réplica siguen sin cierre, especialmente en 202512 y 202601. | **Parcial** |
| U13 | El análisis mensual de Gini tiene alta volatilidad por la baja prevalencia. | Complementar o priorizar una vista agregada, por ejemplo trimestral. | Se mantienen tablas mensuales y se añaden métricas Top-K, pero no se observa un resultado agregado que sustituya o contextualice suficientemente la apertura mensual. | **Parcial** |
| U14 | El documento metodológico no cumple estándares documentales de Interbank: identidad gráfica, índice, control de versiones, anexos y bibliografía. | Alinear el documento a los estándares corporativos. | Las revisiones posteriores siguen señalando ausencia de control de versiones, responsables, fecha de corte y anexos trazables. | **Abierta** |

### 3.2 Réplica y calidad de datos

| ID | Observación de Ubimia | Recomendación de Ubimia | Tratamiento en el nuevo documento/artefactos | Estado verificable |
|---|---|---|---|---|
| U15 | El tamaño de test no coincide entre la base de test y `01_resumen_estadistico.csv`; la diferencia corresponde al periodo 202512. | Usar el mismo periodo en todos los análisis o documentar explícitamente las diferencias. | Las revisiones posteriores siguen encontrando discrepancias de tamaño: se citan 1,509,824 frente a 1,338,493 y también otros conteos en notebooks. No existe una tabla congelada única con fuente y periodo. | **Abierta** |
| U16 | No se puede validar la unicidad de train porque no se entregaron los ID de clientes; además, un cliente puede repetirse en otro mes. | Entregar IDs y aclarar la unidad de independencia. | `03_validacion_clientes_unicos.py` fue incorporado y genera un CSV/HTML, pero depende de S3, no tiene resultados generados en la carpeta y acepta explícitamente que un cliente aparezca en varios conjuntos en meses distintos. Eso no cumple la recomendación original de exclusividad total por cliente. | **Abierta** |
| U17 | No se pudo replicar la construcción de la muestra por falta de insumos y filtros de origen. | Entregar consultas, insumos y salidas de cada etapa. | Existen consultas y notebooks de construcción, pero no un paquete congelado de entradas/salidas que permita replicar la muestra completa y reconciliar sus conteos. | **Parcial** |
| U18 | No se pudo replicar independientemente la variable respuesta. | Entregar los insumos y la lógica reproducible del target. | Existe `model_target.sql`, pero la lógica no demuestra el horizonte de 30 días ni todas las reglas de clasificación documentadas. | **Parcial** |
| U19 | No se pudo replicar la creación de variables explicativas. | Entregar las fuentes, consultas, transformaciones y salidas. | `model_variables.sql` y scripts de preprocesamiento mejoran la trazabilidad, aunque faltan salidas congeladas y el manifiesto completo del vector final. | **Parcial** |
| U20 | El objeto entregado no coincide con el modelo documentado: Ubimia replicó 29 variables frente a 36 documentadas. | Verificar que documento y objeto oficial correspondan al mismo modelo. | La carpeta actual incluye `model.tar.gz`, `Variables_Finales_32_LightGBM.csv`, `selected_columns.csv` y una ejecución nueva con otros hiperparámetros. No hay manifiesto ni hash que identifique el modelo oficial. | **Abierta** |
| U21 | En la réplica existen diferencias relevantes de AUC y Gini para el universo de alertas automáticas, principalmente 202512 y 202601. | Analizar y explicar las diferencias con una base congelada y el filtro productivo exacto. | La revisión posterior confirma que la diferencia sigue abierta. Se reconoce que diciembre tiene pocos positivos, pero no existe una conciliación reproducible que explique ambos meses. | **Abierta** |
| U22 | Las diferencias de importancia de variables entre modelo documentado y réplica son menores; no se emitió recomendación. | Sin acción obligatoria; mantener trazabilidad del modelo. | Los archivos actuales contienen rankings y nomenclaturas distintas, por lo que la comparación no queda completamente trazable aunque la observación original no fuera material. | **Parcial** |

### 3.3 Revisión metodológica

| ID | Observación de Ubimia | Recomendación de Ubimia | Tratamiento en el nuevo documento/artefactos | Estado verificable |
|---|---|---|---|---|
| U23 | La etiqueta depende del juicio del analista y la misma alerta podría ser clasificada de forma distinta por analistas diferentes. | Documentar la mitigación o avanzar a una definición más directa del fenómeno PLAFT. | Las revisiones describen la clasificación como proxy del criterio analista, pero no se encontró un control de concordancia, regla de desempate o análisis de variabilidad entre analistas. | **Abierta** |
| U24 | La proporción de clientes sin alerta de 0.5% no está justificada cuantitativamente. | Probar proporciones alternativas y seleccionar con un criterio de performance defendible. | El notebook usa `porcentaje_sin_alerta = 0.005`, mientras los documentos mencionan 0.05%, 0.5% y 15%. No se encontró un análisis de sensibilidad ejecutado que justifique la elección. | **Abierta** |
| U25 | No se demuestra que las ventanas de variables y target sean disjuntas; existe riesgo de leakage temporal. | Revisar fuentes y fechas para asegurar que las variables preceden al target. | La query disponible solo usa periodos mensuales y no impone fecha de corte/clasificación ni ventana de 30 días. | **Abierta** |
| U26 | No hay separación explícita de clientes entre train, validation y test. | Garantizar independencia entre conjuntos o justificar formalmente cualquier repetición. | El nuevo script define periodos sin solapamiento para validation/test, pero su metodología permite que el mismo cliente aparezca en distintos conjuntos en meses diferentes y no se entregó el resultado ejecutado. | **Abierta** |
| U27 | La calibración usa el mismo conjunto de validation, que no sería independiente. | Usar un conjunto independiente para calibrar. | La v2 declara que la calibración no está implementada en producción, pero tampoco aporta evidencia de una calibración independiente ejecutada. | **Abierta** |
| U28 | Las variables numéricas se imputan con cero, lo que es inadecuado para ratios, variaciones y antigüedad. | Aplicar estrategias según el significado de cada variable y cuantificar el missing antes y después. | `preprocessing_1.py` ahora contiene una función `imputar` diferenciada por tipo; `04_reportes_preprocesamiento.py` define reglas y genera tres reportes. No están disponibles las salidas ejecutadas y falta verificar que el pipeline oficial use exactamente esas reglas. | **Parcial** |
| U29 | El AUC no es suficiente para decidir el poder predictivo de un modelo de priorización. | Incluir precisión y recall Top-K en train/validation y reportar métricas en alertas automáticas. | La v2 incorpora Top-K y Lift, atendiendo la parte documental. La evidencia de train/validation y del universo productivo no está unificada con el modelo oficial. | **Parcial** |
| U30 | `scale_pos_weight=494` requiere justificación porque la muestra ya fue balanceada; además faltan criterios sobre regularización. | Documentar la decisión y los parámetros evaluados. | La v2 incorpora una explicación del hiperparámetro, pero los artefactos no presentan una matriz completa de experimentos ni una decisión trazable sobre `lambda` y `alpha`. | **Parcial** |
| U31 | Gini y KS no bastan para este caso de uso. | Complementar con Lift y métricas de priorización. | La v2 incluye Lift, precisión y recall Top-K. | **Cerrada documentalmente; falta validar el universo operativo** |

## 4. Hallazgos nuevos de la revisión posterior

Estos puntos no son observaciones textuales nuevas de Ubimia; son inconsistencias detectadas al verificar el documento posterior contra los artefactos disponibles. Se incluyen porque deben acompañar la respuesta y no quedar fuera del seguimiento.

| ID | Nuevo hallazgo | Evidencia | Tratamiento requerido | Estado |
|---|---|---|---|---|
| N01 | Inconsistencia de versión: archivo/documento v2 y encabezado interno 3.1. | Revisión v2 vs artefactos. | Definir una convención única y actualizar portada, encabezados y referencias. | **Abierto** |
| N02 | Hay tres conjuntos de hiperparámetros: documento, `hpo.txt` y ejecución del 03/08/2026. | `hpo.txt` reporta eta 0.01346 y 780 rounds; `metricas_train+hpo.txt` reporta eta 0.03402 y 396 rounds; la v2 documenta otros valores. | Congelar el modelo oficial, actualizar parámetros, métricas y hash. | **Crítico abierto** |
| N03 | Las métricas AUC del documento no coinciden con la ejecución del 03/08/2026. | Documento: AUC train 0.9904/validation 0.9585; log nuevo: aproximadamente 0.9836/0.9738. | Identificar qué ejecución es oficial y rehacer la tabla de resultados. | **Crítico abierto** |
| N04 | La separación temporal sigue siendo contradictoria. | `preprocessing_1.py` define test desde 202508; `03_validacion_clientes_unicos.py` define test desde 202510. | Regenerar todas las bases con una sola partición disjunta y actualizar el documento. | **Crítico abierto** |
| N05 | La ventana de 30 días continúa sin implementación. | `model_target.sql` no contiene fechas de generación/clasificación. | Corregir query, conservar salidas y reevaluar el modelo. | **Crítico abierto** |
| N06 | El script oficial anterior de preprocesamiento fue inconsistente o no estuvo disponible; ahora hay scripts nuevos con reglas diferenciadas, pero sin salidas. | Diferencia entre revisiones previas y `04_reportes_preprocesamiento.py`. | Ejecutar reportes, versionar salidas y demostrar que el pipeline de entrenamiento/inferencia usa las mismas reglas. | **Abierto** |
| N07 | La proporción sin alerta aparece como 0.05%, 0.5% y 15%. | Documento, notebook y revisión v2. | Elegir un único valor sustentado por sensibilidad y actualizar todas las secciones. | **Abierto** |
| N08 | Las importancias de variables no son comparables entre documentos y CSV. | Valores SHAP raw, porcentajes de documento y nueva tabla del notebook difieren; también cambian los nombres. | Definir método de normalización, usar nomenclatura dataset y publicar la tabla fuente. | **Abierto** |
| N09 | El conteo de Comercio Exterior es incorrecto. | Se declaran 4 variables, pero se listan 5. | Corregir el conteo y el porcentaje. | **Abierto** |
| N10 | Los tamaños de train, validation y test varían entre documento, notebooks y archivos. | Revisiones v1/v2 y salidas citadas. | Publicar una tabla única con conteo, periodo, tasa target y hash de entrada. | **Abierto** |
| N11 | Los números de clientes compartidos se declaran sin el CSV/HTML generado. | Se citan cifras exactas, pero no están los reportes de salida en la carpeta. | Ejecutar el script con datos congelados y adjuntar resultados. | **Abierto** |
| N12 | El documento afirma ~457 rounds, mientras los artefactos indican 780 y 396. | Documento, `hpo.txt` y `metricas_train+hpo.txt`. | Sustituir por el valor del modelo oficial. | **Abierto** |
| N13 | La tabla SHAP contiene valores y porcentajes que no coinciden con `importancia_variables.csv`. | Revisión v2 vs artefactos. | Recalcular y documentar una única definición de importancia. | **Abierto** |
| N14 | El flujo de selección presenta una aritmética imposible y mezcla universos 187 y 305. | Revisión v2 vs artefactos. | Rehacer el diagrama 305→vector final con salidas por etapa. | **Abierto** |
| N15 | La calibración se declara no productiva, pero se presentan afirmaciones que pueden interpretarse como análisis ejecutado. | Sección de calibración y ausencia de scripts citados. | Declarar “no aplicada/no evaluada” o entregar evidencia reproducible. | **Abierto** |
| N16 | La conclusión “listo para producción” no es compatible con C1–C6 y otros pendientes. | Revisión posterior. | Retirar la conclusión hasta cerrar trazabilidad, particiones, target y modelo oficial. | **Crítico abierto** |
| N17 | Los nombres de notebooks y anexos citados no coinciden con los archivos reales. | Revisión v1/v2. | Corregir referencias para que coincidan exactamente con la carpeta entregada. | **Abierto** |
| N18 | Las métricas mensuales de test no tienen todos sus archivos fuente disponibles. | Revisión v2. | Adjuntar salidas reproducibles o retirar las cifras no sustentadas. | **Abierto** |
| N19 | Se citan anexos inexistentes o no entregados: validación temporal, sensibilidad, resumen estadístico, HPO, calibración, SHAP y matriz de trazabilidad. | Revisión v1/v2 y listado actual de archivos. | Crear/adicionar anexos o reemplazar las referencias por evidencia existente. | **Abierto** |
| N20 | No existe control de versiones completo con responsable, aprobador, fecha de corte y versión/hash del artefacto. | Revisión v2. | Añadir tabla de control de cambios y manifiesto del modelo. | **Abierto** |

## 5. Estado de los avances incorporados

| Avance | Evidencia actual | Limitación que impide marcarlo como cierre total |
|---|---|---|
| Lista de 32 variables | `Train/Variables_Finales_32_LightGBM.csv`, `Train/04_reportes_preprocesamiento.py` | La réplica de Ubimia reportó 29 y el documento histórico reportó 36/37; falta manifiesto del objeto oficial. |
| Imputación diferenciada | `Train/preprocessing_1.py`, función `imputar`; `Train/04_reportes_preprocesamiento.py` | Faltan reportes ejecutados y prueba de que entrenamiento e inferencia usan el mismo pipeline. |
| Validación de independencia | `Train/03_validacion_clientes_unicos.py` | No hay salida ejecutada; la lógica acepta repetición de clientes en conjuntos distintos. |
| Métricas Top-K y Lift | Documento metodológico v2 y revisión v2 | Falta la tabla consolidada del universo de alertas automáticas y del modelo oficial. |
| Explicación de `scale_pos_weight` | Documento metodológico v2 | Falta evidencia completa de clases antes/después y de la decisión sobre regularización. |
| Proceso de selección por etapas | Documento metodológico v2 | Las cifras y universos no coinciden con los notebooks y CSV disponibles. |
| Identificación del subsegmento BPE | Documento y scripts de validación | Debe mantenerse consistente en todas las secciones y anexos. |

## 6. Paquete mínimo para cerrar las observaciones

1. Definir y congelar el modelo oficial, con versión, hash SHA-256, lista ordenada de variables, tipos, transformaciones e hiperparámetros.
2. Corregir `model_target.sql` para demostrar precedencia temporal y ventana de 30 días; guardar la salida congelada.
3. Regenerar train, validation y test con periodos disjuntos y publicar conteos, tasas target y reglas de inclusión/exclusión.
4. Resolver la política de independencia: exclusividad total por cliente o justificación cuantitativa de la unidad cliente-mes, alineada con Ubimia.
5. Ejecutar `03_validacion_clientes_unicos.py` y adjuntar el CSV/HTML resultante.
6. Ejecutar `04_reportes_preprocesamiento.py` y adjuntar los tres CSV; verificar que el pipeline oficial aplique las mismas reglas.
7. Entregar diccionario formal de las variables finales y trazabilidad desde las variables fuente.
8. Ejecutar la sensibilidad de la proporción sin alerta y documentar la decisión cuantitativa.
9. Conciliar AUC/Gini del universo de alertas automáticas para 202512 y 202601 con una base y filtro productivo congelados.
10. Alinear el documento con los nombres reales de archivos, anexos, control de versiones, fecha de corte, responsables y aprobaciones.
11. Retirar la declaración “listo para producción” hasta cerrar los puntos críticos y contar con una revisión final independiente.

## 7. Fuentes consultadas

- `Documentacion/Ubimia - Interbank - Réplica - Informe de validación modelo PLAFT (v1.0).seguro.pdf`
- `Documentacion/Ubimia - Interbank - Réplica - Resultados validación modelo PLAFT (v2.0).pdf`
- `Documentacion/REVISION_PREENVIO_UBIMIA_v1.md`
- `Train/REVISION_INTEGRAL_DOCUMENTO_PLAFT_v1.md`
- `Train/REVISION_DOCUMENTO_v2_vs_ARTEFACTOS.md`
- `Train/03_validacion_clientes_unicos.py`
- `Train/04_reportes_preprocesamiento.py`
- `Train/preprocessing_1.py`
- `Train/hpo.txt`
- `Train/metricas_train+hpo.txt`
- `Train/Variables_Finales_32_LightGBM.csv`
- `Train/selected_columns.csv`
- `Querys/model_target.sql`
- `Querys/model_variables.sql`
