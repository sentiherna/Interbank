# ADR-001: Representación de Transferencias — Arista vs Nodo

**Estado**: Propuesto | **Fecha**: 2026-08-06 | **Autores**: Equipo PLAFT Graph

---

## Contexto

El subgrafo PLAFT requiere modelar transferencias financieras entre cuentas. Existen dos
enfoques arquitectónicos para representar una transferencia:

**Opción A — Arista con atributos** (`Cuenta ── TRANSFIERE_A ──> Cuenta`):
Cada transferencia se modela como una arista dirigida entre la cuenta origen y la cuenta
destino, con todos los atributos como propiedades de la arista.

**Opción B — Nodo transacción** (`Cuenta ── ENVIADA_POR ──> Transferencia ── RECIBIDA_EN ──> Cuenta`):
Cada transferencia es un nodo explícito conectado a ambas cuentas mediante relaciones
de entrada y salida.

Un factor crítico: pueden existir múltiples transferencias entre las mismas cuentas
(mismo par origen-destino) en el mismo período, cada una con su propio `id_transaccion`.

---

## Decisión

**Se elige Opción A: arista con atributos**, con la restricción explícita de que cada
transferencia es una arista independiente identificada por `id_transaccion`.

**Las aristas NO se deduplicarán por par cuenta_origen + cuenta_destino.**

Para Graph Analytics (PageRank, comunidades, grados), se construirá adicionalmente
una capa agregada (peso = count o monto) sobre las aristas individuales cuando el
algoritmo lo requiera.

---

## Motivación

| Criterio | Arista (A) | Nodo (B) |
|----------|-----------|---------|
| Simplicidad del modelo | Alta | Baja (duplica nodos) |
| Filtros por fecha/monto/canal | Requiere filtrar aristas | Requiere traversal de 2 saltos |
| Trazabilidad individual | Alta (id en arista) | Alta (id en nodo) |
| Graph Analytics nativo | Directo sobre aristas | Requiere proyección |
| Escala en S3 (Parquet) | Tabla plana eficiente | Dos tablas + joins |
| Visualización para analista | Natural (arista etiquetada) | Ruido visual (nodos intermedios) |
| Compatibilidad PySpark / GraphFrames | Alta | Requiere transformación |
| Múltiples transferencias mismo par | Soportado con id_transaccion | Soportado nativamente |

---

## Separación en dos capas

- **Capa transaccional detallada**: tabla `edges_transfiere` donde cada fila = una
  transferencia con su `id_transaccion`. Usada para trazabilidad, filtros y variables
  individuales.
- **Capa agregada para Analytics**: vista o tabla derivada donde el peso de la arista
  entre dos cuentas es la suma de montos o count de transferencias. Usada para
  PageRank, componentes conectados, etc.

Esta separación evita que Graph Analytics trabaje sobre millones de aristas duplicadas
cuando el algoritmo solo necesita la estructura topológica.

---

## Consecuencias

- La tabla `edges_transfiere` puede tener múltiples filas por par cuenta-cuenta en el
  mismo período. Esto es correcto y esperado.
- La capa de Graph Analytics debe siempre indicar si opera sobre el grafo detallado o
  el agregado.
- Las variables de flujo (monto, frecuencia) se calculan siempre desde la capa detallada.
- Las variables topológicas (PageRank, grado, comunidades) pueden usar la capa agregada.

---

## Alternativas descartadas

- **Arista única agregada**: pierde la trazabilidad individual y el detalle de cada
  transacción. Incompatible con el requisito de explicabilidad (spec.md FR-023).
- **Nodo transacción**: introduce complejidad innecesaria para los algoritmos de
  Graph Analytics estándar y requiere proyecciones adicionales para graphframes.

---

## Referencias

- spec.md FR-011 (atributos de TRANSFIERE_A)
- spec.md FR-010 (trazabilidad al registro fuente)
- spec.md FR-016 (Graph Analytics)
- plan.md Capa 5 (Construcción del Subgrafo)
- plan.md Capa 7 (Graph Analytics)
