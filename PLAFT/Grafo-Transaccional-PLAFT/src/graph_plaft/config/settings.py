"""Carga y validación de la configuración del proyecto por entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SignalWeights:
    """Pesos configurables para cada tipo de señal de riesgo."""

    alerta: float = 0.7
    ros: float = 1.0
    pep: float = 0.3
    caso: float = 0.9


@dataclass(frozen=True)
class SelectionCriteria:
    """Criterios de selección de clientes sospechosos habilitados."""

    alerta: bool = True
    ros: bool = True
    pep: bool = True
    caso: bool = True
    lista_objetivo: bool = False
    regla: bool = False


@dataclass(frozen=True)
class RunDefaults:
    """Parámetros por defecto para cada ejecución del pipeline."""

    expansion_depth: int = 1
    date_cutoff: str | None = None
    algorithm_seed: int = 42
    observation_window_months: int = 12
    signal_weights: SignalWeights = field(default_factory=SignalWeights)
    selection_criteria: SelectionCriteria = field(default_factory=SelectionCriteria)


@dataclass(frozen=True)
class StorageConfig:
    """Configuración de almacenamiento (local o S3)."""

    base_path: str = "./data/local"
    format: str = "parquet"


@dataclass(frozen=True)
class MLflowConfig:
    """Configuración del servidor MLflow."""

    enabled: bool = True
    tracking_uri: str = "./mlruns"
    experiment_name: str = "graph-plaft-local"


@dataclass(frozen=True)
class FeatureStoreConfig:
    """Configuración de SageMaker Feature Store."""

    enabled: bool = False
    feature_group_name: str = "plaft-graph-variables-v1"
    offline_store_s3_uri: str = ""


@dataclass(frozen=True)
class GlueConfig:
    """Configuración del AWS Glue Data Catalog."""

    enabled: bool = False
    database_name: str = "graph_plaft_dev"


@dataclass(frozen=True)
class Settings:
    """Configuración completa del proyecto."""

    environment: str
    data_engine: str  # "pandas" | "spark"
    graph_engine: str  # "networkx" | "graphframes"
    log_level: str
    log_format: str
    storage: StorageConfig
    mlflow: MLflowConfig
    feature_store: FeatureStoreConfig
    glue: GlueConfig
    run_defaults: RunDefaults

    def is_local(self) -> bool:
        """Retorna True si el entorno es local."""
        return self.environment == "local"

    def is_aws(self) -> bool:
        """Retorna True si el entorno es AWS."""
        return self.environment == "aws"


def _expand_env_vars(value: Any) -> Any:
    """Expande variables de entorno ${VAR} en strings de configuración."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Carga la configuración desde un archivo YAML.

    Si no se especifica ruta, usa la variable de entorno GRAPH_PLAFT_CONFIG
    o por defecto ``config/local.yaml``.
    """
    if config_path is None:
        config_path = os.environ.get("GRAPH_PLAFT_CONFIG", "config/local.yaml")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    raw = _expand_env_vars(raw)

    storage_raw = raw.get("storage", {})
    mlflow_raw = raw.get("mlflow", {})
    fs_raw = raw.get("feature_store", {})
    glue_raw = raw.get("glue", {})
    defaults_raw = raw.get("run_defaults", {})
    weights_raw = defaults_raw.get("signal_weights", {})
    criteria_raw = raw.get("selection_criteria", {})

    return Settings(
        environment=raw.get("environment", "local"),
        data_engine=raw.get("data_engine", "pandas"),
        graph_engine=raw.get("graph_engine", "networkx"),
        log_level=raw.get("log_level", "INFO"),
        log_format=raw.get("log_format", "json"),
        storage=StorageConfig(
            base_path=storage_raw.get("base_path", "./data/local"),
            format=storage_raw.get("format", "parquet"),
        ),
        mlflow=MLflowConfig(
            enabled=mlflow_raw.get("enabled", True),
            tracking_uri=mlflow_raw.get("tracking_uri", "./mlruns"),
            experiment_name=mlflow_raw.get("experiment_name", "graph-plaft-local"),
        ),
        feature_store=FeatureStoreConfig(
            enabled=fs_raw.get("enabled", False),
            feature_group_name=fs_raw.get("feature_group_name", "plaft-graph-variables-v1"),
            offline_store_s3_uri=fs_raw.get("offline_store_s3_uri", ""),
        ),
        glue=GlueConfig(
            enabled=glue_raw.get("enabled", False),
            database_name=glue_raw.get("database_name", "graph_plaft_dev"),
        ),
        run_defaults=RunDefaults(
            expansion_depth=defaults_raw.get("expansion_depth", 1),
            date_cutoff=defaults_raw.get("date_cutoff"),
            algorithm_seed=defaults_raw.get("algorithm_seed", 42),
            observation_window_months=defaults_raw.get("observation_window_months", 12),
            signal_weights=SignalWeights(
                alerta=weights_raw.get("alerta", 0.7),
                ros=weights_raw.get("ros", 1.0),
                pep=weights_raw.get("pep", 0.3),
                caso=weights_raw.get("caso", 0.9),
            ),
            selection_criteria=SelectionCriteria(
                alerta=criteria_raw.get("alerta", True),
                ros=criteria_raw.get("ros", True),
                pep=criteria_raw.get("pep", True),
                caso=criteria_raw.get("caso", True),
                lista_objetivo=criteria_raw.get("lista_objetivo", False),
                regla=criteria_raw.get("regla", False),
            ),
        ),
    )
