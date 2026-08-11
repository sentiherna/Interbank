# Implementation Plan: Grafo Transaccional para Investigacion PLAFT

**Branch**: `002-plaft-investigation-graph` | **Date**: 2026-08-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-plaft-investigation-graph/spec.md`

**Constitucion aplicable**: v4.0.0

---

## Summary

Construir un flujo investigativo PLAFT orientado a producir un expediente de caso
investigado con evidencia trazable y reproducible. El grafo transaccional y Graph Analytics
se utilizan como instrumentos para identificar relaciones, patrones y senales que el
analista revisa, interpreta y consolida. Las salidas para modelamiento (variables
estructurales y Feature Store) se mantienen como capacidad secundaria y opcional.

El plan reutiliza de forma obligatoria la infraestructura ya implementada para ingesta,
validacion, mapeo fisico-conceptual, trazabilidad y pruebas, evitando implementaciones
paralelas de los mismos componentes.

---

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas, pyarrow, pyyaml, click, boto3, mlflow, pytest, mypy,
ruff, pyspark (entorno AWS/produccion)

**Storage**: Amazon S3 (datasets, artefactos de grafo, evidencia, manifests), AWS Glue
Data Catalog, Amazon Athena, SageMaker Feature Store (opcional y selectivo)

**Testing**: pytest (unit/integration/contract), mypy strict, ruff lint/format

**Target Platform**: AWS (SageMaker Processing/Pipelines, S3, Glue, Athena) con ejecucion
local de desarrollo sobre datos sinteticos y CSV controlados

**Project Type**: plataforma analitica investigativa + herramienta interna para analistas

**Performance Goals**:
- Procesar lotes de millones de transacciones por corrida en entorno AWS.
- Mantener tiempos de respuesta adecuados para exploracion analitica por caso.
- Garantizar reproducibilidad 1:1 de expediente y evidencia a partir de `run_id`.

**Constraints**:
- Sin datos reales en Git.
- Sin duplicar implementaciones de ingesta/validacion/mapeo ya existentes.
- Senales automaticas no equivalen a conclusion PLAFT.
- Feature Store no puede ser precondicion para operar investigacion.

**Scale/Scope**:
- Fuentes iniciales prioritarias: clientes, cuentas, titularidades, transferencias,
  alertas PLAFT, casos historicos.
- Integracion progresiva: ROS, PEP, productos, documentos, KYC, beneficiarios finales y
  otras relaciones.

---

## Constitution Check

*GATE: verificado contra Constitucion v4.0.0 antes de Fase 0; revalidado post diseno de
Fase 1.*

| Principio Constitucional v4.0.0 | Estado | Evidencia en este plan |
|---------------------------------|--------|-------------------------|
| I. Proposito: investigacion PLAFT y caso con evidencia | PASS | Summary y flujo principal orientado a expediente investigado |
| II. Plataforma AWS oficial | PASS | Contexto tecnico y capas AWS-compatible |
| III. Arquitectura por capas con separacion explicita | PASS | Seccion de 16 capas definidas |
| IV. Datos de entrada multipfuente y extensibles | PASS | Priorizacion inicial + integracion progresiva |
| V. Modelo de grafo centrado en investigacion | PASS | Entidades de caso, hallazgo, evidencia y trazabilidad |
| VI. Calidad de datos con detencion en errores criticos | PASS | Reuso de QualityChecker + reglas criticas |
| VII. Trazabilidad y reproducibilidad | PASS | run_id, graph_version, data_version, evidencia reproducible |
| VIII-IX. Variables y ML como capacidad secundaria | PASS | Capa 16 transversal y opcional; no central en MVP |
| X-XII. Evidencia, casos y explicabilidad | PASS | Dominios investigation/cases, hallazgos y evidencia explicita |
| XIII-XIV. Seguridad y calidad de software | PASS | IAM/minimo privilegio + mypy/ruff/pytest |
| XV-XVIII. Hoja de ruta evolutiva y gobernanza | PASS | Fases 1-8 + capacidad transversal y ADRs alineados |

**Resultado de gate**: PASS. No se identifican violaciones ni excepciones.

---

## Estado de reutilizacion del proyecto 001

Objetivo: reutilizar todo componente compatible y evitar reimplementacion paralela.

### Confirmacion operativa Phase 1 (T001)

Validado en 2026-08-10:

- El alcance de reutilizacion de feature 002 mantiene una sola implementacion para
  configuracion, ingesta, validacion, mapeo fisico-conceptual y observabilidad.
- Las tareas de Phase 1 se limitan a configurar y documentar reutilizacion/adaptacion,
  sin crear pipelines paralelos.

### REUTILIZAR SIN CAMBIOS

| Componente | Ubicacion | Motivo |
|------------|-----------|--------|
| Python 3.12 + tooling base | `pyproject.toml`, `Makefile` | Ya alineado a constitucion y estandares de calidad |
| Configuracion local/AWS | `src/graph_plaft/config/settings.py` | Permite alternar entornos sin duplicar logica |
| Mapeo fisico-conceptual base | `src/graph_plaft/config/column_mapping.py` | Ya contempla traduccion de columnas fisicas |
| Logging y manifest de corrida | `src/graph_plaft/observability/*.py` | Base de trazabilidad y reproducibilidad existente |
| Motores de lectura | `src/graph_plaft/ingestion/pandas_engine.py`, `spark_engine.py` | Mantienen misma interfaz y son compatibles con fase actual |
| Registro de datasets | `src/graph_plaft/ingestion/registry.py` | Evita duplicar inventario de fuentes |
| Carga y metadata/checksum | `src/graph_plaft/ingestion/loaders.py` | Ya resuelve carga + metadatos de origen |
| Calidad y reglas criticas | `src/graph_plaft/validation/quality.py`, `rules.py` | Cumple principio VI sin cambios estructurales |
| Filtros temporales y deduplicacion | `src/graph_plaft/validation/temporal.py`, `deduplication.py` | Requisitos de fecha_corte y PK ya cubiertos |
| Datos sinteticos reproducibles | `scripts/generate_synthetic.py`, `data/synthetic/` | Soporte local deterministico existente |
| Suite de pruebas existente | `tests/contract`, `tests/unit`, `tests/integration` | Base valida para extender cobertura investigativa |

### ADAPTAR

| Componente | Ubicacion | Adaptacion requerida |
|------------|-----------|----------------------|
| Contratos de fuentes | `specs/001-mvp-graph-variables/contracts/` | Reenfocar prioridad de fuentes para feature 002 |
| Esquemas de nodos/relaciones | `src/graph_plaft/graph/node_schemas.py`, `edge_schemas.py` | Extender trazabilidad para caso/hallazgo/evidencia |
| Esquemas de resultados analiticos | `src/graph_plaft/analytics/result_schemas.py` | Mapear salida a hallazgos investigativos |
| CLI de orquestacion | `src/graph_plaft/cli/commands.py` | Incorporar comandos de casos y evidencia |
| Tests de validacion | `tests/integration/test_validation_pipeline.py` | Extender a corridas con fuentes reales progresivas |

### DEPRECAR

| Componente | Estado |
|------------|--------|
| Narrativa de plan centrada en variables como entregable principal | Se reemplaza por enfoque investigacion + evidencia |
| Supuesto de Feature Store como destino principal del pipeline | Se reduce a salida opcional por caso de uso explicito |

### NUEVO

| Dominio/Modulo | Proposito |
|----------------|-----------|
| `src/graph_plaft/patterns/` | Detectores de cadenas, ciclos, hubs, intermediarios, concentracion |
| `src/graph_plaft/investigation/` | Gestion de casos y ciclo de vida investigativo |
| `src/graph_plaft/evidence/` | Modelo y trazabilidad de evidencia reproducible |
| `src/graph_plaft/querying/` (expansion funcional) | Consultas orientadas a caso, hallazgo y evidencia |
| `src/graph_plaft/tool/` (expansion funcional) | Flujo de analista: abrir caso, seleccionar hallazgos, cerrar expediente |

---

## Flujo principal de negocio

Fuentes de datos
-> Ingesta
-> Validacion y calidad
-> Normalizacion / mapeo fisico-conceptual
-> Construccion del grafo transaccional
-> Persistencia y versionado
-> Graph Analytics
-> Deteccion de patrones y senales
-> Investigacion PLAFT
-> Gestion de hallazgos
-> Evidencia trazable
-> Interpretacion del analista
-> Expediente / caso investigado

La plataforma apoya decision analitica; no automatiza conclusion definitiva PLAFT.

---

## Arquitectura por capas (feature 002)

### Capa 1 - Ingesta de fuentes

- Reutiliza `DataEngine`, `PandasEngine`, `SparkEngine`, `load_dataset`, `DatasetRegistry`.
- Soporta CSV locales controlados y migracion a S3 sin cambiar logica de negocio.

### Capa 2 - Validacion y calidad

- Reutiliza `validation/rules.py`, `quality.py`, `temporal.py`, `deduplication.py`.
- Mantiene stop en errores criticos y reporte estructurado de calidad.

### Capa 3 - Normalizacion y mapeo fisico-conceptual

- Reutiliza `config/column_mapping.py` y `validation/contracts.py`.
- Formaliza mapeos por fuente; primer caso real iniciado: `cod_cli -> cliente_id`.

### Capa 4 - Construccion del grafo transaccional

- Adapta contratos de `graph/` para nodos y relaciones investigativas.
- Mantiene trazabilidad por registro fuente, periodo y version de corrida.

### Capa 5 - Persistencia y versionado

- Reutiliza `observability/run_manifest.py` y convenciones de `run_id`.
- Versiona grafo y datasets para reconstruccion exacta.

### Capa 6 - Graph Analytics

- Adapta resultados en `analytics/result_schemas.py`.
- Incluye: grado, PageRank, componentes, comunidades, flujos, distancias.

### Capa 7 - Deteccion de patrones y senales

- Nuevo dominio `patterns/` para cadenas, ciclos, hubs, intermediarios, concentracion,
  anomalias y exposiciones a senales PLAFT.
- Produce senales candidatas para revision humana.

### Capa 8 - Gestion de investigaciones/casos

- Nuevo dominio `investigation/`.
- Distingue casos historicos (fuente contextual) de casos nuevos creados en la
  plataforma.

### Capa 9 - Gestion de hallazgos

- Define entidad `HallazgoAnalitico` con estado revisado/aceptado/descartado,
  comentarios y asociacion a evidencia.

### Capa 10 - Gestion y trazabilidad de evidencia

- Nuevo dominio `evidence/`.
- Garantiza cadena: dato fuente -> hecho de grafo -> patron/senal/hallazgo -> evidencia
  -> interpretacion -> resultado del caso.

### Capa 11 - Consultas analiticas

- Amplia `querying/` para consultas por caso, sujeto, hallazgo y evidencia.
- Mantiene compatibilidad con Athena/Glue y ejecucion local controlada.

### Capa 12 - Visualizacion y exploracion para el analista

- Amplia `tool/` para flujo investigativo guiado por caso/sujeto.
- Tecnologia especifica puede mantenerse en ADR segun validacion corporativa.

### Capa 13 - Seguridad y permisos

- Reutiliza base `security/` y define politicas por caso, sujeto y evidencia.
- Principio de minimo privilegio + separacion datos/documentos.

### Capa 14 - Auditoria

- Reutiliza dominio `audit/` y extiende eventos de investigacion y evidencia.

### Capa 15 - Observabilidad y reproducibilidad

- Reutiliza `observability/` con enriquecimiento de metadatos de casos/hallazgos.

### Capa 16 - Salidas analiticas reutilizables para ML (secundaria)

- Variables estructurales y Feature Store permanecen opcionales y selectivos.
- Publicacion solo cuando exista caso de uso analitico explicito.

---

## Caso investigado: modelo objetivo

Se incorpora dominio explicito `investigation/cases` con `CasoInvestigado`:

- `caso_id`
- `sujeto_id`
- `motivo`
- `fecha_apertura`
- `periodo_analisis`
- `fecha_corte`
- `hipotesis` (una o varias)
- `hallazgos` (referencias)
- `evidencias` (referencias)
- `observaciones_analista`
- `interpretacion`
- `conclusion`
- `resultado`
- `estado`
- `usuario_responsable`
- `created_at`, `updated_at`, `closed_at`
- `graph_version`
- `data_version`
- `run_id`

Estados sugeridos: `abierto`, `en_revision`, `cerrado`, `reabierto`, `archivado`.

---

## Hallazgos analiticos: modelo objetivo

Entidad `HallazgoAnalitico`:

- `hallazgo_id`
- `caso_id`
- `tipo_hallazgo` (relacion_relevante, cadena, ciclo, hub, intermediario,
  concentracion, comunidad, anomalia, exposicion_alerta, exposicion_ros,
  relacion_pep, relacion_caso_historico, otro)
- `descripcion`
- `severidad`
- `origen_algoritmo_o_regla`
- `parametros`
- `estado_revision` (pendiente, aceptado, descartado)
- `comentarios_analista`
- `usuario_revision`
- `timestamp_revision`
- `graph_version`
- `run_id`

Regla de negocio: una senal automatica no implica conclusion.

---

## Evidencia trazable: modelo objetivo

Entidad `Evidencia`:

- `evidencia_id`
- `caso_id`
- `hallazgo_id`
- `entidades_involucradas`
- `relaciones_involucradas`
- `transacciones_involucradas`
- `periodo`
- `fecha_corte`
- `dataset_fuente`
- `clave_registro_fuente`
- `algoritmo_o_regla`
- `parametros`
- `graph_version`
- `run_id`
- `timestamp`
- `usuario_validador`

Requisito de reproducibilidad: toda evidencia debe regenerarse con los mismos insumos,
parametros y versiones.

---

## Integracion progresiva de datos reales

### Principios

- Desarrollo inicial con CSV locales controlados y datos sinteticos.
- Migracion posterior a S3 sin reescribir reglas de negocio.
- Validacion contractual y de calidad antes de integracion al grafo.
- Nunca versionar datos reales en Git.

### Estado actual reconocido

- Integracion iniciada para fuente real `clientes.csv`.
- Mapeo ya definido: `cod_cli -> cliente_id`.

### Orden de priorizacion

1. Clientes
2. Cuentas
3. Titularidades
4. Transferencias
5. Alertas PLAFT
6. Casos historicos

Etapa posterior:

1. ROS
2. PEP
3. Productos
4. Documentos
5. KYC
6. Beneficiarios finales y otras relaciones

---

## Investigacion del analista (capacidad funcional incremental)

Capacidades esperadas por iteracion:

1. Crear o abrir caso.
2. Seleccionar sujeto investigado.
3. Visualizar red del sujeto y vecinos autorizados.
4. Ajustar profundidad y filtros (periodo, monto, direccion entrada/salida).
5. Inspeccionar transacciones y contrapartes.
6. Revisar patrones y senales PLAFT.
7. Aceptar/descartar hallazgos y comentar.
8. Asociar evidencia a hallazgos.
9. Registrar observaciones, interpretacion y conclusion.
10. Cerrar o mantener abierto el caso.
11. Reabrir/reconstruir expediente con trazabilidad completa.

---

## Project Structure

### Documentacion (feature 002)

```text
specs/002-plaft-investigation-graph/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── README.md
    ├── clientes.md
    ├── cuentas.md
    ├── titularidades.md
    ├── transferencias.md
    ├── alertas_plaft.md
    ├── casos_historicos.md
    ├── caso_investigado.md
    ├── hallazgo_analitico.md
    └── evidencia.md
```

### Codigo fuente (estructura real)

```text
src/graph_plaft/
├── cli/
├── config/
├── ingestion/
├── validation/
├── graph/
├── analytics/
├── persistence/
├── querying/
├── security/
├── audit/
├── observability/
├── tool/
├── feature_store/
├── features/
├── population/
├── patterns/          # nuevo
├── investigation/     # nuevo
└── evidence/          # nuevo

tests/
├── contract/
├── integration/
├── unit/
└── performance/
```

**Structure Decision**: se mantiene `src/graph_plaft/` como base unica. Solo se agregan
modulos nuevos donde el dominio lo requiere (`patterns`, `investigation`, `evidence`).

---

## Fases de implementacion (alineadas a Constitucion 4.0.0)

### Fase 1 - Base de datos e ingesta

- Consolidar contratos prioritarios de fuentes.
- Integrar fuentes reales progresivamente via mapeo fisico-conceptual.
- Reusar motores de ingesta y calidad existentes.
- Validar temporalidad, integridad y trazabilidad de carga.

### Fase 2 - Grafo transaccional

- Construir nodos/relaciones investigativas con trazabilidad.
- Persistir versiones del grafo y metadatos de corrida.
- Garantizar reproduccion por `run_id`.

### Fase 3 - Graph Analytics

- Ejecutar metricas y algoritmos orientados a relaciones y patrones.
- Producir salidas para deteccion de hallazgos, no conclusiones automaticas.

### Fase 4 - Investigacion PLAFT

- Implementar dominio de casos (`investigation`).
- Incorporar ciclo de revision de hallazgos y estado de caso.

### Fase 5 - Evidencia y explicabilidad

- Implementar dominio `evidence` con cadena de trazabilidad completa.
- Consolidar expediente reproducible con interpretacion del analista.

### Fase 6 - Enriquecimiento

- Agregar ROS, PEP, documentos, KYC, beneficiarios y relaciones avanzadas.

### Fase 7 - GraphRAG

- Diseñar consultas sobre grafo + evidencia + documentacion.
- No incluido en el MVP de esta feature.

### Fase 8 - Asistente inteligente PLAFT

- Soporte conversacional con evidencia y politicas de abstencion.
- No incluido en el MVP de esta feature.

### Capacidad transversal

- Variables para ML y publicacion selectiva en Feature Store cuando exista caso de uso
  explicito.

---

## Alcance MVP de esta feature

El MVP de la feature 002 se enfoca en demostrar:

1. Flujo investigativo de extremo a extremo.
2. Gestion de caso investigado con interpretacion humana.
3. Evidencia trazable y reproducible.
4. Reuso de infraestructura existente sin duplicaciones.

Fuera de alcance MVP:

- Implementacion completa de GraphRAG.
- Implementacion de asistente inteligente PLAFT.
- Publicacion masiva de variables sin caso de uso explicito.

---

## Riesgos principales y mitigaciones

| ID | Riesgo | Impacto | Mitigacion |
|----|--------|---------|------------|
| R-01 | Divergencia entre fuentes reales y contratos definidos | Alto | Validacion incremental por fuente + ajuste de mapeo sin tocar logica |
| R-02 | Sobrepeso de pipeline en calculos de patrones complejos | Medio/Alto | Priorizacion por valor investigativo + ejecucion incremental de detectores |
| R-03 | Confusion entre senal automatica y conclusion final | Alto | Reglas explicitas de revision humana en dominio de hallazgos |
| R-04 | Feature Store asumido como obligatorio | Medio | Capa 16 opcional y desacoplada del flujo principal |
| R-05 | Riesgo de fuga de datos reales en repositorio | Critico | Politicas de exclusiones y uso de rutas externas a Git |

---

## Artefactos generados por /speckit-plan

| Archivo | Estado | Objetivo |
|---------|--------|----------|
| `plan.md` | Completo | Plan tecnico alineado a feature 002 |
| `research.md` | Completo | Decisiones y racionales de arquitectura y reutilizacion |
| `data-model.md` | Completo | Modelo de datos de caso, hallazgo y evidencia |
| `quickstart.md` | Completo | Guia de validacion end-to-end del MVP |
| `contracts/*` | Completo | Contratos de fuentes prioritarias y dominios investigativos |

`tasks.md` no se genera en esta etapa.

---

## Re-check constitucional post diseno de Fase 1

Resultado: PASS.

- El flujo principal mantiene investigacion + evidencia como objetivo.
- Se evita arquitectura paralela de componentes ya implementados.
- Variables/Feature Store quedan como capacidad secundaria y opcional.
- El diseno usa estructura real `src/graph_plaft/` y mantiene plataforma AWS oficial.

