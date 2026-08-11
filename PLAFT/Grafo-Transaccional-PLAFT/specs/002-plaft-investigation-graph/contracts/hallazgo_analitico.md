# Contrato - HallazgoAnalitico

| Campo | Tipo | Obligatorio | Regla |
|------|------|-------------|-------|
| `hallazgo_id` | STRING | Si | Unico |
| `caso_id` | STRING | Si | FK a CasoInvestigado |
| `tipo_hallazgo` | STRING | Si | Catalogo de tipos validos |
| `descripcion` | STRING | Si | No vacio |
| `severidad` | STRING | Si | baja/media/alta/critica |
| `origen_algoritmo_o_regla` | STRING | Si | Metodo de deteccion |
| `parametros` | JSON | No | Parametros del metodo |
| `estado_revision` | STRING | Si | pendiente/aceptado/descartado |
| `comentarios_analista` | STRING | No | Comentarios de revision |
| `usuario_revision` | STRING | No | Usuario de revision |
| `timestamp_revision` | TIMESTAMP | No | Fecha/hora de revision |
| `graph_version` | STRING | Si | Version de grafo |
| `run_id` | STRING | Si | Corrida asociada |

**Tipos minimos permitidos**
- relacion_relevante
- cadena
- ciclo
- hub
- intermediario
- concentracion
- comunidad
- anomalia
- exposicion_alerta
- exposicion_ros
- relacion_pep
- relacion_caso_historico
- otro

**Reglas**
- Todo hallazgo inicia en `pendiente`.
- Senal automatica no equivale a conclusion del caso.
- Hallazgo aceptado debe tener al menos una evidencia asociada.
