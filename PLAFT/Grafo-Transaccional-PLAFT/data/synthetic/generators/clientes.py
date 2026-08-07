"""Synthetic client generator (T035).

Produces two datasets:
- ``clientes``     — 10 clients matching the CLIENTES_CONTRACT schema.
- ``lista_objetivo`` — 6 "objetivo" clients matching the LISTA_OBJETIVO_CONTRACT schema.

Client signal profiles
----------------------
CLI-001 : objetivo — 2 alertas PLAFT
CLI-002 : objetivo — 1 alerta PLAFT
CLI-003 : objetivo — 1 ROS
CLI-004 : objetivo — condición PEP
CLI-005 : objetivo — 1 caso investigado
CLI-006 : objetivo — múltiples señales (alerta + ROS + PEP + caso)
CLI-007 : contraparte — sin señales
CLI-008 : contraparte — sin señales (cotitular de CTA-009, cuenta compartida)
CLI-009 : contraparte — sin señales
CLI-010 : contraparte — sin señales (excluido de permisos del analista ANA-001)
"""

from __future__ import annotations

import pandas as pd

from .base import FECHA_CORTE, SyntheticDataGenerator


class ClientesGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "clientes"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {
            "clientes": self._clientes(),
            "lista_objetivo": self._lista_objetivo(),
        }

    # ------------------------------------------------------------------
    # clientes — columnas: cliente_id, tipo_persona, estado_cliente,
    #                       fecha_alta, segmento
    # ------------------------------------------------------------------
    def _clientes(self) -> pd.DataFrame:
        rows = [
            # 2 alertas → high-signal objective client
            {
                "cliente_id": "CLI-001",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2020-01-15"),
                "segmento": "RETAIL",
            },
            # 1 alerta
            {
                "cliente_id": "CLI-002",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2019-03-22"),
                "segmento": "RETAIL",
            },
            # ROS
            {
                "cliente_id": "CLI-003",
                "tipo_persona": "JURIDICA",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2018-07-10"),
                "segmento": "EMPRESAS",
            },
            # PEP
            {
                "cliente_id": "CLI-004",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2021-11-01"),
                "segmento": "PREFERENCIAL",
            },
            # caso investigado
            {
                "cliente_id": "CLI-005",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2017-05-08"),
                "segmento": "RETAIL",
            },
            # múltiples señales
            {
                "cliente_id": "CLI-006",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2016-09-30"),
                "segmento": "RETAIL",
            },
            # contraparte — cotitular de CTA-009
            {
                "cliente_id": "CLI-007",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2022-02-14"),
                "segmento": "RETAIL",
            },
            # contraparte — cotitular de CTA-009
            {
                "cliente_id": "CLI-008",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2023-06-01"),
                "segmento": "RETAIL",
            },
            # contraparte
            {
                "cliente_id": "CLI-009",
                "tipo_persona": "JURIDICA",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2015-12-20"),
                "segmento": "EMPRESAS",
            },
            # contraparte — excluido de permisos de ANA-001
            {
                "cliente_id": "CLI-010",
                "tipo_persona": "NATURAL",
                "estado_cliente": "ACTIVO",
                "fecha_alta": pd.Timestamp("2024-03-07"),
                "segmento": "RETAIL",
            },
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # lista_objetivo — columnas: cliente_id, motivo_inclusion,
    #                             fecha_inclusion, version_lista
    # ------------------------------------------------------------------
    def _lista_objetivo(self) -> pd.DataFrame:
        motivos = {
            "CLI-001": "ALERTA_MULTIPLE",
            "CLI-002": "ALERTA_PLAFT",
            "CLI-003": "ROS_PRESENTADO",
            "CLI-004": "CONDICION_PEP",
            "CLI-005": "CASO_INVESTIGADO",
            "CLI-006": "SENALES_MULTIPLES",
        }
        rows = [
            {
                "cliente_id": cid,
                "motivo_inclusion": motivo,
                "fecha_inclusion": FECHA_CORTE - pd.Timedelta(days=30),
                "version_lista": "v1.0",
            }
            for cid, motivo in motivos.items()
        ]
        return pd.DataFrame(rows)
