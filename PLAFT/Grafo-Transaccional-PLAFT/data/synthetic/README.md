# Datos Sintéticos — Plataforma PLAFT

Directorio de datos sintéticos reproducibles para pruebas del MVP.  
**No contiene datos reales.** Todos los registros son ficticios.

---

## Generación

```bash
# Generar con semilla por defecto (42)
python scripts/generate_synthetic.py --seed 42

# Directorio de salida personalizado
python scripts/generate_synthetic.py --seed 42 --output-dir /tmp/synthetic_run
```

Dos invocaciones con el mismo `--seed` producen archivos Parquet bit-idénticos  
(checksums SHA-256 iguales). Esto se verifica en `tests/unit/test_synthetic_generators.py`.

**Fecha de corte**: `2026-06-30` — registros con fecha posterior son deliberados  
(patrones P7 y P8) para probar filtrado.

---

## Estructura

```
data/synthetic/
├── generators/              # Código Python de los generadores
│   ├── __init__.py
│   ├── base.py              # Clase base, constantes compartidas, RNG con semilla
│   ├── clientes.py          # ClientesGenerator
│   ├── cuentas.py           # CuentasGenerator
│   ├── transferencias.py    # TransferenciasGenerator
│   ├── senales.py           # SenalesGenerator
│   ├── documentos.py        # DocumentosGenerator
│   └── permisos.py          # PermisosGenerator
├── expected_outputs/        # JSON con valores esperados por análisis
│   ├── patterns.json        # Descripción de los 8 patrones de transferencia
│   ├── degree_variables.json# Grados esperados por cliente
│   └── signals.json         # Señales PLAFT esperadas por cliente
└── README.md                # Este archivo
```

---

## Datasets generados

| Archivo Parquet           | Generador           | Filas | Descripción |
|---------------------------|---------------------|-------|-------------|
| `clientes.parquet`        | ClientesGenerator   | 10    | Maestro de clientes |
| `lista_objetivo.parquet`  | ClientesGenerator   | 6     | Clientes objetivo v1.0 |
| `cuentas.parquet`         | CuentasGenerator    | 11    | Cuentas bancarias |
| `titularidades.parquet`   | CuentasGenerator    | 12    | Titularidades (CTA-009 compartida) |
| `productos.parquet`       | CuentasGenerator    | 8     | Productos financieros |
| `transferencias.parquet`  | TransferenciasGenerator | 17 | 8 patrones de transferencia |
| `alertas_plaft.parquet`   | SenalesGenerator    | 4     | Alertas PLAFT |
| `ros.parquet`             | SenalesGenerator    | 2     | Reportes de Operación Sospechosa |
| `pep.parquet`             | SenalesGenerator    | 2     | Condiciones PEP |
| `casos_investigados.parquet` | SenalesGenerator | 2    | Casos de investigación |
| `catalogo_documental.parquet` | DocumentosGenerator | 5 | Documentos (incluye sin S3 y post-corte) |
| `permisos_analistas.parquet` | PermisosGenerator | 9    | Permisos ANA-001 (excluye CLI-010) |

---

## Clientes

| ID      | Rol        | Señales                              | Patrón transaccional |
|---------|------------|--------------------------------------|----------------------|
| CLI-001 | Objetivo   | 2 alertas (LAVADO + ESTRATIFICACION) | Star hub saliente, intermediario |
| CLI-002 | Objetivo   | 1 alerta (LAVADO)                    | Relay en cadena, ciclo con CLI-003 |
| CLI-003 | Objetivo   | 1 ROS                                | Ciclo con CLI-002 |
| CLI-004 | Objetivo   | PEP (NACIONAL, vigente)              | Receptor aislado |
| CLI-005 | Objetivo   | 1 caso abierto                       | Receptor aislado |
| CLI-006 | Objetivo   | Alerta + ROS + PEP + caso            | Hub receptor de alto grado |
| CLI-007 | Contraparte| Sin señales                          | Intermediario (P5) |
| CLI-008 | Contraparte| Sin señales                          | Cotitular CTA-009, sin transacciones |
| CLI-009 | Contraparte| Sin señales                          | Aislado, sin transacciones |
| CLI-010 | Contraparte| Sin señales                          | Excluido de permisos ANA-001 |

---

## Cuentas

| ID      | Tipo      | Moneda | Titulares                              |
|---------|-----------|--------|----------------------------------------|
| CTA-001 | AHORRO    | PEN    | CLI-001 (Principal)                    |
| CTA-002 | CORRIENTE | USD    | CLI-001 (Principal)                    |
| CTA-003 | AHORRO    | PEN    | CLI-002 (Principal)                    |
| CTA-004 | CORRIENTE | PEN    | CLI-003 (Principal)                    |
| CTA-005 | AHORRO    | PEN    | CLI-004 (Principal)                    |
| CTA-006 | CORRIENTE | PEN    | CLI-005 (Principal)                    |
| CTA-007 | AHORRO    | PEN    | CLI-006 (Principal)                    |
| CTA-008 | AHORRO    | PEN    | CLI-007 (Principal)                    |
| CTA-009 | CORRIENTE | PEN    | CLI-007 (Principal) + CLI-008 (Cotitular) ← cuenta compartida |
| CTA-010 | AHORRO    | USD    | CLI-009 (Principal) — estado: CERRADA  |
| CTA-011 | AHORRO    | PEN    | CLI-010 (Principal)                    |

---

## Patrones de transferencias

| ID  | Patrón          | Transacciones | Descripción |
|-----|-----------------|---------------|-------------|
| P1  | STAR            | TX-001..TX-004| CLI-001 envía a 4 contrapartes distintas |
| P2  | CHAIN           | TX-001, TX-005| CLI-001 → CLI-002 → CLI-003 (relay) |
| P3  | CYCLE           | TX-005, TX-006| CLI-002 ↔ CLI-003 (ciclo bidireccional) |
| P4  | HUB_IN          | TX-007..TX-009| CLI-001, CLI-002, CLI-003 → CLI-006 (hub receptor) |
| P5  | INTERMEDIARY    | TX-010, TX-011| CLI-001 → CLI-007 → CLI-002 (nodo puente) |
| P6  | MULTI_TX        | TX-012..TX-014| 3 TX entre CTA-002 y CTA-003 (sin deduplicar) |
| P7  | CANCELLED       | TX-015, TX-016| ANULADA + REVERTIDA (no generan aristas activas) |
| P8  | POST_CUTOFF     | TX-017        | fecha_hora = 2026-07-15 (rechazada por TRF-Q05) |

---

## Valores esperados de análisis

Los archivos en `expected_outputs/` documentan los valores que deben producir
los algoritmos de Graph Analytics sobre este dataset:

| Archivo                   | Contenido |
|---------------------------|-----------|
| `patterns.json`           | Descripción de cada patrón y su implicación analítica |
| `degree_variables.json`   | Grado in/out, conteos TX y montos por cliente |
| `signals.json`            | Flags de señales y conteos por cliente |

### Resumen de grado (transacciones EJECUTADA dentro del corte)

| Cliente | out_degree | in_degree | tx_env | tx_rec | Nota |
|---------|-----------|-----------|--------|--------|------|
| CLI-001 | 6 | 0 | 9 | 0 | Hub saliente |
| CLI-002 | 2 | 3 | 2 | 6 | Relay y receptor |
| CLI-003 | 2 | 2 | 2 | 2 | Ciclo |
| CLI-004 | 0 | 1 | 0 | 1 | Receptor PEP |
| CLI-005 | 0 | 1 | 0 | 1 | Receptor |
| CLI-006 | 0 | 3 | 0 | 3 | Hub receptor, alto PageRank |
| CLI-007 | 1 | 1 | 1 | 1 | Intermediario |
| CLI-008 | 0 | 0 | 0 | 0 | Aislado (cotitular) |
| CLI-009 | 0 | 0 | 0 | 0 | Aislado |
| CLI-010 | 0 | 0 | 0 | 0 | Aislado (excluido permisos) |

### Componentes conectados esperados

- **Componente 1**: CLI-001, CLI-002, CLI-003, CLI-004, CLI-005, CLI-006, CLI-007 (7 nodos)
- **Singletons**: CLI-008, CLI-009, CLI-010 (sin transacciones activas)

---

## Contrato de compatibilidad con Fase 1

Todos los datasets son compatibles con los contratos definidos en
`src/graph_plaft/validation/schemas.py`:

| Dataset            | Contrato Phase 1               |
|--------------------|-------------------------------|
| clientes           | `CLIENTES_CONTRACT`           |
| lista_objetivo     | `LISTA_OBJETIVO_CONTRACT`     |
| cuentas            | `CUENTAS_CONTRACT`            |
| titularidades      | `TITULARIDADES_CONTRACT`      |
| productos          | `PRODUCTOS_CONTRACT`          |
| transferencias     | `TRANSFERENCIAS_CONTRACT`     |
| alertas_plaft      | `ALERTAS_PLAFT_CONTRACT`      |
| ros                | `ROS_CONTRACT`                |
| pep                | `PEP_CONTRACT`                |
| casos_investigados | `CASOS_INVESTIGADOS_CONTRACT` |
| catalogo_documental| `CATALOGO_DOCUMENTAL_CONTRACT`|
| permisos_analistas | `PERMISOS_ANALISTAS_CONTRACT` |
