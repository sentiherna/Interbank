# Contrato - Titularidades

| Campo canonico | Tipo | Obligatorio | Regla |
|----------------|------|-------------|-------|
| `cliente_id` | STRING | Si | FK a Clientes |
| `cuenta_id` | STRING | Si | FK a Cuentas |
| `tipo_titularidad` | STRING | Si | Dominio: TITULAR/COTITULAR/APODERADO |
| `fecha_inicio` | DATE | No | `fecha_inicio <= fecha_corte` |
| `fecha_fin` | DATE | No | Nulo o `fecha_fin >= fecha_inicio` |

**Clave primaria sugerida**: (`cliente_id`, `cuenta_id`, `tipo_titularidad`, `fecha_inicio`)

**Reglas**
- No deduplicar titularidades vigentes de distintos tipos.
- Debe mantenerse consistencia temporal por relacion.
