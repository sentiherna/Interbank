# ADR-008: Separación entre Grafo Detallado y Grafo Agregado

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

El subgrafo PLAFT contiene transferencias individuales (capa detallada). Sin embargo,
algunos algoritmos de Graph Analytics son más eficientes operando sobre un grafo
agregado donde el peso de la arista entre dos cuentas es la suma de montos o el count
de transferencias.

Se debe decidir cuándo usar cada capa y cómo materializarlas.

---

## Definición de capas

### Capa transaccional detallada

- **Tabla**: `edges_transfiere_a`
- **Cardinalidad**: una fila por transferencia (`id_transaccion`)
- **Uso**: trazabilidad individual, variables de flujo (montos, frecuencia), filtros por
  fecha/monto/canal/estado, visualización en herramienta del analista.

### Capa agregada

- **Tabla**: `edges_transfiere_a_agg`
- **Cardinalidad**: una fila por par (`cuenta_origen`, `cuenta_destino`, `periodo`)
- **Atributos**: `count_tx`, `monto_total`, `monto_promedio`, `fecha_primera`, `fecha_ultima`,
  `monedas_distintas`, `canales_distintos`
- **Uso**: Graph Analytics (PageRank, componentes, comunidades), cálculo de grados ponderados.

---

## Reglas de materialización

La capa agregada se construye como paso intermedio dentro de la Capa 7 (Graph Analytics),
**no es persistida como tabla principal del grafo**. Se genera en memoria (PySpark) a
partir de la capa detallada antes de ejecutar los algoritmos que la requieren.

**Excepción**: si el cálculo repetido de la capa agregada resulta costoso (>10 min en
producción), puede persistirse como tabla auxiliar en S3 junto a los resultados de
Graph Analytics.

---

## Decisión

**Se mantienen dos capas separadas**:
1. `edges_transfiere_a`: detallada, siempre persistida, clave de identidad = `id_transaccion`.
2. Agregación ad hoc generada en Spark antes de ejecutar algoritmos topológicos.

No se persiste la capa agregada como tabla principal del grafo para evitar ambigüedad
sobre qué datos usar para trazabilidad.

---

## Cuándo usar cada capa

| Caso de uso | Capa a usar |
|-------------|------------|
| Trazabilidad de una transferencia | Detallada |
| Cálculo de monto enviado/recibido | Detallada |
| Filtros por fecha, canal, monto | Detallada |
| PageRank | Agregada (grafo dirigido ponderado) |
| Connected Components | Agregada (grafo no dirigido binario) |
| Louvain / Label Propagation | Agregada |
| Distancia mínima a señal de riesgo | Agregada (topology only) |
| Variable: concentración de flujo | Detallada |
| Variable: monto recibido de PEP | Detallada |
| Visualización del analista | Detallada (con límite de aristas mostradas) |

---

## Límite de visualización

Para la herramienta del analista, mostrar aristas individuales puede ser costoso si un
cliente tiene miles de transferencias. Se implementa una paginación o límite configurable
(default: 200 aristas más recientes) con la opción de ampliar el filtro.

---

## Consecuencias

- La capa de Graph Analytics recibe la capa detallada y genera la agregada internamente.
- Los resultados de Analytics siempre indican si se calcularon sobre la capa detallada
  o la agregada.
- La herramienta del analista siempre consulta la capa detallada para trazabilidad.

---

## Referencias

- ADR-001 (Transfer Representation)
- ADR-002 (Graph Analytics Framework)
- plan.md Capa 7 (Graph Analytics)
- plan.md Capa 12 (Herramienta de Investigación)
