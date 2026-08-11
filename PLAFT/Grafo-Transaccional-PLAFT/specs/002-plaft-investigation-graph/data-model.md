# Data Model: Grafo Transaccional para Investigacion PLAFT

**Feature**: `002-plaft-investigation-graph`  
**Date**: 2026-08-10  
**Plan**: [plan.md](plan.md)

---

## Entidades principales

### CasoInvestigado

Representa el expediente de investigacion generado dentro de la plataforma.

| Campo | Tipo | Obligatorio | Descripcion |
|-------|------|-------------|-------------|
| `caso_id` | STRING | Si | Identificador unico del caso |
| `sujeto_id` | STRING | Si | Cliente o entidad principal investigada |
| `motivo` | STRING | Si | Motivo de apertura del caso |
| `fecha_apertura` | DATE | Si | Fecha de inicio de investigacion |
| `periodo_analisis_inicio` | DATE | Si | Inicio de ventana de analisis |
| `periodo_analisis_fin` | DATE | Si | Fin de ventana de analisis |
| `fecha_corte` | DATE | Si | Fecha de corte para no fuga temporal |
| `hipotesis` | ARRAY<STRING> | No | Hipotesis o lineas de investigacion |
| `observaciones_analista` | STRING | No | Notas de analista |
| `interpretacion` | STRING | No | Interpretacion analitica del caso |
| `conclusion` | STRING | No | Conclusiones registradas por analista |
| `resultado` | STRING | No | Resultado formal del caso |
| `estado` | STRING | Si | `abierto`, `en_revision`, `cerrado`, `reabierto`, `archivado` |
| `usuario_responsable` | STRING | Si | Usuario analista responsable |
| `graph_version` | STRING | Si | Version del grafo usada |
| `data_version` | STRING | Si | Version de datos fuente |
| `run_id` | STRING | Si | Corrida que sustenta analisis |
| `created_at` | TIMESTAMP | Si | Timestamp de creacion |
| `updated_at` | TIMESTAMP | Si | Timestamp de ultima actualizacion |
| `closed_at` | TIMESTAMP | No | Timestamp de cierre |

**Reglas**
- `periodo_analisis_inicio <= periodo_analisis_fin <= fecha_corte`.
- `closed_at` es obligatorio cuando `estado = cerrado`.
- Un caso cerrado puede reabrirse solo con registro de usuario y motivo.

---

### CasoHistoricoFuente

Fuente contextual externa de investigaciones historicas; no equivale a caso nuevo de la
plataforma.

| Campo | Tipo | Obligatorio | Descripcion |
|-------|------|-------------|-------------|
| `caso_historico_id` | STRING | Si | ID de caso en sistema fuente |
| `sujeto_id` | STRING | Si | Entidad asociada en historial |
| `fecha_apertura` | DATE | Si | Fecha de apertura historica |
| `fecha_cierre` | DATE | No | Fecha de cierre historica |
| `estado` | STRING | Si | Estado historico |
| `resultado` | STRING | No | Resultado historico |
| `dataset_origen` | STRING | Si | Fuente fisica |
| `registro_fuente` | STRING | Si | Clave en sistema origen |

---

### HallazgoAnalitico

Resultado analitico revisable que surge de grafo/algoritmos/reglas.

| Campo | Tipo | Obligatorio | Descripcion |
|-------|------|-------------|-------------|
| `hallazgo_id` | STRING | Si | Identificador unico del hallazgo |
| `caso_id` | STRING | Si | Caso al que pertenece |
| `tipo_hallazgo` | STRING | Si | Catalogo de tipo de hallazgo |
| `descripcion` | STRING | Si | Explicacion corta del hallazgo |
| `severidad` | STRING | Si | `baja`, `media`, `alta`, `critica` |
| `origen_algoritmo_o_regla` | STRING | Si | Metodo que detecto el hallazgo |
| `parametros` | JSON | No | Parametros del detector |
| `entidades_relacionadas` | ARRAY<STRING> | No | IDs involucrados |
| `relaciones_relacionadas` | ARRAY<STRING> | No | IDs de relaciones relevantes |
| `transacciones_relacionadas` | ARRAY<STRING> | No | IDs de transferencias asociadas |
| `estado_revision` | STRING | Si | `pendiente`, `aceptado`, `descartado` |
| `comentarios_analista` | STRING | No | Comentarios de revision |
| `usuario_revision` | STRING | No | Usuario que reviso |
| `timestamp_revision` | TIMESTAMP | No | Fecha/hora de revision |
| `graph_version` | STRING | Si | Version de grafo |
| `run_id` | STRING | Si | Corrida asociada |

**Reglas**
- Todo hallazgo inicia en `pendiente`.
- Solo hallazgos `aceptado` o `descartado` pueden cerrar revision.
- Un hallazgo `aceptado` debe poder asociarse al menos a una evidencia.

---

### Evidencia

Soporte verificable y reproducible de uno o mas hallazgos.

| Campo | Tipo | Obligatorio | Descripcion |
|-------|------|-------------|-------------|
| `evidencia_id` | STRING | Si | Identificador de evidencia |
| `caso_id` | STRING | Si | Caso al que pertenece |
| `hallazgo_id` | STRING | Si | Hallazgo respaldado |
| `entidades_involucradas` | ARRAY<STRING> | Si | Entidades implicadas |
| `relaciones_involucradas` | ARRAY<STRING> | Si | Relaciones implicadas |
| `transacciones_involucradas` | ARRAY<STRING> | No | Transacciones asociadas |
| `periodo_inicio` | DATE | Si | Inicio del periodo sustentado |
| `periodo_fin` | DATE | Si | Fin del periodo sustentado |
| `fecha_corte` | DATE | Si | Fecha de corte de corrida |
| `dataset_fuente` | STRING | Si | Dataset del dato fuente |
| `clave_registro_fuente` | STRING | Si | PK del registro fuente |
| `algoritmo_o_regla` | STRING | Si | Metodo aplicado |
| `parametros` | JSON | No | Parametros usados |
| `graph_version` | STRING | Si | Version de grafo |
| `run_id` | STRING | Si | Corrida de origen |
| `timestamp` | TIMESTAMP | Si | Fecha/hora de creacion |
| `usuario_validador` | STRING | Si | Usuario que incorpora/valida |

**Reglas**
- Debe conservar referencia verificable al dato origen.
- Debe ser reproducible con mismas versiones y parametros.

---

## Entidades de grafo base (fuentes prioritarias)

### Cliente

- ID canonico: `cliente_id`.
- Mapeo inicial real reconocido: `cod_cli -> cliente_id`.

### Cuenta

- Clave: `cuenta_id`.
- Relacion principal con Cliente via Titularidad.

### Titularidad

- Clave compuesta: (`cliente_id`, `cuenta_id`, `tipo_titularidad`, `fecha_inicio`).

### Transferencia

- Clave de identidad: `id_transaccion`.
- No deduplicar por par cuenta origen/destino.

### AlertaPLAFT

- Clave: `alerta_id`.
- Fuente de senal analitica, no conclusion.

---

## Relaciones clave

- `CasoInvestigado` 1..N `HallazgoAnalitico`
- `HallazgoAnalitico` 1..N `Evidencia`
- `CasoInvestigado` N..N `Cliente` (sujeto principal + entidades relacionadas)
- `HallazgoAnalitico` N..N `RelacionTransaccional`
- `Evidencia` N..N `Transferencia`

---

## Transiciones de estado

### CasoInvestigado

`abierto -> en_revision -> cerrado`

Transiciones adicionales:
- `cerrado -> reabierto`
- `reabierto -> en_revision`
- `cerrado -> archivado`

### HallazgoAnalitico

`pendiente -> aceptado`
`pendiente -> descartado`

No se permite `descartado -> aceptado` sin nueva revision formal registrada.

---

## Reglas de validacion de negocio

- Ningun caso puede cerrarse sin interpretacion, conclusion y resultado.
- Ningun hallazgo aceptado puede quedar sin evidencia asociada.
- Ninguna evidencia puede referenciar `run_id` o `graph_version` inexistente.
- Toda consulta investigativa debe respetar `fecha_corte` de la corrida.
- Senal automatica siempre requiere revision humana antes de impactar expediente.
