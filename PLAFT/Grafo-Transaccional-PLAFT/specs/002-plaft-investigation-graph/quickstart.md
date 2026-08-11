# Quickstart: Validacion MVP Investigacion + Evidencia

**Feature**: `002-plaft-investigation-graph`  
**Date**: 2026-08-10  
**Plan**: [plan.md](plan.md)

Esta guia valida el flujo principal investigativo sin implementar aun tareas de
construccion detallada.

---

## Prerrequisitos

1. Python 3.12 instalado.
2. Entorno virtual activo.
3. Dependencias de desarrollo instaladas.

```bash
pip install -e ".[dev]"
```

4. Configuracion local disponible en `config/local.yaml`.
5. Datos reales fuera de Git; usar solo rutas locales controladas o sinteticos.

---

## Validacion 1: Calidad base del repositorio

```bash
make lint
make typecheck
make test
```

**Resultado esperado**
- `ruff` sin errores.
- `mypy` sin errores en `src`.
- `pytest` verde en suites unitarias, contract e integracion vigentes.

---

## Validacion 2: Carga de fuentes prioritarias con mapeo fisico-conceptual

Objetivo: verificar que la capa de ingesta reutilizable acepta fuentes prioritarias y
normaliza identificadores base.

Ejemplo de control minimo para clientes reales:

```bash
python -c "import pandas as pd; df=pd.read_csv(r'data/real/clientes.csv'); print('rows:', len(df)); print('cod_cli nulls:', df['cod_cli'].isna().sum())"
```

**Resultado esperado**
- El archivo carga correctamente en entorno local.
- Se confirma disponibilidad de columna fisica `cod_cli`.
- El mapeo `cod_cli -> cliente_id` queda habilitado en configuracion.

---

## Validacion 3: Pipeline de validacion de calidad reutilizado

Objetivo: probar reglas de calidad, temporalidad y deduplicacion sin crear segunda
implementacion.

```bash
pytest tests/unit/test_validation_rules.py
pytest tests/unit/test_temporal_cutoff.py
pytest tests/integration/test_validation_pipeline.py
```

**Resultado esperado**
- Reglas criticas detienen la ejecucion cuando corresponde.
- Filtro temporal aplica `fecha_corte` correctamente.
- Duplicados se resuelven segun contrato por fuente.

---

## Validacion 4: Base para flujo de investigacion de casos

Objetivo: validar que los artefactos de diseno de la feature 002 estan consistentes para
pasar a `/speckit-tasks`.

1. Revisar [data-model.md](data-model.md) para entidades `CasoInvestigado`,
   `HallazgoAnalitico` y `Evidencia`.
2. Revisar contratos en [contracts/README.md](contracts/README.md).
3. Confirmar que `plan.md` incluye la seccion de reutilizacion obligatoria del proyecto
   001 y arquitectura de 16 capas.

**Resultado esperado**
- Modelo de datos completo para caso/hallazgo/evidencia.
- Contratos de fuentes prioritarias y contratos investigativos definidos.
- Sin contradicciones con constitucion v4.0.0 ni con `spec.md`.

---

## Validacion 5: Criterios de salida MVP

Se considera listo para planificacion de tareas cuando:

1. El flujo investigativo completo esta especificado en plan y modelo de datos.
2. La reutilizacion de infraestructura existente esta explicitamente clasificada.
3. El expediente de caso investigado incluye interpretacion humana y evidencia
   reproducible.
4. Feature Store queda definido como opcional y no bloqueante.

---

## Siguientes pasos

- Ejecutar `/speckit-tasks` para descomponer implementacion por fases.
- Priorizar tareas de Fases 1 a 5 del plan para demostrar investigacion + evidencia.
- Mantener fuera de alcance MVP las fases 7 y 8 (GraphRAG y asistente).
