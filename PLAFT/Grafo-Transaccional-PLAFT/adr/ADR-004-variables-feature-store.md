# ADR-004: Estrategia de Variables y SageMaker Feature Store

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

Las variables estructurales generadas por el MVP deben estar disponibles para:
1. Modelos PLAFT y otros modelos analíticos del banco (scoring batch).
2. La herramienta de investigación del analista.
3. Consultas ad hoc mediante Athena.

Se debe decidir cómo y dónde persistir estas variables, y en particular qué rol juega
SageMaker Feature Store.

---

## Alcance de SageMaker Feature Store en el MVP

**El grafo completo NO se almacena en Feature Store.** El Feature Store es para
variables estructurales por entidad (cliente), no para tablas de nodos y aristas.

| Qué | Dónde |
|-----|-------|
| Tablas de nodos y aristas | S3 (Parquet) + Glue Catalog |
| Resultados de Graph Analytics | S3 (Parquet) |
| Variables por cliente | S3 (Parquet) + **SageMaker Feature Store** |
| Catálogo documental | S3 (Parquet) |
| Metadatos de ejecución | S3 (JSON) + MLflow |

---

## Opciones para publicación de variables

### Opción A: Solo S3 + Athena

Variables en Parquet en S3, consultadas via Athena.

| Pro | Contra |
|-----|--------|
| Sin dependencia adicional | Modelos deben conocer la ruta S3 |
| Athena-compatible | Sin versionado semántico de features |
| Bajo costo | Sin API de feature lookup |

### Opción B: SageMaker Feature Store (Offline Store)

Variables registradas en Feature Store con entidad = `cliente_id`, event_time = fecha de corte.

| Pro | Contra |
|-----|--------|
| API estándar para consumo por modelos | Requiere setup inicial del Feature Group |
| Versionado temporal nativo (point-in-time) | Costo adicional de almacenamiento |
| Integración con SageMaker Training/Inference | Requiere validación de acceso en el banco |
| Previene fuga temporal en entrenamiento | Solo Offline Store necesario en MVP batch |

---

## Decisión

**Opción B: SageMaker Feature Store (Offline Store únicamente)** para variables
estructurales por cliente. Las tablas de nodos/aristas y los resultados de Graph Analytics
permanecen en S3/Athena.

**Online Store**: NO implementar en el MVP. El caso de uso actual es scoring batch, que
no requiere baja latencia. El diseño debe permitir habilitar Online Store en el futuro
sin reescribir la lógica de escritura.

---

## Diseño del Feature Group

```python
feature_group_name = "plaft-graph-variables-v1"
entity_identifier = "cliente_id"        # Record identifier
event_time_feature = "fecha_corte"      # Event time (fecha de corte del run)
```

**Features mínimas por record** (adicionalmente a las 40+ variables calculadas):

| Feature | Tipo | Descripción |
|---------|------|-------------|
| `cliente_id` | STRING | Identificador del cliente |
| `fecha_corte` | STRING | Fecha de corte del período analizado |
| `graph_version` | STRING | Versión del grafo del que se derivaron |
| `variables_version` | STRING | Versión del conjunto de variables |
| `run_id` | STRING | Identificador de la ejecución |
| `es_cliente_objetivo` | INT | 1 si fue seleccionado como sospechoso |

---

## Tratamiento de reprocesos

Al reprocesar un período, el Feature Store recibe nuevos records con el mismo
`cliente_id` y `fecha_corte` actualizados. El Feature Store resuelve duplicados por
`(entity_id, event_time)` conservando el record más reciente.

---

## Integridad temporal

Las variables se calculan exclusivamente con datos hasta la `fecha_corte`. El campo
`event_time` en Feature Store equals `fecha_corte`. Esto permite point-in-time lookups
correctos al entrenar modelos (sin data leakage).

---

## Consecuencias

- Los modelos consumen variables usando la API de Feature Store con `get_record` o
  `batch_get_record`.
- La herramienta del analista lee directamente desde S3/Athena (tablas Parquet), no
  necesariamente desde Feature Store.
- Feature Store actúa como interfaz pública de variables para consumo por modelos.

---

## Pendiente de validación

- Confirmar que el banco tiene SageMaker Feature Store habilitado en su cuenta.
- Validar permisos IAM para escritura y lectura del Feature Group.
- Si Feature Store no está disponible, usar S3 + Athena con partición por `fecha_corte`.

---

## Referencias

- plan.md Capa 10 (Feature Store)
- spec.md FR-025/026
- Constitución v3.0.0 Principio II (plataforma tecnológica)
