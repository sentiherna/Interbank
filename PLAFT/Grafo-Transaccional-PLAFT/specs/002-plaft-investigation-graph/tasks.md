# Tasks: Grafo Transaccional para Investigacion PLAFT

**Input**: Design documents from `specs/002-plaft-investigation-graph/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Se incluyen tareas de pruebas por historia para mantener validacion independiente por incremento.

**Organization**: Tareas agrupadas por fase y por historia de usuario (US1-US4), con priorizacion investigacion-first y reutilizacion explicita del trabajo existente.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: puede ejecutarse en paralelo (archivos distintos, sin dependencia directa)
- `[Story]`: etiqueta de historia (`[US1]`, `[US2]`, `[US3]`, `[US4]`) solo en fases de historias
- Marcadores de reutilizacion en descripcion: REUSE, ADAPT, NEW

---

## Phase 1: Setup (Shared Alignment)

**Purpose**: Alinear la feature 002 con la base existente sin duplicar infraestructura ya implementada.

- [X] T001 REUSE: Confirmar alcance de reutilizacion y actualizar matriz en `specs/002-plaft-investigation-graph/plan.md`
- [X] T002 REUSE: Verificar configuracion activa de feature en `.specify/feature.json`
- [X] T003 ADAPT: Crear mapa inicial de fuentes reales prioritarias en `config/local.yaml`
- [X] T004 ADAPT: Registrar mapeos fisico-conceptuales prioritarios en `src/graph_plaft/config/column_mapping.py`
- [X] T005 REUSE: Validar baseline de calidad ejecutando criterios de `specs/002-plaft-investigation-graph/quickstart.md`
- [X] T006 REUSE: Documentar decision de no duplicacion de ingesta/validacion en `specs/002-plaft-investigation-graph/research.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Adaptaciones base necesarias antes de cualquier historia.

**CRITICAL**: Ninguna historia inicia hasta cerrar esta fase.

- [ ] T007 ADAPT: Extender definiciones de fuentes prioritarias en `src/graph_plaft/ingestion/registry.py`
- [ ] T008 [P] ADAPT: Ajustar contratos de entrada para fuentes prioritarias en `src/graph_plaft/validation/contracts.py`
- [ ] T009 [P] ADAPT: Incorporar reglas de dominios y obligatoriedad por fuente en `src/graph_plaft/validation/rules.py`
- [ ] T010 ADAPT: Asegurar control temporal por `fecha_corte` para nuevas fuentes en `src/graph_plaft/validation/temporal.py`
- [ ] T011 [P] ADAPT: Configurar deduplicacion por claves de negocio (incluyendo `id_transaccion`) en `src/graph_plaft/validation/deduplication.py`
- [ ] T012 ADAPT: Extender esquema de run manifest con versionado de caso/evidencia en `src/graph_plaft/observability/run_manifest.py`
- [ ] T013 [P] ADAPT: Agregar pruebas contractuales de fuentes prioritarias en `tests/contract/test_input_schemas.py`
- [ ] T014 ADAPT: Agregar prueba de integracion de validacion para fuentes reales progresivas en `tests/integration/test_validation_pipeline.py`

**Checkpoint**: Ingesta, validacion, temporalidad y trazabilidad base listas para implementar historias.

---

## Phase 3: User Story 1 - Investigar un caso con evidencia trazable (Priority: P1) MVP

**Goal**: Permitir investigacion del sujeto sobre grafo transaccional y generar evidencia trazable vinculada a hallazgos.

**Independent Test**: Cargar fuentes prioritarias, construir grafo, detectar hallazgos y verificar evidencia trazable al dato fuente con `run_id` y `graph_version`.

### Tests for User Story 1

- [ ] T015 [P] [US1] NEW: Crear pruebas unitarias de construccion de grafo investigativo en `tests/unit/test_graph_build_investigation.py`
- [ ] T016 [P] [US1] NEW: Crear pruebas unitarias de deteccion de patrones base en `tests/unit/test_patterns_detectors.py`
- [ ] T017 [P] [US1] NEW: Crear pruebas de contrato de evidencia trazable en `tests/contract/test_evidence_schema.py`
- [ ] T018 [US1] NEW: Crear prueba de integracion de flujo investigacion-evidencia en `tests/integration/test_us1_investigation_flow.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] ADAPT: Extender esquemas de nodos para trazabilidad investigativa en `src/graph_plaft/graph/node_schemas.py`
- [ ] T020 [P] [US1] ADAPT: Extender esquemas de relaciones transaccionales en `src/graph_plaft/graph/edge_schemas.py`
- [ ] T021 [US1] NEW: Implementar constructor de subgrafo transaccional en `src/graph_plaft/graph/builder.py`
- [ ] T022 [P] [US1] ADAPT: Extender resultados analiticos base (grado, pagerank, componentes, comunidades) en `src/graph_plaft/analytics/result_schemas.py`
- [ ] T023 [US1] NEW: Implementar detectores de patrones y senales iniciales en `src/graph_plaft/patterns/detectors.py`
- [ ] T024 [P] [US1] NEW: Implementar modelo de `HallazgoAnalitico` en `src/graph_plaft/investigation/hallazgo.py`
- [ ] T025 [P] [US1] NEW: Implementar modelo de `Evidencia` con cadena de trazabilidad en `src/graph_plaft/evidence/evidence_schema.py`
- [ ] T026 [US1] NEW: Implementar servicio de vinculacion hallazgo-evidencia en `src/graph_plaft/evidence/evidence_service.py`
- [ ] T027 [US1] ADAPT: Integrar ejecucion investigativa en CLI para flujo base en `src/graph_plaft/cli/commands.py`
- [ ] T028 [US1] ADAPT: Registrar metadatos de reproducibilidad de evidencia en `src/graph_plaft/observability/run_manifest.py`

**Checkpoint**: US1 funcional y validable de forma independiente como MVP tecnico.

---

## Phase 4: User Story 2 - Documentar y cerrar una investigacion (Priority: P1)

**Goal**: Permitir registrar observaciones, interpretacion, conclusion y resultado en expediente reproducible del caso.

**Independent Test**: Crear caso, revisar hallazgos, registrar interpretacion/conclusion y cerrar caso validando trazabilidad completa.

### Tests for User Story 2

- [ ] T029 [P] [US2] NEW: Crear pruebas unitarias de transiciones de estado de caso en `tests/unit/test_case_state_machine.py`
- [ ] T030 [P] [US2] NEW: Crear pruebas unitarias de validacion de cierre de caso en `tests/unit/test_case_closure_rules.py`
- [ ] T031 [P] [US2] NEW: Crear pruebas de contrato de expediente de caso en `tests/contract/test_case_schema.py`
- [ ] T032 [US2] NEW: Crear prueba de integracion de cierre de investigacion en `tests/integration/test_us2_case_closure.py`

### Implementation for User Story 2

- [ ] T033 [P] [US2] NEW: Implementar modelo `CasoInvestigado` en `src/graph_plaft/investigation/case_schema.py`
- [ ] T034 [P] [US2] NEW: Implementar repositorio de casos con versionado en `src/graph_plaft/investigation/case_repository.py`
- [ ] T035 [US2] NEW: Implementar servicio de ciclo de vida del caso en `src/graph_plaft/investigation/case_service.py`
- [ ] T036 [US2] ADAPT: Extender auditoria de acciones del analista sobre casos en `src/graph_plaft/audit/audit_schema.py`
- [ ] T037 [US2] ADAPT: Agregar comandos CLI para abrir, actualizar y cerrar casos en `src/graph_plaft/cli/commands.py`

**Checkpoint**: US2 funcional y comprobable sin depender de US3/US4.

---

## Phase 5: User Story 3 - Explorar relaciones y patrones para soporte analitico (Priority: P2)

**Goal**: Permitir exploracion analitica por sujeto/caso, consultas de red y revision operativa de hallazgos.

**Independent Test**: Consultar sujeto y caso, visualizar relaciones y patrones detectados, y priorizar hipotesis con evidencia asociada.

### Tests for User Story 3

- [ ] T038 [P] [US3] NEW: Crear pruebas unitarias de consultas de red por profundidad en `tests/unit/test_querying_network.py`
- [ ] T039 [P] [US3] NEW: Crear pruebas unitarias de filtros (periodo/monto/direccion) en `tests/unit/test_querying_filters.py`
- [ ] T040 [P] [US3] NEW: Crear pruebas de integracion de exploracion investigativa en `tests/integration/test_us3_exploration.py`

### Implementation for User Story 3

- [ ] T041 [P] [US3] ADAPT: Implementar consultas por caso/sujeto/hallazgo en `src/graph_plaft/querying/case_queries.py`
- [ ] T042 [P] [US3] NEW: Implementar consultas de patrones y senales en `src/graph_plaft/querying/pattern_queries.py`
- [ ] T043 [US3] ADAPT: Implementar servicio de exploracion de red en `src/graph_plaft/tool/exploration_service.py`
- [ ] T044 [US3] NEW: Implementar flujo de seleccion de hallazgos y comentarios de revision en `src/graph_plaft/tool/hallazgo_review.py`
- [ ] T045 [US3] ADAPT: Aplicar control de permisos por sujeto/caso en `src/graph_plaft/security/access_control.py`
- [ ] T046 [US3] ADAPT: Extender logging de consultas investigativas en `src/graph_plaft/observability/logging.py`
- [ ] T047 [US3] ADAPT: Integrar comandos CLI de exploracion investigativa en `src/graph_plaft/cli/commands.py`

**Checkpoint**: US3 funcional con exploracion independiente y trazable.

---

## Phase 6: User Story 4 - Reutilizar resultados para monitoreo y modelos (Priority: P3)

**Goal**: Habilitar salida secundaria de metricas seleccionadas para analitica avanzada, sin bloquear flujo investigativo principal.

**Independent Test**: Seleccionar metricas explicitas, exportarlas con trazabilidad y validar operacion completa aun sin Feature Store habilitado.

### Tests for User Story 4

- [ ] T048 [P] [US4] NEW: Crear pruebas unitarias de seleccion de metricas reutilizables en `tests/unit/test_reusable_metrics_selection.py`
- [ ] T049 [P] [US4] NEW: Crear pruebas de contrato de artefacto reutilizable en `tests/contract/test_reusable_output_schema.py`
- [ ] T050 [US4] NEW: Crear prueba de integracion de export opcional a Feature Store en `tests/integration/test_us4_optional_feature_store.py`

### Implementation for User Story 4

- [ ] T051 [P] [US4] ADAPT: Implementar selector de metricas con caso de uso explicito en `src/graph_plaft/features/selection_policy.py`
- [ ] T052 [US4] ADAPT: Implementar export de artefactos reutilizables en `src/graph_plaft/features/reusable_export.py`
- [ ] T053 [US4] ADAPT: Hacer opcional la publicacion en Feature Store en `src/graph_plaft/feature_store/publisher.py`
- [ ] T054 [US4] ADAPT: Incorporar comando CLI para export secundario de metricas en `src/graph_plaft/cli/commands.py`

**Checkpoint**: US4 habilitada como capacidad secundaria y no bloqueante.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cierre transversal de calidad, documentacion y preparacion arquitectonica.

- [ ] T055 [P] ADAPT: Actualizar guia de ejecucion y validacion en `specs/002-plaft-investigation-graph/quickstart.md`
- [ ] T056 [P] ADAPT: Actualizar decisiones y supuestos en `specs/002-plaft-investigation-graph/research.md`
- [ ] T057 ADAPT: Ejecutar y registrar verificacion completa (`ruff`, `mypy`, `pytest`) en `specs/002-plaft-investigation-graph/quickstart.md`
- [ ] T058 [P] NEW: Agregar nota de preparacion arquitectonica GraphRAG (sin implementacion) en `docs/adr/README.md`
- [ ] T059 [P] NEW: Agregar nota de preparacion arquitectonica asistente PLAFT (sin implementacion) en `docs/adr/README.md`
- [ ] T060 ADAPT: Actualizar trazabilidad final de reutilizacion/adaptacion/nuevo en `specs/002-plaft-investigation-graph/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: inicia de inmediato.
- **Phase 2 (Foundational)**: depende de Phase 1 y bloquea todas las historias.
- **Phase 3 (US1)**: depende de Phase 2.
- **Phase 4 (US2)**: depende de Phase 3 para usar hallazgos/evidencia en cierre de caso.
- **Phase 5 (US3)**: depende de Phase 3; puede avanzar parcialmente en paralelo con US2 tras T041-T042.
- **Phase 6 (US4)**: depende de Phase 3 y de contratos de salida definidos en US2/US3.
- **Phase 7 (Polish)**: depende de historias objetivo completadas.

### User Story Dependencies

- **US1 (P1)**: base MVP investigacion + evidencia.
- **US2 (P1)**: requiere artefactos de US1 para documentar y cerrar caso.
- **US3 (P2)**: consume base de US1 y puede convivir con US2 en iteraciones.
- **US4 (P3)**: capacidad secundaria; no bloquea US1-US3.

### Parallel Opportunities

- Setup paralelizable: `T003-T006`.
- Foundational paralelizable: `T008-T011`, `T013-T014`.
- US1 paralelizable: `T015-T017`, `T019-T020`, `T024-T025`.
- US2 paralelizable: `T029-T031`, `T033-T034`.
- US3 paralelizable: `T038-T040`, `T041-T042`.
- US4 paralelizable: `T048-T049`, `T051`.
- Polish paralelizable: `T055-T056`, `T058-T059`.

---

## Parallel Example: User Story 1

```bash
Task: "T015 [US1] tests/unit/test_graph_build_investigation.py"
Task: "T016 [US1] tests/unit/test_patterns_detectors.py"
Task: "T017 [US1] tests/contract/test_evidence_schema.py"

Task: "T019 [US1] src/graph_plaft/graph/node_schemas.py"
Task: "T020 [US1] src/graph_plaft/graph/edge_schemas.py"
Task: "T024 [US1] src/graph_plaft/investigation/hallazgo.py"
Task: "T025 [US1] src/graph_plaft/evidence/evidence_schema.py"
```

## Parallel Example: User Story 2

```bash
Task: "T029 [US2] tests/unit/test_case_state_machine.py"
Task: "T030 [US2] tests/unit/test_case_closure_rules.py"
Task: "T031 [US2] tests/contract/test_case_schema.py"

Task: "T033 [US2] src/graph_plaft/investigation/case_schema.py"
Task: "T034 [US2] src/graph_plaft/investigation/case_repository.py"
```

## Parallel Example: User Story 3

```bash
Task: "T038 [US3] tests/unit/test_querying_network.py"
Task: "T039 [US3] tests/unit/test_querying_filters.py"

Task: "T041 [US3] src/graph_plaft/querying/case_queries.py"
Task: "T042 [US3] src/graph_plaft/querying/pattern_queries.py"
```

## Parallel Example: User Story 4

```bash
Task: "T048 [US4] tests/unit/test_reusable_metrics_selection.py"
Task: "T049 [US4] tests/contract/test_reusable_output_schema.py"

Task: "T051 [US4] src/graph_plaft/features/selection_policy.py"
Task: "T053 [US4] src/graph_plaft/feature_store/publisher.py"
```

---

## Implementation Strategy

### MVP First (US1)

1. Completar Phase 1 y Phase 2.
2. Completar US1 (Phase 3).
3. Validar flujo extremo a extremo de investigacion + evidencia.
4. Congelar baseline MVP antes de US2.

### Incremental Delivery

1. US1: investigacion y evidencia trazable.
2. US2: expediente, interpretacion, conclusion y cierre de caso.
3. US3: exploracion analitica avanzada para analista.
4. US4: salidas secundarias para modelamiento (opcional).

### Scope Guardrails

- No crear implementacion paralela de ingesta, validacion o mapeo.
- No hacer GraphRAG ni asistente inteligente en MVP.
- Mantener Feature Store desacoplado y opcional.

---

## Notes

- Todas las tareas siguen formato checklist con ID secuencial, etiquetas y ruta de archivo.
- El orden de fases respeta dependencias y prioridad de negocio definida en la especificacion.
- La clasificacion `[REUSE]`, `[ADAPT]`, `[NEW]` identifica claramente el tratamiento del trabajo previo.


