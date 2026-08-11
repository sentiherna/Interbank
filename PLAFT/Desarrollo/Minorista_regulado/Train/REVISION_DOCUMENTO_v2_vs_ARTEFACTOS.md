# Revisión Integral — DOCUMENTO_METODOLOGICO_PLAFT_PJ_MINORISTA_v2.txt
**Fecha de revisión:** 3 de agosto de 2026  
**Revisor:** Análisis automatizado contra todos los artefactos disponibles en `Minorista_regulado/`  
**Artefactos contrastados:**
- `Train/hpo.txt` (mejor configuración HPO previa)
- `Train/metricas_train+hpo.txt` (última ejecución de entrenamiento — 3 ago 2026)
- `Train/importancia_variables.csv` (importancias SHAP del modelo)
- `Bases/Querys/model_target.sql` y `model_variables.sql`
- `02.bivariados+EDA_train+seleccion_variables.ipynb`
- `REVISION_INTEGRAL_DOCUMENTO_PLAFT_v1.md` (revisión anterior)
- `REVISION_PREENVIO_UBIMIA_v1.md` (observaciones auditoría Ubimia)

---

## DICTAMEN GLOBAL

> **La v2 es una mejora material respecto a v3.1 anterior, pero NO resuelve todas las observaciones críticas de Ubimia y contiene inconsistencias nuevas generadas por la última ejecución del modelo (3 ago 2026) que aún no se incorporaron al texto.**

La documentación puede avanzar hacia una versión enviable si se corrigen los puntos marcados como `🔴 CRÍTICO` y `🟠 ALTO` listados a continuación.

---

## TABLA DE HALLAZGOS

### 🔴 CRÍTICOS — Impiden cierre de observaciones de auditoría

| # | Sección | Qué dice el documento | Qué dice el artefacto | Acción requerida |
|---|---|---|---|---|
| C1 | Portada / Control de versiones | Nombre del archivo: `v2.txt`; Encabezado interno: "Versión: **3.1**" | — | Unificar. Si es la v2 del proceso de revisión, el encabezado debe decir "Versión 2.0" o definir una convención única. |
| C2 | §11.4 HPO — Hiperparámetros finales | eta=**0.0708**, subsample=**0.8163**, colsample=**0.8449**, gamma=**5.3742**, num_round=**457** | `hpo.txt`: eta=0.01346, subsample=0.989, colsample=0.889, gamma=6.320, num_round=**780**<br>`metricas_train+hpo.txt` (3 ago 2026): eta=0.03402, subsample=0.680, colsample=0.709, gamma=6.607, num_round=**396** | Los valores del documento NO coinciden con ningún artefacto disponible. Hay **tres conjuntos distintos de hiperparámetros**. Documentar exactamente qué ejecución corresponde al modelo en producción e incluir su hash. |
| C3 | §13.2 Métricas AUC | AUC_train=**0.9904**, AUC_val=**0.9585** | `metricas_train+hpo.txt` (3 ago 2026): AUC_train≈**0.9836**, AUC_val≈**0.9738** en round 395 | El modelo fue re-entrenado el 3 de agosto de 2026 y sus métricas son distintas. O se actualiza el documento con las métricas reales de este entrenamiento, o se especifica a qué versión de ejecución corresponden cada cifra. |
| C4 | §6.1 / §6.3 Integridad temporal | "NO EXISTE TRASLAPE entre períodos de Train, Validation y Test" | `preprocessing_1.py` (versión revisada anteriormente): validación=202508–202509; test=**202508**–202604 → 202508 y 202509 en ambos conjuntos | Esta es la observación de Ubimia que sigue sin cerrarse. El documento declara su corrección pero el código y las tablas de composición (§5.7) siguen mostrando 202508 en Validación y el periodo test declarado en §3.3 empieza en octubre. **La partición no es disjunta** o hay una inconsistencia entre el código y el documento. |
| C5 | §4.3 Horizonte 30 días | "El analista debe clasificar la alerta dentro de [t, t+30 días]" | `Bases/Querys/model_target.sql`: une por `a.cod_mes = b.periodo_alerta` sin ningún campo de fecha de generación ni de clasificación | La ventana de 30 días no está implementada en ninguna query disponible. No se puede demostrar este horizonte. |
| C6 | §8.2 Imputación diferenciada | Describe 4 estrategias distintas por tipo de variable | No existe `preprocessing_1.py` en la carpeta; la revisión anterior confirmaba `df.fillna(0)` global. El script fue eliminado o renombrado y no está disponible. | Sin evidencia del código de preprocesamiento no se puede verificar ni la imputación diferenciada ni ninguna otra transformación. Restaurar o crear el script con la lógica declarada. |

---

### 🟠 ALTOS — Observaciones de auditoría pendientes o inconsistencias materiales

| # | Sección | Inconsistencia | Detalle |
|---|---|---|---|
| A1 | §5.1 vs §5.5 | Proporción sin alerta: **0.05%** (§5.1) vs **15%** (§5.5) | Contradicción interna. En el notebook `01.genera_base_train.ipynb` se usó `porcentaje_sin_alerta = 0.005` (0.5%). Ninguno de los tres valores coincide entre sí. |
| A2 | §9.5 Tabla 3 — Importancias | Documento: cod_ubigeo_cd=4.2%, cnt_trx_cargostot_3m=**15.8%** | `importancia_variables.csv`: cnt_trx_cargostot_3m=**65.6%** (valor raw SHAP), cod_ubigeo_cd=3.8%. La celda nueva del notebook declara cnt_trx_cargostot_3m=**9.77%**. Son **tres conjuntos de importancias distintos** sin aclaración de método/normalización. |
| A3 | §9.5 Tabla 3 — Nombres de variables | Usa nombres de usuario: `pasivo_vs_ingresos`, `ratio_abonos_1m_vs_6m`, `ingresos_vs_facturacion`, `ratio_cargos_1m_vs_6m` | `importancia_variables.csv` usa nombres de dataset: `rat_pastot_x_ingtot_6m`, `rat_abonos_1m_vs_6m`, `rat_ing_tot_x_factura_6m`, `ratio_cargos_1m_vs_6m`. La mezcla de nomenclaturas en la tabla del modelo es ambigua para auditoría. |
| A4 | §7.3 Categoría Comercio Exterior | Dice "4 variables (12.5%)" pero lista 5: mto_del_ext_12m, mto_al_ext_12m, ratio_egresos_exterior, ratio_ingresos_exterior, cnt_trx_sinenv_alext_12m | Error de conteo. Son 5 variables = 15.6% si el total es 32. |
| A5 | §5.4 Tamaños de muestra | Train=**174.523**, Validation=**324.035**, Test=**1.184.738** | La revisión anterior encontró en los notebooks: train≈175.400, validation=324.253, test=1.509.824. Los valores de test difieren en ~325K registros. |
| A6 | §6.4 Clientes compartidos | Declara valores exactos: "Train ∩ Validation: **3.421** clientes", "Validation ∩ Test: **1.234**", etc. | No existe el script `03_validacion_clientes_unicos.py` ni el reporte `cliente_distribucion_por_conjunto.csv` que generarían estos números. Son cifras sin evidencia disponible. |
| A7 | §10.7 Iteraciones óptimas | "~**457 rounds**" | `hpo.txt`: num_round=**780**. `metricas_train+hpo.txt`: num_round=**396**. Ninguno dice 457. |
| A8 | §14.2 Tabla 9 SHAP vs LightGBM | Presenta importancias SHAP (columna separada) | `importancia_variables.csv` tiene columna "Valor Absoluto SHAP" con valores negativos (ej: cnt_trx_cargostot_3m = -0.514). Los valores SHAP del CSV no coinciden con los porcentajes de la tabla del documento. |
| A9 | §9.2 Etapas de eliminación | Declara: 187 iniciales → 245 → 187 → 175 → 128 → **32** | El flujo es internamente contradictorio: Etapa 1 dice "eliminamos 80 de 187 → quedan 245", pero 187 - 80 = 107, no 245. También: "305 variables únicas después de transformaciones" (nota en §9.1) contradice "187 iniciales". |
| A10 | §12 Calibración | "Calibración NO se implementa en producción v3.1" | Sin el script `3.calibracion_modelo.py` ni el notebook `07_calibracion_y_validacion.ipynb`, ni siquiera puede decirse que se analizó teóricamente. Eliminar la sección completa o declarar "no evaluada". |
| A11 | §15 Conclusiones — Estado final | "✓ Listo para implementación en producción" | Persisten C1–C6 sin resolver. Esta afirmación no puede sostenerse ante auditoría. |

---

### 🟡 MEDIOS — Mejoras editoriales / trazabilidad

| # | Sección | Observación |
|---|---|---|
| M1 | §1.5 Referencias | Los notebooks se llaman `0.limpieza_datos.ipynb`, `Train/1.PRE PROCESSING.ipynb`, etc. El documento los llama `00.limpieza_datos.ipynb`, `11.PRE PROCESSING.ipynb`, `13.VALIDACION_TOTAL.ipynb`. Los nombres deben coincidir exactamente. |
| M2 | §9.5 Tabla 3 | La columna "Importancia LightGBM" suma exactamente 100% pero tiene muchas cifras redondas (15.8%, 10.8%, etc.) que no corresponden a ningún artefacto. Actualizar con los valores reales del `importancia_variables.csv` (normalizado). |
| M3 | §13.6 Tabla 7 Test | Las métricas por mes (AUC, Gini, KS) para el periodo oct2025–abr2026 no tienen fuente disponible que las respalde. El notebook `Train/3.VALIDACION_TOTAL.ipynb` (según revisión anterior) calcula Gini mensual, pero sus valores específicos no están en ningún CSV de salida disponible. |
| M4 | §15 Cambios vs v3.0 | Dice "actualización de rutas de archivo (todos en Minorista_regulado/)" pero las referencias a `03_validacion_clientes_unicos.py`, `sagemaker_hpo_results.csv` y otras siguen siendo archivos inexistentes. |
| M5 | Control de versiones | El documento no tiene historial de cambios ni tabla de control (quién aprobó, fecha de corte de datos, versión del artefacto). Requerimiento estándar para auditoría. |

---

## ESTADO POR OBSERVACIÓN DE UBIMIA

Basado en `REVISION_PREENVIO_UBIMIA_v1.md` y `REVISION_INTEGRAL_DOCUMENTO_PLAFT_v1.md`:

| Observación Ubimia | Estado en v2 | Evidencia |
|---|---|---|
| Ventana de target de 30 días no demostrada | 🔴 **SIN RESOLVER** | `model_target.sql` sin fechas de generación/clasificación |
| Validación y test se solapan temporalmente | 🔴 **SIN RESOLVER** | §5.7 aún muestra 202508 en Validation; §6.1 dice test desde oct pero §5.7 muestra 202508 en partición posterior |
| Tratamiento de faltantes no es diferenciado | 🟡 **No verificable** | Script de preprocesamiento no disponible en carpeta |
| Variables finales inconsistentes (36/37/32) | 🟢 **MEJORADO** | v2 declara consistentemente 32 en sección 9 y conclusiones, aunque tablas internas aún tienen mezcla de nombres |
| Parámetros HPO no coinciden | 🔴 **EMPEORÓ** | Ahora hay 3 conjuntos distintos: documento, `hpo.txt`, y nueva ejecución del 3/8/2026 |
| Tamaños de muestra inconsistentes | 🟡 **PARCIALMENTE MEJORADO** | Sección 5.4 más detallada pero valores aún difieren de notebooks |
| Clientes compartidos entre conjuntos | 🟡 **Declarado pero sin evidencia** | Sección 6.4 presenta cifras exactas pero sin los scripts/reportes que las generan |
| Calibración sin evidencia | 🟢 **MEJORADO** | Se aclara explícitamente que NO está implementada |
| Métricas operativas (Precision/Recall TopK) ausentes | 🟢 **RESUELTO** | Sección 13.3 añade Precisión TopK, Recall TopK y Lift de forma detallada |
| Anexos no disponibles | 🔴 **SIN RESOLVER** | `03_validacion_clientes_unicos.py`, `sagemaker_hpo_results.csv`, `Variables_Finales_32_LightGBM.csv`, `01_resumen_estadistico.csv` y otros siguen sin existir |

---

## HALLAZGO NUEVO CRÍTICO — Ejecución del 3 de agosto de 2026

El archivo `metricas_train+hpo.txt` contiene logs de entrenamiento del **3 de agosto de 2026** con hiperparámetros distintos a los declarados en el documento:

```
eta             = 0.03402   (documento declara 0.0708)
subsample       = 0.6803    (documento declara 0.8163)
colsample_bytree= 0.7086    (documento declara 0.8449)
gamma           = 6.607     (documento declara 5.3742)
num_round       = 396       (documento declara 457)
AUC_train       ≈ 0.9836    (documento declara 0.9904)
AUC_val         ≈ 0.9738    (documento declara 0.9585)
```

**Esto implica que el modelo fue re-entrenado DESPUÉS de escribir el documento v2.** El documento describe un modelo diferente al que está actualmente en la carpeta. Deben tomarse estas decisiones:
1. ¿El modelo del 3/8/2026 es el modelo oficial? → Actualizar todas las métricas e hiperparámetros del documento.
2. ¿El modelo anterior (hpo.txt) es el oficial? → Documentar por qué se ejecutó un nuevo entrenamiento y si reemplaza al anterior.
3. ¿Ambas ejecuciones son experimentos? → Definir cuál es el modelo congelado para producción y documentarlo con hash.

---

## LO QUE SÍ ESTÁ BIEN EN v2 (mejoras reales vs versiones anteriores)

| Sección | Mejora |
|---|---|
| §9 | Proceso de selección de 5 etapas bien documentado y justificado |
| §9.4 | Eliminación explícita de 4 variables con importancia < 0.1% — responde observación de Ubimia |
| §10.4 | Explicación de `scale_pos_weight` con 3 niveles — responde observación de Ubimia |
| §12 | Se declara explícitamente que calibración NO está en producción |
| §13.3 | Métricas operativas (Precisión/Recall/Lift Top-K) bien desarrolladas |
| §13.7 | Comparación de algoritmos incluida |
| §14 | Explicación SHAP con ejemplo de caso individual — buena práctica |
| §6.1 | Corrección explícita de períodos train/test respecto a versión anterior |

---

## ACCIONES PRIORITARIAS PARA CIERRE

**Antes de enviar a Ubimia:**

1. 🔴 Definir y congelar el modelo oficial: ¿cuál ejecución (hpo.txt vs metricas_train+hpo.txt)? Generar hash SHA-256 del artefacto.
2. 🔴 Actualizar §11.4 con los hiperparámetros reales del modelo congelado.
3. 🔴 Actualizar §13.2 con las métricas AUC/Gini/KS reales del modelo congelado.
4. 🔴 Corregir o demostrar la separación train/validation/test — las tablas §5.7 y §3.3 son contradictorias entre sí.
5. 🔴 Unificar número de versión en portada y encabezado del archivo.
6. 🟠 Unificar proporción sin alerta (0.05%, 0.5% o 15%) con un solo valor sustentado.
7. 🟠 Reemplazar la Tabla 3 de §9.5 con los valores reales de `importancia_variables.csv` normalizado y usar nombres de dataset consistentes.
8. 🟠 Corregir error de conteo en §7.3 (5 variables de Comercio Exterior, no 4).
9. 🟠 Retirar afirmaciones de evidencia que no existen (clientes únicos §6.4, SHAP HTML, etc.) o crear los artefactos correspondientes.
10. 🟠 Añadir tabla de control de versiones con responsables y fecha de corte de datos.
