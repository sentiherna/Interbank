<!-- Sync Impact Report
Version change: 2.0.0 → 3.0.0
Motivo del bump MAJOR: cambio de enfoque conceptual del proyecto. El objetivo ya no es
construir un grafo transaccional como producto final, sino una plataforma para generar
variables estructurales basadas en grafos que enriquezcan los modelos de riesgo PLAFT.
El grafo pasa a ser un medio analítico, no el fin del proyecto.
Principios modificados: todos reemplazados (reestructuración completa, 13 → 16 principios).
Secciones añadidas: IV. Datos de Entrada, VIII. Variables Analíticas, XIV. Métricas del
Proyecto.
Secciones eliminadas: ninguna (reestructuración y expansión integral).
Cambios materiales:
  - Propósito reorientado hacia generación de variables estructurales para modelos PLAFT.
  - Plataforma tecnológica ampliada: SageMaker Feature Store, AWS Glue Data Catalog,
    Amazon Athena, Spark SQL.
  - Modelo del grafo expandido con nodos y relaciones adicionales planificados.
  - Variables analíticas clasificadas en 8 categorías explícitas.
  - Hoja de ruta de 7 fases incorporada al principio de Evolución.
  - Métricas del proyecto formalizadas como principio propio.
Follow-up TODOs: Ninguno.
-->

# Constitución — Plataforma de Variables Estructurales PLAFT basada en Grafos

## I. Propósito del Proyecto

El propósito del proyecto es construir una plataforma para generar variables estructurales
mediante análisis de grafos sobre clientes, cuentas, productos y transacciones financieras,
con el fin de enriquecer los modelos de riesgo PLAFT del banco.

El grafo es un medio analítico para derivar variables de alto valor predictivo, no el
producto final del proyecto. Las variables obtenidas DEBERÁN complementar los modelos PLAFT
existentes y servirán como base para futuras capacidades de Graph Analytics, GraphRAG y
asistentes inteligentes para analistas PLAFT.

Toda decisión técnica DEBERÁ alinearse con este propósito. Las decisiones que lo contradigan
o desvíen DEBERÁN justificarse explícitamente mediante un ADR.

## II. Plataforma Tecnológica

La plataforma oficial del proyecto es AWS. Toda solución DEBERÁ diseñarse para ejecutarse
sobre la infraestructura aprobada por el banco. Las tecnologías autorizadas son:

- Amazon S3 — almacenamiento de datos, grafos y artefactos.
- Amazon SageMaker Processing — ejecución de jobs de procesamiento y cómputo de métricas.
- Amazon SageMaker Pipelines — orquestación de flujos ML y generación de variables.
- Amazon SageMaker Feature Store — registro y servicio de variables estructurales.
- AWS Glue Data Catalog — catálogo de datos y gestión de metadatos.
- Amazon Athena — consultas analíticas ad hoc sobre datos en S3.
- Python 3.12 — lenguaje principal del proyecto.
- PySpark — procesamiento distribuido en producción.
- Spark SQL — consultas estructuradas sobre datasets distribuidos.
- pandas — únicamente para desarrollo y pruebas locales.
- MLflow — versionado de modelos, experimentos y artefactos.
- GitHub — control de versiones del código.

El desarrollo local DEBERÁ ser posible para facilitar pruebas y depuración. La ejecución
oficial será sobre la infraestructura AWS definida por la organización.

La arquitectura NO DEBERÁ depender de servicios incompatibles con este entorno. Toda
incorporación de una tecnología no listada DEBERÁ aprobarse mediante un ADR y contar con
la aprobación del responsable técnico del proyecto.

## III. Arquitectura por Capas

El sistema DEBERÁ mantener separación estricta entre las siguientes capas, cada una con
responsabilidades claramente definidas e interfaz explícita:

- **Ingesta**: carga y recepción de fuentes primarias de datos.
- **Validación**: verificación de calidad, esquemas e integridad referencial.
- **Construcción del grafo**: creación de nodos y aristas a partir de datos validados.
- **Persistencia**: almacenamiento y versionado del grafo y sus artefactos.
- **Cálculo de métricas**: cómputo de indicadores estructurales sobre el grafo.
- **Generación de variables**: derivación y registro de features para modelos ML.
- **Visualización**: exploración gráfica del grafo y sus métricas.
- **Consultas**: acceso analítico estructurado al grafo y a las variables generadas.
- **Integraciones futuras**: conectores para sistemas externos (KYC, alertas, GraphRAG).

Cada capa DEBERÁ tener responsabilidades claramente definidas. Una capa NO DEBERÁ depender
directamente de componentes internos de una capa distinta de su dependencia inmediata.

## IV. Datos de Entrada

La plataforma DEBERÁ admitir múltiples datasets como fuentes de datos de entrada.

**Fuentes iniciales**:

- Clientes
- Cuentas
- Transferencias
- Productos
- Alertas PLAFT
- Casos investigados

**Fuentes planificadas para fases posteriores**:

- KYC y documentación de clientes
- Empresas y personas relacionadas
- Beneficiarios finales
- Listas restrictivas
- Resultados de modelos ML

La incorporación de nuevas fuentes de datos NO DEBERÁ requerir rediseñar la arquitectura.
Todo nuevo dataset DEBERÁ cumplir los estándares de calidad definidos en el Principio VI.

## V. Modelo del Grafo

El grafo representa entidades financieras y sus relaciones. Toda entidad y relación
DEBERÁ conservar trazabilidad hasta el registro de origen que la generó.

**Nodos iniciales**:

- Cliente
- Cuenta
- Transferencia
- Producto
- Persona
- Empresa

**Nodos planificados para fases posteriores**:

- Beneficiario Final
- Apoderado
- Canal
- Dispositivo
- Dirección IP
- Sucursal
- Comercio
- País

**Relaciones iniciales**:

- Transferencia
- Titularidad
- Beneficiario
- Apoderado
- Representación
- Relación Comercial

La incorporación de nuevos tipos de nodos o relaciones DEBERÁ documentarse y evaluarse en
función de su alineación con el propósito del proyecto (Principio I).

## VI. Calidad de Datos

Toda ingesta DEBERÁ validar como mínimo:

- esquema de los datos recibidos;
- tipos de datos de cada campo;
- presencia de columnas obligatorias;
- ausencia de duplicados;
- integridad referencial entre entidades;
- consistencia temporal de registros;
- pertenencia de valores a dominios válidos.

Los errores críticos de calidad DEBERÁN detener la ejecución de forma controlada y registrar
el motivo. NUNCA DEBERÁN ocultarse errores de calidad mediante manejo silencioso.

## VII. Trazabilidad y Reproducibilidad

Toda ejecución del sistema DEBERÁ registrar:

- versión del código ejecutado;
- versión del conjunto de datos utilizado;
- parámetros de configuración empleados;
- timestamp de ejecución;
- versión del grafo generado;
- versión de las variables producidas.

Todo resultado DEBERÁ ser completamente reproducible a partir de los insumos y parámetros
registrados. Todo nodo y relación DEBERÁ mantener referencia directa al dato de origen.

## VIII. Variables Analíticas

La finalidad principal del proyecto es generar variables estructurales reutilizables para
modelos PLAFT. Las variables DEBERÁN clasificarse al menos en las siguientes categorías:

- **Centralidad**: grado de entrada/salida, PageRank, betweenness, eigenvector centrality.
- **Conectividad**: cantidad de contrapartes, profundidad de red, componentes conectados.
- **Comunidades**: membresía, tamaño de comunidad, modularidad local.
- **Flujo de dinero**: monto recibido/enviado, velocidad de circulación, concentración.
- **Riesgo de vecinos**: exposición directa a nodos de riesgo conocido.
- **Riesgo propagado**: exposición indirecta a nodos de riesgo en niveles superiores.
- **Anomalías estructurales**: patrones atípicos respecto al comportamiento esperado.
- **Patrones transaccionales**: frecuencia, regularidad, estacionalidad, dispersión.

Todas las variables DEBERÁN ser completamente reproducibles, trazables y registradas en
SageMaker Feature Store para su reutilización por múltiples modelos.

## IX. Machine Learning

El grafo y las variables estructurales complementan los modelos PLAFT existentes. El grafo
NO constituye un motor autónomo de decisión.

Las variables DEBERÁN poder utilizarse como features reutilizables para modelos supervisados
y no supervisados. Las decisiones de riesgo DEBERÁN considerar múltiples fuentes de
información. Ningún sistema descendente DEBERÁ depender exclusivamente de las variables del
grafo para emitir alertas o decisiones de riesgo.

## X. Explicabilidad

Toda variable generada por el sistema DEBERÁ poder explicar:

- qué datos utilizó para su cálculo;
- qué algoritmo o lógica fue aplicada;
- qué relaciones del grafo participaron;
- qué transacciones originaron el resultado.

La explicabilidad constituye un requisito funcional obligatorio, no una característica
opcional. Todo componente que produzca variables DEBERÁ exponer su trazabilidad de forma
que sea comprensible para un analista PLAFT o auditor.

## XI. Seguridad

Los datos productivos ÚNICAMENTE PODRÁN procesarse dentro de la infraestructura autorizada
por el banco. El repositorio NO DEBERÁ contener credenciales, secretos, tokens ni información
sensible de ningún tipo.

Los datos utilizados para desarrollo local DEBERÁN ser sintéticos o anonimizados en su
totalidad. El repositorio DEBERÁ incluir un `.gitignore` que excluya explícitamente datos
sensibles, credenciales y entornos locales. El incumplimiento de este principio invalida la
contribución afectada.

## XII. Calidad del Software

Todo componente del sistema DEBERÁ cumplir como mínimo los siguientes estándares:

- Python 3.12 como versión base.
- Tipado estático con anotaciones en todas las funciones y métodos públicos.
- Documentación pública de funciones, clases y módulos.
- Pruebas unitarias para toda lógica de negocio.
- `mypy` para verificación estática de tipos.
- `ruff` como linter y formateador de código.
- Integración continua que valide pruebas y análisis estático en cada PR.
- Manejo explícito de errores; los errores silenciosos están PROHIBIDOS.

El código sin pruebas unitarias NO DEBERÁ integrarse a la rama principal.

## XIII. Evolución

La hoja de ruta del proyecto contempla las siguientes fases. La arquitectura DEBERÁ
soportar todas estas etapas sin requerir rediseño:

| Fase | Objetivo |
|------|----------|
| 1 | Grafo transaccional: nodos, relaciones y persistencia. |
| 2 | Variables estructurales: cálculo, clasificación y registro en Feature Store. |
| 3 | Integración con modelos PLAFT: features disponibles para scoring. |
| 4 | Explicabilidad: trazabilidad completa de variables para analistas y auditores. |
| 5 | Integración con documentación KYC: enriquecimiento del grafo con información documental. |
| 6 | GraphRAG: recuperación aumentada por grafo para análisis de riesgo. |
| 7 | Asistente inteligente PLAFT: interfaz conversacional para analistas. |

Ninguna decisión técnica en la fase actual DEBERÁ impedir la incorporación de fases
posteriores. Toda decisión que limite la extensibilidad DEBERÁ justificarse mediante un ADR.

## XIV. Métricas del Proyecto

Como mínimo, cada ejecución del sistema DEBERÁ registrar las siguientes métricas
operacionales del grafo:

- Número de nodos totales y por tipo.
- Número de relaciones totales y por tipo.
- Densidad del grafo.
- Modularidad global.
- Número de comunidades detectadas.
- Distribución de grados (entrada y salida).
- Tiempo de construcción del grafo.
- Tiempo de generación de variables.
- Tiempo de respuesta a consultas.
- Cantidad de variables generadas por categoría.

Estas métricas DEBERÁN almacenarse junto a los artefactos del grafo y estar disponibles
para monitoreo y comparación entre ejecuciones.

## XV. Gobernanza

Esta constitución rige todas las decisiones de diseño, desarrollo y operación de la
plataforma. En caso de conflicto entre esta constitución y cualquier otro documento del
proyecto, la constitución prevalece.

Toda decisión arquitectónica relevante DEBERÁ documentarse mediante Architecture Decision
Records (ADR) en el repositorio. Todo ADR DEBERÁ incluir: motivo, impacto esperado, riesgos
identificados y compatibilidad con esta constitución.

**Proceso de enmienda**: los cambios MAJOR requieren revisión de todo el equipo y ADR
correspondiente. Los cambios MINOR y PATCH pueden ser aprobados por el responsable técnico.

**Política de versiones** (semántico):
- MAJOR: redefinición incompatible o eliminación de principios de gobernanza.
- MINOR: adición de nuevos principios o secciones con guía material.
- PATCH: aclaraciones, correcciones de redacción o ajustes no semánticos.

**Revisión de cumplimiento**: cada iteración DEBERÁ incluir verificación de cumplimiento de
esta constitución para las contribuciones realizadas en ese período.

## XVI. Principios de Diseño

El proyecto se regirá por los siguientes principios rectores:

- **El negocio guía la arquitectura**: toda decisión técnica parte de una necesidad del
  negocio PLAFT.
- **La trazabilidad prevalece sobre la complejidad**: ante la duda, se prioriza la
  trazabilidad del dato sobre la elegancia técnica.
- **La reproducibilidad es obligatoria**: toda ejecución DEBE poder replicarse con los
  mismos insumos y producir los mismos resultados.
- **La simplicidad tiene prioridad sobre la optimización prematura**: no se optimizará lo
  que no ha demostrado ser un cuello de botella.
- **La explicabilidad es un requisito funcional**: toda variable DEBE poder justificarse
  ante un analista o auditor.
- **Escala desde el diseño**: toda funcionalidad DEBERÁ diseñarse para operar correctamente
  a escala de millones de transacciones.
- **Sin bloqueos para GraphRAG**: ninguna decisión técnica DEBERÁ impedir la futura
  incorporación de capacidades de GraphRAG o asistentes inteligentes.

---

**Versión**: 3.0.0 | **Ratificada**: 2026-08-05 | **Última enmienda**: 2026-08-06
