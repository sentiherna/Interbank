# Contrato - Evidencia

| Campo | Tipo | Obligatorio | Regla |
|------|------|-------------|-------|
| `evidencia_id` | STRING | Si | Unico |
| `caso_id` | STRING | Si | FK a CasoInvestigado |
| `hallazgo_id` | STRING | Si | FK a HallazgoAnalitico |
| `entidades_involucradas` | ARRAY<STRING> | Si | No vacio |
| `relaciones_involucradas` | ARRAY<STRING> | Si | No vacio |
| `transacciones_involucradas` | ARRAY<STRING> | No | IDs de transferencias |
| `periodo_inicio` | DATE | Si | <= `periodo_fin` |
| `periodo_fin` | DATE | Si | <= `fecha_corte` |
| `fecha_corte` | DATE | Si | Fecha de referencia |
| `dataset_fuente` | STRING | Si | Dataset de origen |
| `clave_registro_fuente` | STRING | Si | PK del registro origen |
| `algoritmo_o_regla` | STRING | Si | Metodo aplicado |
| `parametros` | JSON | No | Parametros de ejecucion |
| `graph_version` | STRING | Si | Version del grafo |
| `run_id` | STRING | Si | Corrida de origen |
| `timestamp` | TIMESTAMP | Si | Momento de registro |
| `usuario_validador` | STRING | Si | Usuario que incorpora/valida |

**Cadena de trazabilidad obligatoria**

`dato_fuente -> hecho_grafo -> hallazgo -> evidencia -> interpretacion -> resultado_caso`

**Reglas**
- Evidencia sin dataset y clave de origen es invalida.
- Evidencia debe ser reproducible con mismas versiones y parametros.
- Evidencia puede reutilizarse entre hallazgos solo con referencia explicita.
