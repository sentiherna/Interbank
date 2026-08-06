# ADR-007: Algoritmos Exactos, Aproximados y Postergados

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

No todos los algoritmos de Graph Analytics son viables a escala sobre el subgrafo de
clientes sospechosos. Se necesita un criterio claro para clasificar y gestionar algoritmos
según su costo computacional y beneficio analítico.

---

## Criterios de clasificación

| Criterio | Descripción |
|----------|-------------|
| Complejidad computacional | O(V), O(E), O(V·E), O(V²), etc. |
| Escala esperada | Nodos: 10k–500k; Aristas: 1M–50M |
| Tiempo máximo aceptable por run | < 4 horas en instancia ml.m5.4xlarge |
| Disponibilidad en GraphFrames | Si/No |
| Beneficio analítico en el MVP | Alto/Medio/Bajo |

---

## Clasificación definitiva

### Obligatorios para el MVP (viables a escala completa)

| Algoritmo | Complejidad | Tiempo estimado | Observación |
|-----------|------------|-----------------|-------------|
| in-degree / out-degree | O(E) | Segundos | Spark SQL trivial |
| monto recibido/enviado | O(E) | Segundos | Spark SQL |
| contrapartes únicas | O(E) | Segundos | Count distinct |
| PageRank | O(k·E) | Minutos | k=100 iteraciones |
| Connected Components (WCC) | O(V+E) | Minutos | GraphFrames |
| Exposición directa a señales | O(E) | Segundos | Join |
| Distancia mínima a señal | O(V·E) sobre subgrafo | Minutos | BFS truncado a profundidad 5 |

### Viables sobre componentes o ego-networks (no sobre grafo completo)

| Algoritmo | Estrategia | Condición |
|-----------|-----------|-----------|
| Louvain | Label Propagation como aproximación sobre grafo completo; Louvain exacto sobre componentes < 50k nodos | Documentar que es aproximación |
| Eigenvector Centrality | Power Iteration con límite 100 iter; solo sobre componente principal | Puede no converger; registrar convergencia |

### Aproximados (con muestreo o truncado)

| Algoritmo | Estrategia de aproximación | Umbral de activación |
|-----------|---------------------------|----------------------|
| Betweenness Centrality | Muestreo aleatorio de nodos pivote (< 1000) | Solo si nodos del componente < 50k |
| Closeness Centrality | BFS truncado a profundidad 5 desde cada nodo | Solo si nodos del componente < 10k |
| Shortest Paths masivos | Solo entre pares de nodos de interés (objetivo ↔ señal) | Siempre mediante BFS dirigido |

### Experimentales (Fase 3+, requieren validación empírica)

| Algoritmo | Bloqueador | Acción |
|-----------|-----------|--------|
| Betweenness exacto | Costo O(V·E) inviable en producción | Implementar aproximación + ADR de umbral |
| Closeness exacto | O(V²), no escala | Implementar sobre componentes pequeños |
| Label Propagation estocástico | Convergencia no determinista | Fijar semilla para reproducibilidad |

### Postergados (post-MVP)

| Algoritmo | Motivo | Fase |
|-----------|--------|------|
| Triangle Count | Bajo beneficio analítico en MVP | Fase 3+ |
| Motif Detection | Alta complejidad; requiere caso de uso claro | Fase 5+ |
| GNN embeddings | Fuera del alcance del MVP | Fase 6+ (GraphRAG) |

---

## Política de habilitación de algoritmos experimentales

Antes de ejecutar un algoritmo aproximado o experimental en producción, se debe registrar
en el `run_manifest.json`:

```json
{
  "experimental_algorithms": {
    "betweenness_approx": {
      "enabled": true,
      "reason": "Componente principal < 50k nodos",
      "sample_size": 500,
      "result_flag": "aproximado"
    }
  }
}
```

Los resultados marcados como `"aproximado"` en las variables deben propagarse a los
metadatos de cada variable afectada.

---

## Consecuencias

- Los algoritmos obligatorios del MVP no requieren aproximaciones.
- La primera implementación puede omitir completamente los algoritmos experimentales.
- Las variables derivadas de algoritmos aproximados deben marcarse explícitamente como
  aproximadas en su metadata.
- El catálogo de variables debe indicar para cada variable si depende de un algoritmo
  exacto o aproximado.

---

## Referencias

- ADR-002 (Framework de Graph Analytics)
- plan.md Capa 7 (Graph Analytics)
- research.md Decisión 2
