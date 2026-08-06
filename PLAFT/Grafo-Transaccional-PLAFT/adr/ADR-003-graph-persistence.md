# ADR-003: Persistencia y Versionado del Grafo

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

El subgrafo construido debe persistirse de forma que sea:
- Recuperable por versión exacta para reproducibilidad.
- Consultable por Athena para análisis ad hoc.
- Compatible con PySpark para Graph Analytics.
- Eficiente a escala de millones de aristas.

---

## Opciones evaluadas

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **Parquet en S3 (tablas planas)** | Tablas separadas por tipo de nodo/arista en Parquet | Nativo PySpark; Athena-compatible; columnar; compresión snappy | Sin transacciones ACID; versionado manual |
| **Iceberg en S3** | Formato de tabla con ACID, versionado y time travel | Time travel nativo; ACID; schema evolution | Requiere soporte Iceberg en SageMaker/Athena del banco; mayor complejidad operacional |
| **GraphML** | Formato XML estándar de grafos | Legible; soportado por herramientas de grafos | No escala (XML, sin columnar); no compatible con Athena; no productivo para millones |
| **DGL/PyG checkpoint** | Formato de framework de deep learning para grafos | Útil para GNN | No relevante para el MVP (sin modelos de grafos en v1) |

---

## Decisión

**Parquet en S3 con versionado por directorio**, estructurado así:

```
s3://bucket/graph/v{graph_version}/
  nodes/tipo=cliente/part-*.parquet
  nodes/tipo=cuenta/part-*.parquet
  nodes/tipo=alerta_plaft/part-*.parquet
  ...
  edges/tipo=transfiere_a/part-*.parquet
  edges/tipo=es_titular_de/part-*.parquet
  ...
  manifest.json
```

El `manifest.json` registra todos los metadatos de la versión del grafo. El catálogo
AWS Glue indexa cada versión como una tabla separada o mediante partición por versión.

**GraphML**: disponible como artefacto auxiliar de exportación para subgrafos pequeños
(< 10,000 nodos) en pruebas y demostración. No es el formato productivo principal.

**Iceberg**: evaluado para una versión futura si el banco confirma soporte en su entorno
Athena/SageMaker. La arquitectura de directorios Parquet es compatible con una migración
a Iceberg sin cambiar la lógica de negocio.

---

## Estructura del manifiesto `manifest.json`

```json
{
  "graph_version": "v-{uuid4}",
  "run_id": "uuid4",
  "created_at": "ISO-8601",
  "code_version": "git-semver-o-tag",
  "git_commit": "sha-7",
  "date_cutoff": "YYYY-MM-DD",
  "period": "YYYY-MM",
  "selection_criteria": {"alerta": true, "ros": true, "pep": true, "caso": true, "lista": false},
  "expansion_depth": 1,
  "algorithm_params": {},
  "datasets": {
    "clientes": {"s3_path": "...", "version": "...", "checksum": "..."},
    "transferencias": {"s3_path": "...", "version": "...", "checksum": "..."}
  },
  "counts": {
    "nodes_cliente": N,
    "nodes_cuenta": N,
    "edges_transfiere_a": N
  },
  "checksum_nodes": "sha256-...",
  "checksum_edges": "sha256-..."
}
```

---

## Versionado de datasets de entrada

Cada dataset de entrada se versiona por:
1. Ruta S3 fija por período (p.ej. `transferencias/yyyy=2026/mm=07/`).
2. Checksum del archivo Parquet al momento de la ingestión.
3. Registro en `run_manifest.json` bajo `datasets`.

---

## Consecuencias

- La recuperación de cualquier versión del grafo requiere solo el `graph_version`.
- Dos runs con los mismos parámetros y mismos checksums de dataset producen grafos
  estructuralmente idénticos (reproducibilidad).
- El Glue Catalog debe tener una tabla por tipo de nodo y arista.
- La capa de consultas (Athena) puede filtrar por `graph_version` como partición.

---

## Referencias

- plan.md Capa 6 (Persistencia Versionada)
- research.md Decisión 5 (Formato de Persistencia)
- spec.md FR-014/015
