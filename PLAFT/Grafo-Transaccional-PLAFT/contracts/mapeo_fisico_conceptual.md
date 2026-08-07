# Mapeo Físico → Conceptual: Fuentes del MVP

**Propósito**: Documentar la traducción entre los nombres de columna reales del banco
(físicos) y los nombres conceptuales del proyecto definidos en `validation/schemas.py`.
Completar en Fase 3 cuando se integren los datasets reales.

**Referencia de contratos**: `specs/001-mvp-graph-variables/contracts/`
**Implementación**: `src/graph_plaft/config/column_mapping.py` — `ColumnMappingRegistry`

---

## Instrucciones

Para cada fuente, completar la columna **Nombre Físico** con el nombre real de la
columna en el dataset del banco. Si el nombre físico coincide con el conceptual, se
puede omitir (el registry asume identidad si no hay mapeo explícito).

Formato de registro en código:
```python
SourceMapping(
    source_name="clientes",
    mappings=[
        ColumnMapping(conceptual="cliente_id", physical="ID_CLIENTE"),
        ColumnMapping(conceptual="tipo_persona", physical="TIPO_PERSONA", required=False),
    ],
)
```

---

## 1. Clientes

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `cliente_id`      | _POR COMPLETAR_ | Sí | Clave primaria del cliente |
| `tipo_persona`    | _POR COMPLETAR_ | No | NATURAL / JURIDICA |

---

## 2. Cuentas

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `cuenta_id`       | _POR COMPLETAR_ | Sí | Clave primaria de la cuenta |
| `tipo_cuenta`     | _POR COMPLETAR_ | No | Tipo de producto bancario |
| `moneda`          | _POR COMPLETAR_ | No | ISO 4217 |
| `estado`          | _POR COMPLETAR_ | No | activa / cerrada / bloqueada |
| `fecha_apertura`  | _POR COMPLETAR_ | No | DATE |

---

## 3. Titularidades

| Nombre Conceptual   | Nombre Físico | Obligatorio | Notas |
|---------------------|---------------|-------------|-------|
| `cliente_id`        | _POR COMPLETAR_ | Sí | FK → Clientes |
| `cuenta_id`         | _POR COMPLETAR_ | Sí | FK → Cuentas |
| `tipo_titularidad`  | _POR COMPLETAR_ | No | principal / cotitular / apoderado |
| `fecha_inicio`      | _POR COMPLETAR_ | No | |
| `fecha_fin`         | _POR COMPLETAR_ | No | null si vigente |

---

## 4. Productos

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `producto_id`     | _POR COMPLETAR_ | Sí | |
| `tipo_producto`   | _POR COMPLETAR_ | Sí | Categoría del producto financiero |
| `estado`          | _POR COMPLETAR_ | No | |

---

## 5. Transferencias

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `id_transaccion`  | _POR COMPLETAR_ | Sí | Clave de identidad (ver ADR-001) |
| `cuenta_origen`   | _POR COMPLETAR_ | Sí | FK → Cuentas |
| `cuenta_destino`  | _POR COMPLETAR_ | Sí | FK → Cuentas |
| `fecha_hora`      | _POR COMPLETAR_ | Sí | TIMESTAMP |
| `monto`           | _POR COMPLETAR_ | Sí | DECIMAL(18,2) |
| `moneda`          | _POR COMPLETAR_ | Sí | ISO 4217 |
| `estado`          | _POR COMPLETAR_ | Sí | EJECUTADA / ANULADA / PENDIENTE / REVERTIDA |
| `canal`           | _POR COMPLETAR_ | No | APP / WEB / AGENCIA / ATM / SWIFT / OTROS |
| `periodo`         | _POR COMPLETAR_ | No | YYYY-MM |
| `cliente_origen`  | _POR COMPLETAR_ | No | Resoluble por join con titularidades |
| `cliente_destino` | _POR COMPLETAR_ | No | Resoluble por join con titularidades |

---

## 6. Alertas PLAFT

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `alerta_id`       | _POR COMPLETAR_ | Sí | |
| `cliente_id`      | _POR COMPLETAR_ | Sí | FK → Clientes |
| `tipo_alerta`     | _POR COMPLETAR_ | Sí | |
| `fecha_alerta`    | _POR COMPLETAR_ | Sí | TIMESTAMP |
| `estado`          | _POR COMPLETAR_ | No | activa / cerrada / escalada |
| `periodo`         | _POR COMPLETAR_ | No | YYYY-MM |

---

## 7. ROS (Reportes de Operación Sospechosa)

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `ros_id`          | _POR COMPLETAR_ | Sí | |
| `cliente_id`      | _POR COMPLETAR_ | Sí | FK → Clientes |
| `fecha_reporte`   | _POR COMPLETAR_ | Sí | DATE |
| `estado`          | _POR COMPLETAR_ | No | |

---

## 8. Condición PEP

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `pep_id`          | _POR COMPLETAR_ | Sí | |
| `cliente_id`      | _POR COMPLETAR_ | Sí | FK → Clientes |
| `categoria_pep`   | _POR COMPLETAR_ | No | nacional / extranjero / familiar / etc. |
| `fecha_inicio`    | _POR COMPLETAR_ | No | DATE |
| `fecha_fin`       | _POR COMPLETAR_ | No | null si vigente |
| `vigente`         | _POR COMPLETAR_ | Sí | BOOLEAN |

---

## 9. Casos Investigados

| Nombre Conceptual | Nombre Físico | Obligatorio | Notas |
|-------------------|---------------|-------------|-------|
| `caso_id`         | _POR COMPLETAR_ | Sí | |
| `cliente_id`      | _POR COMPLETAR_ | Sí | FK → Clientes |
| `tipo_caso`       | _POR COMPLETAR_ | No | Tipología del caso |
| `fecha_apertura`  | _POR COMPLETAR_ | Sí | DATE |
| `fecha_cierre`    | _POR COMPLETAR_ | No | null si abierto |
| `estado`          | _POR COMPLETAR_ | Sí | abierto / cerrado / archivado |
| `resultado`       | _POR COMPLETAR_ | No | Si cerrado |

---

## 10. Catálogo Documental

| Nombre Conceptual      | Nombre Físico | Obligatorio | Notas |
|------------------------|---------------|-------------|-------|
| `documento_id`         | _POR COMPLETAR_ | Sí | |
| `cliente_id`           | _POR COMPLETAR_ | Sí | FK → Clientes |
| `tipo_documental`      | _POR COMPLETAR_ | Sí | DNI / contrato / estado de cuenta / etc. |
| `nombre`               | _POR COMPLETAR_ | No | |
| `fecha_documento`      | _POR COMPLETAR_ | No | DATE |
| `fecha_incorporacion`  | _POR COMPLETAR_ | No | TIMESTAMP |
| `referencia_s3`        | _POR COMPLETAR_ | No | Ruta S3; null si no disponible |
| `sistema_origen`       | _POR COMPLETAR_ | Sí | Sistema generador del documento |
| `estado`               | _POR COMPLETAR_ | No | |
| `version_doc`          | _POR COMPLETAR_ | No | |
| `checksum`             | _POR COMPLETAR_ | No | Hash de integridad |

---

## 11. Lista Objetivo

| Nombre Conceptual     | Nombre Físico | Obligatorio | Notas |
|-----------------------|---------------|-------------|-------|
| `cliente_id`          | _POR COMPLETAR_ | Sí | FK → Clientes |
| `criterio_seleccion`  | _POR COMPLETAR_ | Sí | Criterio que incluye al cliente |
| `fecha_inclusion`     | _POR COMPLETAR_ | Sí | DATE |
| `version_criterios`   | _POR COMPLETAR_ | Sí | Versión de los criterios aplicados |

---

## 12. Permisos de Analistas

| Nombre Conceptual     | Nombre Físico | Obligatorio | Notas |
|-----------------------|---------------|-------------|-------|
| `usuario_id`          | _POR COMPLETAR_ | Sí | Identidad del analista |
| `cliente_id`          | _POR COMPLETAR_ | Sí | Cliente al que tiene acceso |
| `rol`                 | _POR COMPLETAR_ | Sí | Rol del analista (viewer / investigador) |
| `activo`              | _POR COMPLETAR_ | Sí | BOOLEAN |

---

## Estado de Completitud

| Fuente               | Estado |
|----------------------|--------|
| Clientes             | ⬜ Pendiente Fase 3 |
| Cuentas              | ⬜ Pendiente Fase 3 |
| Titularidades        | ⬜ Pendiente Fase 3 |
| Productos            | ⬜ Pendiente Fase 3 |
| Transferencias       | ⬜ Pendiente Fase 3 |
| Alertas PLAFT        | ⬜ Pendiente Fase 3 |
| ROS                  | ⬜ Pendiente Fase 3 |
| Condición PEP        | ⬜ Pendiente Fase 3 |
| Casos Investigados   | ⬜ Pendiente Fase 3 |
| Catálogo Documental  | ⬜ Pendiente Fase 3 |
| Lista Objetivo       | ⬜ Pendiente Fase 3 |
| Permisos Analistas   | ⬜ Pendiente Fase 3 |
