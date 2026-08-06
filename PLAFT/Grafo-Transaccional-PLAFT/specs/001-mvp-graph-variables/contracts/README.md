# Contratos de Datos: Resumen de Todas las Fuentes

**Feature**: `001-mvp-graph-variables` | **Date**: 2026-08-06

Los contratos detallados individuales se encuentran en archivos separados. Este archivo
resume los esquemas mínimos de todas las fuentes del MVP.

---

## Clientes

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | Identificador único del cliente |
| `tipo_persona` | STRING | No | NATURAL / JURIDICA |
| `estado_cliente` | STRING | No | Estado en el banco |
| `fecha_alta` | DATE | No | Fecha de alta como cliente |
| `segmento` | STRING | No | Segmento de negocio |

**Clave primaria**: `cliente_id`
**Deduplicación**: por `cliente_id`; retener registro más reciente por fecha de procesamiento.
**Particionamiento**: por `tipo_persona` o sin particionamiento adicional.

---

## Cuentas

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `cuenta_id` | STRING | Sí | Identificador único de la cuenta |
| `tipo_cuenta` | STRING | No | Tipo de producto bancario |
| `moneda` | STRING | No | Moneda de la cuenta |
| `estado` | STRING | No | Estado: ACTIVA / CERRADA / BLOQUEADA |
| `fecha_apertura` | DATE | No | Fecha de apertura |

**Clave primaria**: `cuenta_id`
**Regla crítica**: `cuenta_id` no nulo.

---

## Titularidades

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | FK → Clientes |
| `cuenta_id` | STRING | Sí | FK → Cuentas |
| `tipo_titularidad` | STRING | No | Principal / Cotitular / Apoderado |
| `fecha_inicio` | DATE | No | |
| `fecha_fin` | DATE | No | Null si vigente |

**Clave primaria**: (`cliente_id`, `cuenta_id`, `tipo_titularidad`)
**Integridad referencial**: `cliente_id` en Clientes; `cuenta_id` en Cuentas.
**Nota**: una cuenta puede tener múltiples titulares. No deduplicar por par cliente-cuenta.

---

## Productos

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `producto_id` | STRING | Sí | Identificador del producto del cliente |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `tipo_producto` | STRING | Sí | Categoría del producto |
| `estado` | STRING | No | Estado del producto |
| `fecha_contratacion` | DATE | No | |

**Clave primaria**: `producto_id`
**Integridad referencial**: `cliente_id` en Clientes.

---

## Transferencias

Ver contrato detallado: [transferencias.md](transferencias.md)

**Resumen**: `id_transaccion` (PK), `cuenta_origen`, `cuenta_destino`, `fecha_hora`,
`monto`, `moneda`, `estado`, `canal`, `periodo`. No deduplicar por par de cuentas.

---

## Alertas PLAFT

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `alerta_id` | STRING | Sí | Identificador único |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `tipo_alerta` | STRING | Sí | Código o tipo de alerta |
| `fecha_alerta` | TIMESTAMP | Sí | Fecha de generación |
| `estado` | STRING | No | ACTIVA / CERRADA / ESCALADA |
| `periodo` | STRING | No | YYYY-MM de la alerta |

**Clave primaria**: `alerta_id`
**Regla de calidad**: `cliente_id` debe existir en Clientes; `fecha_alerta` no futura.

---

## ROS (Reporte de Operación Sospechosa)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `ros_id` | STRING | Sí | Identificador único del ROS |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `fecha_reporte` | DATE | Sí | Fecha del reporte |
| `estado` | STRING | No | Estado del ROS |

**Clave primaria**: `ros_id`
**Nota**: la existencia de un ROS es una señal de investigación, no de culpabilidad.

---

## Condición PEP

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `pep_id` | STRING | Sí | Identificador del registro PEP |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `categoria_pep` | STRING | No | Tipo de PEP |
| `fecha_inicio` | DATE | No | |
| `fecha_fin` | DATE | No | Null si vigente |
| `vigente` | BOOLEAN | Sí | Vigencia a la fecha de corte |

**Clave primaria**: `pep_id`
**IMPORTANTE**: La Condición PEP es un factor de debida diligencia reforzada. NO
constituye automáticamente evidencia de operación sospechosa.

---

## Casos Investigados

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `caso_id` | STRING | Sí | Identificador único del caso |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `tipo_caso` | STRING | No | Tipología |
| `fecha_apertura` | DATE | Sí | |
| `fecha_cierre` | DATE | No | Null si abierto |
| `estado` | STRING | Sí | ABIERTO / CERRADO / ARCHIVADO |
| `resultado` | STRING | No | Resultado si cerrado |

**Clave primaria**: `caso_id`

---

## Catálogo Documental

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `documento_id` | STRING | Sí | Identificador único del documento |
| `cliente_id` | STRING | Sí | FK → Clientes |
| `tipo_documental` | STRING | Sí | Tipo de documento |
| `nombre` | STRING | No | Nombre descriptivo |
| `fecha_documento` | DATE | No | Fecha del documento |
| `fecha_incorporacion` | TIMESTAMP | No | Fecha de ingreso al sistema |
| `referencia_s3` | STRING | No | Ruta en S3 (puede ser nula si no disponible) |
| `sistema_origen` | STRING | Sí | Sistema fuente |
| `estado` | STRING | No | Estado del documento |
| `version_doc` | STRING | No | Versión |
| `checksum` | STRING | No | Hash de integridad |

**Clave primaria**: `documento_id`
**Nota sobre `referencia_s3`**: puede ser nula. Si nula, el analista verá indicador de
referencia no disponible. El MVP no extrae ni procesa el contenido del documento.

---

## Lista de Clientes Objetivo (provista por PLAFT)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `cliente_id` | STRING | Sí | FK → Clientes |
| `motivo_inclusion` | STRING | No | Justificación de la inclusión en la lista |
| `fecha_inclusion` | DATE | Sí | Fecha de incorporación a la lista |
| `version_lista` | STRING | Sí | Versión de la lista (para versionado del run) |

**Clave primaria**: (`cliente_id`, `version_lista`)
**Nota**: esta lista se considera input válido de selección. El MVP no valida los criterios
internos que la generaron.

---

## Permisos de Acceso de Analistas

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `usuario_id` | STRING | Sí | Identificador del analista |
| `cliente_id` | STRING | Sí | Cliente al que el analista tiene acceso |
| `nivel_acceso` | STRING | Sí | Datos / Documentos / Ambos |
| `fecha_inicio` | DATE | Sí | Inicio de vigencia del permiso |
| `fecha_fin` | DATE | No | Fin de vigencia (null si vigente) |
| `vigente` | BOOLEAN | Sí | Calculado a la fecha de corte |

**Clave primaria**: (`usuario_id`, `cliente_id`, `nivel_acceso`)
**Nota**: los permisos son provistos por el sistema de control de acceso corporativo. El
MVP los consume pero no los gestiona. La herramienta verifica autorización antes de cada
consulta.

---

## Reglas de Calidad Transversales (todas las fuentes)

| Regla | Descripción |
|-------|-------------|
| **TRX-01** | Ningún campo marcado como Obligatorio puede ser nulo. Viola → proceso se detiene. |
| **TRX-02** | Las claves foráneas deben referenciar registros existentes en la tabla destino. Violación → advertencia + registro en informe. |
| **TRX-03** | Los campos de fecha no pueden ser posteriores a la fecha de corte del run. Violación → rechazo del registro + registro. |
| **TRX-04** | Los campos con dominio definido (lista de valores) deben pertenecer a ese dominio. Violación → advertencia + mapeo a valor por defecto documentado. |
| **TRX-05** | Errores críticos (TRX-01) detienen el proceso de forma controlada con log descriptivo. |
| **TRX-06** | Errores no críticos (TRX-02, TRX-03, TRX-04) se registran en el informe de calidad sin detener el proceso. |
