# Contrato - Casos historicos (fuente contextual)

| Campo canonico | Tipo | Obligatorio | Regla |
|----------------|------|-------------|-------|
| `caso_historico_id` | STRING | Si | Unico en fuente |
| `sujeto_id` | STRING | Si | FK a Clientes (si aplica) |
| `motivo` | STRING | No | Texto de contexto |
| `fecha_apertura` | DATE | Si | `fecha_apertura <= fecha_corte` |
| `fecha_cierre` | DATE | No | Nulo o `fecha_cierre >= fecha_apertura` |
| `estado` | STRING | Si | Dominio controlado |
| `resultado` | STRING | No | Resultado historico |

**Clave primaria**: `caso_historico_id`

**Regla de separacion**
- Este contrato es solo fuente de contexto. No reemplaza `CasoInvestigado` creado en
  la plataforma.
