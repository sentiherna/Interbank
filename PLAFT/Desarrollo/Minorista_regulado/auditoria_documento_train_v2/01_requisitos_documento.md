# Requisitos verificables del documento

**Documento:** `Documentacion/Documento_Metodologico_PLAFT_PJ_Minorista_Formato_Modelo_v2.pdf` (55 paginas; texto extraible verificado).

| ID | Pagina/seccion | Requisito o afirmacion | Evidencia tecnica requerida |
|---|---|---|---|
| R-001 | p. 5, 21, 30, 53 | El modelo usa un vector final de variables declarado en el documento. | Lista de columnas y artefacto de seleccion/version.
| R-002 | p. 15 | Train, validacion y test no se solapan temporalmente. | Periodos implementados y prueba de disjuncion.
| R-003 | Seccion target | El target y su ventana de clasificacion son los declarados. | Query/codigo con fecha de generacion y horizonte.
| R-004 | Seccion datos | La fuente y unidad de analisis son las declaradas. | Lectura de datos y columnas identificadoras.
| R-005 | Seccion muestreo | La proporcion de casos sin alerta y tamanos muestrales son los declarados. | Codigo y conteos reproducibles.
| R-006 | Seccion preprocesamiento | Los faltantes reciben tratamiento diferenciado. | Funcion de imputacion y parametros.
| R-007 | Seccion variables | La seleccion de variables sigue los filtros y conteos declarados. | EDA, filtros, correlacion y archivo final.
| R-008 | p. 27-29, 31-33 | Se usan LightGBM/XGBoost conforme al desarrollo documentado. | Entrenamiento, modelo y parametros.
| R-009 | Seccion HPO | Los hiperparametros finales y numero de iteraciones son los declarados. | Log/CSV de HPO y ejecucion oficial.
| R-010 | p. 27-29, 34, 37-40, 42-44, 46-47 | Las metricas AUC/Gini/KS y operativas coinciden con resultados. | Salidas persistidas y calculo reproducible.
| R-011 | Seccion validacion | La validacion temporal, por cliente y por mes es demostrable. | Scripts, conteos y reportes.
| R-012 | p. 30-31, 47-48, 50-51, 53 | La interpretabilidad SHAP/importancias coincide con artefactos. | CSV/HTML y formula de normalizacion.
| R-013 | Seccion calibracion | El estado de calibracion declarado esta respaldado por artefactos. | Script/notebook y resultados, o declaracion de no implementacion.
| R-014 | Secciones implementacion/gobierno | Integracion, monitoreo, aprobaciones y gobierno estan evidenciados. | Jobs, configuracion, reportes y aprobaciones.
| R-015 | p. 54 | Las conclusiones de validacion y produccion son sustentables. | Consistencia global y ausencia de hallazgos criticos.

**Nota:** Los IDs representan afirmaciones verificables; no se asigna `CUMPLE` por coincidencia conceptual sin validar valores exactos.