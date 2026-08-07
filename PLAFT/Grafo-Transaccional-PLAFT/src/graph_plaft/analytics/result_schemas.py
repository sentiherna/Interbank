"""Esquemas de salida de los algoritmos de Graph Analytics.

Cada esquema define las columnas que deben estar presentes en el DataFrame
de resultados de cada algoritmo. Son los insumos directos de la capa de
Generación de Variables (FR-017, ADR-002).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsResultColumn:
    """Definición de una columna de resultado de analytics."""

    name: str
    required: bool = True
    nullable: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# analytics_degree
# ---------------------------------------------------------------------------

ANALYTICS_DEGREE_COLUMNS: tuple[AnalyticsResultColumn, ...] = (
    AnalyticsResultColumn("cliente_id", required=True, nullable=False),
    AnalyticsResultColumn(
        "in_degree",
        description="Número de transferencias recibidas (aristas entrantes).",
    ),
    AnalyticsResultColumn(
        "out_degree",
        description="Número de transferencias enviadas (aristas salientes).",
    ),
    AnalyticsResultColumn(
        "total_degree",
        description="in_degree + out_degree.",
    ),
    AnalyticsResultColumn(
        "tx_recibidas",
        description="Conteo de transferencias recibidas.",
    ),
    AnalyticsResultColumn(
        "tx_enviadas",
        description="Conteo de transferencias enviadas.",
    ),
    AnalyticsResultColumn(
        "monto_recibido",
        description="Suma de montos de transferencias recibidas.",
    ),
    AnalyticsResultColumn(
        "monto_enviado",
        description="Suma de montos de transferencias enviadas.",
    ),
    AnalyticsResultColumn(
        "contrapartes_unicas",
        description="Cantidad de clientes únicos con los que tuvo transferencias.",
    ),
    AnalyticsResultColumn("run_id", required=True),
    AnalyticsResultColumn("graph_version", required=True),
)

# ---------------------------------------------------------------------------
# analytics_pagerank
# ---------------------------------------------------------------------------

ANALYTICS_PAGERANK_COLUMNS: tuple[AnalyticsResultColumn, ...] = (
    AnalyticsResultColumn("cliente_id", required=True),
    AnalyticsResultColumn(
        "pagerank",
        nullable=True,
        description="PageRank del nodo. Null si nodo aislado.",
    ),
    AnalyticsResultColumn(
        "pagerank_params",
        nullable=True,
        description="JSON con parámetros del algoritmo (damping, max_iter, seed).",
    ),
    AnalyticsResultColumn("run_id", required=True),
    AnalyticsResultColumn("graph_version", required=True),
)

# ---------------------------------------------------------------------------
# analytics_components
# ---------------------------------------------------------------------------

ANALYTICS_COMPONENTS_COLUMNS: tuple[AnalyticsResultColumn, ...] = (
    AnalyticsResultColumn("cliente_id", required=True),
    AnalyticsResultColumn(
        "componente_id",
        nullable=True,
        description="Identificador del componente conectado débil (WCC).",
    ),
    AnalyticsResultColumn(
        "tamano_componente",
        description="Número de nodos en el componente.",
    ),
    AnalyticsResultColumn("run_id", required=True),
    AnalyticsResultColumn("graph_version", required=True),
)

# ---------------------------------------------------------------------------
# analytics_communities
# ---------------------------------------------------------------------------

ANALYTICS_COMMUNITIES_COLUMNS: tuple[AnalyticsResultColumn, ...] = (
    AnalyticsResultColumn("cliente_id", required=True),
    AnalyticsResultColumn(
        "comunidad_id",
        nullable=True,
        description="Identificador de la comunidad asignada. Null si nodo aislado.",
    ),
    AnalyticsResultColumn(
        "tamano_comunidad",
        description="Número de nodos en la comunidad.",
    ),
    AnalyticsResultColumn(
        "modularidad_global",
        nullable=True,
        description="Modularidad global del grafo.",
    ),
    AnalyticsResultColumn(
        "method",
        description="Método usado: 'label_propagation' (aproximación de Louvain, ADR-007).",
    ),
    AnalyticsResultColumn(
        "algorithm_seed",
        description="Semilla para reproducibilidad.",
    ),
    AnalyticsResultColumn("run_id", required=True),
    AnalyticsResultColumn("graph_version", required=True),
)

# ---------------------------------------------------------------------------
# analytics_risk_distance
# ---------------------------------------------------------------------------

ANALYTICS_RISK_DISTANCE_COLUMNS: tuple[AnalyticsResultColumn, ...] = (
    AnalyticsResultColumn("cliente_id", required=True),
    AnalyticsResultColumn(
        "distancia_min_alerta",
        nullable=True,
        description="Saltos mínimos dirigidos a cliente con alerta PLAFT. Null si no alcanzable.",
    ),
    AnalyticsResultColumn(
        "distancia_min_ros",
        nullable=True,
        description="Saltos mínimos a cliente con ROS. Null si no alcanzable.",
    ),
    AnalyticsResultColumn(
        "distancia_min_pep",
        nullable=True,
        description="Saltos mínimos a cliente PEP. Null si no alcanzable.",
    ),
    AnalyticsResultColumn(
        "distancia_min_caso",
        nullable=True,
        description="Saltos mínimos a cliente con caso investigado. Null si no alcanzable.",
    ),
    AnalyticsResultColumn(
        "max_depth_searched",
        description="Profundidad máxima de búsqueda utilizada.",
    ),
    AnalyticsResultColumn("run_id", required=True),
    AnalyticsResultColumn("graph_version", required=True),
)

# ---------------------------------------------------------------------------
# Registro de esquemas de resultados
# ---------------------------------------------------------------------------

RESULT_SCHEMAS: dict[str, tuple[AnalyticsResultColumn, ...]] = {
    "analytics_degree": ANALYTICS_DEGREE_COLUMNS,
    "analytics_pagerank": ANALYTICS_PAGERANK_COLUMNS,
    "analytics_components": ANALYTICS_COMPONENTS_COLUMNS,
    "analytics_communities": ANALYTICS_COMMUNITIES_COLUMNS,
    "analytics_risk_distance": ANALYTICS_RISK_DISTANCE_COLUMNS,
}


def get_required_columns(result_name: str) -> list[str]:
    """Retorna la lista de columnas requeridas para un resultado de analytics."""
    if result_name not in RESULT_SCHEMAS:
        raise KeyError(
            f"Resultado '{result_name}' no tiene esquema. "
            f"Disponibles: {sorted(RESULT_SCHEMAS.keys())}"
        )
    return [c.name for c in RESULT_SCHEMAS[result_name] if c.required]
