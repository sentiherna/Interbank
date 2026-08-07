# Tasks: MVP — Plataforma Analítica PLAFT basada en Grafos

**Feature**: `001-mvp-graph-variables` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Constitución**: v3.0.0 | **Spec**: v2.0 | **Date**: 2026-08-06

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | ADR-001–008 ✅

---

## Formato: `[ID] [P?] [Story?] Descripción con ruta/al/archivo.py`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias bloqueantes).
- **[USN]**: Historia de usuario relacionada según spec.md v2.0.
- Las fases transversales (infraestructura, AWS, rendimiento) no llevan [USN].
- **Definition of Done**: código implementado + tipado + documentación + pytest ✅ + ruff ✅ + mypy ✅.

---

## Fase 0 — Preparación y Estructura del Proyecto

**Propósito**: Inicializar el repositorio con la estructura, configuración y herramientas de calidad
que habilitan el desarrollo de todas las fases posteriores.

**Entregable verificable**: `make check` pasa (ruff + mypy + pytest --collect-only) con cero errores.

- [x] T001 Crear estructura de paquetes Python en `src/graph_plaft/__init__.py` y todos los subdirectorios del plan
- [x] T002 [P] Crear `pyproject.toml` con Python 3.12, dependencias fijadas, grupos dev/prod, configuración ruff y mypy
- [x] T003 [P] Crear `Makefile` con targets: `install`, `check`, `test`, `test-unit`, `test-integration`, `lint`, `typecheck`
- [x] T004 [P] Crear `.gitignore` que excluye: `data/`, `*.parquet`, `*.csv`, `.env`, `secrets/`, `__pycache__/`, `.mypy_cache/`
- [x] T005 [P] Crear `config/local.yaml` y `config/aws.yaml` con parámetros de entorno según ADR-006
- [x] T006 Implementar `src/graph_plaft/config/settings.py` con carga de configuración por entorno, tipado con dataclasses
- [x] T007 [P] Implementar `src/graph_plaft/config/schemas.py` con tipos base y constantes del proyecto
- [x] T008 Implementar `src/graph_plaft/observability/logging.py` con logging estructurado JSON, `execution_id`, nivel configurable
- [x] T009 [P] Implementar `src/graph_plaft/observability/errors.py` con clases base de excepciones: `CriticalValidationError`, `GraphBuildError`, `PersistenceError`
- [x] T010 [P] Implementar `src/graph_plaft/observability/run_id.py` con generador de `execution_id` (UUID-v4) reproducible con semilla opcional
- [x] T011 [P] Crear `src/graph_plaft/cli/__init__.py` y `src/graph_plaft/cli/commands.py` con estructura Click o Typer para comandos básicos
- [x] T012 [P] Configurar `pytest` en `pyproject.toml`: directorios, markers (`unit`, `integration`, `contract`, `performance`), cobertura mínima 80%
- [x] T013 Crear `tests/conftest.py` con fixtures globales: `tmp_path_parquet`, `synthetic_config`, `local_engine`
- [x] T014 [P] Crear `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py`, `tests/performance/__init__.py`
- [x] T015 [P] Crear `docs/adr/README.md` con índice de ADR-001 a ADR-008 y links a `adr/`
- [x] T016 [P] Configurar GitHub Actions CI en `.github/workflows/ci.yml`: ruff, mypy, pytest unitarios en push/PR
- [x] T017 [P] Crear `scripts/check_secrets.sh` que bloquea commits con patrones de credenciales o datos sensibles

---

## Fase 1 — Contratos y Modelos de Datos

**Propósito**: Establecer los contratos de datos para todas las fuentes, nodos, relaciones y salidas.
Toda fase posterior depende de estos contratos.

**Entregable verificable**: `pytest tests/contract/ -v` pasa para todos los esquemas con datos sintéticos mínimos.

- [X] T018 Implementar `src/graph_plaft/config/column_mapping.py` con capa de mapeo configurable entre nombres conceptuales y nombres físicos (a mapear en Fase 3 con datos reales)
- [X] T019 Implementar `src/graph_plaft/validation/schemas.py` con esquemas PySpark y pandas/PyArrow para: `clientes`, `cuentas`, `titularidades`, `productos`, `transferencias`
- [X] T020 [P] Implementar en `src/graph_plaft/validation/schemas.py` esquemas para: `alertas_plaft`, `ros`, `pep`, `casos_investigados`, `catalogo_documental`, `lista_objetivo`, `permisos_analistas`
- [X] T021 [P] Implementar `src/graph_plaft/graph/node_schemas.py` con esquemas para nodos: `Cliente`, `Cuenta`, `Producto`, `AlertaPLAFT`, `ROS`, `CondicionPEP`, `CasoInvestigado`, `Documento`
- [X] T022 [P] Implementar `src/graph_plaft/graph/edge_schemas.py` con esquemas para relaciones: `ES_TITULAR_DE`, `POSEE`, `TRANSFIERE_A`, `TIENE_ALERTA`, `TIENE_ROS`, `TIENE_CONDICION_PEP`, `TIENE_CASO`, `TIENE_DOCUMENTO`
- [X] T023 [P] Implementar `src/graph_plaft/analytics/result_schemas.py` con esquemas de salida para: `analytics_degree`, `analytics_pagerank`, `analytics_components`, `analytics_communities`, `analytics_risk_distance`
- [X] T024 [P] Implementar `src/graph_plaft/features/variable_schema.py` con esquema `variables_estructurales` (cliente_id, variable_nombre, categoria, valor, valor_nulo_razon, insumos, algoritmo, senales_origen, ventana_inicio, ventana_fin, fecha_calculo, graph_version, run_id)
- [X] T025 [P] Implementar `src/graph_plaft/observability/run_manifest.py` con dataclass `RunManifest` y serialización JSON según `data-model.md`
- [X] T026 [P] Implementar `src/graph_plaft/audit/audit_schema.py` con esquema del log de auditoría (audit_id, timestamp, usuario_id, accion, cliente_id, graph_version, datos_version, filtros_aplicados, documentos_consultados, exportacion_realizada, resultado, session_id)
- [X] T027 Implementar `src/graph_plaft/validation/contracts.py` con función `validate_schema(df, schema, source_name, execution_id)` que retorna `ValidationReport` con errores críticos y advertencias
- [X] T028 [P] Crear `tests/contract/test_input_schemas.py` con pruebas de validación de cada esquema de entrada contra datasets sintéticos mínimos (una fila válida + una inválida por regla)
- [X] T029 [P] Crear `tests/contract/test_node_schemas.py` con pruebas de validación de esquemas de nodos
- [X] T030 [P] Crear `tests/contract/test_edge_schemas.py` con pruebas de validación de esquemas de relaciones
- [X] T031 [P] Crear `tests/contract/test_variable_schema.py` con pruebas de esquema de variables (incluyendo nulos documentados)
- [X] T032 [P] Crear `contracts/mapeo_fisico_conceptual.md` como plantilla de mapeo con instrucciones para completar en Fase 3

---

## Fase 2 — Datos Sintéticos de Prueba

**Propósito**: Crear datasets sintéticos reproducibles con semilla fija para todas las fases de prueba.
Cubre todos los patrones definidos en research.md y quickstart.md.

**Entregable verificable**: `python scripts/generate_synthetic.py --seed 42` produce los mismos archivos Parquet en toda ejecución; checksums idénticos.

- [X] T033 Implementar `scripts/generate_synthetic.py` con argumento `--seed` y generación de todos los datasets sintéticos con pandas; salida en `data/synthetic/`
- [X] T034 [P] Crear `data/synthetic/generators/base.py` con `SyntheticDataGenerator` base que acepta semilla y garantiza reproducibilidad
- [X] T035 [P] Crear `data/synthetic/generators/clientes.py`: 10 clientes (2 con alerta, 1 con ROS, 1 PEP, 1 con caso, 1 con múltiples señales, 4 sin señales)
- [X] T036 [P] Crear `data/synthetic/generators/cuentas.py`: cuentas incluyendo cuenta compartida entre 2 titulares
- [X] T037 [P] Crear `data/synthetic/generators/transferencias.py`: patrones estrella, cadena, ciclo, hub, intermediario, múltiples TX entre mismas cuentas, anuladas, posteriores al corte
- [X] T038 [P] Crear `data/synthetic/generators/senales.py`: alertas, ROS, PEP, casos para clientes de `clientes.py`
- [X] T039 [P] Crear `data/synthetic/generators/documentos.py`: documentos válidos, documentos sin `referencia_s3`, documentos posteriores al corte
- [X] T040 [P] Crear `data/synthetic/generators/permisos.py`: analista con acceso a subconjunto de clientes (excluye al menos 1 cliente para pruebas de rechazo)
- [X] T041 Crear `data/synthetic/expected_outputs/` con archivos JSON que documentan valores esperados de variables para cada patrón sintético (grado, componente, PageRank, etc.)
- [X] T042 [P] Crear `tests/unit/test_synthetic_generators.py` que verifica reproducibilidad: dos generaciones con misma semilla producen checksums idénticos
- [X] T043 [P] Crear `data/synthetic/README.md` que documenta cada dataset sintético, patron incluido y valores esperados

---

## Fase 3 — Ingesta y Validación

**Propósito**: Implementar la capa de Ingesta (Capa 1) y Validación (Capa 2) del plan.

**Entregable verificable**: Job de validación sobre datos sintéticos produce `quality_report.json` correcto;
error crítico detiene el proceso con exit code ≠ 0.

- [X] T044 Implementar `src/graph_plaft/ingestion/data_engine.py` con interfaz abstracta `DataEngine` y métodos: `read_parquet`, `read_csv`, `write_parquet` (ADR-006)
- [X] T045 Implementar `src/graph_plaft/ingestion/pandas_engine.py` con `PandasEngine(DataEngine)` para modo local (pandas + pyarrow)
- [X] T046 Implementar `src/graph_plaft/ingestion/spark_engine.py` con `SparkEngine(DataEngine)` para modo PySpark; lectura/escritura S3
- [X] T047 Implementar `src/graph_plaft/ingestion/loaders.py` con función `load_dataset(source_name, engine, config, execution_id)` que registra versión y checksum del archivo fuente
- [X] T048 [P] Implementar `src/graph_plaft/ingestion/registry.py` con `DatasetRegistry` que registra nombre, ruta S3, versión, checksum y row_count por dataset por ejecución
- [X] T049 Implementar `src/graph_plaft/validation/rules.py` con reglas de validación para `clientes` (obligatorios, tipos, unicidad de clave primaria)
- [X] T050 [P] Implementar en `src/graph_plaft/validation/rules.py` reglas para `cuentas`, `titularidades`, `productos`
- [X] T051 [P] Implementar en `src/graph_plaft/validation/rules.py` reglas para `transferencias` (id_transaccion único en batch, estado en dominio, fecha ≤ fecha_corte, monto > 0 si EJECUTADA)
- [X] T052 [P] Implementar en `src/graph_plaft/validation/rules.py` reglas para `alertas_plaft`, `ros`, `pep`, `casos_investigados`
- [X] T053 [P] Implementar en `src/graph_plaft/validation/rules.py` reglas para `catalogo_documental`, `lista_objetivo`, `permisos_analistas`
- [X] T054 Implementar `src/graph_plaft/validation/quality.py` con `QualityChecker` que ejecuta todas las reglas, clasifica errores (CRITICAL/WARNING) y genera `ValidationReport`
- [X] T055 Implementar `src/graph_plaft/validation/temporal.py` con `apply_date_cutoff(df, date_col, date_cutoff)` que rechaza registros posteriores al corte
- [X] T056 [P] Implementar `src/graph_plaft/validation/deduplication.py` con `deduplicate_by_pk(df, pk_columns, source_name)` que retiene el primero y registra duplicados como advertencia
- [X] T057 Implementar lógica de detención controlada en `src/graph_plaft/validation/quality.py`: si `CriticalValidationError`, raise con mensaje estructurado y log completo del reporte
- [X] T058 [P] Crear `tests/unit/test_validation_rules.py` con pruebas de cada regla: fila válida pasa, fila inválida produce error con severidad correcta
- [X] T059 [P] Crear `tests/unit/test_temporal_cutoff.py` que verifica que transferencias posteriores al corte son rechazadas y anteriores son aceptadas
- [X] T060 [P] Crear `tests/integration/test_validation_pipeline.py` que ejecuta validación completa sobre datos sintéticos y verifica quality_report correcto
- [X] T061 Crear `tests/unit/test_critical_error_stops_pipeline.py` que verifica exit code ≠ 0 y log de error cuando hay error crítico

---

## Fase 4 — Selección de Clientes Sospechosos

**Propósito**: Implementar la capa de Selección (Capa 3) con criterios configurables y versionados.

**Entregable verificable**: Dado datos sintéticos, la selección por criterio produce la lista correcta de clientes objetivo
con todos los motivos registrados; re-ejecución con mismos parámetros produce resultado idéntico.

- [ ] T062 [US1] Implementar `src/graph_plaft/population/criteria.py` con interfaz `SelectionCriterion` y método `apply(clients_df, signals_df, config) -> DataFrame`
- [ ] T063 [US1] Implementar `src/graph_plaft/population/criteria.py` criterio `AlertaCriterion`: selecciona clientes con al menos una alerta PLAFT ≤ fecha_corte
- [ ] T064 [P] [US1] Implementar criterio `ROSCriterion` en `src/graph_plaft/population/criteria.py`: clientes con ROS ≤ fecha_corte
- [ ] T065 [P] [US1] Implementar criterio `PEPCriterion` en `src/graph_plaft/population/criteria.py`: clientes con PEP vigente a fecha_corte (fecha_inicio ≤ corte AND (fecha_fin IS NULL OR fecha_fin ≥ corte))
- [ ] T066 [P] [US1] Implementar criterio `CasoInvestigadoCriterion` en `src/graph_plaft/population/criteria.py`: clientes con caso abierto antes del corte
- [ ] T067 [P] [US1] Implementar criterio `ListaObjetivoCriterion` en `src/graph_plaft/population/criteria.py`: clientes en lista provista por PLAFT ≤ fecha_corte
- [ ] T068 [P] [US1] Implementar criterio `ReglaCriterion` en `src/graph_plaft/population/criteria.py`: regla configurable con expresión SQL o lógica parametrizable
- [ ] T069 [US1] Implementar `src/graph_plaft/population/selector.py` con `PopulationSelector` que combina criterios, une resultados, elimina duplicados y registra todos los motivos por cliente
- [ ] T070 [US1] Implementar en `src/graph_plaft/population/selector.py` generación del dataframe `clientes_objetivo` con columnas: cliente_id, criterios_cumplidos (lista), fecha_seleccion, periodo, run_id
- [ ] T071 [US1] Implementar `src/graph_plaft/population/manifest.py` con `PopulationManifest` que registra: count por criterio, count total, run_id, fecha_corte, version_seleccion
- [ ] T072 [P] [US1] Crear `tests/unit/test_criteria.py` con prueba de cada criterio individual: dato que cumple → incluido, dato que no cumple → excluido
- [ ] T073 [P] [US1] Crear `tests/unit/test_selector.py` que verifica: cliente con múltiples criterios tiene todos los motivos; no hay duplicados; total correcto
- [ ] T074 [P] [US1] Crear `tests/unit/test_population_reproducibility.py`: misma semilla y parámetros producen mismo conjunto de selección

---

## Fase 5 — Resolución de Identidades y Expansión de Contrapartes

**Propósito**: Implementar la capa de Expansión (Capa 4): resolver cliente↔cuenta y expandir contrapartes.

**Entregable verificable**: Dado un cliente sospechoso con transferencias, el módulo identifica correctamente
las contrapartes a profundidad 1; una contraparte que también es sospechosa aparece con ambos roles.

- [ ] T075 [US1] Implementar `src/graph_plaft/population/identity_resolver.py` con `IdentityResolver` que resuelve cliente_id desde cuenta_id usando titularidades
- [ ] T076 [US1] Implementar en `src/graph_plaft/population/identity_resolver.py` resolución de cliente_origen y cliente_destino en transferencias (puede ser null si no resoluble)
- [ ] T077 [US1] Implementar lógica de cuentas compartidas en `src/graph_plaft/population/identity_resolver.py`: una cuenta con N titulares genera N registros de titularidad independientes
- [ ] T078 [US1] Implementar `src/graph_plaft/population/expander.py` con `SubgraphExpander` que identifica contrapartes de clientes objetivo a profundidad configurable (default: 1)
- [ ] T079 [US1] Implementar en `src/graph_plaft/population/expander.py` control de límites: la expansión no puede superar el `max_depth` configurado
- [ ] T080 [US1] Implementar en `src/graph_plaft/population/expander.py` marcado de contraparte: si una contraparte es también cliente objetivo, asignar `es_cliente_objetivo=True` y `es_contraparte=True` sin duplicar el nodo
- [ ] T081 [US1] Implementar en `src/graph_plaft/population/expander.py` registro de `nivel_expansion` (0=objetivo, 1=contraparte directa, 2+=expansión adicional) y `motivo_incorporacion`
- [ ] T082 [P] [US1] Crear `tests/unit/test_identity_resolver.py` con: cuenta con 2 titulares, cuenta sin titular conocido, resolución de cliente_origen en transferencia
- [ ] T083 [P] [US1] Crear `tests/unit/test_expander.py` con: expansión profundidad 1, contraparte que también es sospechosa, cliente sin contrapartes, ciclo en la red

---

## Fase 6 — Construcción del Subgrafo

**Propósito**: Implementar la capa de Construcción (Capa 5): generar tablas de nodos y aristas con trazabilidad.

**Entregable verificable**: Dado los datos sintéticos de estrella, el subgrafo contiene el número correcto
de nodos y aristas; cada nodo tiene `dataset_origen` y `registro_fuente` no nulos.

- [ ] T084 [US1] Implementar `src/graph_plaft/graph/nodes.py` con función `build_cliente_nodes(clients_df, population_df, run_id, graph_version)` → tabla `nodes_cliente` con todos los atributos del data-model.md
- [ ] T085 [P] [US1] Implementar `build_cuenta_nodes`, `build_producto_nodes` en `src/graph_plaft/graph/nodes.py`
- [ ] T086 [P] [US1] Implementar `build_alerta_nodes`, `build_ros_nodes`, `build_pep_nodes`, `build_caso_nodes`, `build_documento_nodes` en `src/graph_plaft/graph/nodes.py`
- [ ] T087 [US1] Implementar `src/graph_plaft/graph/edges.py` con `build_transfer_edges(transfers_df, identity_resolver, run_id, graph_version)` — cada `id_transaccion` es arista independiente; NO deduplicar por par cuenta-cuenta (ADR-001)
- [ ] T088 [P] [US1] Implementar `build_titularidad_edges`, `build_producto_edges` en `src/graph_plaft/graph/edges.py`
- [ ] T089 [P] [US1] Implementar `build_alerta_edges`, `build_ros_edges`, `build_pep_edges`, `build_caso_edges`, `build_documento_edges` en `src/graph_plaft/graph/edges.py`
- [ ] T090 [US1] Implementar `src/graph_plaft/graph/builder.py` con `SubgraphBuilder.build(config, engine, population, signals, docs, run_id)` que orquesta Fases 5-6 y retorna `SubgraphArtifact`
- [ ] T091 [US1] Implementar en `src/graph_plaft/graph/builder.py` filtrado de transferencias anuladas (estado IN {'ANULADA','REVERTIDA'}) antes de construir aristas
- [ ] T092 [US1] Implementar en `src/graph_plaft/graph/builder.py` construcción de capa agregada `edges_transfiere_a_agg` (count_tx, monto_total, fecha_primera, fecha_ultima) en memoria para uso en Analytics (ADR-008)
- [ ] T093 [P] [US1] Implementar `src/graph_plaft/graph/stable_ids.py` con generación de identificadores estables para nodos (hash determinista de campos clave)
- [ ] T094 [P] [US1] Crear `tests/unit/test_nodes.py` con: nodo cliente con ambos roles, nodo sin señales, documento sin referencia_s3
- [ ] T095 [P] [US1] Crear `tests/unit/test_edges.py` con: 3 transferencias entre mismas cuentas producen 3 aristas; transferencia anulada excluida; trazabilidad correcta
- [ ] T096 [US1] Crear `tests/integration/test_graph_builder.py` con: datos sintéticos de estrella producen estructura correcta; ciclo en grafo no lanza excepción

---

## Fase 7 — Persistencia y Versionado del Grafo

**Propósito**: Implementar la capa de Persistencia (Capa 6): guardar y recuperar versiones del subgrafo.

**Entregable verificable**: Se persiste un grafo, se recupera por `graph_version`; el grafo recuperado tiene
el mismo checksum que el grafo original.

- [ ] T097 [US2] Implementar `src/graph_plaft/persistence/versioning.py` con `GraphVersionManager`: genera `graph_version` UUID, computa checksums de nodos y aristas, registra metadatos
- [ ] T098 [US2] Implementar `src/graph_plaft/persistence/graph_store.py` con `GraphStore.save(subgraph, version, engine)` que persiste tablas Parquet en `s3://.../graph/v{version}/` (ADR-003)
- [ ] T099 [US2] Implementar `src/graph_plaft/persistence/graph_store.py` con `GraphStore.load(graph_version, engine)` que recupera y valida integridad (checksum)
- [ ] T100 [US2] Implementar `src/graph_plaft/persistence/graph_store.py` con escritura idempotente: si la versión ya existe, validar checksum antes de sobreescribir
- [ ] T101 [US2] Implementar `src/graph_plaft/persistence/graph_store.py` con registro del grafo en Glue Catalog (configurable; deshabilitado en local)
- [ ] T102 [US2] Implementar `src/graph_plaft/observability/run_manifest.py` con `RunManifest.save(path, engine)` y `RunManifest.load(path, engine)`
- [ ] T103 [US2] Implementar registro del run en MLflow en `src/graph_plaft/persistence/mlflow_tracker.py` con parámetros, métricas y artefactos (configurable; modo stub para local sin MLflow)
- [ ] T104 [P] [US2] Crear `tests/unit/test_versioning.py`: dos grafos con misma estructura producen mismo checksum; grafos distintos producen checksums distintos
- [ ] T105 [P] [US2] Crear `tests/integration/test_graph_store.py`: save → load produce DataFrame idéntico; carga de versión inexistente lanza error descriptivo
- [ ] T106 [US2] Crear `tests/integration/test_graph_reproducibility.py`: dos ejecuciones con mismos datos y semilla producen mismo `graph_version` (mismo checksum)

---

## Fase 8 — Graph Analytics Mínimo Viable

**Propósito**: Implementar la capa de Graph Analytics (Capa 7) con algoritmos obligatorios del MVP.
Algoritmos experimentales marcados como tales según ADR-007.

**Entregable verificable**: Dado el grafo de estrella sintético, los grados, PageRank y componentes
coinciden con los valores esperados de `data/synthetic/expected_outputs/`.

- [ ] T107 [US3] Implementar `src/graph_plaft/analytics/graph_engine.py` con interfaz abstracta `GraphAnalyticsEngine` y método `run(algorithm_name, graph, params) -> DataFrame` (ADR-002)
- [ ] T108 [US3] Implementar `src/graph_plaft/analytics/networkx_engine.py` con `NetworkXEngine(GraphAnalyticsEngine)` para modo local (solo subgrafos < 10,000 nodos)
- [ ] T109 [US3] Implementar `src/graph_plaft/analytics/graphframes_engine.py` con `GraphFramesEngine(GraphAnalyticsEngine)` para PySpark (carga condicional; stub si graphframes no disponible)
- [ ] T110 [US3] Implementar `src/graph_plaft/analytics/mandatory.py`: `compute_degree(graph, engine)` → `analytics_degree` (in_degree, out_degree, total_degree, tx_recibidas, tx_enviadas, monto_recibido, monto_enviado, contrapartes_unicas)
- [ ] T111 [P] [US3] Implementar `compute_pagerank(graph, engine, damping=0.85, max_iter=100)` → `analytics_pagerank` en `src/graph_plaft/analytics/mandatory.py`
- [ ] T112 [P] [US3] Implementar `compute_connected_components(graph, engine)` → `analytics_components` en `src/graph_plaft/analytics/mandatory.py`
- [ ] T113 [US3] Implementar `compute_communities(graph, engine, method='label_propagation', seed=42)` → `analytics_communities` en `src/graph_plaft/analytics/mandatory.py`; documentar que es aproximación de Louvain (ADR-007)
- [ ] T114 [US3] Implementar `compute_risk_distance(graph, signal_nodes, engine, max_depth=5)` → `analytics_risk_distance` (distancia mínima dirigida a cliente con alerta/ROS/PEP/caso) en `src/graph_plaft/analytics/mandatory.py`
- [ ] T115 [US3] Implementar `compute_risk_exposure(graph, signal_nodes, engine)` → `analytics_risk_exposure` (exposición directa e indirecta a señales, diferenciada por tipo) en `src/graph_plaft/analytics/mandatory.py`
- [ ] T116 [P] [US3] Implementar `src/graph_plaft/analytics/experimental.py` con stubs documentados para: `compute_betweenness_approx`, `compute_closeness_approx`, `compute_eigenvector`; cada uno verifica umbral de ADR-007 antes de ejecutar
- [ ] T117 [US3] Implementar `src/graph_plaft/analytics/runner.py` con `AnalyticsRunner.run(graph, config, engine)` que ejecuta obligatorios en orden y persiste resultados en `s3://.../runs/{run_id}/analytics/`
- [ ] T118 [P] [US3] Crear `tests/unit/test_degree.py`: grafo de estrella sintético → grados esperados; hub tiene máximo out_degree; cliente aislado tiene grado 0
- [ ] T119 [P] [US3] Crear `tests/unit/test_pagerank.py`: grafo de cadena A→B→C → PageRank de C > B > A; suma de PageRank ≈ 1
- [ ] T120 [P] [US3] Crear `tests/unit/test_components.py`: grafo con 2 componentes → 2 component_ids distintos; grafo de ciclo → 1 componente
- [ ] T121 [P] [US3] Crear `tests/unit/test_communities.py`: grafo de comunidad → clientes de la misma comunidad tienen mismo comunidad_id
- [ ] T122 [US3] Crear `tests/unit/test_risk_distance.py`: cliente conectado a contraparte con ROS tiene distancia_min_ros=1; cliente no conectado tiene null
- [ ] T123 [US3] Crear `tests/unit/test_analytics_handles_cycles.py`: grafo con ciclo A→B→C→A no produce loop infinito en ningún algoritmo

---

## Fase 9 — Catálogo de Variables Estructurales

**Propósito**: Implementar las 8 categorías de variables MVP con trazabilidad completa.

**Entregable verificable**: Para cada cliente del subgrafo sintético existe una fila por cada variable del catálogo;
los nulos tienen `valor_nulo_razon` documentado; señales de riesgo diferenciadas.

- [ ] T124 [US3] Implementar `src/graph_plaft/features/catalog.py` con `VariableCatalog` que registra metadatos de cada variable: nombre, definición, categoría, fórmula, ventana, costo, estado (MVP/recomendada/experimental)
- [ ] T125 [US3] Implementar `src/graph_plaft/features/centrality.py` con variables MVP: `grado_entrada`, `grado_salida`, `grado_total`, `pagerank`, `centralidad_ponderada_monto` (out_degree ponderado por monto_enviado)
- [ ] T126 [P] [US3] Implementar `src/graph_plaft/features/connectivity.py` con variables MVP: `contrapartes_unicas`, `cuentas_propias`, `componente_conectado`, `tamano_componente`, `vinculos_unicos`
- [ ] T127 [P] [US3] Implementar `src/graph_plaft/features/communities.py` con variables MVP: `comunidad_id`, `tamano_comunidad`, `prop_sospechosos_comunidad`, `senales_distintas_comunidad`
- [ ] T128 [US3] Implementar `src/graph_plaft/features/flow.py` con variables MVP: `monto_enviado_total`, `monto_recibido_total`, `tx_enviadas`, `tx_recibidas`, `saldo_flujo`, `concentracion_contraparte`, `concentracion_cuenta`, `reciprocidad`, `pct_enviado_principal_contraparte`
- [ ] T129 [P] [US3] Implementar `src/graph_plaft/features/patterns.py` con variables MVP: `frecuencia_tx`, `monto_promedio_tx`, `dias_activos`, `canales_distintos`, `actividad_por_periodo`, `prop_entradas_salidas`
- [ ] T130 [P] [US3] Implementar `src/graph_plaft/features/anomalies.py` con variables MVP: `desviacion_grado`, `es_intermediario`, `concentracion_atipica`, `flujo_atipico`, `patron_intermediacion`; sin modelos ML externos
- [ ] T131 [US3] Implementar `src/graph_plaft/features/neighbor_risk.py` con variables MVP (señales diferenciadas): `contrapartes_con_alerta`, `contrapartes_con_ros`, `contrapartes_con_pep`, `contrapartes_con_caso`, `monto_recibido_de_alerta`, `monto_enviado_a_pep`, `prop_contrapartes_investigadas`, `prop_flujo_senales`
- [ ] T132 [US3] Implementar `src/graph_plaft/features/propagated_risk.py` con variables MVP (señales diferenciadas): `distancia_min_alerta`, `distancia_min_ros`, `distancia_min_pep`, `distancia_min_caso`, `exposicion_ponderada_senales`, `exposicion_por_profundidad`, `pct_flujo_sospechosos`
- [ ] T133 [US3] Implementar en `src/graph_plaft/features/propagated_risk.py` pesos de señales como parámetro configurable (alerta=0.7, ros=1.0, pep=0.3, caso=0.9 como defaults); pesos almacenados en RunManifest
- [ ] T134 [US3] Implementar `src/graph_plaft/features/generator.py` con `VariableGenerator.generate(analytics, subgraph, config, run_id, graph_version)` que produce `variables_estructurales` DataFrame garantizando una fila por variable por cliente
- [ ] T135 [US3] Implementar en `src/graph_plaft/features/generator.py` comportamiento para clientes sin actividad: variables de flujo = 0, variables de distancia = null con `valor_nulo_razon='no_alcanzable'`
- [ ] T136 [P] [US3] Crear `tests/unit/test_flow_variables.py`: cliente con 3 TX enviadas y 2 recibidas → valores correctos; cliente sin TX → 0 o null documentado
- [ ] T137 [P] [US3] Crear `tests/unit/test_neighbor_risk.py`: cliente con contraparte con alerta → contrapartes_con_alerta=1, contrapartes_con_ros=0; señales diferenciadas correctas
- [ ] T138 [US3] Crear `tests/unit/test_complete_schema.py`: para cada cliente del subgrafo sintético, existe exactamente una fila por variable del catálogo; ninguna variable faltante

---

## Fase 10 — Integridad Temporal

**Propósito**: Garantizar que ninguna variable usa información posterior a la `fecha_corte`.

**Entregable verificable**: Dado un dataset con señales posteriores al corte, las variables calculadas
son idénticas a las calculadas sin esas señales; prueba de no-leakage pasa.

- [ ] T139 Implementar `src/graph_plaft/validation/temporal.py` con `TemporalIntegrityChecker.check(df, temporal_config)` que valida vigencia de cada tipo de señal según la tabla del plan
- [ ] T140 [P] Implementar en `src/graph_plaft/validation/temporal.py`: PEP → `fecha_inicio ≤ fecha_corte AND (fecha_fin IS NULL OR fecha_fin ≥ fecha_corte)`
- [ ] T141 [P] Implementar en `src/graph_plaft/validation/temporal.py`: Casos → solo los con `fecha_apertura ≤ fecha_corte` (abiertos Y cerrados)
- [ ] T142 [P] Implementar en `src/graph_plaft/validation/temporal.py`: Documentos → solo `fecha_incorporacion ≤ fecha_corte`
- [ ] T143 Implementar registro de ventana temporal en cada variable: añadir `ventana_inicio`, `ventana_fin`, `fecha_calculo` al schema `variables_estructurales`
- [ ] T144 [P] Crear `tests/unit/test_no_temporal_leakage.py`: variable calculada con dataset que incluye señal posterior al corte = variable calculada sin esa señal
- [ ] T145 [P] Crear `tests/unit/test_pep_vigencia.py`: PEP expirado antes del corte no se incluye; PEP vigente sí se incluye
- [ ] T146 [P] Crear `tests/unit/test_boundary_dates.py`: transferencia exactamente en fecha_corte → incluida; un día después → excluida

---

## Fase 11 — Persistencia de Variables

**Propósito**: Persistir variables en S3 con versionado y preparar para Feature Store.

**Entregable verificable**: Variables persistidas en Parquet recuperables con `variables_version`; reproceso no genera duplicados.

- [ ] T147 [US3] Implementar `src/graph_plaft/features/variable_store.py` con `VariableStore.save(variables_df, version, engine)`: persiste en `s3://.../variables/v{version}/` particionado por `categoria`
- [ ] T148 [US3] Implementar `VariableStore.load(variables_version, engine)` con validación de integridad
- [ ] T149 [US3] Implementar escritura idempotente en `VariableStore`: checksum previo comparado antes de sobreescribir
- [ ] T150 [P] [US3] Crear `tests/integration/test_variable_store.py`: save → load produce DataFrame idéntico; reproceso con mismos datos no duplica
- [ ] T151 [P] [US3] Crear `tests/unit/test_variable_versioning.py`: dos conjuntos de variables con mismos datos producen mismo checksum

---

## Fase 12 — SageMaker Feature Store

**Propósito**: Publicar variables en SageMaker Feature Store (Offline Store únicamente según ADR-004).

**Entregable verificable**: Variables de datos sintéticos se escriben y leen desde Feature Store; la lectura produce
los valores correctos para el `event_time` (fecha_corte) correcto.

- [ ] T152 [US5] Implementar `src/graph_plaft/feature_store/feature_group.py` con definición conceptual del Feature Group: nombre, entity_id=`cliente_id`, event_time=`fecha_corte`, lista de features según catálogo
- [ ] T153 [US5] Implementar `src/graph_plaft/feature_store/writer.py` con `FeatureStoreWriter.write(variables_df, engine_type)` que en AWS escribe a SageMaker Feature Store; en local simula escritura en Parquet
- [ ] T154 [US5] Implementar `src/graph_plaft/feature_store/writer.py` manejo de duplicados: Feature Store resuelve por `(cliente_id, fecha_corte)` conservando el más reciente
- [ ] T155 [US5] Implementar stub local `src/graph_plaft/feature_store/local_store.py` para pruebas sin acceso AWS: escribe/lee Parquet simulando la semántica de Feature Store
- [ ] T156 [P] [US5] Crear `tests/unit/test_feature_store_writer.py` sobre stub local: write → read retorna mismos valores; reproceso no duplica
- [ ] T157 [P] [US5] Crear `tests/unit/test_feature_store_temporal.py`: batch_get_record con `event_time=fecha_corte_A` retorna features de ese período, no de período posterior

---

## Fase 13 — Consultas y Explicación

**Propósito**: Implementar la capa de Consultas (Capa 11) separada de la interfaz visual.
Toda la lógica de negocio de consulta es reutilizable independientemente de la UI.

**Entregable verificable**: Dado `cliente_id` válido, `QueryEngine.get_client_subgraph()` retorna el subgrafo correcto
con trazabilidad; dado cliente no autorizado, retorna `AccessDeniedError`.

- [ ] T158 [US4] [US6] Implementar `src/graph_plaft/querying/query_engine.py` con `QueryEngine(graph_store, variables_store, access_control, audit_log)` y métodos: `get_client_subgraph`, `get_client_signals`, `get_client_variables`, `get_client_documents`
- [ ] T159 [US4] Implementar `QueryEngine.get_client_subgraph(client_id, graph_version, filters, user_id)` con validación de autorización antes de acceder a datos
- [ ] T160 [US4] Implementar filtros en `src/graph_plaft/querying/filters.py`: por período, monto mínimo/máximo, moneda, canal, dirección (entrada/salida), tipo de relación, condición de riesgo de contraparte
- [ ] T161 [US6] Implementar `QueryEngine.get_variable_explanation(client_id, variable_name, graph_version, user_id)` que retorna insumos, algoritmo, relaciones y señales de origen
- [ ] T162 [US6] Implementar `src/graph_plaft/querying/traceability.py` con `get_node_source(node_id, graph_version)` que retorna dataset_origen y registro_fuente
- [ ] T163 [US4] Implementar `src/graph_plaft/querying/query_engine.py` método `export_summary(client_id, graph_version, filters, user_id)` que produce JSON estructurado con todos los datos de la consulta
- [ ] T164 [P] [US4] Crear `tests/unit/test_query_engine.py`: cliente válido → subgrafo correcto; cliente sin relaciones → respuesta vacía con mensaje; cliente no autorizado → AccessDeniedError
- [ ] T165 [P] [US4] Crear `tests/unit/test_filters.py`: filtro por período excluye transferencias fuera del rango; filtro por señal de riesgo incluye solo contrapartes con esa señal
- [ ] T166 [P] [US6] Crear `tests/unit/test_variable_explanation.py`: explicación de `contrapartes_con_ros` incluye la lista de ROS fuente y las cuentas involucradas

---

## Fase 14 — Herramienta de Investigación

**Propósito**: Implementar la interfaz visual para analistas (Streamlit según ADR-005).
La lógica de negocio NO se implementa aquí; se reutiliza la capa de Consultas.

**Entregable verificable**: La herramienta se lanza localmente con datos sintéticos; se puede buscar un cliente,
visualizar su subgrafo y ver sus variables sin reconstruir el grafo.

- [ ] T167 [US4] Implementar `src/graph_plaft/tool/app.py` con estructura Streamlit: sidebar de búsqueda, área principal de visualización, panel de métricas y panel de documentos
- [ ] T168 [US4] Implementar `src/graph_plaft/tool/app.py` pantalla de búsqueda por `cliente_id` con validación de autorización y mensaje descriptivo si cliente no encontrado o no autorizado
- [ ] T169 [US4] Implementar `src/graph_plaft/tool/views/subgraph_view.py` con visualización del subgrafo usando pyvis o streamlit-agraph; diferenciación de tipos de nodo y relación por forma/iconografía (no solo color)
- [ ] T170 [US4] Implementar `src/graph_plaft/tool/views/transfers_view.py` con tabla de transferencias: dirección diferenciada (↑ entrada / ↓ salida), monto, fecha, moneda, canal, cuenta contraparte
- [ ] T171 [P] [US4] Implementar `src/graph_plaft/tool/views/signals_view.py` con tabs separados para: Alertas PLAFT, ROS, Condición PEP, Casos Investigados; señales diferenciadas, no combinadas
- [ ] T172 [P] [US4] Implementar `src/graph_plaft/tool/views/documents_view.py` con lista de documentos del cliente: tipo, nombre, fecha, estado, referencia S3; indicador visible si referencia_s3 no disponible
- [ ] T173 [P] [US4] Implementar `src/graph_plaft/tool/views/variables_view.py` con tabla de variables por categoría; enlace a explicación para cada variable
- [ ] T174 [US4] Implementar `src/graph_plaft/tool/views/filters_panel.py` con controles para: período (fecha inicio/fin), monto mínimo/máximo, dirección, tipo de relación, condición de riesgo
- [ ] T175 [US4] Implementar `src/graph_plaft/tool/views/subgraph_view.py` expansión controlada de contrapartes: solo nodos ya presentes en el subgrafo persistido con autorización del analista (ADR-005)
- [ ] T176 [US4] Implementar en `src/graph_plaft/tool/app.py` widget permanente con: versión del grafo activo, fecha de corte de los datos; visible en todo momento
- [ ] T177 [US4] Implementar `src/graph_plaft/tool/export.py` con `export_summary_json(query_result)` que produce JSON exportable con todos los datos de la consulta
- [ ] T178 [US4] Implementar en `src/graph_plaft/tool/app.py` manejo de errores de UI: cliente sin datos → mensaje descriptivo; error de consulta → mensaje de error sin stack trace expuesto al analista
- [ ] T179 [US4] Crear `tests/unit/test_tool_components.py` con pruebas de lógica de presentación: formato de monto, diferenciación entrada/salida, indicador de referencia_s3 faltante
- [ ] T180 [P] [US4] Crear `docs/guia_analista.md` con instrucciones de uso de la herramienta para analistas PLAFT no técnicos

---

## Fase 15 — Seguridad y Autorización

**Propósito**: Implementar la capa de Seguridad (Capa 13) con control de acceso por mínimo privilegio.

**Entregable verificable**: Analista con permisos sobre cliente_A puede consultarlo; intento de consultar
cliente_B (sin permisos) produce `AccessDeniedError` y el intento queda en el log de auditoría.

- [ ] T181 Implementar `src/graph_plaft/security/access_control.py` con interfaz abstracta `AccessControl` y método `authorize(user_id, resource_type, resource_id) -> AuthResult`
- [ ] T182 Implementar `src/graph_plaft/security/local_access_control.py` con `LocalAccessControl(AccessControl)` que carga permisos desde `permisos_analistas.parquet` (modo local y pruebas)
- [ ] T183 Implementar `src/graph_plaft/security/access_control.py` segregación de permisos: `DATOS` (acceso a subgrafo y variables) y `DOCUMENTOS` (acceso a referencias documentales) son permisos independientes
- [ ] T184 Implementar en `src/graph_plaft/security/access_control.py` rechazo de expansión más allá del subgrafo autorizado: `authorize_expansion(user_id, target_client_id)` verifica que el nodo destino esté en el subgrafo autorizado
- [ ] T185 [P] Implementar `src/graph_plaft/security/secrets.py` con validación en CI/startup que el entorno no contiene credenciales hard-coded; lectura de secretos solo desde variables de entorno o AWS Secrets Manager
- [ ] T186 [P] Crear `tests/unit/test_access_control.py`: analista con permiso → AuthResult.allowed=True; sin permiso → AuthResult.allowed=False; permiso DATOS no implica permiso DOCUMENTOS
- [ ] T187 [P] Crear `tests/unit/test_expansion_authorization.py`: expandir nodo en subgrafo autorizado → permitido; nodo fuera del subgrafo → denegado + registro en auditoría
- [ ] T188 [P] Crear `tests/security/test_privilege_escalation.py`: analista sin permiso de DOCUMENTOS no puede acceder a referencias S3 aunque tenga permiso de DATOS

---

## Fase 16 — Auditoría

**Propósito**: Implementar la capa de Auditoría (Capa 14) con log inmutable de todas las acciones.

**Entregable verificable**: Toda acción del analista (search, view, export, denied) produce entrada en `audit_log`;
la entrada contiene todos los campos requeridos; el log no puede modificarse una vez escrito.

- [ ] T189 Implementar `src/graph_plaft/audit/audit_log.py` con `AuditLogger.log(action, user_id, context)` que escribe entrada JSON inmutable; en producción: append-only en S3; en local: append a archivo JSON
- [ ] T190 Implementar en `src/graph_plaft/audit/audit_log.py` todas las acciones del spec.md SA-002: `search`, `view_subgraph`, `view_variable`, `view_document`, `expand_node`, `export`, `denied`
- [ ] T191 Implementar en `src/graph_plaft/audit/audit_log.py` campos obligatorios por acción: `audit_id`, `timestamp`, `usuario_id`, `accion`, `cliente_id`, `graph_version`, `datos_version`, `filtros_aplicados`, `documentos_consultados`, `exportacion_realizada`, `resultado`, `session_id`
- [ ] T192 Implementar `src/graph_plaft/audit/audit_log.py` política de retención: configurable en días (default: 365); registrada en `run_manifest.json`
- [ ] T193 [P] Crear `tests/unit/test_audit_completeness.py`: cada tipo de acción produce entrada con todos los campos requeridos; ningún campo obligatorio es nulo
- [ ] T194 [P] Crear `tests/unit/test_audit_denied_logged.py`: intento de acceso denegado produce entrada con `resultado='denied'` antes de retornar el error al usuario
- [ ] T195 [P] Crear `tests/unit/test_audit_idempotency.py`: no se generan entradas de auditoría duplicadas para la misma acción con mismo `session_id`

---

## Fase 17 — Observabilidad y Manifiestos

**Propósito**: Implementar la capa de Observabilidad (Capa 15) con métricas operacionales completas.

**Entregable verificable**: Al finalizar el pipeline sobre datos sintéticos, `run_manifest.json` contiene
todos los campos del data-model.md; las métricas del grafo son correctas.

- [ ] T196 Implementar `src/graph_plaft/observability/metrics.py` con `PipelineMetrics` que acumula métricas de cada etapa y produce el bloque `metrics` del RunManifest
- [ ] T197 [P] Implementar en `src/graph_plaft/observability/metrics.py` métricas de ingesta: row_count por dataset, tiempo de carga, checksum
- [ ] T198 [P] Implementar métricas del grafo en `src/graph_plaft/observability/metrics.py`: nodes por tipo, edges por tipo, densidad, community_count, connected_components
- [ ] T199 [P] Implementar métricas de variables: variables_generated por categoría, tiempo de generación, count de nulos por variable
- [ ] T200 Implementar `src/graph_plaft/observability/run_manifest.py` método `to_json()` y validación de campos completos antes de persistir
- [ ] T201 [P] Implementar consultas Athena de monitoreo en `scripts/athena_queries/run_metrics.sql`: comparar métricas entre dos run_ids
- [ ] T202 [P] Crear `tests/unit/test_run_manifest.py`: manifest con campos completos pasa validación; manifest con campo faltante lanza error descriptivo

---

## Fase 18 — SageMaker Processing Jobs

**Propósito**: Empaquetar cada etapa como job independiente de SageMaker Processing (plan Fase 7/8).

**Entregable verificable**: Cada script puede ejecutarse localmente con `--config config/local.yaml` y producir
el mismo resultado que en AWS; smoke test en entorno de prepro pasa.

- [ ] T203 Crear `jobs/run_selection.py`: entrada (datasets de señales), argumentos (run_id, fecha_corte, criterios JSON, profundidad), salida S3 `clientes_objetivo.parquet`, logging CloudWatch, idempotente
- [ ] T204 [P] Crear `jobs/run_validation.py`: valida todos los datasets, produce `quality_report.json`, falla con exit≠0 en error crítico
- [ ] T205 Crear `jobs/run_graph_build.py`: orquesta Fases 5-6, produce tablas de nodos/aristas en S3, acepta `--depth` parametrizable
- [ ] T206 [P] Crear `jobs/run_persistence.py`: persiste tablas versionadas, actualiza Glue Catalog (configurable), registra en MLflow (configurable)
- [ ] T207 Crear `jobs/run_analytics.py`: ejecuta algoritmos obligatorios del MVP según ADR-007, acepta `--algorithms` (lista), persiste resultados, loguea tiempo por algoritmo
- [ ] T208 Crear `jobs/run_variables.py`: genera las 8 categorías, garantiza esquema completo (nulos documentados), persiste en S3
- [ ] T209 [P] Crear `jobs/run_feature_store.py`: publica variables en SageMaker Feature Store Offline; stub local para CI
- [ ] T210 [P] Crear `jobs/run_query_artifacts.py`: genera tablas optimizadas para Athena, actualiza vistas en Glue
- [ ] T211 Crear `scripts/run_pipeline_local.sh`: ejecuta los 8 jobs en secuencia con `config/local.yaml` y datos sintéticos
- [ ] T212 [P] Crear `tests/integration/test_jobs_smoke.py`: cada job importa correctamente y acepta `--help` sin error (smoke test de CLI)

---

## Fase 19 — Glue y Athena

**Propósito**: Registrar artefactos en AWS Glue Data Catalog y definir consultas analíticas en Athena.

**Entregable verificable**: Las definiciones de tablas Glue son correctas; las consultas de validación
retornan resultados coherentes con los datos sintéticos.

- [ ] T213 Crear `scripts/glue/register_tables.py` con definiciones de tablas Glue para: nodes_cliente, nodes_cuenta, edges_transfiere_a, variables_estructurales, audit_log, run_manifest; configurable por entorno
- [ ] T214 [P] Crear `scripts/athena_queries/validate_graph.sql`: consulta que verifica count de nodos y aristas del último run
- [ ] T215 [P] Crear `scripts/athena_queries/validate_variables.sql`: consulta que verifica count de variables por categoría y detecta variables faltantes
- [ ] T216 [P] Crear `scripts/athena_queries/audit_summary.sql`: reporte de acciones de analistas por período
- [ ] T217 [P] Crear `docs/infraestructura_aws.md` con instrucciones de despliegue: permisos IAM mínimos, políticas S3, creación de Feature Group; separado del código

---

## Fase 20 — Rendimiento y Escalabilidad

**Propósito**: Verificar que el pipeline escala a millones de transacciones con tiempos aceptables.

**Entregable verificable**: El pipeline completo (selección → variables) con dataset de 1M transferencias
completa en < 4 horas en una instancia ml.m5.4xlarge; tiempos registrados por fase.

- [ ] T218 Crear `tests/performance/test_validation_scale.py`: benchmark de validación sobre 100k, 500k, 1M filas; registrar tiempo y memoria
- [ ] T219 [P] Crear `tests/performance/test_graph_build_scale.py`: benchmark de construcción del subgrafo con N clientes objetivo y N contrapartes
- [ ] T220 [P] Crear `tests/performance/test_analytics_scale.py`: benchmark de PageRank, Connected Components y Louvain sobre grafos de 10k, 50k, 100k nodos
- [ ] T221 [P] Crear `tests/performance/test_variable_generation_scale.py`: benchmark de generación de las 8 categorías sobre subgrafo de 50k clientes
- [ ] T222 Crear `scripts/generate_scale_data.py`: genera datos sintéticos a escala controlada (argumento `--scale` en N_clientes, N_transferencias) con semilla fija
- [ ] T223 [P] Crear `docs/performance_benchmarks.md` con resultados de benchmarks, instancias usadas, tiempos observados, cuellos de botella identificados y recomendaciones

---

## Fase 21 — Pruebas End-to-End

**Propósito**: Validar el sistema completo con escenarios representativos de uso real.

**Entregable verificable**: Los 12 escenarios E2E producen resultados correctos y verificables.

- [ ] T224 [US1] [US2] [US3] Crear `tests/integration/e2e/test_scenario_alerta.py`: cliente sospechoso por alerta → subgrafo correcto → variables → trazabilidad → auditoría
- [ ] T225 [P] [US1] Crear `tests/integration/e2e/test_scenario_ros.py`: cliente con ROS → seleccionado → subgrafo → `distancia_min_ros=0` (el mismo cliente tiene ROS)
- [ ] T226 [P] [US1] Crear `tests/integration/e2e/test_scenario_pep.py`: cliente PEP vigente → seleccionado; PEP expirado → no seleccionado; variable `contrapartes_con_pep` correcta
- [ ] T227 [P] [US1] Crear `tests/integration/e2e/test_scenario_multiples_criterios.py`: cliente con alerta+ROS+caso → todos los criterios en `motivos_seleccion`; señales diferenciadas en variables
- [ ] T228 [US4] Crear `tests/integration/e2e/test_scenario_sin_transferencias.py`: cliente sospechoso sin TX → subgrafo con señales; variables de flujo = 0 documentado; herramienta muestra ausencia sin error
- [ ] T229 [P] [US1] Crear `tests/integration/e2e/test_scenario_cuenta_compartida.py`: cuenta con 2 titulares → 2 nodos cliente distintos → relaciones de titularidad independientes
- [ ] T230 [P] [US4] Crear `tests/integration/e2e/test_scenario_contraparte_riesgosa.py`: contraparte directa tiene ROS → visible con señal en herramienta → variable `contrapartes_con_ros=1`
- [ ] T231 [P] [US4] Crear `tests/integration/e2e/test_scenario_documentos.py`: cliente con 3 documentos (1 sin referencia_s3) → 3 nodos Documento → herramienta muestra indicador de referencia faltante
- [ ] T232 [US4] Crear `tests/integration/e2e/test_scenario_no_autorizado.py`: analista sin permiso consulta cliente → AccessDeniedError → entrada de auditoría con resultado='denied'
- [ ] T233 [US7] Crear `tests/integration/e2e/test_reproduccion_historica.py`: persiste run_A, ejecuta run_B con mismos parámetros → checksums de variables idénticos; run_A recuperable por `run_id`
- [ ] T234 [US7] Crear `tests/integration/e2e/test_idempotencia.py`: re-ejecutar pipeline con mismo `run_id` produce mismo resultado; no crea entradas duplicadas en auditoría
- [ ] T235 [US4] Crear `tests/integration/e2e/test_multiple_tx_same_pair.py`: 3 TX entre cuenta_A y cuenta_B → 3 aristas en grafo; variables de flujo suman los 3 montos correctamente

---

## Fase 22 — Documentación y Operación

**Propósito**: Documentación operacional completa para analistas, ingenieros y auditores.

**Entregable verificable**: Un analista nuevo puede seguir `docs/guia_analista.md` y realizar una consulta
exitosa en entorno local con datos sintéticos.

- [ ] T236 [P] Crear `README.md` en raíz del repositorio: propósito, arquitectura en diagrama, prereqs, instalación, ejecución local, referencias
- [ ] T237 [P] Crear `docs/guia_local.md`: setup local paso a paso, configuración, ejecución del pipeline sintético, verificación de resultados
- [ ] T238 [P] Crear `docs/guia_aws.md`: despliegue en SageMaker, permisos IAM mínimos, ejecución de jobs, monitoreo; incluye instrucción de NO poner credenciales en el repo
- [ ] T239 [P] Crear `docs/catalogo_variables.md`: catálogo completo de variables MVP con nombre, definición, categoría, fórmula, ventana, costo y estado (generado desde `VariableCatalog`)
- [ ] T240 [P] Crear `docs/modelo_grafo.md`: descripción del modelo de nodos y relaciones con tablas, atributos y diagrama textual
- [ ] T241 [P] Crear `docs/guia_consultas.md`: ejemplos de consultas Athena sobre las tablas del grafo
- [ ] T242 [P] Actualizar `docs/guia_analista.md` (creada en T180) con escenarios de uso, capturas conceptuales y preguntas frecuentes
- [ ] T243 [P] Crear `docs/runbook.md`: procedimiento de ejecución normal, re-ejecución parcial, rollback, resolución de errores comunes
- [ ] T244 [P] Crear `docs/limitaciones_mvp.md`: lista explícita de qué NO hace el MVP (GraphRAG, LLM, Neo4j, grafo completo, etc.) y backlog futuro
- [ ] T245 [P] Crear `docs/controles_seguridad.md`: resumen de controles implementados, roles IAM, gestión de secretos, auditoría y retención

---

## Diagrama de Dependencias

```
Fase 0: Preparación
    ↓
Fase 1: Contratos y Modelos de Datos
    ↓
Fase 2: Datos Sintéticos
    ↓
Fase 3: Ingesta y Validación
    ↓
Fase 4: Selección de Clientes Sospechosos
    ↓
Fase 5: Resolución de Identidades y Expansión
    ↓
Fase 6: Construcción del Subgrafo
    ↓
Fase 7: Persistencia y Versionado     ←──────── Fase 10: Integridad Temporal
    ↓                                                     ↑
    ├──→ Fase 8: Graph Analytics ────────────────────────┤
    │         ↓                                           │
    │    Fase 9: Variables Estructurales ─────────────────┘
    │         ↓
    │    Fase 11: Persistencia de Variables
    │         ↓
    │    Fase 12: SageMaker Feature Store ──→ Fase 5 (US5: Consumo)
    │
    └──→ Fase 13: Consultas y Explicación
              ↓
         Fase 14: Herramienta del Analista
              ↓
         Fase 15: Seguridad y Autorización
              ↓
         Fase 16: Auditoría
              ↓
         Fase 17: Observabilidad y Manifiestos
              ↓
         Fase 18: SageMaker Processing Jobs
              ↓
         Fase 19: Glue y Athena
              ↓
         Fase 20: Rendimiento y Escalabilidad
              ↓
         Fase 21: Pruebas End-to-End
              ↓
         Fase 22: Documentación y Operación
```

**Tareas paralelas dentro de fases**: Ver etiquetas `[P]` en cada tarea.

---

## Incrementos Funcionales

### Incremento 1 — Subgrafo Sintético
Tareas: T001–T096 (Fases 0–6)
**Verificación**: `python scripts/run_pipeline_local.sh --synthetic` produce tablas de nodos y aristas correctas para el patrón de estrella.

### Incremento 2 — Grafo Persistido y Recuperable
Tareas: T097–T106 (Fase 7)
**Verificación**: `GraphStore.load(version)` retorna grafo con checksum idéntico al persisitido.

### Incremento 3 — Métricas y Variables Base
Tareas: T107–T146 + T139–T146 (Fases 8–10)
**Verificación**: Variables de centralidad, flujo y conectividad para todos los clientes sintéticos coinciden con `expected_outputs/`.

### Incremento 4 — Señales de Riesgo Integradas
Tareas: T131–T133 (variables de riesgo dentro de Fase 9)
**Verificación**: `contrapartes_con_ros`, `distancia_min_alerta`, etc. con valores correctos y diferenciación de señales.

### Incremento 5 — Consulta desde Interfaz Interna
Tareas: T147–T179 (Fases 11–14)
**Verificación**: Analista busca cliente en Streamlit local y ve subgrafo, transferencias y variables correctamente.

### Incremento 6 — Documentos, Autorización y Auditoría
Tareas: T181–T202 (Fases 15–17)
**Verificación**: Acceso denegado logueado; documentos sin referencia muestran indicador; log de auditoría completo.

### Incremento 7 — Pipeline en SageMaker Processing
Tareas: T203–T217 (Fases 18–19)
**Verificación**: Jobs ejecutan en SageMaker con datos reales anonimizados; artefactos accesibles desde Athena.

### Incremento 8 — Variables en Feature Store Offline
Tareas: T152–T157 (Fase 12)
**Verificación**: `batch_get_record` retorna variables correctas con `event_time=fecha_corte`.

---

## Cobertura de User Stories

| User Story | Fases | Tareas clave |
|-----------|-------|-------------|
| US1: Construcción del Subgrafo | 4, 5, 6 | T062–T096 |
| US2: Persistencia del Grafo | 7 | T097–T106 |
| US3: Graph Analytics y Variables | 8, 9, 10, 11 | T107–T157 |
| US4: Investigación de Cliente | 13, 14 | T158–T180 |
| US5: Consumo por Modelos | 12 | T152–T157 |
| US6: Explicabilidad y Trazabilidad | 13 | T158–T166 |
| US7: Reproducibilidad Histórica | 7, 21 | T106, T233, T234 |

## Cobertura de Requisitos Funcionales

| FR | Tarea(s) |
|----|---------|
| FR-001 (criterios de selección) | T062–T074 |
| FR-002 (datasets de entrada) | T019–T020, T044–T048 |
| FR-003 (nuevos datasets sin rediseño) | T044 (DataEngine abstracto) |
| FR-004–006 (validación) | T049–T061 |
| FR-007 (subgrafo profundidad configurable) | T078–T083 |
| FR-008 (nodo Cliente unificado) | T084 |
| FR-009–011 (relaciones) | T087–T092 |
| FR-012 (documentos) | T086, T172 |
| FR-013 (profundidad configurable) | T079 |
| FR-014–015 (persistencia versionada) | T097–T106 |
| FR-016–019 (Graph Analytics) | T107–T123 |
| FR-020–024 (variables) | T124–T138 |
| FR-025–026 (persistencia variables) | T147–T151 |
| FR-027–038 (herramienta) | T167–T180 |
| FR-039–040 (consultas) | T158–T166 |
| FR-041–042 (reproducibilidad) | T106, T233–T234 |
| FR-043 (métricas operacionales) | T196–T202 |

## Cobertura de Requisitos de Seguridad

| SA / RNF Seguridad | Tarea(s) |
|-------------------|---------|
| SA-001 (solo infraestructura interna) | T217, T237 |
| SA-002 (log de auditoría completo) | T189–T195 |
| SA-003 (mínimo privilegio) | T181–T188 |
| SA-004 (no exponer datos no autorizados) | T159, T181 |
| SA-005 (acceso denegado registrado) | T192–T194 |
| SA-006 (sin secretos en repo) | T004, T017, T185 |
| SA-007 (datos dev sintéticos) | T033–T043 |
| RNF-010 (controles de acceso) | T181–T188 |
| RNF-011 (auditoría inmutable) | T189–T195 |

---

## Resumen

| Métrica | Valor |
|---------|-------|
| **Total de tareas** | **245** |
| **Tareas paralelizables [P]** | ~105 |
| **Fases** | 23 (0–22) |
| **User Stories cubiertas** | 7/7 |
| **Requisitos funcionales cubiertos** | 43/43 |
| **Requisitos de seguridad cubiertos** | 9/9 |

| Fase | Tareas |
|------|--------|
| 0 — Preparación | T001–T017 (17) |
| 1 — Contratos | T018–T032 (15) |
| 2 — Datos Sintéticos | T033–T043 (11) |
| 3 — Ingesta y Validación | T044–T061 (18) |
| 4 — Selección | T062–T074 (13) |
| 5 — Resolución y Expansión | T075–T083 (9) |
| 6 — Construcción | T084–T096 (13) |
| 7 — Persistencia Grafo | T097–T106 (10) |
| 8 — Graph Analytics | T107–T123 (17) |
| 9 — Variables | T124–T138 (15) |
| 10 — Integridad Temporal | T139–T146 (8) |
| 11 — Persistencia Variables | T147–T151 (5) |
| 12 — Feature Store | T152–T157 (6) |
| 13 — Consultas | T158–T166 (9) |
| 14 — Herramienta | T167–T180 (14) |
| 15 — Seguridad | T181–T188 (8) |
| 16 — Auditoría | T189–T195 (7) |
| 17 — Observabilidad | T196–T202 (7) |
| 18 — SageMaker Jobs | T203–T212 (10) |
| 19 — Glue y Athena | T213–T217 (5) |
| 20 — Rendimiento | T218–T223 (6) |
| 21 — E2E | T224–T235 (12) |
| 22 — Documentación | T236–T245 (10) |

**Camino crítico**: T001 → T018 → T033 → T044 → T062 → T075 → T084 → T097 → T107 → T124 → T147 → T158 → T167 → T181 → T189 → T203 → T224

**Primer incremento implementable**: Tareas T001–T043 (Fases 0–2) son completamente independientes de AWS.
