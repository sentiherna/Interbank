"""Comandos CLI del proyecto graph_plaft.

Punto de entrada principal: ``graph-plaft <comando> [opciones]``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from graph_plaft.config.settings import load_settings
from graph_plaft.observability.logging import configure_logging
from graph_plaft.observability.run_id import generate_run_id


@click.group()
@click.option(
    "--config",
    default="config/local.yaml",
    envvar="GRAPH_PLAFT_CONFIG",
    help="Ruta al archivo de configuración YAML.",
    show_default=True,
)
@click.pass_context
def main(ctx: click.Context, config: str) -> None:
    """Plataforma Analítica PLAFT basada en Grafos — CLI principal."""
    ctx.ensure_object(dict)
    settings = load_settings(config)
    configure_logging(level=settings.log_level, fmt=settings.log_format)
    ctx.obj["settings"] = settings


@main.command()
@click.option("--run-id", default=None, help="ID de ejecución (UUID autogenerado si omitido).")
@click.option("--depth", default=1, show_default=True, help="Profundidad de expansión.")
@click.option("--fecha-corte", default=None, help="Fecha de corte YYYY-MM-DD (hoy si omitida).")
@click.option("--dry-run", is_flag=True, default=False, help="Validar configuración sin ejecutar.")
@click.pass_context
def run_pipeline(
    ctx: click.Context,
    run_id: str | None,
    depth: int,
    fecha_corte: str | None,
    dry_run: bool,
) -> None:
    """Ejecuta el pipeline completo: selección → subgrafo → analytics → variables."""
    settings = ctx.obj["settings"]
    effective_run_id = run_id or generate_run_id()

    click.echo(f"run_id={effective_run_id}")
    click.echo(f"environment={settings.environment}")
    click.echo(f"expansion_depth={depth}")
    if fecha_corte:
        click.echo(f"fecha_corte={fecha_corte}")

    if dry_run:
        click.echo("[dry-run] Configuración válida. Pipeline no ejecutado.")
        return

    # La lógica del pipeline se implementa en fases posteriores.
    click.echo("[info] Pipeline no implementado todavía. Use --dry-run para validar config.")


@main.command()
@click.argument("config_path", default="config/local.yaml")
def validate_config(config_path: str) -> None:
    """Valida un archivo de configuración YAML y muestra su contenido."""
    try:
        settings = load_settings(config_path)
        click.echo(f"✓ Configuración válida: {config_path}")
        click.echo(f"  environment   = {settings.environment}")
        click.echo(f"  data_engine   = {settings.data_engine}")
        click.echo(f"  graph_engine  = {settings.graph_engine}")
        click.echo(f"  storage.path  = {settings.storage.base_path}")
        click.echo(f"  mlflow.uri    = {settings.mlflow.tracking_uri}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"✗ Error en configuración: {exc}", err=True)
        sys.exit(1)


@main.command()
def info() -> None:
    """Muestra información sobre el proyecto."""
    click.echo("graph-plaft — Plataforma Analítica PLAFT basada en Grafos")
    click.echo(f"Python {sys.version}")
    click.echo(f"Configuración activa: {Path('config/local.yaml').resolve()}")
