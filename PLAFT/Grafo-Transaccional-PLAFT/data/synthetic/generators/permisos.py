"""Synthetic analyst permissions generator (T040).

Produces one dataset:
- ``permisos_analistas`` — access control rows matching PERMISOS_ANALISTAS_CONTRACT.

Test scenario
-------------
Analyst ANA-001 has AMBOS-level access to CLI-001..CLI-009 (9 of the 10 clients).
CLI-010 is **intentionally excluded** to test rejection logic: any query for
CLI-010 by ANA-001 must be denied by the security layer.
"""

from __future__ import annotations

import pandas as pd

from .base import SyntheticDataGenerator

# Clients accessible to ANA-001 (CLI-010 deliberately excluded)
_ALLOWED_CLIENTS = [f"CLI-{i:03d}" for i in range(1, 10)]


class PermisosGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "permisos_analistas"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {"permisos_analistas": self._permisos()}

    # ------------------------------------------------------------------
    # permisos_analistas — columnas: usuario_id, cliente_id,
    #   nivel_acceso, fecha_inicio, fecha_fin, vigente
    # ------------------------------------------------------------------
    def _permisos(self) -> pd.DataFrame:
        rows = [
            {
                "usuario_id": "ANA-001",
                "cliente_id": cid,
                "nivel_acceso": "AMBOS",
                "fecha_inicio": pd.Timestamp("2026-01-01"),
                "fecha_fin": None,
                "vigente": True,
            }
            for cid in _ALLOWED_CLIENTS
        ]
        return pd.DataFrame(rows)
