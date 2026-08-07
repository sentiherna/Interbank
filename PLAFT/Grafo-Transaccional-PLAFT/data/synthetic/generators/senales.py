"""Synthetic signal generator (T038).

Produces four datasets:
- ``alertas_plaft``      — alerts matching ALERTAS_PLAFT_CONTRACT
- ``ros``                — suspicious activity reports matching ROS_CONTRACT
- ``pep``                — PEP conditions matching PEP_CONTRACT
- ``casos_investigados`` — investigation cases matching CASOS_INVESTIGADOS_CONTRACT

Signal assignment summary
--------------------------
CLI-001 : ALT-001 (LAVADO, ACTIVA) + ALT-002 (ESTRATIFICACION, CERRADA)
CLI-002 : ALT-003 (LAVADO, ACTIVA)
CLI-003 : ROS-001 (PRESENTADO)
CLI-004 : PEP-001 (NACIONAL, vigente)
CLI-005 : CAS-001 (INVESTIGACION_LAVADO, ABIERTO)
CLI-006 : ALT-004 + ROS-002 + PEP-002 + CAS-002  ← multiple signals
"""

from __future__ import annotations

import pandas as pd

from .base import SyntheticDataGenerator


class SenalesGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "senales"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {
            "alertas_plaft": self._alertas(),
            "ros": self._ros(),
            "pep": self._pep(),
            "casos_investigados": self._casos(),
        }

    # ------------------------------------------------------------------
    # alertas_plaft — columnas: alerta_id, cliente_id, tipo_alerta,
    #                            fecha_alerta, estado, periodo
    # ------------------------------------------------------------------
    def _alertas(self) -> pd.DataFrame:
        rows = [
            {
                "alerta_id": "ALT-001", "cliente_id": "CLI-001",
                "tipo_alerta": "LAVADO",
                "fecha_alerta": pd.Timestamp("2026-04-10 08:00:00"),
                "estado": "ACTIVA", "periodo": "2026-04",
            },
            {
                "alerta_id": "ALT-002", "cliente_id": "CLI-001",
                "tipo_alerta": "ESTRATIFICACION",
                "fecha_alerta": pd.Timestamp("2026-05-15 10:30:00"),
                "estado": "CERRADA", "periodo": "2026-05",
            },
            {
                "alerta_id": "ALT-003", "cliente_id": "CLI-002",
                "tipo_alerta": "LAVADO",
                "fecha_alerta": pd.Timestamp("2026-03-20 09:00:00"),
                "estado": "ACTIVA", "periodo": "2026-03",
            },
            # CLI-006 — parte de las múltiples señales
            {
                "alerta_id": "ALT-004", "cliente_id": "CLI-006",
                "tipo_alerta": "LAVADO",
                "fecha_alerta": pd.Timestamp("2026-04-01 07:30:00"),
                "estado": "ACTIVA", "periodo": "2026-04",
            },
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # ros — columnas: ros_id, cliente_id, fecha_reporte, estado
    # ------------------------------------------------------------------
    def _ros(self) -> pd.DataFrame:
        rows = [
            {
                "ros_id": "ROS-001", "cliente_id": "CLI-003",
                "fecha_reporte": pd.Timestamp("2026-02-15"),
                "estado": "PRESENTADO",
            },
            {
                "ros_id": "ROS-002", "cliente_id": "CLI-006",
                "fecha_reporte": pd.Timestamp("2026-03-01"),
                "estado": "EN_REVISION",
            },
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # pep — columnas: pep_id, cliente_id, categoria_pep, fecha_inicio,
    #                  fecha_fin, vigente
    # ------------------------------------------------------------------
    def _pep(self) -> pd.DataFrame:
        rows = [
            {
                "pep_id": "PEP-001", "cliente_id": "CLI-004",
                "categoria_pep": "NACIONAL",
                "fecha_inicio": pd.Timestamp("2024-01-01"),
                "fecha_fin": None,
                "vigente": True,
            },
            {
                "pep_id": "PEP-002", "cliente_id": "CLI-006",
                "categoria_pep": "FAMILIAR",
                "fecha_inicio": pd.Timestamp("2023-06-01"),
                "fecha_fin": None,
                "vigente": True,
            },
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # casos_investigados — columnas: caso_id, cliente_id, tipo_caso,
    #                                 fecha_apertura, fecha_cierre,
    #                                 estado, resultado
    # ------------------------------------------------------------------
    def _casos(self) -> pd.DataFrame:
        rows = [
            {
                "caso_id": "CAS-001", "cliente_id": "CLI-005",
                "tipo_caso": "INVESTIGACION_LAVADO",
                "fecha_apertura": pd.Timestamp("2026-01-10"),
                "fecha_cierre": None,
                "estado": "ABIERTO",
                "resultado": None,
            },
            {
                "caso_id": "CAS-002", "cliente_id": "CLI-006",
                "tipo_caso": "INVESTIGACION_LAVADO",
                "fecha_apertura": pd.Timestamp("2025-11-20"),
                "fecha_cierre": pd.Timestamp("2026-04-30"),
                "estado": "CERRADO",
                "resultado": "CONFIRMADO",
            },
        ]
        return pd.DataFrame(rows)
