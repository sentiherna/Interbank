"""RunManifest — manifiesto de ejecución del pipeline.

Registra todo el contexto de una ejecución para garantizar reproducibilidad.
Se persiste como ``run_manifest.json`` en S3 junto a los artefactos del run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from graph_plaft.config.schemas import PipelineStatus
from graph_plaft.observability.errors import PersistenceError


@dataclass
class DatasetInfo:
    """Información de un dataset de entrada utilizado en el run."""

    s3_path: str = ""
    version: str = ""
    row_count: int = 0
    checksum: str = ""


@dataclass
class QualityReport:
    """Resumen del reporte de calidad del run."""

    critical_errors: int = 0
    warnings: int = 0
    records_rejected: int = 0


@dataclass
class GraphMetrics:
    """Métricas operacionales del subgrafo construido."""

    nodes_cliente: int = 0
    nodes_cuenta: int = 0
    nodes_producto: int = 0
    nodes_alerta: int = 0
    nodes_ros: int = 0
    nodes_pep: int = 0
    nodes_caso: int = 0
    nodes_documento: int = 0
    edges_transfiere_a: int = 0
    edges_es_titular_de: int = 0
    edges_posee: int = 0
    edges_tiene_alerta: int = 0
    edges_tiene_ros: int = 0
    edges_tiene_condicion_pep: int = 0
    edges_tiene_caso: int = 0
    edges_tiene_documento: int = 0
    graph_density: float = 0.0
    community_count: int = 0
    connected_components: int = 0
    variables_generated: int = 0
    build_time_seconds: float = 0.0
    analytics_time_seconds: float = 0.0
    variables_time_seconds: float = 0.0
    total_time_seconds: float = 0.0


@dataclass
class SignalWeightsSnapshot:
    """Snapshot de pesos de señales para reproducibilidad."""

    alerta: float = 0.7
    ros: float = 1.0
    pep: float = 0.3
    caso: float = 0.9


@dataclass
class SelectionCriteriaSnapshot:
    """Snapshot de criterios de selección para reproducibilidad."""

    alerta: bool = True
    ros: bool = True
    pep: bool = True
    caso: bool = True
    lista_objetivo: bool = False
    regla: bool = False


@dataclass
class RunManifest:
    """Manifiesto completo de una ejecución del pipeline.

    Todos los campos necesarios para reproducir exactamente la misma ejecución:
    código, datos, parámetros, configuración y resultados.
    """

    run_id: str
    created_at: str           # ISO-8601
    status: PipelineStatus
    code_version: str = ""
    git_commit: str = ""
    date_cutoff: str = ""     # YYYY-MM-DD
    period: str = ""          # YYYY-MM
    observation_window_months: int = 12
    expansion_depth: int = 1
    graph_version: str = ""
    analytics_version: str = ""
    variables_version: str = ""
    completed_at: str = ""    # ISO-8601; vacío si no completado

    selection_criteria: SelectionCriteriaSnapshot = field(
        default_factory=SelectionCriteriaSnapshot
    )
    signal_weights: SignalWeightsSnapshot = field(
        default_factory=SignalWeightsSnapshot
    )
    algorithm_params: dict[str, Any] = field(default_factory=dict)
    experimental_algorithms: dict[str, Any] = field(default_factory=dict)

    datasets: dict[str, DatasetInfo] = field(default_factory=dict)
    metrics: GraphMetrics = field(default_factory=GraphMetrics)
    quality_report: QualityReport = field(default_factory=QualityReport)
    errors: list[str] = field(default_factory=list)

    # --- serialización -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Convierte el manifiesto a diccionario serializable."""
        d = asdict(self)
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serializa el manifiesto a JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)

    def save(self, path: str | Path) -> None:
        """Persiste el manifiesto como archivo JSON.

        Args:
            path: Ruta del archivo (local o S3 via instancia de DataEngine en fases posteriores).

        Raises:
            PersistenceError: Si no se puede escribir el archivo.
        """
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(self.to_json(), encoding="utf-8")
        except OSError as exc:
            raise PersistenceError(
                f"No se pudo persistir run_manifest en {path}: {exc}"
            ) from exc

    @classmethod
    def load(cls, path: str | Path) -> RunManifest:
        """Carga un manifiesto desde un archivo JSON local.

        Args:
            path: Ruta del archivo JSON.

        Raises:
            PersistenceError: Si el archivo no existe o no puede parsearse.
        """
        try:
            content = Path(path).read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(content)
        except (OSError, json.JSONDecodeError) as exc:
            raise PersistenceError(
                f"No se pudo cargar run_manifest desde {path}: {exc}"
            ) from exc
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> RunManifest:
        """Reconstruye un RunManifest desde un diccionario."""
        manifest = cls(
            run_id=data["run_id"],
            created_at=data["created_at"],
            status=data["status"],
            code_version=data.get("code_version", ""),
            git_commit=data.get("git_commit", ""),
            date_cutoff=data.get("date_cutoff", ""),
            period=data.get("period", ""),
            observation_window_months=data.get("observation_window_months", 12),
            expansion_depth=data.get("expansion_depth", 1),
            graph_version=data.get("graph_version", ""),
            analytics_version=data.get("analytics_version", ""),
            variables_version=data.get("variables_version", ""),
            completed_at=data.get("completed_at", ""),
            algorithm_params=data.get("algorithm_params", {}),
            experimental_algorithms=data.get("experimental_algorithms", {}),
            errors=data.get("errors", []),
        )

        if "selection_criteria" in data:
            sc = data["selection_criteria"]
            manifest.selection_criteria = SelectionCriteriaSnapshot(**sc)

        if "signal_weights" in data:
            sw = data["signal_weights"]
            manifest.signal_weights = SignalWeightsSnapshot(**sw)

        if "datasets" in data:
            manifest.datasets = {
                k: DatasetInfo(**v) for k, v in data["datasets"].items()
            }

        if "metrics" in data:
            manifest.metrics = GraphMetrics(**data["metrics"])

        if "quality_report" in data:
            manifest.quality_report = QualityReport(**data["quality_report"])

        return manifest

    def validate_complete(self) -> list[str]:
        """Retorna lista de campos faltantes o vacíos que son obligatorios.

        Returns:
            Lista vacía si el manifiesto está completo.
        """
        required = ["run_id", "created_at", "status", "code_version", "date_cutoff"]
        return [f for f in required if not getattr(self, f, None)]
