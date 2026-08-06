# Implementation Plan: MVP — Plataforma Analítica PLAFT basada en Grafos

**Branch**: `001-mvp-graph-variables` | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Constitución aplicable**: v3.0.0

---

## Summary

Construir una plataforma analítica AWS-native centrada en clientes sospechosos que
produce dos entregables: (1) variables estructurales mediante Graph Analytics persistidas
en SageMaker Feature Store para enriquecer modelos PLAFT, y (2) una herramienta interna
de investigación para que los analistas visualicen subgrafos, señales de riesgo,
transferencias y documentos. El grafo opera sobre un subgrafo de profundidad configurable
(default: 1 salto) construido a partir de criterios de selección versionados. Todo el
procesamiento se ejecuta en SageMaker Processing sobre Python 3.12 + PySpark.

---

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PySpark (procesamiento distribuido), pandas (solo local/tests),
PyArrow (serialización Parquet), pytest + mypy + ruff (calidad), MLflow (experimentos
y artefactos)

**Storage**: Amazon S3 (grafo, nodos, relaciones, variables en Parquet), Amazon SageMaker
Feature Store (variables por entidad), AWS Glue Data Catalog (metadatos), Amazon Athena
(consultas ad hoc)

**Testing**: pytest con fixtures sintéticas, contratos de datos validados con pandera,
pruebas de integración sobre datasets sintéticos en S3

**Target Platform**: Amazon SageMaker Processing (producción), entorno local con pandas
(desarrollo y pruebas)

**Project Type**: Pipeline analítico + herramienta de investigación interna

**Performance Goals**: procesamiento de millones de transacciones por ejecución sin
degradación; consultas del analista con latencia aceptable para uso interactivo

**Constraints**: sin Neo4j ni bases de datos externas de grafos; NetworkX únicamente para
pruebas locales y subgrafos pequeños; motor de grafos distribuido a definir mediante ADR;
datos reales solo en infraestructura AWS aprobada; datos de desarrollo deben ser sintéticos

**Scale/Scope**: millones de transacciones; decenas de miles de clientes sospechosos;
grafo de profundidad 1 (expandible); 8 categorías de variables por entidad

---

## Constitution Check

*GATE: verificado contra Constitución v3.0.0 antes de comenzar diseño.*

| Principio Constitucional | Estado | Evidencia |
|--------------------------|--------|-----------|
| I. Propósito: variables estructurales + herramienta analítica | ✅ | Dos entregables del MVP bien definidos |
| II. Plataforma AWS (S3, SageMaker, Glue, Athena, PySpark) | ✅ | Toda la stack es aprobada |
| III. Arquitectura por capas (15 capas separadas) | ✅ | Ver sección Arquitectura |
| IV. Modelo del Grafo con trazabilidad | ✅ | Cada nodo/relación referencia registro fuente |
| V. Calidad de datos validada en ingesta | ✅ | Capa de Validación independiente |
| VI. Trazabilidad y Reproducibilidad con run_id | ✅ | Esquema de versionado completo |
| VII. ML como señal complementaria | ✅ | Variables no son decisión autónoma |
| VIII. Explicabilidad obligatoria | ✅ | Cada variable expone insumos y algoritmo |
| IX. Seguridad: solo infraestructura autorizada | ✅ | SA-001 a SA-007 |
| X. Calidad software: Python 3.12, tipado, tests, ruff, mypy | ✅ | En todos los componentes |
| XI. Extensibilidad (KYC, GraphRAG futuros) | ✅ | Capas desacopladas, nodos extensibles |
| XII. Gobernanza: ADR para decisiones arquitectónicas | ✅ | ADR-001 a ADR-004 definidos |
| XIII. Principios de diseño (negocio, trazabilidad, escala) | ✅ | Refleja todos los principios |

**Violaciones identificadas en spec.md y corregidas antes del plan**:

1. `Cliente Sospechoso` / `Cliente Contraparte` como tipos separados → unificado en nodo
   único `Cliente` con atributos de rol `es_cliente_objetivo` / `es_contraparte`.
2. Deduplicación incorrecta de transferencias por par cuenta-cuenta → `id_transaccion`
   es la clave de identidad; múltiples transferencias entre las mismas cuentas coexisten.
3. Expansión visual de herramienta sin restricción → limitada al subgrafo persistido
   autorizado; no incorpora datos externos durante consulta interactiva.
4. Algoritmos Betweenness/Closeness/Eigenvector mezclados con obligatorios → separados
   en grupo experimental, condicionados a pruebas de escala (ADR-002).
5. Referencias a 6 datasets/6 categorías → corregidas a 10 datasets/8 categorías.
6. Condición PEP descripta como señal de sospecha equivalente a alerta → clarificada
   como factor de debida diligencia reforzada, no evidencia automática.

---

## Correcciones aplicadas a spec.md v2.0

Las siguientes correcciones fueron aplicadas al archivo `spec.md` como parte de la
planificación:

| ID | Corrección | Sección afectada |
|----|------------|-----------------|
| C-01 | Unificación de nodo Cliente (eliminación de tipos separados) | Modelo del Grafo, FR-008, Key Entities |
| C-02 | Atributo `id_transaccion` como clave de identidad de transferencia | Modelo del Grafo |
| C-03 | Restricción de expansión visual al subgrafo persistido | FR-033 |
| C-04 | Separación de algoritmos obligatorios vs experimentales | FR-016 |
| C-05 | Condición PEP: factor de due diligence, no automáticamente sospechosa | Modelo del Grafo |

---

## Project Structure

### Documentación (esta feature)

```text
specs/001-mvp-graph-variables/
├── plan.md              # Este archivo
├── research.md          # Decisiones de investigación técnica
├── data-model.md        # Modelo de datos y esquemas
├── quickstart.md        # Guía de validación rápida
├── contracts/           # Contratos de datos por fuente
│   ├── clientes.md
│   ├── cuentas.md
│   ├── transferencias.md
│   ├── productos.md
│   ├── titularidades.md
│   ├── alertas_plaft.md
│   ├── ros.md
│   ├── pep.md
│   ├── casos_investigados.md
│   ├── catalogo_documental.md
│   ├── lista_objetivo.md
│   └── permisos_analistas.md
└── tasks.md             # Generado por /speckit-tasks (no creado aquí)
```

### Estructura propuesta del repositorio

```text
plaft-graph-platform/
├── pyproject.toml                   # Python 3.12, dependencias, ruff, mypy
├── Makefile                         # Comandos de desarrollo local
├── .gitignore                       # Excluye datos, credenciales, envs locales
│
├── src/
│   └── plaft_graph/
│       ├── __init__.py
│       ├── config/                  # Configuración por entorno (local/AWS)
│       │   ├── settings.py
│       │   └── schemas.py
│       ├── ingestion/               # Capa 1: Ingesta
│       │   ├── loaders.py
│       │   └── registry.py
│       ├── validation/              # Capa 2: Validación
│       │   ├── rules.py
│       │   ├── quality.py
│       │   └── contracts.py
│       ├── selection/               # Capa 3: Selección de sospechosos
│       │   ├── criteria.py
│       │   └── population.py
│       ├── expansion/               # Capa 4: Expansión de contrapartes
│       │   └── expander.py
│       ├── graph/                   # Capa 5: Construcción del subgrafo
│       │   ├── builder.py
│       │   ├── nodes.py
│       │   └── edges.py
│       ├── persistence/             # Capa 6: Persistencia versionada
│       │   ├── graph_store.py
│       │   └── versioning.py
│       ├── analytics/               # Capa 7: Graph Analytics
│       │   ├── algorithms.py
│       │   ├── mandatory.py
│       │   └── experimental.py
│       ├── variables/               # Capa 8: Generación de variables
│       │   ├── catalog.py
│       │   ├── centrality.py
│       │   ├── connectivity.py
│       │   ├── communities.py
│       │   ├── flow.py
│       │   ├── patterns.py
│       │   ├── anomalies.py
│       │   ├── neighbor_risk.py
│       │   └── propagated_risk.py
│       ├── feature_store/           # Capa 9-10: Persistencia y Feature Store
│       │   ├── writer.py
│       │   └── feature_group.py
│       ├── queries/                 # Capa 11: Consultas analíticas
│       │   └── query_engine.py
│       ├── tool/                    # Capa 12: Herramienta del analista
│       │   ├── app.py
│       │   ├── auth.py
│       │   └── audit.py
│       ├── security/                # Capa 13: Seguridad y permisos
│       │   └── access_control.py
│       ├── audit/                   # Capa 14: Auditoría
│       │   └── audit_log.py
│       └── observability/           # Capa 15: Observabilidad
│           └── metrics.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── traceability/
│   ├── reproducibility/
│   ├── security/
│   └── synthetic/                   # Datasets sintéticos de prueba
│
├── jobs/                            # Scripts de SageMaker Processing
│   ├── run_ingestion.py
│   ├── run_validation.py
│   ├── run_selection.py
│   ├── run_graph_build.py
│   ├── run_analytics.py
│   ├── run_variables.py
│   └── run_feature_store.py
│
├── adr/                             # Architecture Decision Records
│   ├── ADR-001-graph-engine.md
│   ├── ADR-002-experimental-algorithms.md
│   ├── ADR-003-analyst-tool.md
│   └── ADR-004-incremental-strategy.md
│
└── docs/
    └── data-dictionary/
```

---

## Arquitectura por Capas

### Capa 1 — Ingesta

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Cargar datasets desde S3 y registrar su versión en el run |
| **Entradas** | Particiones S3 de cada fuente de datos (Parquet/CSV/JSON) |
| **Salidas** | DataFrames Spark tipados; log de versión y tamaño de cada fuente |
| **Componentes** | `ingestion/loaders.py`, `ingestion/registry.py` |
| **Formato** | Parquet o CSV particionado en S3 según fuente |
| **Errores esperados** | Fuente no encontrada, formato no reconocido, acceso S3 denegado |
| **Pruebas** | Test de carga de cada fuente con dataset sintético; test de registro de versión |

### Capa 2 — Validación

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Validar esquema, tipos, obligatorios, duplicados, integridad referencial, consistencia temporal y dominios. Detener ante errores críticos. |
| **Entradas** | DataFrames de la capa de Ingesta |
| **Salidas** | DataFrames validados + informe de calidad por fuente |
| **Componentes** | `validation/rules.py`, `validation/quality.py`, `validation/contracts.py` |
| **Formato** | DataFrames Spark; informe JSON en S3 |
| **Errores esperados** | Campos obligatorios nulos, tipos incorrectos, registros duplicados, inconsistencia temporal, violación referencial |
| **Pruebas** | Test de cada regla por fuente; test que confirma detención ante error crítico; test que confirma que errores no críticos se registran sin detener |

### Capa 3 — Selección de Clientes Sospechosos

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Materializar la población de clientes objetivo para el run, usando criterios configurables. Versionar y persistir la lista de selección. |
| **Entradas** | DataFrames validados de clientes, alertas, ROS, PEP, casos, lista objetivo |
| **Salidas** | DataFrame `clientes_objetivo` con columnas: `cliente_id`, `criterios_cumplidos`, `version_seleccion`, `run_id` |
| **Componentes** | `selection/criteria.py`, `selection/population.py` |
| **Formato** | Parquet en S3: `s3://.../runs/{run_id}/seleccion/` |
| **Errores esperados** | Criterio mal configurado, fuente de lista objetivo vacía, intersección vacía |
| **Pruebas** | Test de cada criterio individualmente; test de unión de criterios; test de idempotencia |

### Capa 4 — Expansión de Contrapartes

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Para cada cliente objetivo, identificar sus contrapartes directas a la profundidad configurada (default: 1). Enriquecer contrapartes con sus señales de riesgo disponibles. |
| **Entradas** | `clientes_objetivo`, transferencias validadas, titularidades |
| **Salidas** | DataFrame `clientes_subgrafo` con atributo `nivel_expansion` y señales de riesgo propias |
| **Componentes** | `expansion/expander.py` |
| **Formato** | Parquet en S3: `s3://.../runs/{run_id}/expansion/` |
| **Errores esperados** | Profundidad fuera de rango, grafo sin contrapartes (cliente aislado) |
| **Pruebas** | Test con profundidad 1 y 2; test de cliente sin contrapartes; test de contraparte que también es cliente objetivo |

### Capa 5 — Construcción del Subgrafo

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Construir las tablas de nodos y relaciones del subgrafo con trazabilidad completa. Cada entidad y relación referencia su registro de origen. |
| **Entradas** | Todos los DataFrames validados + resultado de expansión |
| **Salidas** | Tablas Parquet: `nodes_cliente`, `nodes_cuenta`, `nodes_producto`, `nodes_alerta`, `nodes_ros`, `nodes_pep`, `nodes_caso`, `nodes_documento`, `edges_titular`, `edges_producto`, `edges_transfiere`, `edges_alerta`, `edges_ros`, `edges_pep`, `edges_caso`, `edges_documento` |
| **Componentes** | `graph/builder.py`, `graph/nodes.py`, `graph/edges.py` |
| **Formato** | Parquet en S3: `s3://.../runs/{run_id}/subgraph/` |
| **Errores esperados** | Nodo sin identificador, relación sin nodo existente, transferencia sin cuenta origen |
| **Pruebas** | Test de cada tipo de nodo; test de cada tipo de relación; test de trazabilidad; test de cliente con múltiples señales simultáneas; test de contraparte también objetivo |

### Capa 6 — Persistencia Versionada

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Persistir el subgrafo con metadatos de versión completos. Actualizar el catálogo Glue. Registrar el run en MLflow. |
| **Entradas** | Tablas de nodos y relaciones del subgrafo |
| **Salidas** | Tablas Parquet versionadas en S3 + registro de versión en MLflow + catálogo Glue actualizado |
| **Componentes** | `persistence/graph_store.py`, `persistence/versioning.py` |
| **Formato** | `s3://.../graph/v{graph_version}/` con metadatos: `graph_manifest.json` |
| **Errores esperados** | Conflicto de versión, escritura S3 fallida, error de registro en Glue |
| **Pruebas** | Test de recuperación exacta de versión; test de integridad estructural post-recuperación; test de múltiples versiones coexistentes |

### Capa 7 — Graph Analytics

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Ejecutar algoritmos de análisis estructural sobre el subgrafo. Separar algoritmos obligatorios (MVP) de experimentales (condicionados a escala). |
| **Entradas** | Tablas de nodos y relaciones de la versión del grafo |
| **Salidas** | Tablas de resultados por algoritmo: `analytics_degree`, `analytics_pagerank`, `analytics_components`, `analytics_communities`, `analytics_risk_distance`, `analytics_risk_exposure` |
| **Componentes** | `analytics/mandatory.py`, `analytics/experimental.py` |
| **Formato** | Parquet en S3: `s3://.../runs/{run_id}/analytics/` |
| **Errores esperados** | Grafo con ciclos (algoritmos deben manejarlo), timeout en algoritmos costosos, OOM en subgrafo grande |
| **Pruebas** | Test de cada algoritmo obligatorio contra grafo sintético con resultado conocido; test de manejo de ciclos; test de idempotencia |

**Algoritmos obligatorios del MVP**:
- in-degree, out-degree, grado total
- cantidad de transferencias recibidas y enviadas
- monto total recibido y enviado
- cantidad de contrapartes únicas
- PageRank (con parámetros documentados)
- Connected Components
- Louvain Community Detection
- Distancia mínima dirigida a clientes con señales de riesgo
- Exposición directa e indirecta a señales de riesgo

**Algoritmos experimentales** (requieren ADR-002 y pruebas de escala):
- Betweenness Centrality
- Closeness Centrality
- Eigenvector Centrality
- Label Propagation
- Cálculos masivos de Shortest Paths

### Capa 8 — Generación de Variables

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Derivar variables estructurales por entidad a partir de resultados de Graph Analytics. Exponer trazabilidad completa de cada variable. |
| **Entradas** | Resultados de Graph Analytics + tablas del subgrafo |
| **Salidas** | DataFrame `variables_estructurales` con columnas: `cliente_id`, `variable_nombre`, `categoria`, `valor`, `valor_nulo_razon`, `insumos`, `algoritmo`, `relaciones_participantes`, `run_id`, `graph_version` |
| **Componentes** | `variables/catalog.py` + módulo por categoría |
| **Formato** | Parquet en S3: `s3://.../runs/{run_id}/variables/` |
| **Errores esperados** | Cliente sin actividad (variable debe ser nulo documentado, no error), resultado de algoritmo faltante |
| **Pruebas** | Test de las 8 categorías; test de cliente sin actividad (nulos correctos); test de diferenciación de señales en variables de riesgo |

**Clientes sin actividad**: un nodo Cliente sin transferencias ni relaciones DEBE
conservar el esquema completo de variables con valores `null` o documentados (`0`,
`"sin_actividad"`). Nunca debe omitirse del dataset de salida.

### Capa 9 — Persistencia de Variables

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Persistir el dataset de variables en S3 con versionado. Separada de la escritura en Feature Store. |
| **Entradas** | DataFrame `variables_estructurales` |
| **Salidas** | Parquet en S3: `s3://.../variables/v{variables_version}/` |
| **Componentes** | `feature_store/writer.py` |
| **Formato** | Parquet particionado por `categoria` y `run_id` |
| **Errores esperados** | Escritura S3 fallida, schema mismatch |
| **Pruebas** | Test de recuperación correcta; test de versionado independiente del grafo |

### Capa 10 — Registro en SageMaker Feature Store

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Registrar variables estructurales por entidad en SageMaker Feature Store para consumo por modelos analíticos externos. El grafo completo NO se registra en Feature Store. |
| **Entradas** | DataFrame `variables_estructurales` de Capa 9 |
| **Salidas** | Feature Group actualizado en SageMaker Feature Store |
| **Componentes** | `feature_store/feature_group.py` |
| **Formato** | Feature Group por categoría de variable |
| **Errores esperados** | Error de escritura en Feature Store, incompatibilidad de schema |
| **Pruebas** | Test de escritura y lectura en Feature Store con dataset sintético |

### Capa 11 — Consultas Analíticas

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Proveer acceso a nodos, relaciones, variables y señales del subgrafo mediante Athena y el catálogo Glue. |
| **Entradas** | Tablas en S3 registradas en Glue Catalog |
| **Salidas** | Resultados de consultas SQL |
| **Componentes** | `queries/query_engine.py`, tablas Athena |
| **Formato** | SQL sobre tablas Parquet; respuestas en JSON o Parquet |
| **Errores esperados** | Timeout de Athena, tabla no registrada en catálogo |
| **Pruebas** | Test de consulta por cliente; test de trazabilidad al registro fuente |

### Capa 12 — Herramienta de Investigación

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Interfaz interna para analistas PLAFT: búsqueda, visualización del subgrafo, filtros, señales, variables, documentos, trazabilidad, exportación y auditoría. |
| **Entradas** | Tablas S3 del subgrafo, variables, señales y catálogo documental (via Athena o lectura directa de Parquet) |
| **Salidas** | Vista del subgrafo del cliente; resultados de filtros; explicación de variables; metadatos de documentos; export estructurado |
| **Componentes** | `tool/app.py`, `tool/auth.py`, `tool/audit.py` |
| **Tecnología** | A definir en ADR-003 (Streamlit vs alternativa compatible con AWS) |
| **Errores esperados** | Cliente no en subgrafo autorizado → acceso denegado + log; documento sin referencia → indicador en UI |
| **Pruebas** | Test de búsqueda; test de visualización de subgrafo; test de filtros; test de control de acceso; test de log de auditoría |

**Restricción de expansión**: la herramienta solo muestra relaciones que pertenecen al
subgrafo persistido y para las que el analista tiene autorización. No consulta datos
externos ni incorpora nuevos nodos durante una sesión interactiva.

### Capa 13 — Seguridad y Permisos

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Control de acceso basado en mínimo privilegio. Autorización por cliente, subgrafo y documento. Separación entre permisos de datos y permisos documentales. |
| **Componentes** | `security/access_control.py`, IAM roles y políticas AWS |
| **Errores esperados** | Intento de acceso no autorizado → rechazo + registro de auditoría |
| **Pruebas** | Test de acceso autorizado; test de rechazo ante acceso no autorizado; test de separación de permisos datos/documentos |

### Capa 14 — Auditoría

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Registrar de forma inmutable toda interacción del analista: usuario, cliente consultado, timestamp, filtros, versión del grafo, documentos consultados, exportaciones e intentos denegados. |
| **Componentes** | `audit/audit_log.py` |
| **Formato** | JSON append-only en S3 con retención configurable |
| **Pruebas** | Test de completitud del log; test de inmutabilidad; test de acceso denegado registrado |

### Capa 15 — Observabilidad

| Campo | Detalle |
|-------|---------|
| **Responsabilidad** | Registrar métricas operacionales de cada ejecución: nodos/relaciones por tipo, densidad, comunidades, tiempos, errores. |
| **Componentes** | `observability/metrics.py`, MLflow (métricas de run) |
| **Formato** | JSON en S3 + métricas en MLflow |
| **Pruebas** | Test de registro completo de métricas; test de comparación entre runs |

---

## Catálogo de Variables Estructurales

### Categoría 1: Centralidad

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `grado_entrada` | Número de transferencias recibidas | Count de aristas TRANSFIERE_A entrantes | Subgrafo | Cliente | edges_transfiere | 0 si sin actividad | Bajo |
| `grado_salida` | Número de transferencias enviadas | Count de aristas TRANSFIERE_A salientes | Subgrafo | Cliente | edges_transfiere | 0 si sin actividad | Bajo |
| `grado_total` | Suma de grado entrada + salida | `grado_entrada + grado_salida` | Subgrafo | Cliente | edges_transfiere | 0 | Bajo |
| `pagerank` | Importancia relativa del nodo en la red | PageRank con damping=0.85, iter=100 | Subgrafo | Cliente | nodes_cliente + edges_transfiere | null si nodo aislado | Medio |

### Categoría 2: Conectividad

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `contrapartes_unicas` | Clientes únicos con los que tuvo transferencias | Count distinct de cliente_origen/destino en TRANSFIERE_A | Subgrafo | Cliente | edges_transfiere | 0 | Bajo |
| `cuentas_propias` | Número de cuentas titulares | Count de ES_TITULAR_DE | Subgrafo | Cliente | edges_titular | 0 | Bajo |
| `componente_conectado` | ID del componente conectado al que pertenece | Connected Components (WCC) | Subgrafo | Cliente | edges_transfiere | null si aislado | Bajo |
| `tamano_componente` | Número de nodos en el mismo componente | Join con tamaño del componente | Subgrafo | Cliente | analytics_components | 1 si aislado | Bajo |

### Categoría 3: Comunidades

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `comunidad_id` | ID de la comunidad Louvain asignada | Louvain Community Detection | Subgrafo | Cliente | analytics_communities | null si aislado | Medio |
| `tamano_comunidad` | Número de nodos en la comunidad | Join con tamaño de comunidad | Subgrafo | Cliente | analytics_communities | 1 si aislado | Bajo |
| `modularidad_local` | Contribución a la modularidad global | Calculado post-Louvain | Subgrafo | Comunidad | analytics_communities | null | Medio |

### Categoría 4: Flujo de Dinero

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `monto_recibido_total` | Suma de montos de transferencias entrantes | SUM(monto) WHERE cliente_destino = cliente_id | Subgrafo / configurable | Cliente | edges_transfiere | 0 | Bajo |
| `monto_enviado_total` | Suma de montos de transferencias salientes | SUM(monto) WHERE cliente_origen = cliente_id | Subgrafo / configurable | Cliente | edges_transfiere | 0 | Bajo |
| `ratio_enviado_recibido` | Proporción de montos | `monto_enviado / monto_recibido` | Subgrafo | Cliente | variables calculadas | null si monto_recibido = 0 | Bajo |
| `concentracion_contraparte` | Proporción del flujo hacia la contraparte principal | `max_monto_contraparte / monto_total` | Subgrafo | Cliente | edges_transfiere | null si sin flujo | Bajo |

### Categoría 5: Patrones Transaccionales

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `frecuencia_tx` | Cantidad total de transacciones | COUNT(id_transaccion) | Configurable | Cliente | edges_transfiere | 0 | Bajo |
| `monto_promedio_tx` | Monto promedio por transacción | AVG(monto) | Configurable | Cliente | edges_transfiere | null si sin tx | Bajo |
| `canales_distintos` | Número de canales de transacción únicos | COUNT(DISTINCT canal) | Subgrafo | Cliente | edges_transfiere | 0 | Bajo |
| `dias_activos` | Días distintos con al menos una transacción | COUNT(DISTINCT DATE(fecha_hora)) | Configurable | Cliente | edges_transfiere | 0 | Bajo |

### Categoría 6: Anomalías Estructurales

| Variable | Definición | Fórmula / Algoritmo | Ventana | Nivel | Insumos | Nulos | Costo |
|----------|-----------|---------------------|---------|-------|---------|-------|-------|
| `desviacion_grado` | Cuántas desviaciones estándar se aleja el grado del promedio de la comunidad | `(grado_total - media_comunidad) / std_comunidad` | Subgrafo | Cliente | analytics_degree + analytics_communities | null si comunidad < 3 | Medio |
| `es_intermediario` | Nodo con flujo de entrada y salida alto simultáneo | `grado_entrada > p75 AND grado_salida > p75` | Subgrafo | Cliente | analytics_degree | False | Bajo |
| `patron_receptor_emisor` | Relación entre flujo recibido y enviado en ventana corta | Heurística configurable | Configurable | Cliente | edges_transfiere | null | Bajo |

### Categoría 7: Riesgo de Vecinos

Las señales de riesgo se mantienen separadas. No se combinan en un único valor sin regla explícita.

| Variable | Definición | Señal | Insumos | Nulos |
|----------|-----------|-------|---------|-------|
| `contrapartes_con_alerta` | Cantidad de contrapartes directas con alerta PLAFT | Alerta PLAFT | edges_transfiere + nodes_cliente.tiene_alerta | 0 |
| `contrapartes_con_ros` | Cantidad de contrapartes directas con ROS | ROS | edges_transfiere + nodes_cliente.tiene_ros | 0 |
| `contrapartes_con_pep` | Cantidad de contrapartes directas PEP | PEP | edges_transfiere + nodes_cliente.es_pep | 0 |
| `contrapartes_con_caso` | Cantidad de contrapartes directas con caso | Caso investigado | edges_transfiere + nodes_cliente.tiene_caso | 0 |
| `monto_recibido_de_alerta` | Monto recibido de contrapartes con alerta PLAFT | Alerta PLAFT | edges_transfiere + señales | 0 |
| `monto_enviado_a_pep` | Monto enviado a contrapartes PEP | PEP | edges_transfiere + señales | 0 |
| `prop_contrapartes_investigadas` | Proporción de contrapartes con caso investigado | Caso investigado | edges_transfiere + señales | null si sin contrapartes |
| `senales_distintas_vecinos` | Cantidad de tipos de señal diferentes presentes en vecinos | Todas | nodes_cliente en vecindad | 0 |

### Categoría 8: Riesgo Propagado

| Variable | Definición | Señal | Algoritmo | Nulos |
|----------|-----------|-------|-----------|-------|
| `distancia_min_alerta` | Distancia mínima dirigida a cliente con alerta PLAFT | Alerta PLAFT | BFS sobre subgrafo dirigido | null si no alcanzable |
| `distancia_min_ros` | Distancia mínima a cliente con ROS | ROS | BFS | null si no alcanzable |
| `distancia_min_pep` | Distancia mínima a cliente PEP | PEP | BFS | null si no alcanzable |
| `distancia_min_caso` | Distancia mínima a cliente con caso | Caso | BFS | null si no alcanzable |
| `exposicion_indirecta_alerta` | Fracción del flujo vinculado con clientes con alerta a 2 saltos | Alerta PLAFT | Suma ponderada por flujo | 0 |
| `pct_flujo_sospechosos` | Porcentaje del flujo total vinculado con clientes en subgrafo | Todos | edges_transfiere + selección | 0 |

---

## Esquema de Reproducibilidad y Versionado

```python
# Atributos del run (run_manifest.json)
{
  "run_id": "uuid-v4",
  "created_at": "ISO-8601",
  "code_version": "git-tag-or-semver",
  "git_commit": "sha-corto",
  "datasets": {
    "clientes": {"s3_path": "...", "version": "...", "row_count": N},
    "transferencias": {"s3_path": "...", "version": "...", "row_count": N},
    # ... resto de datasets
  },
  "selection_criteria": {"alerta": true, "ros": true, "pep": true, ...},
  "expansion_depth": 1,
  "date_cutoff": "YYYY-MM-DD",
  "algorithm_params": {"pagerank_damping": 0.85, "louvain_seed": 42, ...},
  "graph_version": "v-{uuid}",
  "variables_version": "v-{uuid}",
  "status": "completed|failed|partial",
  "metrics": {
    "node_count_cliente": N,
    "edge_count_transfiere": N,
    "community_count": N,
    "variables_generated": N,
    "build_time_seconds": N
  },
  "errors": []
}
```

Cada run es idempotente: re-ejecutar con el mismo `run_id` y mismos parámetros produce
resultados idénticos. La idempotencia se verifica usando el checksum del dataset de salida.

---

## Arquitectura de Seguridad

### Control de acceso

- IAM roles de SageMaker con políticas de mínimo privilegio por entorno.
- La herramienta del analista autentica mediante el sistema de identidad corporativo
  del banco (a definir en ADR-003).
- Permisos de datos (subgrafo, variables, transferencias) separados de permisos
  documentales (catálogo documental S3).
- Cada analista tiene una lista de `cliente_id` autorizados o un subgrafo autorizado.
- La herramienta verifica autorización antes de cada consulta.

### Log de auditoría

```json
{
  "audit_id": "uuid",
  "timestamp": "ISO-8601",
  "usuario": "id-analista",
  "accion": "search|view_subgraph|view_variable|view_document|export|denied",
  "cliente_id": "...",
  "grafo_version": "v-...",
  "datos_version": "...",
  "filtros_aplicados": {...},
  "documentos_consultados": ["doc-id-1", ...],
  "exportacion_realizada": true|false,
  "resultado": "ok|denied",
  "ip_origen": "...",
  "session_id": "..."
}
```

- Log append-only en S3 con retención mínima de 12 meses.
- Intentos denegados generan entrada de log y respuesta 403 al usuario.
- No se registran datos sensibles de contenido en el log; solo identificadores y metadatos.

---

## Estrategia de Escalabilidad

### Particionamiento

- **Transferencias**: particionadas por `periodo` (YYYY-MM) en S3.
- **Nodos**: particionadas por `tipo_nodo`.
- **Variables**: particionadas por `categoria` y `run_id`.

### Ejecución incremental

- En el MVP se realiza reconstrucción completa del subgrafo por ejecución.
- La arquitectura separa ingesta, construcción y analítica para permitir en el futuro
  actualizaciones incrementales del grafo sin reconstruir desde cero.
- Los resultados de Graph Analytics se persisten separadamente para reutilización.

### Motor de grafos

- NetworkX: **solo para pruebas locales y subgrafos pequeños** (< 10,000 nodos).
- Para producción: a definir en ADR-001. Candidatos: GraphX (nativo PySpark),
  cuGraph (GPU), graphframes. Decision basada en escala real.

### Algoritmos costosos

- Betweenness Centrality: O(V·E) — no ejecutar sobre grafo completo sin muestreo.
- Eigenvector Centrality: puede no converger en grafos con ciclos — requiere límite de
  iteraciones documentado.
- Shortest Paths masivos: requiere aproximación o ejecución sobre subgrafos reducidos.
- La decisión de ejecutar o no algoritmos experimentales se registra en cada run con
  justificación.

---

## Estrategia de Pruebas

| Tipo | Alcance | Herramienta | Datasets |
|------|---------|-------------|---------|
| Unitarias | Cada módulo por separado | pytest | Fixtures sintéticas en memoria |
| Contratos de datos | Schema y calidad de cada fuente | pandera | CSV sintéticos en tests/synthetic/ |
| Integración | Pipeline completo por capa | pytest | Parquet sintético en S3 de test |
| Trazabilidad | Cada nodo/relación referencia origen | pytest | Subgrafo sintético con origen conocido |
| Reproducibilidad | Dos runs idénticos producen output idéntico | pytest | Run reproducible con semilla fija |
| Seguridad | Acceso autorizado/denegado | pytest | Mock de sistema de permisos |
| Auditoría | Log completo por acción | pytest | Mock de herramienta |
| Exactitud de variables | Comparar contra valores calculados manualmente | pytest | Grafo sintético con resultados conocidos |
| Escala | Performance con millones de transacciones | Script dedicado | Dataset sintético a escala |
| Idempotencia | Re-ejecución produce mismo resultado | pytest | Run reproducible |

---

## ADRs Requeridos

### ADR-001: Motor de Procesamiento de Grafos para Producción

**Decisión requerida**: qué motor usar para Graph Analytics a escala de millones de nodos.
**Candidatos**: GraphX (PySpark nativo), cuGraph (NVIDIA, GPU), graphframes (Spark +
GraphX API), NetworkX (solo local).
**Criterios**: compatibilidad con SageMaker Processing, soporte de algoritmos obligatorios
del MVP, licencia, costo.

### ADR-002: Algoritmos Experimentales — Criterios de Habilitación

**Decisión requerida**: umbrales de tamaño de subgrafo y tiempo de ejecución que
habilitan Betweenness, Closeness, Eigenvector, Label Propagation y Shortest Paths masivos.
**Criterios**: tiempo máximo aceptable, aproximaciones válidas, impacto en variables.

### ADR-003: Tecnología de la Herramienta de Investigación del Analista

**Decisión requerida**: elegir entre alternativas compatibles con la infraestructura AWS
del banco.

| Criterio | Streamlit en SageMaker | Tableau/QuickSight Embedded |
|----------|------------------------|----------------------------|
| Compatibilidad AWS | Alta (SageMaker Studio) | Alta (QuickSight nativo) |
| Flexibilidad UI | Alta (código Python) | Media (configuración) |
| Visualización de grafos | Requiere librería (pyvis, networkx) | Limitada |
| Control de acceso | Requiere implementación | Integrado con IAM |
| Costo | Bajo (uso de instancia) | Variable por usuario |
| Esfuerzo de desarrollo | Medio | Bajo |
| **Recomendación inicial** | Streamlit sobre SageMaker Studio App | Alternativa si restricciones corporativas |

La decisión definitiva requiere validación con los equipos de seguridad y arquitectura
del banco.

### ADR-004: Estrategia de Actualización Incremental del Grafo

**Decisión requerida**: cuándo implementar actualización incremental y qué particiones
actualizar sin reconstruir el subgrafo completo.
**Criterios**: frecuencia de ejecución, tamaño del delta, costo de reconstrucción completa.

---

## Fases de Implementación

### Fase 0 — Investigación y Decisiones Técnicas

**Objetivo**: resolver todas las incógnitas técnicas antes de escribir código de producción.

Tareas:
- Investigar y documentar ADR-001 (motor de grafos).
- Investigar y documentar ADR-003 (herramienta de analista).
- Validar acceso a S3, SageMaker Processing y Feature Store en entorno de desarrollo.
- Definir estructura de particionamiento de S3 por equipo de datos.
- Definir esquema del catálogo Glue.
- Validar con equipos de seguridad el modelo de permisos de analistas.
- Producir `research.md` con todas las decisiones tomadas.

**Entregables**: `research.md`, ADR-001, ADR-003, acceso validado al entorno.

### Fase 1 — Datos y Selección

**Objetivo**: establecer contratos de datos, ingesta, validación y selección de sospechosos.

Tareas:
- Definir y documentar contratos de datos para las 12 fuentes (`contracts/`).
- Implementar capa de Ingesta (Capa 1) con PySpark.
- Implementar capa de Validación (Capa 2) con reglas por fuente.
- Implementar capa de Selección (Capa 3) con criterios configurables.
- Implementar capa de Expansión (Capa 4) con profundidad 1.
- Implementar pruebas unitarias y de contrato para cada capa.
- Generar datasets sintéticos para pruebas.

**Entregables**: módulos de ingesta, validación, selección, expansión + contratos + tests.

### Fase 2 — Construcción y Persistencia del Subgrafo

**Objetivo**: construir el subgrafo con todos los nodos y relaciones definidos.

Tareas:
- Implementar Capa 5 (Construcción) con todos los tipos de nodo y relación.
- Implementar Capa 6 (Persistencia) con versionado y manifesto.
- Registrar grafo en Glue Catalog.
- Registrar run en MLflow.
- Pruebas de trazabilidad y recuperación de versiones.

**Entregables**: grafo construido y persistido en S3 + catálogo Glue + run en MLflow.

### Fase 3 — Graph Analytics

**Objetivo**: ejecutar algoritmos obligatorios del MVP sobre el subgrafo.

Tareas:
- Implementar Capa 7 con algoritmos obligatorios (using ADR-001 motor).
- Persistir resultados de analytics separadamente del grafo.
- Implementar manejo correcto de ciclos.
- Pruebas de exactitud contra grafos sintéticos con resultados conocidos.
- Documentar ADR-002 con umbrales de algoritmos experimentales.

**Entregables**: módulo de analytics + resultados persistidos + ADR-002.

### Fase 4 — Generación de Variables y Feature Store

**Objetivo**: generar las 8 categorías de variables con trazabilidad completa.

Tareas:
- Implementar Capa 8 con módulo por categoría.
- Implementar variables de Riesgo de Vecinos con diferenciación por señal.
- Implementar variables de Riesgo Propagado con distancias dirigidas.
- Implementar Capa 9 (Persistencia de Variables).
- Implementar Capa 10 (Feature Store).
- Pruebas de exactitud de variables y nulos correctos para clientes sin actividad.

**Entregables**: catálogo de variables completo + Feature Store configurado.

### Fase 5 — Herramienta del Analista

**Objetivo**: proveer interfaz de investigación para analistas PLAFT.

Tareas:
- Implementar Capa 12 (Herramienta) con tecnología de ADR-003.
- Búsqueda por cliente, visualización del subgrafo, filtros (período, monto, señal).
- Visualización de transferencias con dirección diferenciada.
- Señales de riesgo diferenciadas por tipo (alerta, ROS, PEP, caso).
- Catálogo documental: listar documentos con metadatos y referencia S3.
- Variables estructurales con explicación.
- Trazabilidad al registro fuente por nodo y relación.
- Exportación de resumen estructurado.
- Versión del grafo y fecha de corte siempre visibles.
- Diferenciación de nodos y relaciones por forma/iconografía (no solo color).

**Entregables**: herramienta funcional en infraestructura interna autorizada.

### Fase 6 — Seguridad y Auditoría

**Objetivo**: garantizar control de acceso, log de auditoría y protección de datos.

Tareas:
- Implementar Capa 13 (Seguridad) con roles IAM y verificación de autorización.
- Implementar Capa 14 (Auditoría) con log inmutable.
- Pruebas de acceso autorizado/denegado.
- Pruebas de completitud del log.
- Validar que el repositorio no contiene credenciales ni datos sensibles.

**Entregables**: control de acceso operativo + log de auditoría + pruebas de seguridad.

### Fase 7 — Validación Integral

**Objetivo**: validar el sistema completo con usuarios PLAFT y datos sintéticos a escala.

Tareas:
- Pruebas end-to-end con datasets sintéticos representativos.
- Pruebas de reproducibilidad: dos runs con mismos parámetros producen output idéntico.
- Pruebas de escala (millones de transacciones).
- Validación con analistas PLAFT (UAT).
- Documentar ADR-004 (estrategia incremental).
- Implementar Capa 15 (Observabilidad) con métricas operacionales completas.
- Revisión final de cumplimiento con Constitución v3.0.0.

**Entregables**: sistema validado, documentación operacional, ADR-004.

---

## Artefactos de este plan

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `plan.md` | ✅ Completo | Este archivo |
| `research.md` | ✅ Generado | Decisiones de investigación técnica |
| `data-model.md` | ✅ Generado | Modelo de datos y esquemas de nodos/relaciones |
| `quickstart.md` | ✅ Generado | Guía de validación rápida |
| `contracts/` | ✅ Generado | Contratos por fuente de datos |
| `adr/ADR-001-graph-engine.md` | Pendiente (Fase 0) | Motor de grafos |
| `adr/ADR-002-experimental-algorithms.md` | Pendiente (Fase 3) | Algoritmos experimentales |
| `adr/ADR-003-analyst-tool.md` | Pendiente (Fase 0) | Tecnología herramienta |
| `adr/ADR-004-incremental-strategy.md` | Pendiente (Fase 7) | Estrategia incremental |
| `tasks.md` | Pendiente (`/speckit-tasks`) | Lista de tareas ordenada |

---

## Integridad Temporal

**Regla fundamental**: toda variable se calcula usando únicamente datos disponibles
hasta (e incluyendo) la `fecha_corte` del run. No se usa información posterior.

### Definiciones

| Concepto | Definición |
|----------|-----------|
| `fecha_corte` | Fecha límite de observación. Los datos con `fecha_hora > fecha_corte` son rechazados. |
| `periodo_objetivo` | Período YYYY-MM del análisis principal. |
| `ventana_observacion` | Rango de fechas utilizado para calcular una variable. Define en meses: 1, 3, 6, 12, "todo". |

### Tratamiento por tipo de señal

| Señal | Vigencia | Regla temporal |
|-------|----------|----------------|
| Alerta PLAFT | Solo alertas con `fecha_alerta ≤ fecha_corte` | Incluidas en variables y subgrafo |
| ROS | Solo ROS con `fecha_reporte ≤ fecha_corte` | Incluidos |
| Condición PEP | `fecha_inicio ≤ fecha_corte` AND (`fecha_fin` IS NULL OR `fecha_fin ≥ fecha_corte`) | Solo PEP vigente a fecha de corte |
| Caso Investigado | Solo casos con `fecha_apertura ≤ fecha_corte` | Se incluyen abiertos Y cerrados a fecha de corte |
| Transferencias | Solo `fecha_hora ≤ fecha_corte` Y `estado ≠ ANULADA` | Rechazar posteriores al corte |
| Documentos | Solo documentos con `fecha_incorporacion ≤ fecha_corte` | Documentos incorporados posterior al corte no visibles |

### Variables y fuga temporal

Cada variable incluye en sus metadatos:
- `fecha_calculo`: timestamp de cuando se calculó.
- `ventana_inicio` y `ventana_fin`: rango de datos usado.
- `fecha_corte`: fecha de corte del run.

**Ejemplo correcto** (sin fuga):
```
Variable: monto_enviado_total
ventana_inicio: 2025-08-01
ventana_fin (= fecha_corte): 2026-07-31
fecha_calculo: 2026-08-06
```

**Error a evitar**: incluir transferencias del 1 de agosto de 2026 en una variable
calculada con fecha_corte 31 de julio de 2026.

---

## Diseño de SageMaker Processing Jobs

Cada etapa del pipeline se implementa como un job independiente de SageMaker Processing.
La primera versión ejecuta los jobs secuencialmente de forma manual. El diseño permite
incorporarlos a SageMaker Pipelines en una versión posterior sin reescribir la lógica.

### Job 1: Selección de Población

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_selection.py` |
| Entradas S3 | `s3://.../raw/clientes/`, `s3://.../raw/alertas/`, `s3://.../raw/ros/`, `s3://.../raw/pep/`, `s3://.../raw/casos/`, `s3://.../raw/lista_objetivo/` |
| Salidas S3 | `s3://.../runs/{run_id}/seleccion/clientes_objetivo.parquet` |
| Argumentos | `--run-id`, `--fecha-corte`, `--criterios` (JSON), `--profundidad` |
| Idempotencia | Re-ejecución con mismo `run_id` sobreescribe salida |
| Logs | CloudWatch + S3 |
| Métricas | `count_clientes_objetivo` por criterio |

### Job 2: Validación

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_validation.py` |
| Entradas S3 | Todos los datasets crudos |
| Salidas S3 | `s3://.../runs/{run_id}/validated/` + `quality_report.json` |
| Comportamiento ante error crítico | Falla con exit code ≠ 0; el job no continúa |

### Job 3: Construcción del Subgrafo

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_graph_build.py` |
| Entradas S3 | Datasets validados + `clientes_objetivo.parquet` |
| Salidas S3 | `s3://.../runs/{run_id}/subgraph/` (nodos + aristas) |
| Argumentos | `--run-id`, `--depth`, `--graph-version` |
| Instancia recomendada | `ml.m5.4xlarge` o mayor según tamaño del subgrafo |

### Job 4: Persistencia y Catalogación

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_persistence.py` |
| Entradas S3 | `s3://.../runs/{run_id}/subgraph/` |
| Salidas S3 | `s3://.../graph/v{graph_version}/` + `manifest.json` |
| Acción adicional | Actualiza Glue Catalog; registra run en MLflow |

### Job 5: Graph Analytics

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_analytics.py` |
| Entradas S3 | `s3://.../graph/v{graph_version}/` |
| Salidas S3 | `s3://.../runs/{run_id}/analytics/` |
| Argumentos | `--algorithms` (lista), `--graph-version`, `--seed` |
| Instancia recomendada | `ml.m5.4xlarge` o `ml.m5.12xlarge` según tamaño |

### Job 6: Generación de Variables

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_variables.py` |
| Entradas S3 | Subgrafo + resultados analytics |
| Salidas S3 | `s3://.../runs/{run_id}/variables/` |
| Comportamiento nulos | Clientes sin actividad → variables con 0 o null documentado |

### Job 7: Publicación en Feature Store

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_feature_store.py` |
| Entradas S3 | `s3://.../runs/{run_id}/variables/` |
| Salida | SageMaker Feature Store (Offline) |
| Tratamiento duplicados | Feature Store resuelve por `(cliente_id, fecha_corte)` |

### Job 8: Generación de Artefactos para Consulta

| Parámetro | Valor |
|-----------|-------|
| Script | `jobs/run_query_artifacts.py` |
| Entradas S3 | Subgrafo + variables + catálogo documental |
| Salidas S3 | `s3://.../query/v{graph_version}/` (tablas optimizadas para Athena) |
| Acción | Actualiza vistas Athena y referencias en Glue |

---

## Desarrollo Local

### Objetivo

Permitir al equipo desarrollar y probar sin acceso a AWS, usando datos sintéticos y
pandas/NetworkX con la misma lógica de negocio que producción.

### Configuración

```bash
# Setup del entorno local
pip install -e ".[dev]"

# Ejecutar pipeline completo con datos sintéticos
python jobs/run_selection.py --config config/local.yaml --synthetic --run-id local-001
python jobs/run_validation.py --config config/local.yaml --run-id local-001
python jobs/run_graph_build.py --config config/local.yaml --run-id local-001 --depth 1
python jobs/run_analytics.py --config config/local.yaml --run-id local-001
python jobs/run_variables.py --config config/local.yaml --run-id local-001
```

### Datasets sintéticos

Ubicación: `tests/synthetic/`

| Dataset | Patrón incluido |
|---------|----------------|
| `patron_cliente_aislado.parquet` | Cliente sin transferencias |
| `patron_estrella.parquet` | Hub con N contrapartes directas |
| `patron_cadena.parquet` | Cadena lineal de transferencias |
| `patron_ciclo.parquet` | Ciclo de transferencias (A→B→C→A) |
| `patron_comunidad.parquet` | Dos comunidades con puente |
| `patron_multiples_senales.parquet` | Cliente con alerta + ROS + PEP simultáneos |
| `patron_cuenta_compartida.parquet` | Cuenta con 3 titulares |
| `patron_contraparte_riesgosa.parquet` | Contraparte directa con ROS |
| `patron_tx_anuladas.parquet` | Mix de transferencias ejecutadas y anuladas |
| `patron_fx_posterior_corte.parquet` | Transferencias posteriores a fecha_corte |

---

## Riesgos y Supuestos

### Riesgos principales

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|-------------|---------|-----------|
| R-01 | GraphFrames no disponible en entorno SageMaker del banco | Media | Alto | ADR-002 prevé alternativas; implementación propia como fallback |
| R-02 | Feature Store no habilitado en la cuenta AWS | Media | Medio | ADR-004 prevé fallback a S3 + Athena |
| R-03 | Mecanismo de autenticación para herramienta del analista no definido | Alta | Alto | Bloquea Fase 5; requiere resolución en Fase 0 |
| R-04 | Datasets de entrada con esquemas no documentados | Media | Alto | Contratos en `contracts/` como punto de negociación |
| R-05 | Subgrafo demasiado grande para instancia SageMaker estándar | Baja | Medio | Profundidad=1 limita el tamaño; instancias escalables |
| R-06 | PEP tratado como señal de sospecha (error conceptual) | Baja | Medio | ADR explícito; revisión de modelos que consuman variables PEP |
| R-07 | Fuga temporal en variables de riesgo | Media | Alto | Sección de integridad temporal; tests de no-leakage |
| R-08 | Datos sensibles en repositorio (credenciales, datos reales) | Baja | Crítico | .gitignore + CI checks + revisión de PRs |

### Supuestos

| ID | Supuesto |
|----|---------|
| S-01 | El banco tiene acceso a SageMaker Processing en su cuenta AWS. |
| S-02 | Los datasets de entrada son accesibles desde SageMaker en S3. |
| S-03 | Existe un sistema de control de acceso corporativo (SSO/IAM) que puede integrarse con la herramienta. |
| S-04 | Los analistas PLAFT tienen estaciones con acceso a la VPC donde se desplegará la herramienta. |
| S-05 | Los identificadores de cliente son estables y únicos entre todos los datasets. |
| S-06 | El banco puede proveer datasets sintéticos o anonimizados para desarrollo. |
| S-07 | MLflow puede ejecutarse en la infraestructura AWS del banco (como servidor o como MLflow Tracking en SageMaker). |

---

## Fase 8 — AWS, Rendimiento y Endurecimiento

**Objetivo**: desplegar el sistema completo en AWS de producción, optimizar para millones
de transacciones y certificar el sistema para uso operativo.

Tareas:
- Empaquetar todos los jobs en imágenes Docker para SageMaker Processing.
- Configurar SageMaker Pipelines para orquestación automática del pipeline.
- Ejecutar el pipeline con datasets reales anonimizados en entorno de pre-producción.
- Pruebas de carga con N millones de transferencias (N = estimado real).
- Optimizar particionamiento S3 según volumen real.
- Configurar alertas de CloudWatch para errores y métricas operacionales.
- Revisar y ajustar roles IAM según principio de mínimo privilegio.
- Pruebas de penetración básicas sobre la herramienta del analista.
- Documentación operacional: runbooks, disaster recovery, recuperación ante fallos.
- Validación final de cumplimiento con Constitución v3.0.0.
- Aceptación formal con el equipo PLAFT (UAT).

**Criterios de aceptación**:
- El pipeline completo se ejecuta en < 4 horas sobre el volumen de datos esperado.
- La herramienta del analista responde en < 5 segundos para cualquier consulta sobre
  el subgrafo persistido.
- Toda acción del analista queda registrada en el log de auditoría.
- Todos los tests pasan en el entorno de pre-producción.
- Los roles IAM han sido revisados por el equipo de seguridad del banco.

**Entregables**: sistema desplegado en AWS, runbooks operacionales, certificación de
seguridad, documentación de usuario para analistas PLAFT.

---

## ADRs del Proyecto

| ADR | Título | Estado |
|-----|--------|--------|
| [ADR-001](../../adr/ADR-001-transfer-representation.md) | Representación de transferencias (arista vs nodo) | Propuesto |
| [ADR-002](../../adr/ADR-002-graph-analytics-framework.md) | Framework de Graph Analytics | Propuesto |
| [ADR-003](../../adr/ADR-003-graph-persistence.md) | Persistencia y versionado del grafo | Propuesto |
| [ADR-004](../../adr/ADR-004-variables-feature-store.md) | Estrategia de variables y Feature Store | Propuesto |
| [ADR-005](../../adr/ADR-005-analyst-tool.md) | Tecnología para herramienta del analista | Propuesto |
| [ADR-006](../../adr/ADR-006-local-vs-production.md) | Estrategia local vs producción | Propuesto |
| [ADR-007](../../adr/ADR-007-exact-vs-approximate-algorithms.md) | Algoritmos exactos, aproximados y postergados | Propuesto |
| [ADR-008](../../adr/ADR-008-detailed-vs-aggregated-graph.md) | Grafo detallado vs grafo agregado | Propuesto |



## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
