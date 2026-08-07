"""Synthetic transfer generator (T037).

Produces one dataset:
- ``transferencias`` — 17 transactions that cover eight test patterns.

Pattern catalogue
-----------------
P1  STAR         CLI-001 sends to CLI-002, CLI-003, CLI-004, CLI-005, CLI-006 (star hub)
P2  CHAIN        CLI-001 → CLI-002 → CLI-003 (sequential relay)
P3  CYCLE        CLI-002 ↔ CLI-003 (bidirectional / cycle)
P4  HUB_IN       CLI-001, CLI-002, CLI-003 → CLI-006 (high in-degree hub)
P5  INTERMEDIARY CLI-001 → CLI-007 → CLI-002 (bridge node)
P6  MULTI_TX     3 separate transfers CTA-002 → CTA-003 (same pair, not deduplicated)
P7  CANCELLED    ANULADA and REVERTIDA transactions (must not produce active edges)
P8  POST_CUTOFF  One EJECUTADA transaction dated after FECHA_CORTE (2026-07-15)

Expected active graph (EJECUTADA, within cutoff): TX-001..TX-014
Expected excluded (P7+P8): TX-015, TX-016, TX-017
"""

from __future__ import annotations

import pandas as pd

from .base import FECHA_CORTE, SyntheticDataGenerator


class TransferenciasGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "transferencias"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {"transferencias": self._transferencias()}

    def _transferencias(self) -> pd.DataFrame:
        rows = [
            # ── P1: STAR — CLI-001 (CTA-001) fans out to four counterparties ─────────
            {
                "id_transaccion": "TX-001", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-03-10 09:00:00"),
                "monto": 5000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-03",
            },
            {
                "id_transaccion": "TX-002", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-004",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-003",
                "fecha_hora": pd.Timestamp("2026-03-12 10:15:00"),
                "monto": 3000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-03",
            },
            {
                "id_transaccion": "TX-003", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-005",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-004",
                "fecha_hora": pd.Timestamp("2026-03-15 11:30:00"),
                "monto": 2000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-03",
            },
            {
                "id_transaccion": "TX-004", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-006",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-005",
                "fecha_hora": pd.Timestamp("2026-03-18 14:00:00"),
                "monto": 1500.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "AGENCIA", "periodo": "2026-03",
            },
            # ── P2: CHAIN continuation — CLI-002 relays to CLI-003 ───────────────────
            {
                "id_transaccion": "TX-005", "cuenta_origen": "CTA-003", "cuenta_destino": "CTA-004",
                "cliente_origen": "CLI-002", "cliente_destino": "CLI-003",
                "fecha_hora": pd.Timestamp("2026-03-20 08:45:00"),
                "monto": 2500.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-03",
            },
            # ── P3: CYCLE — CLI-003 sends back to CLI-002 ────────────────────────────
            {
                "id_transaccion": "TX-006", "cuenta_origen": "CTA-004", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-003", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-03-25 16:20:00"),
                "monto": 2000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-03",
            },
            # ── P4: HUB_IN — three clients converge on CLI-006 ───────────────────────
            {
                "id_transaccion": "TX-007", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-007",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-006",
                "fecha_hora": pd.Timestamp("2026-04-02 09:00:00"),
                "monto": 4000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "SWIFT", "periodo": "2026-04",
            },
            {
                "id_transaccion": "TX-008", "cuenta_origen": "CTA-003", "cuenta_destino": "CTA-007",
                "cliente_origen": "CLI-002", "cliente_destino": "CLI-006",
                "fecha_hora": pd.Timestamp("2026-04-05 11:00:00"),
                "monto": 3000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-04",
            },
            {
                "id_transaccion": "TX-009", "cuenta_origen": "CTA-004", "cuenta_destino": "CTA-007",
                "cliente_origen": "CLI-003", "cliente_destino": "CLI-006",
                "fecha_hora": pd.Timestamp("2026-04-08 13:30:00"),
                "monto": 2000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-04",
            },
            # ── P5: INTERMEDIARY — CLI-007 bridges CLI-001 and CLI-002 ───────────────
            {
                "id_transaccion": "TX-010", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-008",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-007",
                "fecha_hora": pd.Timestamp("2026-05-01 10:00:00"),
                "monto": 8000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-05",
            },
            {
                "id_transaccion": "TX-011", "cuenta_origen": "CTA-008", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-007", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-05-03 15:00:00"),
                "monto": 7500.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-05",
            },
            # ── P6: MULTI_TX — same account pair, three independent transactions ──────
            {
                "id_transaccion": "TX-012", "cuenta_origen": "CTA-002", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-06-01 09:00:00"),
                "monto": 1000.00, "moneda": "USD", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-06",
            },
            {
                "id_transaccion": "TX-013", "cuenta_origen": "CTA-002", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-06-10 10:00:00"),
                "monto": 1100.00, "moneda": "USD", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-06",
            },
            {
                "id_transaccion": "TX-014", "cuenta_origen": "CTA-002", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-06-20 11:00:00"),
                "monto": 900.00,  "moneda": "USD", "estado": "EJECUTADA",
                "canal": "WEB",   "periodo": "2026-06",
            },
            # ── P7: CANCELLED — must not produce active graph edges ───────────────────
            {
                "id_transaccion": "TX-015", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": pd.Timestamp("2026-04-15 12:00:00"),
                "monto": 5000.00, "moneda": "PEN", "estado": "ANULADA",
                "canal": "APP",   "periodo": "2026-04",
            },
            {
                "id_transaccion": "TX-016", "cuenta_origen": "CTA-004", "cuenta_destino": "CTA-005",
                "cliente_origen": "CLI-003", "cliente_destino": "CLI-004",
                "fecha_hora": pd.Timestamp("2026-05-20 09:00:00"),
                "monto": 3000.00, "moneda": "PEN", "estado": "REVERTIDA",
                "canal": "WEB",   "periodo": "2026-05",
            },
            # ── P8: POST_CUTOFF — fecha_hora after FECHA_CORTE (2026-06-30) ───────────
            {
                "id_transaccion": "TX-017", "cuenta_origen": "CTA-001", "cuenta_destino": "CTA-003",
                "cliente_origen": "CLI-001", "cliente_destino": "CLI-002",
                "fecha_hora": FECHA_CORTE + pd.Timedelta(days=15),  # 2026-07-15
                "monto": 2000.00, "moneda": "PEN", "estado": "EJECUTADA",
                "canal": "APP",   "periodo": "2026-07",
            },
        ]
        return pd.DataFrame(rows)
