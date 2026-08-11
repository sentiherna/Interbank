# Contrato - Alertas PLAFT

| Campo canonico | Tipo | Obligatorio | Regla |
|----------------|------|-------------|-------|
| `alerta_id` | STRING | Si | Unico, no nulo |
| `cliente_id` | STRING | Si | FK a Clientes |
| `tipo_alerta` | STRING | Si | Dominio de tipologias |
| `fecha_alerta` | TIMESTAMP | Si | `fecha_alerta <= fecha_corte` |
| `estado` | STRING | No | Dominio controlado |

**Clave primaria**: `alerta_id`

**Nota de negocio**
- Es una senal analitica de riesgo, no conclusion final del caso.
