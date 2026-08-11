# Contrato - Clientes

| Campo fisico | Campo canonico | Tipo | Obligatorio | Regla |
|--------------|----------------|------|-------------|-------|
| `cod_cli` | `cliente_id` | STRING | Si | No nulo, unico |
| `tip_pers` | `tipo_persona` | STRING | No | Dominio: NATURAL/JURIDICA |
| `fec_alta` | `fecha_alta` | DATE | No | `fecha_alta <= fecha_corte` |
| `est_cli` | `estado_cliente` | STRING | No | Dominio controlado |
| `desc_subsegmento` | `subsegmento` | STRING | No | Texto normalizado |

**Clave primaria**: `cliente_id`

**Notas**
- Mapeo inicial real confirmado: `cod_cli -> cliente_id`.
- Si `cliente_id` es nulo o duplicado, la validacion es critica y detiene proceso.
