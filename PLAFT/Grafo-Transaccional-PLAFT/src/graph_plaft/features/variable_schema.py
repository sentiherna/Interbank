"""Esquema de la variable estructural — entidad central del catálogo de features.

Toda variable generada por el sistema DEBE poder justificarse ante un analista
o auditor (Constitución v3.0.0, Principio VIII — Explicabilidad).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from graph_plaft.config.schemas import VARIABLE_CATEGORIES, VariableCategory
from graph_plaft.observability.errors import GraphBuildError


@dataclass
class VariableEstructural:
    """Variable estructural generada por Graph Analytics para un cliente.

    Invariantes:
    - ``valor`` o ``valor_nulo_razon`` DEBE estar informado; no ambos vacíos.
    - ``categoria`` DEBE pertenecer a las 8 categorías definidas.

    Attributes:
        cliente_id: Identificador del cliente al que pertenece la variable.
        variable_nombre: Nombre único de la variable en el catálogo.
        categoria: Una de las 8 categorías de variables (VariableCategory).
        valor: Valor calculado (None si no aplica o no calculable).
        valor_nulo_razon: Razón del null (ej. "sin_actividad", "no_alcanzable").
        insumos: JSON string con tablas y columnas utilizadas en el cálculo.
        algoritmo: Nombre y versión del algoritmo aplicado.
        senales_origen: JSON string diferenciando alerta/ROS/PEP/caso cuando aplica.
        ventana_inicio: Fecha de inicio de la ventana temporal usada.
        ventana_fin: Fecha de fin de la ventana temporal (= fecha_corte).
        fecha_calculo: Timestamp de cuando se calculó la variable.
        graph_version: Versión del grafo fuente.
        run_id: Identificador de la ejecución que generó la variable.
        variables_version: Versión del conjunto de variables.
    """

    cliente_id: str
    variable_nombre: str
    categoria: VariableCategory
    valor: float | None = None
    valor_nulo_razon: str | None = None
    insumos: str = ""           # JSON string: {"tablas": [...], "columnas": [...]}
    algoritmo: str = ""
    senales_origen: str = ""    # JSON string: {"alerta": N, "ros": N, "pep": N, "caso": N}
    ventana_inicio: date | None = None
    ventana_fin: date | None = None
    fecha_calculo: str = ""     # ISO-8601 timestamp
    graph_version: str = ""
    run_id: str = ""
    variables_version: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Valida las invariantes del esquema.

        Raises:
            GraphBuildError: Si alguna invariante se viola.
        """
        # Invariante 1: valor o valor_nulo_razon debe estar informado
        if self.valor is None and not self.valor_nulo_razon:
            raise GraphBuildError(
                f"VariableEstructural [{self.cliente_id}/{self.variable_nombre}]: "
                "debe tener 'valor' o 'valor_nulo_razon' informado; "
                "no pueden estar ambos vacíos."
            )

        # Invariante 2: categoría válida
        if self.categoria not in VARIABLE_CATEGORIES:
            raise GraphBuildError(
                f"VariableEstructural [{self.cliente_id}/{self.variable_nombre}]: "
                f"categoría '{self.categoria}' no válida. "
                f"Categorías permitidas: {VARIABLE_CATEGORIES}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Retorna representación de diccionario para serialización."""
        return {
            "cliente_id": self.cliente_id,
            "variable_nombre": self.variable_nombre,
            "categoria": self.categoria,
            "valor": self.valor,
            "valor_nulo_razon": self.valor_nulo_razon,
            "insumos": self.insumos,
            "algoritmo": self.algoritmo,
            "senales_origen": self.senales_origen,
            "ventana_inicio": self.ventana_inicio.isoformat() if self.ventana_inicio else None,
            "ventana_fin": self.ventana_fin.isoformat() if self.ventana_fin else None,
            "fecha_calculo": self.fecha_calculo,
            "graph_version": self.graph_version,
            "run_id": self.run_id,
            "variables_version": self.variables_version,
        }


# ---------------------------------------------------------------------------
# Columnas del DataFrame de variables estructurales
# ---------------------------------------------------------------------------

VARIABLE_DATAFRAME_COLUMNS: tuple[str, ...] = (
    "cliente_id",
    "variable_nombre",
    "categoria",
    "valor",
    "valor_nulo_razon",
    "insumos",
    "algoritmo",
    "senales_origen",
    "ventana_inicio",
    "ventana_fin",
    "fecha_calculo",
    "graph_version",
    "run_id",
    "variables_version",
)

VARIABLE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "cliente_id",
    "variable_nombre",
    "categoria",
    "graph_version",
    "run_id",
)
