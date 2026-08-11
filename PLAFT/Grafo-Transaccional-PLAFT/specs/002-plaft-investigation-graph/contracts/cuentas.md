# Contrato - Cuentas

| Campo canonico | Tipo | Obligatorio | Regla |
|----------------|------|-------------|-------|
| `cuenta_id` | STRING | Si | Unico, no nulo |
| `cliente_id` | STRING | Si | Debe existir en Clientes |
| `tipo_cuenta` | STRING | No | Dominio controlado |
| `moneda` | STRING | No | ISO 4217 |
| `estado` | STRING | No | Dominio controlado |
| `fecha_apertura` | DATE | No | `fecha_apertura <= fecha_corte` |

**Clave primaria**: `cuenta_id`

**Integridad referencial**
- `cliente_id` debe existir en fuente de clientes normalizada.
