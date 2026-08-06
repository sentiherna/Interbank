"""Tipos base, constantes del dominio y literales del proyecto."""

from __future__ import annotations

from typing import Final, Literal

# ---------------------------------------------------------------------------
# Motores de datos y de grafos
# ---------------------------------------------------------------------------
DataEngine = Literal["pandas", "spark"]
GraphEngine = Literal["networkx", "graphframes"]
Environment = Literal["local", "aws"]
LogFormat = Literal["json", "text"]

# ---------------------------------------------------------------------------
# Tipos de nodo del subgrafo
# ---------------------------------------------------------------------------
NodeType = Literal[
    "cliente",
    "cuenta",
    "producto",
    "alerta_plaft",
    "ros",
    "condicion_pep",
    "caso_investigado",
    "documento",
]

# ---------------------------------------------------------------------------
# Tipos de relación del subgrafo
# ---------------------------------------------------------------------------
EdgeType = Literal[
    "es_titular_de",
    "posee",
    "transfiere_a",
    "tiene_alerta",
    "tiene_ros",
    "tiene_condicion_pep",
    "tiene_caso",
    "tiene_documento",
]

# ---------------------------------------------------------------------------
# Tipos de señal de riesgo
# ---------------------------------------------------------------------------
SignalType = Literal["alerta", "ros", "pep", "caso"]

SIGNAL_TYPES: Final[tuple[str, ...]] = ("alerta", "ros", "pep", "caso")

# ---------------------------------------------------------------------------
# Categorías de variables estructurales
# ---------------------------------------------------------------------------
VariableCategory = Literal[
    "centralidad",
    "conectividad",
    "comunidades",
    "flujo_dinero",
    "patrones_transaccionales",
    "anomalias_estructurales",
    "riesgo_vecinos",
    "riesgo_propagado",
]

VARIABLE_CATEGORIES: Final[tuple[str, ...]] = (
    "centralidad",
    "conectividad",
    "comunidades",
    "flujo_dinero",
    "patrones_transaccionales",
    "anomalias_estructurales",
    "riesgo_vecinos",
    "riesgo_propagado",
)

# ---------------------------------------------------------------------------
# Estados de transacciones
# ---------------------------------------------------------------------------
TransactionStatus = Literal["EJECUTADA", "ANULADA", "REVERTIDA", "PENDIENTE"]
# Estos estados no se incluyen como aristas activas en el grafo
INACTIVE_TRANSACTION_STATUSES: Final[frozenset[str]] = frozenset({"ANULADA", "REVERTIDA"})

# ---------------------------------------------------------------------------
# Acciones de auditoría
# ---------------------------------------------------------------------------
AuditAction = Literal[
    "search",
    "view_subgraph",
    "view_variable",
    "view_document",
    "expand_node",
    "export",
    "denied",
]

# ---------------------------------------------------------------------------
# Permisos de acceso
# ---------------------------------------------------------------------------
AccessLevel = Literal["DATOS", "DOCUMENTOS", "AMBOS"]

# ---------------------------------------------------------------------------
# Estado del pipeline
# ---------------------------------------------------------------------------
PipelineStatus = Literal["running", "completed", "failed", "partial"]

# ---------------------------------------------------------------------------
# Columnas de trazabilidad obligatorias en todo nodo y relación
# ---------------------------------------------------------------------------
TRACEABILITY_COLUMNS: Final[tuple[str, ...]] = (
    "dataset_origen",
    "registro_fuente",
    "run_id",
    "graph_version",
)
