# Architecture Decision Records (ADR)

Este directorio contiene los ADR del proyecto **Plataforma Analítica PLAFT basada en Grafos**.

Los ADR documentan las decisiones técnicas significativas: qué se eligió, por qué,
y qué alternativas fueron evaluadas. Todo cambio arquitectónico relevante DEBE documentarse
mediante un ADR (Constitución v3.0.0, Principio XII).

---

## Índice

| ADR | Título | Estado | Ubicación |
|-----|--------|--------|-----------|
| ADR-001 | Representación de transferencias (arista vs nodo) | Propuesto | [adr/ADR-001-transfer-representation.md](../../adr/ADR-001-transfer-representation.md) |
| ADR-002 | Framework de Graph Analytics | Propuesto | [adr/ADR-002-graph-analytics-framework.md](../../adr/ADR-002-graph-analytics-framework.md) |
| ADR-003 | Persistencia y versionado del grafo | Propuesto | [adr/ADR-003-graph-persistence.md](../../adr/ADR-003-graph-persistence.md) |
| ADR-004 | Estrategia de variables y Feature Store | Propuesto | [adr/ADR-004-variables-feature-store.md](../../adr/ADR-004-variables-feature-store.md) |
| ADR-005 | Tecnología para herramienta del analista | Propuesto | [adr/ADR-005-analyst-tool.md](../../adr/ADR-005-analyst-tool.md) |
| ADR-006 | Estrategia local vs producción | Propuesto | [adr/ADR-006-local-vs-production.md](../../adr/ADR-006-local-vs-production.md) |
| ADR-007 | Algoritmos exactos, aproximados y postergados | Propuesto | [adr/ADR-007-exact-vs-approximate-algorithms.md](../../adr/ADR-007-exact-vs-approximate-algorithms.md) |
| ADR-008 | Grafo detallado vs grafo agregado | Propuesto | [adr/ADR-008-detailed-vs-aggregated-graph.md](../../adr/ADR-008-detailed-vs-aggregated-graph.md) |

---

## Cómo crear un nuevo ADR

1. Copiar la plantilla `adr/template.md`.
2. Nombrar el archivo `ADR-NNN-descripcion-corta.md`.
3. Completar: Contexto, Opciones evaluadas, Decisión, Motivación, Consecuencias.
4. Agregar la entrada a la tabla de este índice.
5. Referenciar el ADR en el `plan.md` y en el código si corresponde.

---

## Estados posibles

- **Propuesto**: en revisión, aún no adoptado.
- **Adoptado**: decisión vigente.
- **Deprecado**: reemplazado por un ADR posterior.
- **Rechazado**: evaluado y descartado explícitamente.
