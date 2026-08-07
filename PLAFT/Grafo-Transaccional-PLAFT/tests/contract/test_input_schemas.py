"""Pruebas de contrato para esquemas de datos de entrada (T028).

Cubre las fuentes: clientes, cuentas, titularidades, productos, transferencias.
Para cada fuente verifica: fila válida, columna obligatoria ausente, nulo no
permitido, duplicado de clave y dominio inválido cuando corresponda.
"""

from __future__ import annotations

import pandas as pd

from graph_plaft.validation.contracts import validate_schema
from graph_plaft.validation.schemas import (
    CLIENTES_CONTRACT,
    CUENTAS_CONTRACT,
    PRODUCTOS_CONTRACT,
    TITULARIDADES_CONTRACT,
    TRANSFERENCIAS_CONTRACT,
)

# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------


class TestClientesContract:
    def _valid_row(self) -> dict:
        return {"cliente_id": "CLI-001", "tipo_persona": "NATURAL"}

    def test_fila_valida_sin_issues_criticos(self):
        df = pd.DataFrame([self._valid_row()])
        report = validate_schema(df, CLIENTES_CONTRACT)
        assert not report.has_critical_errors(), report.summary()

    def test_columna_obligatoria_ausente(self):
        df = pd.DataFrame([{"tipo_persona": "NATURAL"}])  # sin cliente_id
        report = validate_schema(df, CLIENTES_CONTRACT)
        assert report.has_critical_errors()
        assert any("cliente_id" in i.message for i in report.critical_issues())

    def test_nulo_en_columna_obligatoria(self):
        df = pd.DataFrame([{"cliente_id": None}])
        report = validate_schema(df, CLIENTES_CONTRACT)
        assert report.has_critical_errors()

    def test_duplicado_de_clave(self):
        df = pd.DataFrame([
            {"cliente_id": "CLI-001"},
            {"cliente_id": "CLI-001"},
        ])
        report = validate_schema(df, CLIENTES_CONTRACT)
        assert report.has_critical_errors()
        assert any("primary_key_unique" in i.rule for i in report.critical_issues())

    def test_dominio_invalido_tipo_persona(self):
        df = pd.DataFrame([{"cliente_id": "CLI-002", "tipo_persona": "ROBOT"}])
        report = validate_schema(df, CLIENTES_CONTRACT)
        # Dominio inválido es WARNING (no crítico) según el contrato
        assert not report.has_critical_errors()
        assert any("allowed_values" in i.rule for i in report.warnings())


# ---------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------


class TestCuentasContract:
    def test_fila_valida(self):
        df = pd.DataFrame([{"cuenta_id": "CTA-001", "tipo_cuenta": "AHORROS"}])
        report = validate_schema(df, CUENTAS_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_cuenta_id(self):
        df = pd.DataFrame([{"tipo_cuenta": "AHORROS"}])
        report = validate_schema(df, CUENTAS_CONTRACT)
        assert report.has_critical_errors()

    def test_duplicado_cuenta_id(self):
        df = pd.DataFrame([{"cuenta_id": "CTA-001"}, {"cuenta_id": "CTA-001"}])
        report = validate_schema(df, CUENTAS_CONTRACT)
        assert report.has_critical_errors()


# ---------------------------------------------------------------------------
# Titularidades
# ---------------------------------------------------------------------------


class TestTitularidadesContract:
    def _valid_row(self) -> dict:
        return {
            "cliente_id": "CLI-001",
            "cuenta_id": "CTA-001",
            "tipo_titularidad": "Principal",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid_row()])
        report = validate_schema(df, TITULARIDADES_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_cliente_id(self):
        df = pd.DataFrame([{"cuenta_id": "CTA-001", "tipo_titularidad": "Principal"}])
        report = validate_schema(df, TITULARIDADES_CONTRACT)
        assert report.has_critical_errors()

    def test_dominio_invalido_titularidad(self):
        row = self._valid_row()
        row["tipo_titularidad"] = "SOCIO"  # fuera de dominio
        df = pd.DataFrame([row])
        report = validate_schema(df, TITULARIDADES_CONTRACT)
        assert any("allowed_values" in i.rule for i in report.warnings())


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------


class TestProductosContract:
    def _valid_row(self) -> dict:
        return {
            "producto_id": "PROD-001",
            "cliente_id": "CLI-001",
            "tipo_producto": "CREDITO",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid_row()])
        report = validate_schema(df, PRODUCTOS_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_tipo_producto_es_critico(self):
        df = pd.DataFrame([{"producto_id": "PROD-001", "cliente_id": "CLI-001"}])
        report = validate_schema(df, PRODUCTOS_CONTRACT)
        assert report.has_critical_errors()

    def test_nulo_en_tipo_producto(self):
        df = pd.DataFrame([
            {"producto_id": "PROD-001", "cliente_id": "CLI-001", "tipo_producto": None}
        ])
        report = validate_schema(df, PRODUCTOS_CONTRACT)
        assert report.has_critical_errors()


# ---------------------------------------------------------------------------
# Transferencias
# ---------------------------------------------------------------------------


class TestTransferenciasContract:
    def _valid_row(self) -> dict:
        return {
            "id_transaccion": "TX-001",
            "cuenta_origen": "CTA-001",
            "cuenta_destino": "CTA-002",
            "fecha_hora": "2026-07-01T10:00:00",
            "monto": 1000.0,
            "moneda": "PEN",
            "estado": "EJECUTADA",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid_row()])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_id_transaccion(self):
        row = self._valid_row()
        del row["id_transaccion"]
        df = pd.DataFrame([row])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert report.has_critical_errors()

    def test_nulo_en_id_transaccion(self):
        row = self._valid_row()
        row["id_transaccion"] = None
        df = pd.DataFrame([row])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert report.has_critical_errors()

    def test_duplicado_de_transaccion(self):
        row = self._valid_row()
        df = pd.DataFrame([row, row.copy()])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert report.has_critical_errors()
        assert any("primary_key_unique" in i.rule for i in report.critical_issues())

    def test_estado_invalido(self):
        row = self._valid_row()
        row["estado"] = "PROCESANDO"  # fuera de dominio
        df = pd.DataFrame([row])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert any("allowed_values" in i.rule for i in report.warnings())

    def test_canal_invalido(self):
        row = self._valid_row()
        row["canal"] = "TELEPATA"  # fuera de dominio
        df = pd.DataFrame([row])
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert any("allowed_values" in i.rule for i in report.warnings())

    def test_multiples_tx_mismo_par_cuentas_no_son_duplicados(self):
        """Múltiples TX entre las mismas cuentas son aristas distintas (ADR-001)."""
        rows = [
            {**self._valid_row(), "id_transaccion": "TX-001"},
            {**self._valid_row(), "id_transaccion": "TX-002"},
            {**self._valid_row(), "id_transaccion": "TX-003"},
        ]
        df = pd.DataFrame(rows)
        report = validate_schema(df, TRANSFERENCIAS_CONTRACT)
        assert not report.has_critical_errors()
