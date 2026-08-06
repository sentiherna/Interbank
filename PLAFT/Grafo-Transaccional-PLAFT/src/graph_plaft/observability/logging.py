"""Logging estructurado en JSON para el proyecto graph_plaft.

Todo log incluye automáticamente el ``execution_id`` si está configurado.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Formateador que emite líneas JSON por cada registro de log."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Campos extra inyectados por el caller (ej. execution_id, run_id)
        for key in ("execution_id", "run_id", "graph_version", "dataset", "phase"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    """Formateador legible para desarrollo local."""

    FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self.FORMAT, datefmt="%H:%M:%S")


def configure_logging(
    level: str = "INFO",
    fmt: str = "json",
    execution_id: str | None = None,
) -> logging.Logger:
    """Configura el logging raíz del proyecto.

    Args:
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        fmt: Formato de salida ("json" | "text").
        execution_id: Identificador de ejecución para correlación de logs.

    Returns:
        Logger raíz configurado del paquete ``graph_plaft``.
    """
    root_logger = logging.getLogger("graph_plaft")

    if root_logger.handlers:
        # Evitar configurar dos veces en el mismo proceso
        return root_logger

    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter: logging.Formatter
    if fmt == "json":
        formatter = _JsonFormatter()
    else:
        formatter = _TextFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    if execution_id:
        root_logger = logging.LoggerAdapter(  # type: ignore[assignment]
            root_logger,
            extra={"execution_id": execution_id},
        )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger hijo del logger raíz del proyecto.

    Args:
        name: Nombre del módulo (ej. ``graph_plaft.validation``).

    Returns:
        Logger configurado.
    """
    return logging.getLogger(name)
