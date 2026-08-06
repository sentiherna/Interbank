# Data Model: MVP — Plataforma Analítica PLAFT basada en Grafos

**Feature**: `001-mvp-graph-variables` | **Date**: 2026-08-06 | **Plan**: [plan.md](plan.md)

---

## Nodos del Subgrafo

### Cliente

Nodo central. Un único tipo de nodo representa tanto clientes objetivo como contrapartes.

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | Identificador único del cliente en el banco |
| `es_cliente_objetivo` | BOOLEAN | Sí | Cumple criterio de selección de sospechoso |
| `es_contraparte` | BOOLEAN | Sí | Incorporado por expansión del subgrafo |
| `motivos_seleccion` | ARRAY<STRING> | No | Lista de criterios que lo identificaron como objetivo |
| `nivel_expansion` | INTEGER | Sí | 0 = cliente objetivo, 1 = contraparte directa, 2+ = expansión adicional |
| `tiene_alerta` | BOOLEAN | Sí | Tiene al menos una alerta PLAFT asociada |
| `tiene_ros` | BOOLEAN | Sí | Tiene al menos un ROS asociado |
| `es_pep` | BOOLEAN | Sí | Está identificado como PEP |
| `tiene_caso` | BOOLEAN | Sí | Tiene al menos un caso investigado asociado |
| `dataset_origen` | STRING | Sí | Nombre del dataset fuente |
| `registro_fuente` | STRING | Sí | Identificador del registro en el dataset fuente |
| `run_id` | STRING | Sí | Identificador de la ejecución |
| `graph_version` | STRING | Sí | Versión del grafo en el que fue incluido |

**Invariante**: `es_cliente_objetivo OR es_contraparte` debe ser TRUE. Un nodo puede
tener ambos en TRUE simultáneamente.

---

### Cuenta

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `cuenta_id` | STRING | Sí | Identificador único de la cuenta |
| `tipo_cuenta` | STRING | No | Tipo de producto bancario de la cuenta |
| `moneda` | STRING | No | Moneda de la cuenta |
| `estado` | STRING | No | Estado de la cuenta (activa, cerrada, bloqueada) |
| `fecha_apertura` | DATE | No | Fecha de apertura |
| `dataset_origen` | STRING | Sí | Nombre del dataset fuente |
| `registro_fuente` | STRING | Sí | Clave del registro fuente |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### Producto

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `producto_id` | STRING | Sí | Identificador único del producto |
| `tipo_producto` | STRING | Sí | Categoría del producto financiero |
| `estado` | STRING | No | Estado del producto |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### Alerta PLAFT

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `alerta_id` | STRING | Sí | Identificador único de la alerta |
| `cliente_id` | STRING | Sí | Cliente al que pertenece la alerta |
| `tipo_alerta` | STRING | Sí | Tipo o código de la alerta |
| `fecha_alerta` | TIMESTAMP | Sí | Fecha de generación de la alerta |
| `estado` | STRING | No | Estado de la alerta (activa, cerrada, escalada) |
| `periodo` | STRING | No | Período al que corresponde (YYYY-MM) |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### ROS

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `ros_id` | STRING | Sí | Identificador único del ROS |
| `cliente_id` | STRING | Sí | Cliente al que pertenece el ROS |
| `fecha_reporte` | DATE | Sí | Fecha del reporte |
| `estado` | STRING | No | Estado del ROS |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### Condición PEP

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `pep_id` | STRING | Sí | Identificador del registro PEP |
| `cliente_id` | STRING | Sí | Cliente identificado como PEP |
| `categoria_pep` | STRING | No | Categoría de PEP (nacional, extranjero, familiar, etc.) |
| `fecha_inicio` | DATE | No | Fecha de inicio de la condición PEP |
| `fecha_fin` | DATE | No | Fecha de fin (null si vigente) |
| `vigente` | BOOLEAN | Sí | Si la condición PEP está vigente a la fecha de corte |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

**Nota**: la Condición PEP es un factor de debida diligencia reforzada, NO evidencia
automática de operación sospechosa.

---

### Caso Investigado

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `caso_id` | STRING | Sí | Identificador único del caso |
| `cliente_id` | STRING | Sí | Cliente asociado al caso |
| `tipo_caso` | STRING | No | Tipología del caso |
| `fecha_apertura` | DATE | Sí | Fecha de apertura |
| `fecha_cierre` | DATE | No | Fecha de cierre (null si abierto) |
| `estado` | STRING | Sí | Estado del caso (abierto, cerrado, archivado) |
| `resultado` | STRING | No | Resultado del caso si cerrado |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### Documento

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `documento_id` | STRING | Sí | Identificador único del documento |
| `cliente_id` | STRING | Sí | Cliente al que pertenece el documento |
| `tipo_documental` | STRING | Sí | Tipo de documento (DNI, contrato, estado de cuenta, etc.) |
| `nombre` | STRING | No | Nombre descriptivo del documento |
| `fecha_documento` | DATE | No | Fecha del documento |
| `fecha_incorporacion` | TIMESTAMP | No | Fecha de incorporación al sistema |
| `referencia_s3` | STRING | No | Ruta en S3 donde reside el documento |
| `sistema_origen` | STRING | Sí | Sistema que generó el documento |
| `estado` | STRING | No | Estado del documento |
| `version_doc` | STRING | No | Versión del documento |
| `checksum` | STRING | No | Hash de integridad del archivo |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

## Relaciones del Subgrafo

### ES_TITULAR_DE (Cliente → Cuenta)

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | Nodo origen |
| `cuenta_id` | STRING | Sí | Nodo destino |
| `tipo_titularidad` | STRING | No | Principal, cotitular, apoderado |
| `fecha_inicio` | DATE | No | Fecha de inicio de la titularidad |
| `fecha_fin` | DATE | No | Fecha de fin (null si vigente) |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

**Nota**: una cuenta puede tener múltiples titulares. Cada relación es independiente.

---

### POSEE (Cliente → Producto)

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | |
| `producto_id` | STRING | Sí | |
| `fecha_contratacion` | DATE | No | |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

### TRANSFIERE_A (Cuenta → Cuenta)

Relación dirigida. Cada transferencia es una instancia independiente identificada por
`id_transaccion`. Múltiples transferencias entre las mismas cuentas NO se deduplicarán.

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `id_transaccion` | STRING | Sí | Clave de identidad única de la transferencia |
| `cuenta_origen` | STRING | Sí | Cuenta que envía los fondos |
| `cuenta_destino` | STRING | Sí | Cuenta que recibe los fondos |
| `cliente_origen` | STRING | No | Cliente resolvible del origen |
| `cliente_destino` | STRING | No | Cliente resolvible del destino |
| `fecha_hora` | TIMESTAMP | Sí | Fecha y hora de la transferencia |
| `monto` | DECIMAL(18,2) | Sí | Monto de la transferencia |
| `moneda` | STRING | Sí | Código de moneda (ISO 4217) |
| `canal` | STRING | No | Canal de la transacción |
| `estado` | STRING | Sí | Estado de la transacción (ejecutada, anulada, pendiente) |
| `periodo` | STRING | No | Período (YYYY-MM) para particionamiento |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

**Regla de calidad**: transacciones con `estado = 'ANULADA'` NO se integran al grafo
como relaciones activas.

---

### TIENE_ALERTA, TIENE_ROS, TIENE_CONDICION_PEP, TIENE_CASO, TIENE_DOCUMENTO

Comparten estructura base:

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | Nodo origen (Cliente) |
| `{nodo}_id` | STRING | Sí | Nodo destino (Alerta/ROS/PEP/Caso/Documento) |
| `dataset_origen` | STRING | Sí | |
| `registro_fuente` | STRING | Sí | |
| `run_id` | STRING | Sí | |
| `graph_version` | STRING | Sí | |

---

## Tablas de Resultados

### analytics_degree

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | |
| `in_degree` | INTEGER | Transferencias recibidas |
| `out_degree` | INTEGER | Transferencias enviadas |
| `total_degree` | INTEGER | `in_degree + out_degree` |
| `tx_recibidas` | BIGINT | Cuenta de transferencias entrantes |
| `tx_enviadas` | BIGINT | Cuenta de transferencias salientes |
| `monto_recibido` | DECIMAL(18,2) | |
| `monto_enviado` | DECIMAL(18,2) | |
| `contrapartes_unicas` | INTEGER | Clientes únicos con transferencia |
| `run_id` | STRING | |
| `graph_version` | STRING | |

---

### analytics_pagerank

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | |
| `pagerank` | DOUBLE | PageRank con damping=0.85 |
| `pagerank_params` | STRING | JSON con parámetros del algoritmo |
| `run_id` | STRING | |
| `graph_version` | STRING | |

---

### analytics_components

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | |
| `componente_id` | STRING | ID del componente conectado débil |
| `tamano_componente` | INTEGER | Nodos en el componente |
| `run_id` | STRING | |
| `graph_version` | STRING | |

---

### analytics_communities

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | |
| `comunidad_id` | STRING | ID de la comunidad Louvain |
| `tamano_comunidad` | INTEGER | Nodos en la comunidad |
| `modularidad_global` | DOUBLE | Modularidad del grafo completo |
| `louvain_seed` | INTEGER | Semilla para reproducibilidad |
| `run_id` | STRING | |
| `graph_version` | STRING | |

---

### analytics_risk_distance

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | |
| `distancia_min_alerta` | INTEGER | Saltos mínimos a cliente con alerta (null si no alcanzable) |
| `distancia_min_ros` | INTEGER | Saltos mínimos a cliente con ROS |
| `distancia_min_pep` | INTEGER | Saltos mínimos a cliente PEP |
| `distancia_min_caso` | INTEGER | Saltos mínimos a cliente con caso |
| `run_id` | STRING | |
| `graph_version` | STRING | |

---

### variables_estructurales

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | Entidad a la que pertenece la variable |
| `variable_nombre` | STRING | Nombre único de la variable |
| `categoria` | STRING | Una de las 8 categorías |
| `valor` | DOUBLE | Valor calculado (null si no aplica) |
| `valor_nulo_razon` | STRING | Razón del null (p.ej. "sin_actividad", "no_alcanzable") |
| `insumos` | STRING | JSON con tablas y columnas utilizadas |
| `algoritmo` | STRING | Nombre y versión del algoritmo aplicado |
| `relaciones_participantes` | ARRAY<STRING> | IDs de relaciones relevantes |
| `senales_origen` | STRING | JSON diferenciando alerta/ROS/PEP/caso cuando aplica |
| `graph_version` | STRING | |
| `run_id` | STRING | |
| `variables_version` | STRING | |
| `calculado_en` | TIMESTAMP | |

**Invariante**: todo cliente presente en el subgrafo tiene una fila por cada variable
del catálogo, con valor null documentado si no puede calcularse.

---

## Tablas de Auditoría

### audit_log

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `audit_id` | STRING | UUID de la entrada |
| `timestamp` | TIMESTAMP | Momento de la acción |
| `usuario_id` | STRING | Identidad del analista |
| `accion` | STRING | search / view_subgraph / view_variable / view_document / export / denied |
| `cliente_id` | STRING | Cliente consultado (null si búsqueda sin resultado) |
| `graph_version` | STRING | Versión del grafo activa |
| `datos_version` | STRING | Versión de los datos activa |
| `filtros_aplicados` | STRING | JSON con filtros usados |
| `documentos_consultados` | ARRAY<STRING> | IDs de documentos visualizados |
| `exportacion_realizada` | BOOLEAN | |
| `resultado` | STRING | ok / denied |
| `session_id` | STRING | |

---

## Esquema de Particionamiento en S3

```
s3://bucket/
├── raw/                          # Datos de entrada sin procesar
│   ├── clientes/yyyy=.../mm=.../
│   ├── transferencias/yyyy=.../mm=.../
│   └── ...
│
├── validated/                    # Datos validados por capa 2
│   ├── clientes/run_id=.../
│   └── ...
│
├── runs/
│   └── {run_id}/
│       ├── run_manifest.json
│       ├── seleccion/
│       ├── expansion/
│       ├── subgraph/
│       │   ├── nodes/tipo_nodo=cliente/
│       │   ├── nodes/tipo_nodo=cuenta/
│       │   └── edges/tipo_relacion=transfiere_a/
│       ├── analytics/
│       │   ├── degree/
│       │   ├── pagerank/
│       │   ├── components/
│       │   ├── communities/
│       │   └── risk_distance/
│       └── variables/categoria=centralidad/
│
├── graph/
│   └── v{graph_version}/        # Snapshot versionado del grafo
│
├── variables/
│   └── v{variables_version}/    # Variables versionadas para consumo
│
└── audit/
    └── yyyy=.../mm=.../         # Logs de auditoría particionados por fecha

---

## Manifiesto de Ejecución (run_manifest.json)

Almacenado en `s3://.../runs/{run_id}/run_manifest.json`.

```json
{
  "run_id": "uuid-v4",
  "execution_type": "full|incremental",
  "created_at": "2026-08-06T10:00:00Z",
  "completed_at": "2026-08-06T12:30:00Z",
  "status": "completed|failed|partial",
  "code_version": "1.0.0",
  "git_commit": "abc1234",
  "date_cutoff": "2026-07-31",
  "period": "2026-07",
  "observation_window_months": 12,
  "selection_criteria": {
    "alerta": true, "ros": true, "pep": true,
    "caso": true, "lista_objetivo": false
  },
  "expansion_depth": 1,
  "signal_weights": {
    "alerta": 0.7, "ros": 1.0, "pep": 0.3, "caso": 0.9
  },
  "algorithm_params": {
    "pagerank_damping": 0.85,
    "pagerank_max_iter": 100,
    "louvain_seed": 42,
    "louvain_method": "label_propagation_approx"
  },
  "experimental_algorithms": {},
  "datasets": {
    "clientes": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "transferencias": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "alertas_plaft": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "ros": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "pep": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "casos_investigados": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."},
    "catalogo_documental": {"s3_path": "...", "version": "...", "row_count": 0, "checksum": "sha256-..."}
  },
  "graph_version": "v-uuid",
  "analytics_version": "v-uuid",
  "variables_version": "v-uuid",
  "metrics": {
    "nodes_cliente_objetivo": 0,
    "nodes_cliente_contraparte": 0,
    "nodes_cuenta": 0,
    "nodes_alerta": 0,
    "nodes_ros": 0,
    "nodes_pep": 0,
    "nodes_caso": 0,
    "nodes_documento": 0,
    "edges_transfiere_a": 0,
    "edges_es_titular_de": 0,
    "edges_posee": 0,
    "graph_density": 0.0,
    "community_count": 0,
    "connected_components": 0,
    "variables_generated": 0,
    "build_time_seconds": 0,
    "analytics_time_seconds": 0,
    "variables_time_seconds": 0,
    "total_time_seconds": 0
  },
  "quality_report": {
    "critical_errors": 0,
    "warnings": 0,
    "records_rejected": 0
  },
  "errors": []
}
```

---

## Esquema de Consulta del Analista

### Request

```json
{
  "usuario_id": "string",
  "cliente_id": "string",
  "graph_version": "string",
  "filtros": {
    "periodo": {"inicio": "YYYY-MM", "fin": "YYYY-MM"},
    "monto_min": null,
    "monto_max": null,
    "moneda": null,
    "canal": null,
    "direccion": "entrada|salida|ambas",
    "condicion_riesgo": ["alerta", "ros", "pep", "caso"],
    "tipo_relacion": ["transfiere_a", "es_titular_de", "posee"]
  },
  "incluir_variables": true,
  "incluir_documentos": true,
  "max_aristas": 200
}
```

### Response (estructura conceptual)

```json
{
  "cliente": {
    "cliente_id": "string",
    "es_cliente_objetivo": true,
    "tiene_alerta": true,
    "tiene_ros": false,
    "es_pep": false,
    "tiene_caso": true,
    "nivel_expansion": 0
  },
  "subgrafo": {
    "nodos": [...],
    "aristas": [...],
    "graph_version": "string",
    "date_cutoff": "YYYY-MM-DD",
    "total_aristas_disponibles": N,
    "aristas_mostradas": M
  },
  "senales_riesgo": {
    "alertas": [...],
    "ros": [...],
    "pep": [...],
    "casos": [...]
  },
  "variables": [...],
  "documentos": [
    {
      "documento_id": "string",
      "tipo_documental": "string",
      "nombre": "string",
      "fecha_documento": "YYYY-MM-DD",
      "referencia_s3": "string",
      "estado": "string",
      "autorizado": true
    }
  ],
  "audit_id": "string"
}
```

---

## Notas sobre Nombres de Columnas

**IMPORTANTE**: los nombres de columna indicados en este modelo son nombres conceptuales
del diseño. Los nombres físicos reales en los datasets del banco se determinarán mediante
mapeo contra las tablas de origen durante la Fase 1. El contrato de datos debe incluir
una sección de mapeo físico → conceptual por cada fuente.

Ejemplo de mapeo (a completar en Fase 1):

| Nombre conceptual | Nombre físico (a mapear) |
|-------------------|-------------------------|
| `cliente_id` | `cod_cliente` (hipotético) |
| `cuenta_id` | `num_cuenta` (hipotético) |
| `fecha_hora` | `fec_txn` (hipotético) |
| `monto` | `imp_txn` (hipotético) |

El mapeo debe quedar documentado en `contracts/mapeo_fisico_conceptual.md` (Fase 1).

```
