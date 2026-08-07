"""Synthetic document catalogue generator (T039).

Produces one dataset:
- ``catalogo_documental`` — document records matching CATALOGO_DOCUMENTAL_CONTRACT.

Three test scenarios are embedded:
1. DOC-001, DOC-002, DOC-005 — valid documents with referencia_s3 set.
2. DOC-003 — document **without** referencia_s3 (tests nullable path).
3. DOC-004 — document with fecha_incorporacion **after FECHA_CORTE** (tests
   post-cutoff filtering in validation).
"""

from __future__ import annotations

import pandas as pd

from .base import FECHA_CORTE, SyntheticDataGenerator


class DocumentosGenerator(SyntheticDataGenerator):
    SOURCE_NAME = "catalogo_documental"

    def generate_all(self) -> dict[str, pd.DataFrame]:
        return {"catalogo_documental": self._documentos()}

    # ------------------------------------------------------------------
    # catalogo_documental — columnas: documento_id, cliente_id,
    #   tipo_documental, nombre, fecha_documento, fecha_incorporacion,
    #   referencia_s3, sistema_origen, estado, version_doc, checksum
    # ------------------------------------------------------------------
    def _documentos(self) -> pd.DataFrame:
        rows = [
            # Scenario 1: valid document with S3 reference
            {
                "documento_id": "DOC-001", "cliente_id": "CLI-001",
                "tipo_documental": "DNI",
                "nombre": "DNI_CLI001.pdf",
                "fecha_documento": pd.Timestamp("2023-01-10"),
                "fecha_incorporacion": pd.Timestamp("2023-01-15 08:00:00"),
                "referencia_s3": "s3://plaft-docs/cli001/dni.pdf",
                "sistema_origen": "GED",
                "estado": "VIGENTE",
                "version_doc": "1",
                "checksum": "abc123def456",
            },
            {
                "documento_id": "DOC-002", "cliente_id": "CLI-002",
                "tipo_documental": "CONTRATO",
                "nombre": "Contrato_CLI002.pdf",
                "fecha_documento": pd.Timestamp("2022-06-20"),
                "fecha_incorporacion": pd.Timestamp("2022-06-25 10:30:00"),
                "referencia_s3": "s3://plaft-docs/cli002/contrato.pdf",
                "sistema_origen": "GED",
                "estado": "VIGENTE",
                "version_doc": "2",
                "checksum": "def789abc012",
            },
            # Scenario 2: document without referencia_s3
            {
                "documento_id": "DOC-003", "cliente_id": "CLI-003",
                "tipo_documental": "DNI",
                "nombre": "DNI_CLI003.pdf",
                "fecha_documento": pd.Timestamp("2024-03-05"),
                "fecha_incorporacion": pd.Timestamp("2024-03-10 09:00:00"),
                "referencia_s3": None,  # no S3 reference — test nullable path
                "sistema_origen": "MANUAL",
                "estado": "PENDIENTE",
                "version_doc": "1",
                "checksum": None,
            },
            # Scenario 3: document incorporated after FECHA_CORTE
            {
                "documento_id": "DOC-004", "cliente_id": "CLI-004",
                "tipo_documental": "ESTADO_CUENTA",
                "nombre": "Estado_Cuenta_CLI004.pdf",
                "fecha_documento": pd.Timestamp("2026-07-01"),
                "fecha_incorporacion": FECHA_CORTE + pd.Timedelta(days=10),  # 2026-07-10
                "referencia_s3": "s3://plaft-docs/cli004/estado.pdf",
                "sistema_origen": "GED",
                "estado": "VIGENTE",
                "version_doc": "1",
                "checksum": "ghi345jkl678",
            },
            # Scenario 1 continued: CLI-006 valid document
            {
                "documento_id": "DOC-005", "cliente_id": "CLI-006",
                "tipo_documental": "CONTRATO",
                "nombre": "Contrato_CLI006.pdf",
                "fecha_documento": pd.Timestamp("2020-05-01"),
                "fecha_incorporacion": pd.Timestamp("2020-05-05 14:00:00"),
                "referencia_s3": "s3://plaft-docs/cli006/contrato.pdf",
                "sistema_origen": "GED",
                "estado": "VIGENTE",
                "version_doc": "3",
                "checksum": "mno901pqr234",
            },
        ]
        return pd.DataFrame(rows)
