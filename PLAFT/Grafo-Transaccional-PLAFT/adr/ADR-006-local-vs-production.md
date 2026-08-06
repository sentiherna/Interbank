# ADR-006: Estrategia Local vs Producción

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

El sistema debe ejecutarse tanto en entorno local (desarrollo, pruebas) como en
producción (SageMaker Processing + AWS). Se debe decidir cómo compartir la lógica
de negocio sin duplicar implementaciones.

---

## Principio

**Una sola implementación de lógica de negocio**; dos configuraciones de ejecución.

La lógica de negocio (validación, selección, construcción del subgrafo, variables) vive
en módulos Python que son agnósticos al entorno de ejecución. La diferencia entre local
y AWS está en la configuración y en el motor de datos (pandas vs PySpark).

---

## Estrategia

### Capa de abstracción de datos

Se implementa una interfaz `DataEngine` con dos implementaciones:

```
DataEngine (abstract)
├── PandasEngine     → usa pandas, lee/escribe localmente o en S3 con credenciales
└── SparkEngine      → usa PySpark, opera sobre S3 en AWS
```

La lógica de negocio recibe un `DataEngine` por inyección de dependencia. En local
recibe `PandasEngine`; en producción recibe `SparkEngine`.

**Limitación**: los algoritmos de Graph Analytics (GraphFrames) no tienen equivalente
pandas. En local, se usa NetworkX para las mismas operaciones sobre subgrafos pequeños.
La capa de analytics también se abstrae:

```
GraphAnalyticsEngine (abstract)
├── NetworkXEngine   → para desarrollo local y subgrafos < 10k nodos
└── GraphFramesEngine → para producción PySpark
```

---

## Configuración por entorno

```yaml
# config/local.yaml
environment: local
data_engine: pandas
graph_engine: networkx
storage:
  base_path: ./data/local
  format: parquet
logging:
  level: DEBUG

# config/aws.yaml
environment: aws
data_engine: spark
graph_engine: graphframes
storage:
  base_path: s3://bucket/
  format: parquet
logging:
  level: INFO
```

---

## Datos sintéticos para desarrollo local

- Ubicación: `tests/synthetic/`
- Estructura: mismos esquemas que los datos reales (Parquet).
- Generados con scripts en `tests/synthetic/generators/`.
- Patrones incluidos: cliente aislado, estrella, cadena, ciclo, comunidad, hub,
  intermediario, contraparte riesgosa, cuenta compartida, múltiples señales simultáneas.

---

## Verificación de consistencia pandas vs PySpark

Se implementan pruebas de consistencia que verifican que el resultado de `PandasEngine`
y `SparkEngine` sobre el mismo dataset sintético producen resultados idénticos para las
operaciones de validación y construcción del subgrafo. Los algoritmos de grafos (Analytics)
se verifican por separado contra valores de referencia calculados manualmente.

---

## Consecuencias

- Los jobs de SageMaker (`jobs/run_*.py`) son scripts de entrada que inicializan el
  entorno AWS y delegan en la lógica compartida.
- Los scripts de desarrollo local son los mismos, pero con `--config config/local.yaml`.
- No existen dos versiones del código de negocio.
- El tiempo de desarrollo local es más rápido (sin overhead de Spark/AWS).

---

## Dependencias por entorno

| Dependencia | Local | AWS |
|-------------|-------|-----|
| pandas | Sí | Solo para pruebas |
| PySpark | Opcional (tests de consistencia) | Sí |
| NetworkX | Sí | Solo para tests unitarios |
| graphframes | No | Sí |
| boto3 | Opcional (con credenciales) | Sí |
| MLflow | Sí (tracking local) | Sí (tracking remoto) |

---

## Referencias

- plan.md Estructura del Repositorio
- Constitución v3.0.0 Principio II
