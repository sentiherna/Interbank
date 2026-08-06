# Research: MVP — Plataforma Analítica PLAFT basada en Grafos

**Feature**: `001-mvp-graph-variables` | **Date**: 2026-08-06 | **Plan**: [plan.md](plan.md)

---

## Decisión 1: Motor de Procesamiento de Grafos (ADR-001 — Pendiente)

**Pregunta**: ¿Qué motor usar para Graph Analytics a escala de millones de nodos en AWS?

**Contexto**: NetworkX no es apto para producción con millones de nodos. PySpark es el
estándar del proyecto (Constitución v3.0.0, Principio II).

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **GraphX** (Spark nativo) | API de grafos integrada en Apache Spark | Nativa en PySpark; sin dependencias extra; SageMaker compatible | API Java/Scala; wrapper Python limitado (graphframes) |
| **graphframes** | Wrapper Python de GraphX | API Python; soporta PageRank, Connected Components, BFS | Dependencia adicional; mantenimiento comunitario |
| **cuGraph** (NVIDIA RAPIDS) | GPU-accelerated graph analytics | Muy rápido para algoritmos costosos | Requiere GPU en SageMaker; costo más alto |
| **NetworkX** | Librería Python estándar | Simple, bien documentada | Solo para pruebas locales y subgrafos pequeños |

**Recomendación preliminar**: graphframes sobre PySpark como primera opción de producción.
Verificar disponibilidad de la versión compatible con SageMaker Processing. Si graphframes
presenta limitaciones, evaluar cuGraph en instancias GPU.

**Decisión final**: PENDIENTE — requiere validación en entorno AWS del banco (Fase 0).

---

## Decisión 2: Algoritmos Experimentales — Umbrales de Habilitación (ADR-002 — Pendiente)

**Pregunta**: ¿En qué condiciones se ejecutan los algoritmos experimentales?

**Contexto**: Betweenness Centrality (O(V·E)), Eigenvector Centrality (riesgo de no
convergencia), Closeness Centrality (O(V²)) y Shortest Paths masivos son computacionalmente
costosos. Su uso sin restricciones puede causar timeouts.

**Criterios de habilitación propuestos**:

| Algoritmo | Umbral de nodos | Umbral de tiempo | Estrategia de aproximación |
|-----------|-----------------|-----------------|---------------------------|
| Betweenness Centrality | < 50,000 nodos | < 30 min | Muestreo aleatorio de nodos pivote |
| Closeness Centrality | < 50,000 nodos | < 30 min | BFS truncado |
| Eigenvector Centrality | < 100,000 nodos | < 15 min | Límite de 100 iteraciones |
| Label Propagation | < 500,000 nodos | < 60 min | Semilla fija para reproducibilidad |
| Shortest Paths masivos | < 10,000 nodos | < 60 min | Solo sobre subgrafos de interés |

**Decisión final**: PENDIENTE — se define en Fase 3 tras pruebas de escala (ADR-002).

---

## Decisión 3: Tecnología de la Herramienta del Analista (ADR-003 — Pendiente)

**Pregunta**: ¿Qué tecnología usar para la herramienta interna de investigación?

**Opciones evaluadas**:

### Opción A: Streamlit + SageMaker Studio

| Criterio | Evaluación |
|----------|-----------|
| Compatibilidad AWS | Alta — funciona en SageMaker Studio Apps |
| Visualización de grafos | Requiere librería adicional (pyvis, networkx draw, streamlit-agraph) |
| Control de acceso | Implementado a nivel de Studio (IAM + SSO) |
| Esfuerzo de desarrollo | Medio — todo en Python, curva de aprendizaje baja |
| Flexibilidad UI | Alta — código Python libre |
| Visualización de nodos/relaciones con forma | Sí (con pyvis o similar) |
| Filtros interactivos | Sí (Streamlit widgets nativos) |
| Exportación | Sí (CSV, JSON) |
| Recomendado si | El equipo controla Python y SageMaker Studio |

### Opción B: Panel (HoloViz) + SageMaker Studio

| Criterio | Evaluación |
|----------|-----------|
| Compatibilidad AWS | Alta |
| Visualización de grafos | Holoviews + NetworkX; visualizaciones más ricas |
| Control de acceso | Igual que Streamlit |
| Esfuerzo de desarrollo | Medio-alto — curva de aprendizaje mayor |
| Flexibilidad UI | Muy alta |

**Recomendación preliminar**: **Streamlit** sobre SageMaker Studio como primera opción,
dado su ecosistema Python y baja curva de aprendizaje. La diferenciación de nodos y
relaciones se implementará mediante `streamlit-agraph` o `pyvis`, que soportan
forma/iconografía además de color.

**Decisión final**: PENDIENTE — requiere validación con equipos de seguridad y
arquitectura del banco (Fase 0, ADR-003).

---

## Decisión 4: Estrategia de Actualización Incremental (ADR-004 — Pendiente)

**Pregunta**: ¿Cuándo y cómo implementar actualizaciones incrementales del subgrafo?

**Contexto**: en el MVP se reconstruye el subgrafo completo en cada ejecución. Esto es
correcto para la primera versión, pero puede ser costoso con frecuencias altas de
ejecución.

**Estrategia MVP (Fase 0-7)**: reconstrucción completa. El subgrafo es relativamente
pequeño (clientes sospechosos, no toda la cartera). La persistencia por versión permite
reutilizar grafos anteriores para analítica sin reconstruir.

**Estrategia futura (post-MVP)**:
- Detección de cambios en datasets de entrada por partition + checksum.
- Actualización incremental de nodos/relaciones modificados.
- Re-ejecución de Graph Analytics solo sobre subgrafos afectados.

**Decisión final**: PENDIENTE — se define en Fase 7 (ADR-004).

---

## Decisión 5: Formato de Persistencia del Grafo

**Decisión**: **Apache Parquet** en Amazon S3.

**Rationale**:
- Compatible con PySpark, pandas y Athena sin conversión.
- Compresión eficiente (snappy); esquema embebido.
- Particionamiento nativo por columnas.
- Lectura selectiva de columnas (column pruning).
- Alternativas descartadas: JSON (sin tipado estricto, voluminoso), ORC (menor soporte
  en Python), formato de grafo propietario (no compatible con Athena).

---

## Decisión 6: Catálogo de Metadatos

**Decisión**: **AWS Glue Data Catalog** como catálogo central.

**Rationale**: nativo de AWS; integrado con Athena para consultas ad hoc; integrado con
SageMaker para descubrimiento de datasets; sin costo adicional de infraestructura.

---

## Decisión 7: Versionado de Experimentos y Artefactos

**Decisión**: **MLflow** para tracking de runs, parámetros, métricas y artefactos.

**Rationale**: aprobado en Constitución v3.0.0; compatible con SageMaker; provee interfaz
de comparación entre runs; permite registrar `run_manifest.json` como artefacto del run.

---

## Decisión 8: Modelo de Nodo Cliente Unificado

**Decisión**: un único tipo de nodo `Cliente` con atributos de rol.

**Rationale**: en el negocio bancario, un cliente puede ser objetivo de investigación
y contraparte de otro cliente objetivo simultáneamente. Tipos separados crearían
duplicados de nodo y complicarían los algoritmos de Graph Analytics. Los atributos de
rol (`es_cliente_objetivo`, `es_contraparte`, `nivel_expansion`) capturan la semántica
sin duplicar nodos.

**Corrección aplicada a spec.md**: tipos separados `Cliente Sospechoso` y `Cliente
Contraparte` reemplazados por nodo único `Cliente` con atributos de rol (C-01).

---

## Decisión 9: Identidad de Transferencias

**Decisión**: `id_transaccion` es la clave de identidad. Múltiples transferencias entre
las mismas cuentas NO se deduplicarán si poseen identificadores distintos.

**Rationale**: en el análisis PLAFT, la frecuencia y el volumen de transferencias entre
las mismas contrapartes es una señal analítica crítica. Deduplicar por par cuenta-cuenta
eliminaría esta información. La identidad está dada por el identificador único de la
fuente transaccional.

**Corrección aplicada a spec.md**: atributo `id_transaccion` documentado como clave de
identidad con nota explícita sobre no-deduplicación (C-02).

---

## Decisión 10: Separación de Señales de Riesgo

**Decisión**: las señales Alerta PLAFT, ROS, Condición PEP y Caso Investigado se
mantienen como nodos y variables separadas. No se combinan en una variable binaria única
sin regla explícita, versionada y documentada.

**Rationale**: la Condición PEP es un factor de debida diligencia reforzada, no evidencia
automática de operación sospechosa. Combinar señales sin transparencia impediría la
explicabilidad requerida por la Constitución (Principio VIII) y comprometería el juicio
del analista. Cada variable de riesgo expone su señal de origen.

---

## Pendientes de Investigación (Fase 0)

- [ ] Confirmar versión de graphframes compatible con SageMaker Processing 3.12.
- [ ] Validar acceso a SageMaker Feature Store desde el entorno del banco.
- [ ] Confirmar protocolo de autenticación SSO para la herramienta del analista.
- [ ] Definir TTL/retención de logs de auditoría con equipo de compliance.
- [ ] Validar estructura de particionamiento S3 con equipo de datos del banco.
- [ ] Confirmar si existe catálogo Glue ya configurado en la organización.
- [ ] Obtener datasets sintéticos representativos del equipo PLAFT para pruebas.

---

## Decisión 11: Representación de Transferencias (Arista vs Nodo)

Ver [ADR-001](../../adr/ADR-001-transfer-representation.md) para el análisis completo.

**Decisión**: arista con atributos (`TRANSFIERE_A`), con separación en capa detallada
y capa agregada. Cada `id_transaccion` es una arista independiente; no se deduplican
por par cuenta-cuenta.

---

## Decisión 12: Separación Grafo Detallado y Grafo Agregado

Ver [ADR-008](../../adr/ADR-008-detailed-vs-aggregated-graph.md) para el análisis completo.

**Decisión**: mantener ambas capas. La capa detallada se persiste; la agregada se
genera en memoria antes de ejecutar algoritmos topológicos (no persiste como tabla
principal del grafo).

---

## Decisión 13: Variables MVP — Priorización

### Variables MVP Obligatorias (Fase 4)

Las variables mínimas que deben estar disponibles al finalizar la Fase 4:

**Centralidad**:
- `grado_entrada`, `grado_salida`, `grado_total`
- `pagerank` (damping=0.85, iter=100)

**Conectividad**:
- `contrapartes_unicas` (clientes únicos con transferencia)
- `cuentas_propias` (cuentas con titularidad)
- `componente_conectado` (WCC)
- `tamano_componente`

**Comunidades**:
- `comunidad_id` (Louvain o Label Propagation como aproximación)
- `tamano_comunidad`

**Flujo de dinero**:
- `monto_recibido_total`, `monto_enviado_total`
- `tx_recibidas`, `tx_enviadas`
- `ratio_enviado_recibido`

**Patrones transaccionales**:
- `frecuencia_tx`, `monto_promedio_tx`, `canales_distintos`

**Anomalías estructurales**:
- `es_intermediario` (grado_entrada > p75 AND grado_salida > p75)

**Riesgo de vecinos** (señales diferenciadas):
- `contrapartes_con_alerta`, `contrapartes_con_ros`, `contrapartes_con_pep`, `contrapartes_con_caso`
- `monto_recibido_de_alerta`, `monto_enviado_a_pep`
- `prop_contrapartes_investigadas`

**Riesgo propagado**:
- `distancia_min_alerta`, `distancia_min_ros`, `distancia_min_pep`, `distancia_min_caso`
- `pct_flujo_sospechosos`

### Variables Recomendadas (Fase 4+)

- `concentracion_contraparte` (proporción del flujo hacia contraparte principal)
- `desviacion_grado` (Z-score del grado respecto a la comunidad)
- `exposicion_ponderada_senales` (ponderación configurable por tipo de señal)
- `dias_activos` (días distintos con al menos una transacción)
- `modularidad_local`
- `senales_distintas_vecinos`

### Variables Experimentales (Fase 3+ condicionadas a ADR-007)

- Variables basadas en Betweenness Centrality aproximada
- Variables basadas en Closeness Centrality aproximada
- Variables de Eigenvector Centrality

### Variables Futuras (Post-MVP)

- Variables basadas en embeddings de grafos (GNN)
- Variables basadas en motifs o patrones estructurales
- Variables derivadas de documentación KYC

---

## Decisión 14: Ponderación de Señales de Riesgo

Las señales Alerta, ROS, PEP y Caso NO son equivalentes automáticamente. Las variables
de exposición ponderada usan pesos **configurables** por ejecución, documentados en el
`run_manifest.json`. El MVP no fija pesos definitivos; propone valores iniciales que
deben ser validados por el equipo PLAFT.

**Propuesta inicial de pesos relativos** (a validar con PLAFT):

| Señal | Peso inicial propuesto | Razonamiento |
|-------|----------------------|-------------|
| ROS | 1.0 | Señal de investigación formal |
| Caso Investigado | 0.9 | Investigación activa/cerrada |
| Alerta PLAFT | 0.7 | Señal automatizada, puede ser falso positivo |
| PEP | 0.3 | Factor de due diligence, no de sospecha directa |

**Importante**: PEP tiene peso más bajo porque no indica sospecha. Su presencia activa
controles de due diligence reforzada, no de investigación por lavado de activos.

Los pesos se almacenan en la configuración del run y se registran en el manifest.
Cambiar los pesos genera un nuevo run (nueva versión de variables) para trazabilidad.

