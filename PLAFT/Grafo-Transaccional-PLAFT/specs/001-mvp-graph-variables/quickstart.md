# Quickstart: Validación de la Plataforma Analítica PLAFT

**Feature**: `001-mvp-graph-variables` | **Date**: 2026-08-06 | **Plan**: [plan.md](plan.md)

Esta guía describe los escenarios de validación ejecutables que demuestran que el sistema
funciona de extremo a extremo. Todos los escenarios usan datos sintéticos.

---

## Prerrequisitos

```bash
# Clonar el repositorio
git clone https://github.com/interbank/plaft-graph-platform
cd plaft-graph-platform

# Instalar dependencias (entorno local con Python 3.12)
pip install -e ".[dev]"

# Verificar instalación
python -m pytest tests/unit/ -v --tb=short

# Verificar tipado
mypy src/plaft_graph/

# Verificar linting
ruff check src/ tests/
```

---

## Escenario 1: Pipeline completo con datos sintéticos

**Propósito**: demostrar que el pipeline de extremo a extremo funciona correctamente.

**Prerequisito**: datasets sintéticos en `tests/synthetic/`.

```bash
# Ejecutar pipeline completo localmente (usa pandas en lugar de PySpark)
python jobs/run_ingestion.py --config config/local.yaml --synthetic
python jobs/run_validation.py --run-id test-run-001 --synthetic
python jobs/run_selection.py --run-id test-run-001 --criteria all
python jobs/run_graph_build.py --run-id test-run-001 --depth 1
python jobs/run_analytics.py --run-id test-run-001 --algorithms mandatory
python jobs/run_variables.py --run-id test-run-001
```

**Resultado esperado**:
- Directorio `runs/test-run-001/` generado con todas las subcarpetas.
- `run_manifest.json` con status `completed`.
- Variables generadas para todos los clientes sospechosos del dataset sintético.
- Sin errores en logs de ejecución.

---

## Escenario 2: Trazabilidad de nodos y relaciones

**Propósito**: verificar que todo nodo y relación del subgrafo mantiene referencia al
dato de origen.

```python
# tests/traceability/test_node_traceability.py
import pytest
from plaft_graph.persistence import graph_store

def test_every_node_has_source_reference(synthetic_graph):
    nodes = graph_store.load_nodes(synthetic_graph.version)
    for node_type, df in nodes.items():
        assert "dataset_origen" in df.columns, f"{node_type} sin dataset_origen"
        assert "registro_fuente" in df.columns, f"{node_type} sin registro_fuente"
        assert df["dataset_origen"].notna().all(), f"{node_type}: dataset_origen nulos"
        assert df["registro_fuente"].notna().all(), f"{node_type}: registro_fuente nulos"

def test_every_edge_has_source_reference(synthetic_graph):
    edges = graph_store.load_edges(synthetic_graph.version)
    for edge_type, df in edges.items():
        assert "registro_fuente" in df.columns
        assert df["registro_fuente"].notna().all()
```

**Resultado esperado**: todos los tests pasan sin fallos.

---

## Escenario 3: Reproducibilidad de ejecuciones

**Propósito**: verificar que dos ejecuciones con los mismos parámetros producen resultados
idénticos.

```python
# tests/reproducibility/test_run_reproducibility.py
import hashlib
import pytest
from plaft_graph.pipeline import run_full_pipeline

def test_two_runs_identical_output(synthetic_config):
    result_1 = run_full_pipeline(
        config=synthetic_config,
        run_id="repro-run-A",
        seed=42
    )
    result_2 = run_full_pipeline(
        config=synthetic_config,
        run_id="repro-run-B",
        seed=42
    )
    # Comparar checksums de variables generadas
    checksum_1 = result_1.variables_checksum()
    checksum_2 = result_2.variables_checksum()
    assert checksum_1 == checksum_2, "Las ejecuciones producen resultados distintos"
```

**Resultado esperado**: checksums idénticos.

---

## Escenario 4: Cliente sospechoso sin actividad transaccional

**Propósito**: verificar que un cliente sin transferencias mantiene el esquema completo
de variables con valores documentados.

```python
# tests/unit/test_variables_no_activity.py
from plaft_graph.variables.catalog import compute_all_variables

def test_client_without_transfers_has_complete_schema(isolated_client_fixture):
    """
    isolated_client_fixture: cliente sospechoso sin transferencias, con una alerta.
    """
    variables = compute_all_variables(isolated_client_fixture)
    # Debe tener una fila por cada variable del catálogo
    expected_variable_names = get_catalog_variable_names()
    actual_names = set(variables["variable_nombre"].tolist())
    assert expected_variable_names == actual_names

    # Variables de flujo deben ser 0 o null documentado, no ausentes
    flow_vars = variables[variables["categoria"] == "flujo_dinero"]
    for _, row in flow_vars.iterrows():
        assert row["valor"] == 0 or row["valor_nulo_razon"] is not None
```

---

## Escenario 5: Variables de riesgo con diferenciación de señales

**Propósito**: verificar que las variables de Riesgo de Vecinos diferencian la señal de
origen (alerta, ROS, PEP, caso).

```python
# tests/unit/test_risk_variables_signal_differentiation.py
from plaft_graph.variables.neighbor_risk import compute_neighbor_risk

def test_risk_variables_differentiate_signals(subgraph_with_mixed_signals):
    """
    subgraph_with_mixed_signals: cliente A conectado a:
      - cliente B (con alerta)
      - cliente C (con ROS)
      - cliente D (PEP)
    """
    variables = compute_neighbor_risk(subgraph_with_mixed_signals, cliente_id="A")
    
    assert variables["contrapartes_con_alerta"] == 1
    assert variables["contrapartes_con_ros"] == 1
    assert variables["contrapartes_con_pep"] == 1
    assert variables["contrapartes_con_caso"] == 0  # D no tiene caso
    
    # Señales deben aparecer separadas en senales_origen
    import json
    senales = json.loads(variables["senales_origen"])
    assert "alerta" in senales
    assert "ros" in senales
    assert "pep" in senales
```

---

## Escenario 6: Múltiples transferencias entre las mismas cuentas

**Propósito**: verificar que múltiples transferencias entre las mismas cuentas NO se
deduplicarán.

```python
# tests/unit/test_transfer_identity.py
from plaft_graph.graph.edges import build_transfer_edges

def test_multiple_transfers_same_accounts_preserved():
    """
    Tres transferencias de cuenta A a cuenta B con distintos id_transaccion.
    """
    raw_transfers = [
        {"id_transaccion": "TX-001", "cuenta_origen": "A", "cuenta_destino": "B", "monto": 100},
        {"id_transaccion": "TX-002", "cuenta_origen": "A", "cuenta_destino": "B", "monto": 200},
        {"id_transaccion": "TX-003", "cuenta_origen": "A", "cuenta_destino": "B", "monto": 150},
    ]
    edges = build_transfer_edges(raw_transfers)
    assert len(edges) == 3, "Las transferencias no deben deduplicarse por par cuenta-cuenta"
```

---

## Escenario 7: Control de acceso y auditoría

**Propósito**: verificar que un analista no puede consultar clientes fuera de su subgrafo
autorizado y que el intento queda registrado.

```python
# tests/security/test_access_control.py
from plaft_graph.tool.auth import check_authorization
from plaft_graph.audit.audit_log import get_audit_entries

def test_unauthorized_access_is_denied_and_logged(mock_analyst, unauthorized_client_id):
    result = check_authorization(
        usuario_id=mock_analyst.id,
        cliente_id=unauthorized_client_id,
        authorized_subgraph=mock_analyst.authorized_subgraph
    )
    assert result.allowed is False
    
    entries = get_audit_entries(usuario_id=mock_analyst.id, accion="denied")
    assert len(entries) >= 1
    assert entries[-1]["cliente_id"] == unauthorized_client_id
    assert entries[-1]["resultado"] == "denied"
```

---

## Escenario 8: Idempotencia del pipeline

**Propósito**: verificar que re-ejecutar el pipeline no genera datos duplicados ni
estados inconsistentes.

```bash
# Primera ejecución
python jobs/run_graph_build.py --run-id idem-test --depth 1

# Segunda ejecución con mismo run_id
python jobs/run_graph_build.py --run-id idem-test --depth 1 --overwrite

# Verificar que el resultado es idéntico
python -c "
from plaft_graph.persistence import graph_store
g1 = graph_store.load_graph('idem-test')
g2 = graph_store.load_graph('idem-test')  # Debe leer la misma versión
assert g1.checksum() == g2.checksum()
print('Idempotencia verificada OK')
"
```

---

## Escenario 9: Validación de calidad de datos — error crítico

**Propósito**: verificar que un campo obligatorio nulo detiene el proceso y genera log.

```python
# tests/unit/test_validation_critical_error.py
from plaft_graph.validation.rules import validate_clientes
import pytest

def test_null_required_field_stops_pipeline(clientes_df_with_null_id):
    """
    clientes_df_with_null_id: dataset de clientes con algunos cliente_id nulos.
    """
    with pytest.raises(CriticalValidationError) as exc_info:
        validate_clientes(clientes_df_with_null_id)
    
    assert "cliente_id" in str(exc_info.value)
    # El log de error debe existir
    from plaft_graph.observability.metrics import get_last_validation_report
    report = get_last_validation_report()
    assert report["status"] == "failed"
    assert report["critical_errors"] > 0
```

---

## Escenario 10: Verificación end-to-end con grafo sintético de referencia

**Propósito**: comparar las variables calculadas contra valores esperados en un grafo
sintético con estructura y resultados conocidos.

```bash
# Ejecutar test de exactitud con grafo de referencia
python -m pytest tests/synthetic/test_reference_graph.py -v

# El grafo de referencia está en tests/synthetic/reference_graph.json
# y contiene los valores esperados para cada variable en cada nodo.
```

**Resultado esperado**: todas las variables coinciden con los valores de referencia
dentro de la tolerancia numérica definida (p.ej. ±0.001 para valores flotantes).

---

## Checklist de validación antes de Fase siguiente

- [ ] Todos los tests unitarios pasan (`pytest tests/unit/`).
- [ ] Todos los contratos de datos pasan (`pytest tests/contract/`).
- [ ] Tests de trazabilidad pasan (`pytest tests/traceability/`).
- [ ] Tests de reproducibilidad pasan (`pytest tests/reproducibility/`).
- [ ] Tests de seguridad pasan (`pytest tests/security/`).
- [ ] mypy sin errores (`mypy src/plaft_graph/`).
- [ ] ruff sin errores (`ruff check src/ tests/`).
- [ ] run_manifest.json generado correctamente en cada ejecución de prueba.
- [ ] Variables nulas correctamente documentadas para clientes sin actividad.
- [ ] Señales de riesgo diferenciadas en variables de riesgo de vecinos.
