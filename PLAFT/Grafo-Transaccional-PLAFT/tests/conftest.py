"""Fixtures globales de pytest para el proyecto graph_plaft."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_plaft.config.settings import Settings, load_settings
from graph_plaft.observability.run_id import generate_run_id

# ---------------------------------------------------------------------------
# Configuración de pruebas
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def synthetic_config() -> Settings:
    """Settings para pruebas usando config/local.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "local.yaml"
    return load_settings(config_path)


@pytest.fixture
def fixed_run_id() -> str:
    """run_id determinista para pruebas de reproducibilidad."""
    return generate_run_id(seed="test-seed-42")


@pytest.fixture
def graph_version_fixture() -> str:
    """Versión fija del grafo para pruebas."""
    return "v-00000000-0000-4000-0000-000000000001"


# ---------------------------------------------------------------------------
# Directorios temporales
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_parquet_dir(tmp_path: Path) -> Path:
    """Directorio temporal con subdirectorios de Parquet por tipo de artefacto."""
    (tmp_path / "nodes").mkdir()
    (tmp_path / "edges").mkdir()
    (tmp_path / "analytics").mkdir()
    (tmp_path / "variables").mkdir()
    return tmp_path


@pytest.fixture
def synthetic_data_dir() -> Path:
    """Ruta al directorio de datos sintéticos del proyecto."""
    path = Path(__file__).parent.parent / "data" / "synthetic"
    return path
