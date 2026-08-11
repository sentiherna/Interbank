# Contrato - CasoInvestigado (salida principal)

| Campo | Tipo | Obligatorio | Regla |
|------|------|-------------|-------|
| `caso_id` | STRING | Si | Unico |
| `sujeto_id` | STRING | Si | Entidad principal investigada |
| `motivo` | STRING | Si | No vacio |
| `fecha_apertura` | DATE | Si | <= `fecha_corte` |
| `periodo_analisis_inicio` | DATE | Si | <= `periodo_analisis_fin` |
| `periodo_analisis_fin` | DATE | Si | <= `fecha_corte` |
| `fecha_corte` | DATE | Si | Fecha limite oficial |
| `hipotesis` | ARRAY<STRING> | No | Lista de lineas de investigacion |
| `hallazgos_ids` | ARRAY<STRING> | No | Referencias a hallazgos |
| `evidencias_ids` | ARRAY<STRING> | No | Referencias a evidencia |
| `observaciones_analista` | STRING | No | Registro libre |
| `interpretacion` | STRING | No | Requerido para cierre |
| `conclusion` | STRING | No | Requerido para cierre |
| `resultado` | STRING | No | Requerido para cierre |
| `estado` | STRING | Si | abierto/en_revision/cerrado/reabierto/archivado |
| `usuario_responsable` | STRING | Si | Usuario analista |
| `graph_version` | STRING | Si | Version de grafo |
| `data_version` | STRING | Si | Version de datos |
| `run_id` | STRING | Si | Corrida base |
| `created_at` | TIMESTAMP | Si | Auditoria |
| `updated_at` | TIMESTAMP | Si | Auditoria |
| `closed_at` | TIMESTAMP | No | Obligatorio si estado=cerrado |

**Reglas de cierre**
- No cerrar caso sin interpretacion, conclusion y resultado.
- Caso cerrado conserva trazabilidad completa y estado inmutable salvo reapertura formal.
