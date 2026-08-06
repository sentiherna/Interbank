"""Generador de identificadores únicos de ejecución (execution_id / run_id).

Cada ejecución del pipeline recibe un UUID-v4 como ``execution_id``.
Cuando se provee una semilla, el UUID es determinista para facilitar
la reproducibilidad en pruebas.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date


def generate_run_id(seed: str | int | None = None) -> str:
    """Genera un identificador único de ejecución.

    Args:
        seed: Semilla opcional para UUID determinista (solo en pruebas).
              Si es None, genera un UUID-v4 aleatorio.

    Returns:
        String UUID-v4 sin guiones: p.ej. ``"550e8400e29b41d4a716446655440000"``.
    """
    if seed is None:
        return str(uuid.uuid4())

    seed_str = str(seed)
    digest = hashlib.md5(seed_str.encode(), usedforsecurity=False).digest()
    deterministic_uuid = uuid.UUID(bytes=digest, version=4)
    return str(deterministic_uuid)


def generate_graph_version(
    run_id: str,
    date_cutoff: date | str,
    expansion_depth: int,
) -> str:
    """Genera un identificador estable de versión del grafo.

    El identificador es determinista dado los mismos argumentos, lo que
    permite verificar que dos ejecuciones con los mismos parámetros
    producen la misma versión.

    Args:
        run_id: Identificador de la ejecución.
        date_cutoff: Fecha de corte de los datos (YYYY-MM-DD).
        expansion_depth: Profundidad de expansión del subgrafo.

    Returns:
        String con prefijo ``"v-"`` seguido de un UUID determinista.
    """
    seed = f"{run_id}|{date_cutoff}|{expansion_depth}"
    digest = hashlib.sha256(seed.encode()).digest()[:16]
    version_uuid = uuid.UUID(bytes=digest, version=4)
    return f"v-{version_uuid}"


def generate_variables_version(graph_version: str, run_id: str) -> str:
    """Genera un identificador estable de versión del conjunto de variables.

    Args:
        graph_version: Versión del grafo fuente.
        run_id: Identificador de la ejecución.

    Returns:
        String con prefijo ``"vars-"`` seguido de un UUID determinista.
    """
    seed = f"{graph_version}|{run_id}"
    digest = hashlib.sha256(seed.encode()).digest()[:16]
    version_uuid = uuid.UUID(bytes=digest, version=4)
    return f"vars-{version_uuid}"
