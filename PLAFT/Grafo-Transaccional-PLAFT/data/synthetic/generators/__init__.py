"""Synthetic dataset generators for PLAFT MVP testing."""

from .clientes import ClientesGenerator
from .cuentas import CuentasGenerator
from .documentos import DocumentosGenerator
from .permisos import PermisosGenerator
from .senales import SenalesGenerator
from .transferencias import TransferenciasGenerator

__all__ = [
    "ClientesGenerator",
    "CuentasGenerator",
    "DocumentosGenerator",
    "PermisosGenerator",
    "SenalesGenerator",
    "TransferenciasGenerator",
]
