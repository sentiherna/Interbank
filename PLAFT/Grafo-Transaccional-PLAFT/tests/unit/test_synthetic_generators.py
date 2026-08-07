"""Reproducibility tests for the synthetic data generators (T042).

Two calls to ``scripts/generate_synthetic.py --seed 42`` must produce
bit-identical Parquet files.  The suite also verifies that all 12 expected
datasets are generated.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
GENERATE_SCRIPT = ROOT / "scripts" / "generate_synthetic.py"

EXPECTED_DATASETS = frozenset(
    {
        "clientes",
        "lista_objetivo",
        "cuentas",
        "titularidades",
        "productos",
        "transferencias",
        "alertas_plaft",
        "ros",
        "pep",
        "casos_investigados",
        "catalogo_documental",
        "permisos_analistas",
    }
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_generator(output_dir: Path, seed: int = 42) -> None:
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(GENERATE_SCRIPT),
            "--seed",
            str(seed),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Run the generator twice with seed=42 and return both output directories."""
    base = tmp_path_factory.mktemp("synthetic")
    dir1 = base / "run1"
    dir2 = base / "run2"
    _run_generator(dir1)
    _run_generator(dir2)
    return dir1, dir2


class TestReproducibility:
    """All files from two equal-seed runs must be bit-identical."""

    def test_checksums_are_identical_across_runs(self, two_runs: tuple[Path, Path]) -> None:
        dir1, dir2 = two_runs
        files = sorted(dir1.glob("*.parquet"))
        assert files, "No Parquet files found in first run output"

        mismatches: list[str] = []
        for f1 in files:
            f2 = dir2 / f1.name
            assert f2.exists(), f"{f1.name} is missing from second run"
            if _sha256(f1) != _sha256(f2):
                mismatches.append(f1.name)

        assert not mismatches, f"Checksums differ between runs: {mismatches}"

    def test_same_number_of_files_both_runs(self, two_runs: tuple[Path, Path]) -> None:
        dir1, dir2 = two_runs
        count1 = len(list(dir1.glob("*.parquet")))
        count2 = len(list(dir2.glob("*.parquet")))
        assert count1 == count2, f"File counts differ: {count1} vs {count2}"


class TestDatasetCompleteness:
    """All 12 expected datasets must be present after generation."""

    def test_all_expected_datasets_generated(self, two_runs: tuple[Path, Path]) -> None:
        dir1, _ = two_runs
        generated = frozenset(f.stem for f in dir1.glob("*.parquet"))
        missing = EXPECTED_DATASETS - generated
        assert not missing, f"Missing datasets: {sorted(missing)}"

    def test_no_unexpected_datasets(self, two_runs: tuple[Path, Path]) -> None:
        dir1, _ = two_runs
        generated = frozenset(f.stem for f in dir1.glob("*.parquet"))
        extra = generated - EXPECTED_DATASETS
        assert not extra, f"Unexpected datasets: {sorted(extra)}"


class TestDatasetContent:
    """Smoke checks: verify row counts and required columns are present."""

    @pytest.fixture(scope="class")
    @classmethod
    def parquet_dir(cls, two_runs: tuple[Path, Path]) -> Path:
        return two_runs[0]

    def test_clientes_has_ten_rows(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "clientes.parquet")
        assert len(df) == 10

    def test_titularidades_shared_account_has_two_owners(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "titularidades.parquet")
        shared = df[df["cuenta_id"] == "CTA-009"]
        assert len(shared) == 2, "CTA-009 must have exactly 2 titulares"

    def test_transferencias_has_seventeen_rows(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "transferencias.parquet")
        assert len(df) == 17

    def test_transferencias_cancelled_transactions_present(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "transferencias.parquet")
        inactive = df[df["estado"].isin(["ANULADA", "REVERTIDA"])]
        assert len(inactive) == 2, "Expected 2 cancelled/reverted transactions (P7)"

    def test_transferencias_post_cutoff_present(self, parquet_dir: Path) -> None:
        import pandas as pd

        cutoff = pd.Timestamp("2026-06-30")
        df = pd.read_parquet(parquet_dir / "transferencias.parquet")
        post_cutoff = df[df["fecha_hora"] > cutoff]
        assert len(post_cutoff) == 1, "Expected exactly 1 post-cutoff transaction (P8)"

    def test_permisos_excludes_cli010(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "permisos_analistas.parquet")
        assert "CLI-010" not in df["cliente_id"].values, "CLI-010 must be excluded from ANA-001"

    def test_cli006_has_all_four_signal_types(self, parquet_dir: Path) -> None:
        import pandas as pd

        alertas = pd.read_parquet(parquet_dir / "alertas_plaft.parquet")
        ros = pd.read_parquet(parquet_dir / "ros.parquet")
        pep = pd.read_parquet(parquet_dir / "pep.parquet")
        casos = pd.read_parquet(parquet_dir / "casos_investigados.parquet")

        assert "CLI-006" in alertas["cliente_id"].values
        assert "CLI-006" in ros["cliente_id"].values
        assert "CLI-006" in pep["cliente_id"].values
        assert "CLI-006" in casos["cliente_id"].values

    def test_documentos_has_null_s3_reference(self, parquet_dir: Path) -> None:
        import pandas as pd

        df = pd.read_parquet(parquet_dir / "catalogo_documental.parquet")
        null_s3 = df[df["referencia_s3"].isna()]
        assert len(null_s3) >= 1, "Expected at least 1 document without referencia_s3 (DOC-003)"
