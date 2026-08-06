.DEFAULT_GOAL := help
PYTHON := python
PIP    := pip

.PHONY: help install install-dev check lint typecheck test test-unit test-integration test-contract clean

help:  ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install:  ## Instalar dependencias de producción
	$(PIP) install -e .

install-dev:  ## Instalar dependencias de desarrollo
	$(PIP) install -e ".[dev]"

lint:  ## Ejecutar ruff (linter)
	ruff check src tests jobs

format:  ## Formatear código con ruff
	ruff format src tests jobs

typecheck:  ## Ejecutar mypy
	mypy src

check: lint typecheck  ## Ejecutar lint + typecheck

test:  ## Ejecutar todas las pruebas (excluye performance y aws)
	pytest -m "not performance and not aws" --cov=src --cov-report=term-missing

test-unit:  ## Solo pruebas unitarias
	pytest tests/unit -m "not performance and not aws"

test-integration:  ## Solo pruebas de integración
	pytest tests/integration -m "not performance and not aws"

test-contract:  ## Solo pruebas de contrato de datos
	pytest tests/contract -m "not performance and not aws"

test-all:  ## Todas las pruebas incluyendo performance
	pytest --cov=src --cov-report=term-missing

clean:  ## Limpiar archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage
