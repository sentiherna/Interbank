# ADR-002: Framework de Graph Analytics

**Estado**: Propuesto | **Fecha**: 2026-08-06 | **Autores**: Equipo PLAFT Graph

---

## Contexto

El MVP requiere ejecutar algoritmos de Graph Analytics sobre el subgrafo de clientes
sospechosos en la infraestructura AWS aprobada (SageMaker Processing + PySpark). La
elección del framework impacta directamente en la viabilidad técnica, el costo y la
mantenibilidad del sistema.

**Restricciones**:
- Plataforma productiva: SageMaker Processing con Python 3.12 + PySpark.
- Sin Neo4j ni bases de datos de grafos externas.
- Sin costos de licencia no aprobados.
- Datos de desarrollo: pandas local; producción: PySpark.

---

## Opciones evaluadas

### Opción A: GraphFrames (Apache Spark)

Librería open-source que extiende Apache Spark DataFrames con primitivas de grafos.
Soporta: PageRank, Connected Components, Label Propagation, BFS, Shortest Paths,
Triangle Count.

| Pro | Contra |
|-----|--------|
| Nativa en ecosistema PySpark | Mantenimiento comunitario (no Apache core) |
| Compatible con SageMaker Processing | API Python limitada respecto a Scala |
| No requiere infraestructura adicional | Eigenvector y Betweenness no incluidos |
| Soporta grafos dirigidos y no dirigidos | Requiere validación en SageMaker 3.12 |

### Opción B: cuGraph (NVIDIA RAPIDS)

Librería GPU-accelerated para Graph Analytics. Compatible con SageMaker si se usan
instancias GPU (ml.p3, ml.g4).

| Pro | Contra |
|-----|--------|
| Muy rápido en algoritmos costosos | Requiere instancias GPU (costo elevado) |
| API similar a NetworkX | Dependencia de driver NVIDIA |
| Soporta Betweenness, Eigenvector | No disponible en instancias CPU estándar |

### Opción C: NetworkX

Librería Python estándar para análisis de grafos en memoria.

| Pro | Contra |
|-----|--------|
| Simple, bien documentada | No escala a millones de nodos en producción |
| Soporta todos los algoritmos | Requiere grafo completo en memoria (RAM) |
| Ideal para desarrollo local y pruebas | No integración nativa con PySpark |

### Opción D: Implementación propia con PySpark/Spark SQL

Implementar algoritmos específicos directamente sobre DataFrames de Spark (p.ej., PageRank
iterativo, BFS con joins, componentes con Union-Find).

| Pro | Contra |
|-----|--------|
| Sin dependencias adicionales | Alto costo de desarrollo y mantenimiento |
| Control total sobre optimizaciones | Propenso a errores de implementación |
| Compatible con cualquier versión de Spark | Solo viable para algoritmos simples |

---

## Decisión

**Estrategia híbrida**:

| Entorno | Framework | Justificación |
|---------|-----------|---------------|
| Producción AWS | **GraphFrames** como primera opción | Nativo PySpark, sin infraestructura adicional |
| Algoritmos no disponibles en GraphFrames | Implementación Spark/SQL o Spark GraphX | Betweenness, Closeness, Eigenvector |
| Desarrollo y pruebas locales | **NetworkX** | Simplicidad, validación de lógica |
| Futuro (si escala lo requiere) | **cuGraph** | Tras pruebas de escala en GPU |

---

## Clasificación de algoritmos por viabilidad

| Algoritmo | Clasificación | Framework | Observación |
|-----------|--------------|-----------|-------------|
| in-degree / out-degree | Obligatorio MVP | Spark SQL / GraphFrames | O(E), fácil distribución |
| monto recibido/enviado | Obligatorio MVP | Spark SQL | Agregación simple |
| contrapartes únicas | Obligatorio MVP | Spark SQL | Count distinct |
| PageRank | Obligatorio MVP | GraphFrames | Convergencia con damping=0.85 |
| Connected Components (WCC) | Obligatorio MVP | GraphFrames | Escala bien |
| Louvain Community Detection | Obligatorio MVP | GraphFrames (LPA como proxy) o implementación | Louvain nativo no disponible en GraphFrames; Label Propagation como aproximación |
| Distancia min. a señal de riesgo | Obligatorio MVP | BFS con Spark SQL | Solo hasta profundidad ≤ 5 |
| Exposición directa e indirecta | Obligatorio MVP | Spark SQL | Joins sobre tablas de señales |
| Betweenness Centrality | Experimental | Implementación aproximada | O(V·E), requiere muestreo |
| Closeness Centrality | Experimental | Implementación aproximada | O(V²), solo sobre componentes pequeños |
| Eigenvector Centrality | Experimental | GraphFrames (Power Iteration) | Requiere límite de iteraciones; riesgo de no convergencia |
| Label Propagation | Viable con condición | GraphFrames | Convergencia no garantizada; usar como aproximación de Louvain |
| Shortest Paths masivos | Postergado | GraphFrames BFS | Solo sobre subgrafos seleccionados |

---

## Pendiente de validación (Fase 0)

- Confirmar versión de graphframes compatible con PySpark 3.x en SageMaker Processing.
- Validar que `graphframes` puede instalarse en el entorno aprobado por el banco.
- Si graphframes no está disponible, usar Spark GraphX via Scala o implementación propia.

---

## Consecuencias

- Los algoritmos obligatorios del MVP son todos viables con GraphFrames + Spark SQL.
- Louvain requiere usar Label Propagation como aproximación (documentado como tal en cada run).
- Betweenness, Closeness y Eigenvector se marcan como experimentales con umbrales definidos
  en ADR-007.
- La lógica de negocio (selección, variables) es independiente del framework de Analytics.
  Cambiar de GraphFrames a cuGraph no requiere reescribir las capas de negocio.

---

## Referencias

- plan.md Capa 7 (Graph Analytics)
- ADR-007 (Algoritmos exactos vs aproximados)
- research.md Decisión 1 (Motor de grafos)
- spec.md FR-016/017/018/019
