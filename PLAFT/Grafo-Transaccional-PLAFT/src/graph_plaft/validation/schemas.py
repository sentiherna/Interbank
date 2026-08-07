"""Contratos de datos para todas las fuentes del MVP.

Cada contrato define las columnas conceptuales, sus tipos, obligatoriedad,
dominio permitido y claves de negocio. Las columnas físicas se mapean
mediante ``ColumnMappingRegistry`` (ver ``config/column_mapping.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ColumnDtype(StrEnum):
    """Tipos de dato conceptuales compatibles con pandas y PyArrow."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    ARRAY_STRING = "array<string>"


@dataclass(frozen=True)
class ColumnContract:
    """Contrato de una columna individual."""

    name: str
    dtype: ColumnDtype
    required: bool = True
    nullable: bool = False
    description: str = ""
    allowed_values: frozenset[str] | None = None  # dominio permitido
    is_primary_key: bool = False
    is_temporal: bool = False  # True si es columna de fecha/hora


@dataclass(frozen=True)
class SourceContract:
    """Contrato completo para una fuente de datos."""

    source_name: str
    columns: tuple[ColumnContract, ...]
    primary_keys: tuple[str, ...]
    description: str = ""

    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def required_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.required]

    def temporal_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.is_temporal]

    def get_column(self, name: str) -> ColumnContract | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None


# ---------------------------------------------------------------------------
# Constantes de dominio
# ---------------------------------------------------------------------------

_ESTADOS_TX: frozenset[str] = frozenset({"EJECUTADA", "ANULADA", "REVERTIDA", "PENDIENTE"})
_CANALES_TX: frozenset[str] = frozenset({"APP", "WEB", "AGENCIA", "ATM", "SWIFT", "OTROS"})
_TIPOS_PERSONA: frozenset[str] = frozenset({"NATURAL", "JURIDICA"})
_NIVEL_ACCESO: frozenset[str] = frozenset({"DATOS", "DOCUMENTOS", "AMBOS"})


# ---------------------------------------------------------------------------
# Contrato: clientes
# ---------------------------------------------------------------------------

CLIENTES_CONTRACT = SourceContract(
    source_name="clientes",
    primary_keys=("cliente_id",),
    description="Maestro de clientes del banco.",
    columns=(
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único del cliente.",
        ),
        ColumnContract(
            name="tipo_persona",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            allowed_values=_TIPOS_PERSONA,
            description="NATURAL o JURIDICA.",
        ),
        ColumnContract(
            name="estado_cliente",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado operativo del cliente en el banco.",
        ),
        ColumnContract(
            name="fecha_alta",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de incorporación como cliente.",
        ),
        ColumnContract(
            name="segmento",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Segmento de negocio al que pertenece el cliente.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: cuentas
# ---------------------------------------------------------------------------

CUENTAS_CONTRACT = SourceContract(
    source_name="cuentas",
    primary_keys=("cuenta_id",),
    description="Maestro de cuentas bancarias.",
    columns=(
        ColumnContract(
            name="cuenta_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único de la cuenta.",
        ),
        ColumnContract(
            name="tipo_cuenta",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Tipo de producto bancario de la cuenta.",
        ),
        ColumnContract(
            name="moneda",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Código ISO 4217 de la moneda.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado: ACTIVA / CERRADA / BLOQUEADA.",
        ),
        ColumnContract(
            name="fecha_apertura",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de apertura de la cuenta.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: titularidades
# ---------------------------------------------------------------------------

TITULARIDADES_CONTRACT = SourceContract(
    source_name="titularidades",
    primary_keys=("cliente_id", "cuenta_id", "tipo_titularidad"),
    description="Relación cliente↔cuenta. Una cuenta puede tener múltiples titulares.",
    columns=(
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="cuenta_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="FK → cuentas.cuenta_id.",
        ),
        ColumnContract(
            name="tipo_titularidad",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            is_primary_key=True,
            allowed_values=frozenset({"Principal", "Cotitular", "Apoderado"}),
            description="Tipo de titularidad sobre la cuenta.",
        ),
        ColumnContract(
            name="fecha_inicio",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de inicio de la titularidad.",
        ),
        ColumnContract(
            name="fecha_fin",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de fin (null si vigente).",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: productos
# ---------------------------------------------------------------------------

PRODUCTOS_CONTRACT = SourceContract(
    source_name="productos",
    primary_keys=("producto_id",),
    description="Productos financieros contratados por clientes.",
    columns=(
        ColumnContract(
            name="producto_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único del producto.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="tipo_producto",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="Categoría del producto financiero.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado del producto.",
        ),
        ColumnContract(
            name="fecha_contratacion",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de contratación.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: transferencias
# ---------------------------------------------------------------------------

TRANSFERENCIAS_CONTRACT = SourceContract(
    source_name="transferencias",
    primary_keys=("id_transaccion",),
    description=(
        "Transferencias de fondos entre cuentas. "
        "Clave de identidad: id_transaccion. "
        "NO deduplicar por par cuenta_origen+cuenta_destino (ADR-001)."
    ),
    columns=(
        ColumnContract(
            name="id_transaccion",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único de la transferencia.",
        ),
        ColumnContract(
            name="cuenta_origen",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → cuentas.cuenta_id.",
        ),
        ColumnContract(
            name="cuenta_destino",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → cuentas.cuenta_id.",
        ),
        ColumnContract(
            name="fecha_hora",
            dtype=ColumnDtype.TIMESTAMP,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Fecha y hora de la transferencia. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="monto",
            dtype=ColumnDtype.FLOAT,
            required=True,
            nullable=False,
            description="Monto de la transferencia. Debe ser > 0 si estado = EJECUTADA.",
        ),
        ColumnContract(
            name="moneda",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="Código ISO 4217 de la moneda.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            allowed_values=_ESTADOS_TX,
            description="Estado de la transacción.",
        ),
        ColumnContract(
            name="canal",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            allowed_values=_CANALES_TX,
            description="Canal de origen de la transacción.",
        ),
        ColumnContract(
            name="periodo",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Período YYYY-MM coherente con fecha_hora.",
        ),
        ColumnContract(
            name="cliente_origen",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Cliente resolvible como origen (puede ser null).",
        ),
        ColumnContract(
            name="cliente_destino",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Cliente resolvible como destino (puede ser null).",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: alertas_plaft
# ---------------------------------------------------------------------------

ALERTAS_PLAFT_CONTRACT = SourceContract(
    source_name="alertas_plaft",
    primary_keys=("alerta_id",),
    description="Alertas generadas por el sistema PLAFT para clientes.",
    columns=(
        ColumnContract(
            name="alerta_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único de la alerta.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="tipo_alerta",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="Código o tipo de alerta PLAFT.",
        ),
        ColumnContract(
            name="fecha_alerta",
            dtype=ColumnDtype.TIMESTAMP,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Fecha de generación de la alerta. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado de la alerta (ACTIVA, CERRADA, ESCALADA).",
        ),
        ColumnContract(
            name="periodo",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Período YYYY-MM de la alerta.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: ros
# ---------------------------------------------------------------------------

ROS_CONTRACT = SourceContract(
    source_name="ros",
    primary_keys=("ros_id",),
    description="Reportes de Operación Sospechosa.",
    columns=(
        ColumnContract(
            name="ros_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único del ROS.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="fecha_reporte",
            dtype=ColumnDtype.DATE,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Fecha del reporte. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado del ROS.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: pep
# ---------------------------------------------------------------------------

PEP_CONTRACT = SourceContract(
    source_name="pep",
    primary_keys=("pep_id",),
    description=(
        "Condición PEP (Persona Expuesta Políticamente). "
        "Factor de debida diligencia reforzada, NO evidencia de sospecha."
    ),
    columns=(
        ColumnContract(
            name="pep_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador del registro PEP.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="categoria_pep",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Categoría de PEP (nacional, extranjero, familiar, etc.).",
        ),
        ColumnContract(
            name="fecha_inicio",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de inicio de la condición PEP.",
        ),
        ColumnContract(
            name="fecha_fin",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de fin (null si vigente a la fecha de corte).",
        ),
        ColumnContract(
            name="vigente",
            dtype=ColumnDtype.BOOLEAN,
            required=True,
            nullable=False,
            description="True si la condición PEP está vigente a la fecha de corte.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: casos_investigados
# ---------------------------------------------------------------------------

CASOS_INVESTIGADOS_CONTRACT = SourceContract(
    source_name="casos_investigados",
    primary_keys=("caso_id",),
    description="Casos de investigación PLAFT asociados a clientes.",
    columns=(
        ColumnContract(
            name="caso_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único del caso.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="tipo_caso",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Tipología del caso.",
        ),
        ColumnContract(
            name="fecha_apertura",
            dtype=ColumnDtype.DATE,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Fecha de apertura. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="fecha_cierre",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de cierre (null si abierto).",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            allowed_values=frozenset({"ABIERTO", "CERRADO", "ARCHIVADO"}),
            description="Estado del caso.",
        ),
        ColumnContract(
            name="resultado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Resultado del caso si cerrado.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: catalogo_documental
# ---------------------------------------------------------------------------

CATALOGO_DOCUMENTAL_CONTRACT = SourceContract(
    source_name="catalogo_documental",
    primary_keys=("documento_id",),
    description=(
        "Catálogo de documentos asociados a clientes. "
        "Solo metadatos y referencia S3; sin contenido ni OCR en esta versión."
    ),
    columns=(
        ColumnContract(
            name="documento_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador único del documento.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="tipo_documental",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="Tipo de documento (DNI, contrato, estado de cuenta, etc.).",
        ),
        ColumnContract(
            name="nombre",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Nombre descriptivo del documento.",
        ),
        ColumnContract(
            name="fecha_documento",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha del documento.",
        ),
        ColumnContract(
            name="fecha_incorporacion",
            dtype=ColumnDtype.TIMESTAMP,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fecha de incorporación al sistema. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="referencia_s3",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Ruta S3 del documento (puede ser null si no disponible).",
        ),
        ColumnContract(
            name="sistema_origen",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            description="Sistema que generó el documento.",
        ),
        ColumnContract(
            name="estado",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Estado del documento.",
        ),
        ColumnContract(
            name="version_doc",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Versión del documento.",
        ),
        ColumnContract(
            name="checksum",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Hash de integridad del archivo (cuando esté disponible).",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: lista_objetivo
# ---------------------------------------------------------------------------

LISTA_OBJETIVO_CONTRACT = SourceContract(
    source_name="lista_objetivo",
    primary_keys=("cliente_id", "version_lista"),
    description="Lista de clientes objetivo provista por el equipo PLAFT.",
    columns=(
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="motivo_inclusion",
            dtype=ColumnDtype.STRING,
            required=False,
            nullable=True,
            description="Justificación de la inclusión en la lista.",
        ),
        ColumnContract(
            name="fecha_inclusion",
            dtype=ColumnDtype.DATE,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Fecha de incorporación. Debe ser ≤ fecha_corte.",
        ),
        ColumnContract(
            name="version_lista",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Versión de la lista para versionado del run.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Contrato: permisos_analistas
# ---------------------------------------------------------------------------

PERMISOS_ANALISTAS_CONTRACT = SourceContract(
    source_name="permisos_analistas",
    primary_keys=("usuario_id", "cliente_id", "nivel_acceso"),
    description=(
        "Permisos de acceso de analistas a clientes y documentos. "
        "Provistos por el sistema corporativo; el MVP los consume pero no los gestiona."
    ),
    columns=(
        ColumnContract(
            name="usuario_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="Identificador del analista.",
        ),
        ColumnContract(
            name="cliente_id",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            description="FK → clientes.cliente_id.",
        ),
        ColumnContract(
            name="nivel_acceso",
            dtype=ColumnDtype.STRING,
            required=True,
            nullable=False,
            is_primary_key=True,
            allowed_values=_NIVEL_ACCESO,
            description="DATOS / DOCUMENTOS / AMBOS.",
        ),
        ColumnContract(
            name="fecha_inicio",
            dtype=ColumnDtype.DATE,
            required=True,
            nullable=False,
            is_temporal=True,
            description="Inicio de vigencia del permiso.",
        ),
        ColumnContract(
            name="fecha_fin",
            dtype=ColumnDtype.DATE,
            required=False,
            nullable=True,
            is_temporal=True,
            description="Fin de vigencia (null si vigente).",
        ),
        ColumnContract(
            name="vigente",
            dtype=ColumnDtype.BOOLEAN,
            required=True,
            nullable=False,
            description="True si el permiso está vigente a la fecha de consulta.",
        ),
    ),
)

# ---------------------------------------------------------------------------
# Registro de todos los contratos por nombre de fuente
# ---------------------------------------------------------------------------

ALL_CONTRACTS: dict[str, SourceContract] = {
    "clientes": CLIENTES_CONTRACT,
    "cuentas": CUENTAS_CONTRACT,
    "titularidades": TITULARIDADES_CONTRACT,
    "productos": PRODUCTOS_CONTRACT,
    "transferencias": TRANSFERENCIAS_CONTRACT,
    "alertas_plaft": ALERTAS_PLAFT_CONTRACT,
    "ros": ROS_CONTRACT,
    "pep": PEP_CONTRACT,
    "casos_investigados": CASOS_INVESTIGADOS_CONTRACT,
    "catalogo_documental": CATALOGO_DOCUMENTAL_CONTRACT,
    "lista_objetivo": LISTA_OBJETIVO_CONTRACT,
    "permisos_analistas": PERMISOS_ANALISTAS_CONTRACT,
}


def get_contract(source_name: str) -> SourceContract:
    """Retorna el contrato de una fuente por su nombre.

    Args:
        source_name: Nombre de la fuente (ej. ``"transferencias"``).

    Returns:
        Contrato de la fuente.

    Raises:
        KeyError: Si la fuente no tiene contrato definido.
    """
    if source_name not in ALL_CONTRACTS:
        available = sorted(ALL_CONTRACTS.keys())
        raise KeyError(
            f"Fuente '{source_name}' no tiene contrato definido. "
            f"Fuentes disponibles: {available}"
        )
    return ALL_CONTRACTS[source_name]
