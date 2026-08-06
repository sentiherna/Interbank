"""Jerarquía de excepciones del proyecto graph_plaft.

Todas las excepciones heredan de ``GraphPlaftError`` para facilitar
el manejo diferenciado en los jobs de SageMaker Processing.
"""

from __future__ import annotations


class GraphPlaftError(Exception):
    """Excepción base del proyecto."""


# ---------------------------------------------------------------------------
# Errores de configuración
# ---------------------------------------------------------------------------


class ConfigurationError(GraphPlaftError):
    """La configuración del proyecto es inválida o incompleta."""


# ---------------------------------------------------------------------------
# Errores de ingesta y validación
# ---------------------------------------------------------------------------


class IngestionError(GraphPlaftError):
    """Error al cargar un dataset desde la fuente."""


class CriticalValidationError(GraphPlaftError):
    """Error crítico de calidad de datos que detiene el pipeline.

    Debe incluir el nombre del dataset, la regla violada y la cantidad
    de registros afectados para facilitar el diagnóstico.
    """

    def __init__(
        self,
        message: str,
        dataset: str = "",
        rule: str = "",
        affected_records: int = 0,
    ) -> None:
        super().__init__(message)
        self.dataset = dataset
        self.rule = rule
        self.affected_records = affected_records

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.dataset:
            parts.append(f"dataset={self.dataset}")
        if self.rule:
            parts.append(f"rule={self.rule}")
        if self.affected_records:
            parts.append(f"affected_records={self.affected_records}")
        return " | ".join(parts)


class ValidationWarning(GraphPlaftError):
    """Advertencia de calidad de datos que no detiene el pipeline pero se registra."""


# ---------------------------------------------------------------------------
# Errores de construcción del subgrafo
# ---------------------------------------------------------------------------


class GraphBuildError(GraphPlaftError):
    """Error durante la construcción del subgrafo."""


class PopulationSelectionError(GraphPlaftError):
    """Error al seleccionar o expandir la población de clientes sospechosos."""


# ---------------------------------------------------------------------------
# Errores de persistencia
# ---------------------------------------------------------------------------


class PersistenceError(GraphPlaftError):
    """Error al persistir o recuperar artefactos del grafo o variables."""


class VersionNotFoundError(PersistenceError):
    """La versión solicitada del grafo o variables no existe en el almacenamiento."""

    def __init__(self, version: str, artifact_type: str = "graph") -> None:
        super().__init__(f"{artifact_type} version not found: {version}")
        self.version = version
        self.artifact_type = artifact_type


class IntegrityError(PersistenceError):
    """El checksum del artefacto recuperado no coincide con el esperado."""


# ---------------------------------------------------------------------------
# Errores de Graph Analytics
# ---------------------------------------------------------------------------


class AnalyticsError(GraphPlaftError):
    """Error durante la ejecución de un algoritmo de Graph Analytics."""


class AlgorithmNotAvailableError(AnalyticsError):
    """El algoritmo solicitado no está disponible en el motor configurado."""

    def __init__(self, algorithm: str, engine: str) -> None:
        super().__init__(f"Algoritmo '{algorithm}' no disponible en motor '{engine}'")
        self.algorithm = algorithm
        self.engine = engine


# ---------------------------------------------------------------------------
# Errores de seguridad y acceso
# ---------------------------------------------------------------------------


class AccessDeniedError(GraphPlaftError):
    """El analista no tiene permisos para acceder al recurso solicitado.

    Este error se registra siempre en el log de auditoría antes de propagarse.
    """

    def __init__(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
    ) -> None:
        super().__init__(
            f"Acceso denegado: usuario={user_id} recurso={resource_type}/{resource_id}"
        )
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id


# ---------------------------------------------------------------------------
# Errores de reproducibilidad
# ---------------------------------------------------------------------------


class ReproducibilityError(GraphPlaftError):
    """La re-ejecución de un run histórico produjo un resultado diferente."""
