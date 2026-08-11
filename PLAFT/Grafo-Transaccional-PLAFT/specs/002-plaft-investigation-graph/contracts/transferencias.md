# Contrato - Transferencias

| Campo canonico | Tipo | Obligatorio | Regla |
|----------------|------|-------------|-------|
| `id_transaccion` | STRING | Si | Identificador unico de transferencia |
| `cuenta_origen` | STRING | Si | FK a Cuentas |
| `cuenta_destino` | STRING | Si | FK a Cuentas |
| `fecha_hora` | TIMESTAMP | Si | `fecha_hora <= fecha_corte` |
| `monto` | DECIMAL(18,2) | Si | `monto > 0` |
| `moneda` | STRING | Si | ISO 4217 |
| `estado` | STRING | Si | Excluir `ANULADA` para grafo activo |
| `canal` | STRING | No | Dominio controlado |

**Clave primaria**: `id_transaccion`

**Reglas**
- No deduplicar por par origen/destino.
- Multiples transacciones entre mismas cuentas son validas.
