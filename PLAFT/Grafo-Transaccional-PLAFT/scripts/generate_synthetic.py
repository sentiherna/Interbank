"""Generate all synthetic PLAFT datasets with a fixed seed (T033).

Usage
-----
    python scripts/generate_synthetic.py --seed 42
    python scripts/generate_synthetic.py --seed 42 --output-dir /tmp/run1

The script produces one Parquet file per logical dataset under ``output-dir``
(default: ``data/synthetic/``).  Two runs with the same ``--seed`` are
guaranteed to produce bit-identical Parquet files.

Datasets generated
------------------
From ClientesGenerator   : clientes, lista_objetivo
From CuentasGenerator    : cuentas, titularidades, productos
From TransferenciasGenerator : transferencias
From SenalesGenerator    : alertas_plaft, ros, pep, casos_investigados
From DocumentosGenerator : catalogo_documental
From PermisosGenerator   : permisos_analistas
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add data/synthetic/ to sys.path so the generators package is importable.
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "data" / "synthetic"))

from generators import (  # noqa: E402
    ClientesGenerator,
    CuentasGenerator,
    DocumentosGenerator,
    PermisosGenerator,
    SenalesGenerator,
    TransferenciasGenerator,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_LOG = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic PLAFT datasets."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Integer random seed (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_REPO_ROOT / "data" / "synthetic",
        metavar="DIR",
        help="Directory where Parquet files are written (default: data/synthetic/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    seed: int = args.seed
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    generator_classes = [
        ClientesGenerator,
        CuentasGenerator,
        TransferenciasGenerator,
        SenalesGenerator,
        DocumentosGenerator,
        PermisosGenerator,
    ]

    total_rows = 0
    for cls in generator_classes:
        gen = cls(seed=seed)
        datasets = gen.generate_all()
        for name, df in datasets.items():
            out_path = output_dir / f"{name}.parquet"
            df.to_parquet(out_path, index=False, engine="pyarrow")
            _LOG.info("  %-30s %3d rows → %s", name, len(df), out_path.name)
            total_rows += len(df)

    _LOG.info("Done. %d total rows written to %s", total_rows, output_dir)


if __name__ == "__main__":
    main()
