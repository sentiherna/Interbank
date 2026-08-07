"""Synthetic accounts generator (T036).

Produces three datasets:
- ``cuentas``      — 11 accounts matching the CUENTAS_CONTRACT schema.
- ``titularidades`` — account-to-client ownership (CTA-009 has 2 titulares).
- ``productos``    — financial products per client.

CTA-009 is the shared account:
  Principal  → CLI-007
  Cotitular  → CLI-008
This tests the multiple-titular invariant.
"""

from __future__ import annotations

import pandas as pd

from .base import SyntheticDataGenerator


class CuentasGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "cuentas"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {
            "cuentas": self._cuentas(),
            "titularidades": self._titularidades(),
            "productos": self._productos(),
        }

    # ------------------------------------------------------------------
    # cuentas — columnas: cuenta_id, tipo_cuenta, moneda, estado,
    #                      fecha_apertura
    # ------------------------------------------------------------------
    def _cuentas(self) -> pd.DataFrame:
        rows = [
            {"cuenta_id": "CTA-001", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2020-02-01")},
            {"cuenta_id": "CTA-002", "tipo_cuenta": "CORRIENTE",
             "moneda": "USD", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2021-05-15")},
            {"cuenta_id": "CTA-003", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2019-04-10")},
            {"cuenta_id": "CTA-004", "tipo_cuenta": "CORRIENTE",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2018-08-20")},
            {"cuenta_id": "CTA-005", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2021-12-01")},
            {"cuenta_id": "CTA-006", "tipo_cuenta": "CORRIENTE",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2017-06-15")},
            {"cuenta_id": "CTA-007", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2016-10-05")},
            {"cuenta_id": "CTA-008", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2022-03-01")},
            # CTA-009: shared between CLI-007 (Principal) and CLI-008 (Cotitular)
            {"cuenta_id": "CTA-009", "tipo_cuenta": "CORRIENTE",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2020-07-20")},
            {"cuenta_id": "CTA-010", "tipo_cuenta": "AHORRO",
             "moneda": "USD", "estado": "CERRADA",
             "fecha_apertura": pd.Timestamp("2016-01-10")},
            {"cuenta_id": "CTA-011", "tipo_cuenta": "AHORRO",
             "moneda": "PEN", "estado": "ACTIVA",
             "fecha_apertura": pd.Timestamp("2024-04-01")},
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # titularidades — columnas: cliente_id, cuenta_id, tipo_titularidad,
    #                            fecha_inicio, fecha_fin
    # ------------------------------------------------------------------
    def _titularidades(self) -> pd.DataFrame:
        rows = [
            # CLI-001 owns CTA-001 and CTA-002
            {"cliente_id": "CLI-001", "cuenta_id": "CTA-001",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2020-02-01"), "fecha_fin": None},
            {"cliente_id": "CLI-001", "cuenta_id": "CTA-002",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2021-05-15"), "fecha_fin": None},
            # Single-owner accounts
            {"cliente_id": "CLI-002", "cuenta_id": "CTA-003",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2019-04-10"), "fecha_fin": None},
            {"cliente_id": "CLI-003", "cuenta_id": "CTA-004",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2018-08-20"), "fecha_fin": None},
            {"cliente_id": "CLI-004", "cuenta_id": "CTA-005",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2021-12-01"), "fecha_fin": None},
            {"cliente_id": "CLI-005", "cuenta_id": "CTA-006",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2017-06-15"), "fecha_fin": None},
            {"cliente_id": "CLI-006", "cuenta_id": "CTA-007",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2016-10-05"), "fecha_fin": None},
            {"cliente_id": "CLI-007", "cuenta_id": "CTA-008",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2022-03-01"), "fecha_fin": None},
            # Shared account CTA-009: CLI-007 (Principal) + CLI-008 (Cotitular)
            {"cliente_id": "CLI-007", "cuenta_id": "CTA-009",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2020-07-20"), "fecha_fin": None},
            {"cliente_id": "CLI-008", "cuenta_id": "CTA-009",
             "tipo_titularidad": "Cotitular",
             "fecha_inicio": pd.Timestamp("2023-09-01"), "fecha_fin": None},
            {"cliente_id": "CLI-009", "cuenta_id": "CTA-010",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2016-01-10"), "fecha_fin": None},
            {"cliente_id": "CLI-010", "cuenta_id": "CTA-011",
             "tipo_titularidad": "Principal",
             "fecha_inicio": pd.Timestamp("2024-04-01"), "fecha_fin": None},
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # productos — columnas: producto_id, cliente_id, tipo_producto,
    #                        estado, fecha_contratacion
    # ------------------------------------------------------------------
    def _productos(self) -> pd.DataFrame:
        rows = [
            {"producto_id": "PRD-001", "cliente_id": "CLI-001",
             "tipo_producto": "CREDITO_PERSONAL",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2020-06-01")},
            {"producto_id": "PRD-002", "cliente_id": "CLI-002",
             "tipo_producto": "DEPOSITO_PLAZO",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2021-01-15")},
            {"producto_id": "PRD-003", "cliente_id": "CLI-003",
             "tipo_producto": "PRESTAMO_COMERCIAL",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2019-03-20")},
            {"producto_id": "PRD-004", "cliente_id": "CLI-004",
             "tipo_producto": "DEPOSITO_PLAZO",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2022-02-10")},
            {"producto_id": "PRD-005", "cliente_id": "CLI-005",
             "tipo_producto": "CREDITO_HIPOTECARIO",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2018-11-30")},
            {"producto_id": "PRD-006", "cliente_id": "CLI-006",
             "tipo_producto": "CREDITO_PERSONAL",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2017-04-05")},
            {"producto_id": "PRD-007", "cliente_id": "CLI-007",
             "tipo_producto": "DEPOSITO_PLAZO",
             "estado": "ACTIVO", "fecha_contratacion": pd.Timestamp("2022-05-20")},
            {"producto_id": "PRD-008", "cliente_id": "CLI-001",
             "tipo_producto": "SEGURO_VIDA",
             "estado": "CERRADO", "fecha_contratacion": pd.Timestamp("2021-08-12")},
        ]
        return pd.DataFrame(rows)
