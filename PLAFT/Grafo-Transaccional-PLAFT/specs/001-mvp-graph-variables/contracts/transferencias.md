# Contrato de Datos: Transferencias

**Fuente**: Sistema transaccional del banco | **Actualización**: Batch diario o por período

---

## Propósito

Dataset central para la construcción del grafo. Cada registro representa una transferencia
de fondos entre cuentas. Es la fuente principal de relaciones `TRANSFIERE_A`.

---

## Esquema

| Campo | Tipo | Obligatorio | Descripción | Dominio / Restricciones |
|-------|------|-------------|-------------|------------------------|
| `id_transaccion` | STRING | **Sí** | Identificador único de la transferencia. Clave de identidad. | No nulo; único en el dataset |
| `cuenta_origen` | STRING | **Sí** | Cuenta que envía los fondos | Debe existir en dataset de Cuentas |
| `cuenta_destino` | STRING | **Sí** | Cuenta que recibe los fondos | Debe existir en dataset de Cuentas |
| `fecha_hora` | TIMESTAMP | **Sí** | Fecha y hora de la transacción | No nula; no futura respecto a fecha de corte |
| `monto` | DECIMAL(18,2) | **Sí** | Monto de la transferencia | > 0 para transacciones ejecutadas |
| `moneda` | STRING | **Sí** | Código ISO 4217 | Longitud = 3; en lista de monedas válidas |
| `estado` | STRING | **Sí** | Estado de la transacción | {EJECUTADA, ANULADA, PENDIENTE, REVERTIDA} |
| `canal` | STRING | No | Canal de origen | {APP, WEB, AGENCIA, ATM, SWIFT, OTROS} |
| `periodo` | STRING | No | Período YYYY-MM | Formato YYYY-MM; coherente con fecha_hora |
| `cliente_origen` | STRING | No | Cliente resolvible como origen | Puede ser nulo si no se puede resolver |
| `cliente_destino` | STRING | No | Cliente resolvible como destino | Puede ser nulo si no se puede resolver |

---

## Claves

- **Clave primaria**: `id_transaccion`
- **Clave de relación origen**: `cuenta_origen` → tabla Cuentas
- **Clave de relación destino**: `cuenta_destino` → tabla Cuentas

---

## Reglas de Calidad

| ID | Regla | Severidad | Acción |
|----|-------|-----------|--------|
| TRF-Q01 | `id_transaccion` no nulo | Crítica | Detener proceso |
| TRF-Q02 | `id_transaccion` único en el batch | Crítica | Detener proceso |
| TRF-Q03 | `cuenta_origen` no nulo | Crítica | Detener proceso |
| TRF-Q04 | `cuenta_destino` no nulo | Crítica | Detener proceso |
| TRF-Q05 | `fecha_hora` no posterior a fecha de corte | Crítica | Rechazar registro y registrar |
| TRF-Q06 | `monto` > 0 para estado EJECUTADA | Advertencia | Registrar; incluir en grafo |
| TRF-Q07 | `moneda` en lista de códigos válidos | Advertencia | Registrar; incluir en grafo |
| TRF-Q08 | `estado` en dominio válido | Advertencia | Asignar OTROS; registrar |

---

## Reglas de Deduplicación

**Las transferencias NO se deduplicarán por par cuenta_origen + cuenta_destino.**
La identidad está dada exclusivamente por `id_transaccion`. Múltiples transferencias entre
las mismas cuentas coexisten como instancias independientes en el grafo.

Si se detectan `id_transaccion` duplicados en el batch, se retiene la primera ocurrencia
y se registra la duplicación como advertencia en el informe de calidad.

---

## Tratamiento de Transacciones Anuladas

Transacciones con `estado IN ('ANULADA', 'REVERTIDA')` **NO se integran** como relaciones
activas en el grafo. Se registran en la tabla de auditoría del proceso pero no generan
aristas `TRANSFIERE_A`.

---

## Particionamiento en S3

```
s3://bucket/raw/transferencias/
  yyyy=2026/mm=07/transferencias_2026_07.parquet
  yyyy=2026/mm=08/transferencias_2026_08.parquet
```

Particionamiento por `periodo` (YYYY-MM) basado en `fecha_hora`.

---

## Metadatos de Trazabilidad

Cada registro ingestado recibe:
- `dataset_origen`: nombre del archivo fuente (`transferencias_YYYY_MM.parquet`)
- `registro_fuente`: `id_transaccion` del registro original

---

## Contratos con Otras Fuentes

- `cuenta_origen` y `cuenta_destino` deben estar presentes en el dataset de **Cuentas**.
  Los registros que referencian cuentas no existentes se registran como advertencia de
  integridad referencial. La clave `cliente_origen` / `cliente_destino` se resuelve
  mediante join con titularidades.
