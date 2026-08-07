"""Capa de mapeo configurable entre nombres conceptuales y nombres físicos.

Permite traducir DataFrames con columnas físicas (nombres reales del banco)
a columnas conceptuales del proyecto, y viceversa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from graph_plaft.observability.errors import ConfigurationError


@dataclass(frozen=True)
class ColumnMapping:
    """Mapeo de una columna conceptual a su nombre físico en una fuente."""

    conceptual: str
    physical: str
    required: bool = True
    description: str = ""


@dataclass
class SourceMapping:
    """Mapeo completo de columnas para una fuente de datos.

    Args:
        source_name: Nombre de la fuente (ej. ``"clientes"``).
        mappings: Lista de mapeos columna conceptual → física.
    """

    source_name: str
    mappings: list[ColumnMapping] = field(default_factory=list)

    # --- acceso ---------------------------------------------------------------

    def physical_to_conceptual(self) -> dict[str, str]:
        """Retorna diccionario ``{nombre_físico: nombre_conceptual}``."""
        return {m.physical: m.conceptual for m in self.mappings}

    def conceptual_to_physical(self) -> dict[str, str]:
        """Retorna diccionario ``{nombre_conceptual: nombre_físico}``."""
        return {m.conceptual: m.physical for m in self.mappings}

    def required_physical_columns(self) -> list[str]:
        """Retorna los nombres físicos de las columnas obligatorias."""
        return [m.physical for m in self.mappings if m.required]

    def required_conceptual_columns(self) -> list[str]:
        """Retorna los nombres conceptuales de las columnas obligatorias."""
        return [m.conceptual for m in self.mappings if m.required]

    # --- validación -----------------------------------------------------------

    def validate_physical_columns(self, df: pd.DataFrame) -> None:
        """Valida que el DataFrame contiene todas las columnas físicas obligatorias.

        Args:
            df: DataFrame con columnas físicas.

        Raises:
            ConfigurationError: Si falta alguna columna obligatoria.
        """
        required = set(self.required_physical_columns())
        present = set(df.columns)
        missing = required - present
        if missing:
            raise ConfigurationError(
                f"[{self.source_name}] Columnas obligatorias faltantes en el DataFrame: "
                f"{sorted(missing)}. Presentes: {sorted(present)}. "
                "Revisar contracts/mapeo_fisico_conceptual.md para actualizar el mapeo."
            )

    def validate_conceptual_columns(self, df: pd.DataFrame) -> None:
        """Valida que el DataFrame (ya renombrado) tiene las columnas conceptuales obligatorias.

        Args:
            df: DataFrame con columnas conceptuales.

        Raises:
            ConfigurationError: Si falta alguna columna conceptual obligatoria.
        """
        required = set(self.required_conceptual_columns())
        present = set(df.columns)
        missing = required - present
        if missing:
            raise ConfigurationError(
                f"[{self.source_name}] Columnas conceptuales obligatorias faltantes: "
                f"{sorted(missing)}. Verificar que el mapeo physical→conceptual es completo."
            )

    # --- transformación -------------------------------------------------------

    def to_conceptual(self, df: pd.DataFrame, validate: bool = True) -> pd.DataFrame:
        """Renombra las columnas físicas del DataFrame a sus nombres conceptuales.

        Solo renombra las columnas que tienen mapeo definido; las demás se mantienen.

        Args:
            df: DataFrame con columnas físicas.
            validate: Si True, valida primero que las obligatorias estén presentes.

        Returns:
            DataFrame con columnas renombradas; **no** modifica el original.

        Raises:
            ConfigurationError: Si ``validate=True`` y faltan columnas obligatorias.
        """
        if validate:
            self.validate_physical_columns(df)
        rename_map = {
            p: c for p, c in self.physical_to_conceptual().items() if p in df.columns
        }
        return df.rename(columns=rename_map)

    def to_physical(self, df: pd.DataFrame, validate: bool = True) -> pd.DataFrame:
        """Renombra las columnas conceptuales del DataFrame a sus nombres físicos.

        Args:
            df: DataFrame con columnas conceptuales.
            validate: Si True, valida primero que las obligatorias estén presentes.

        Returns:
            DataFrame con columnas renombradas; **no** modifica el original.

        Raises:
            ConfigurationError: Si ``validate=True`` y faltan columnas conceptuales obligatorias.
        """
        if validate:
            self.validate_conceptual_columns(df)
        rename_map = {
            c: p for c, p in self.conceptual_to_physical().items() if c in df.columns
        }
        return df.rename(columns=rename_map)


class ColumnMappingRegistry:
    """Registro central de mapeos por fuente de datos.

    Permite cargar una configuración de mapeos desde un diccionario
    (YAML, JSON, etc.) o construirla programáticamente.
    """

    def __init__(self) -> None:
        self._registry: dict[str, SourceMapping] = {}

    def register(self, source_mapping: SourceMapping) -> None:
        """Registra el mapeo de una fuente."""
        self._registry[source_mapping.source_name] = source_mapping

    def get(self, source_name: str) -> SourceMapping:
        """Retorna el mapeo de una fuente registrada.

        Raises:
            ConfigurationError: Si la fuente no está registrada.
        """
        if source_name not in self._registry:
            raise ConfigurationError(
                f"Fuente '{source_name}' no tiene mapeo registrado. "
                "Registrar el mapeo antes de usarlo."
            )
        return self._registry[source_name]

    def has(self, source_name: str) -> bool:
        """Retorna True si la fuente tiene mapeo registrado."""
        return source_name in self._registry

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> ColumnMappingRegistry:
        """Construye un registro a partir de un diccionario de configuración.

        Formato esperado::

            {
                "clientes": {
                    "columnas": [
                        {"conceptual": "cliente_id", "physical": "cod_cliente", "required": true},
                        ...
                    ]
                }
            }

        Args:
            config: Diccionario con la configuración de mapeos.

        Returns:
            Instancia de ``ColumnMappingRegistry`` con todos los mapeos cargados.
        """
        registry = cls()
        for source_name, source_config in config.items():
            mappings = [
                ColumnMapping(
                    conceptual=col["conceptual"],
                    physical=col["physical"],
                    required=col.get("required", True),
                    description=col.get("description", ""),
                )
                for col in source_config.get("columnas", [])
            ]
            registry.register(SourceMapping(source_name=source_name, mappings=mappings))
        return registry


def identity_mapping(source_name: str, columns: list[str]) -> SourceMapping:
    """Crea un mapeo identidad donde nombres conceptuales = nombres físicos.

    Útil para pruebas o cuando los datasets ya usan nombres conceptuales.

    Args:
        source_name: Nombre de la fuente.
        columns: Lista de nombres de columnas (conceptual = físico).

    Returns:
        ``SourceMapping`` con mapeo identidad para todas las columnas.
    """
    mappings = [
        ColumnMapping(conceptual=col, physical=col, required=True) for col in columns
    ]
    return SourceMapping(source_name=source_name, mappings=mappings)
