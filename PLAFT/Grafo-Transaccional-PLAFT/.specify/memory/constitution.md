<!-- Sync Impact Report
Version change: 3.0.1 → 4.0.0
Motivo del bump MAJOR: redefinición material del propósito y entregable principal del
proyecto. El foco cambia de "plataforma centrada en variables" a "grafo transaccional
para investigación PLAFT con evidencia trazable".
Principios modificados: I, III, IV, V, VIII, IX, X, XIII, XV, XVI, XVIII.
Secciones añadidas: XI. Casos Investigados.
Secciones eliminadas: ninguna.
Cambios materiales:
  - El propósito principal pasa a ser la investigación PLAFT soportada por un grafo
    transaccional integrado.
  - El entregable de negocio principal pasa a ser "caso investigado con evidencia trazable".
  - Las variables estructurales se mantienen como capacidad analítica secundaria y
    reutilizable, no como fin primario.
  - Se redefine la arquitectura por capas para incluir normalización/mapeo,
    investigación de casos y gestión de evidencia.
  - Se incorpora un principio explícito de Investigación PLAFT y Evidencia verificable.
  - Se reformula la hoja de ruta a 8 fases + capacidad transversal de variables para ML.
Follow-up TODOs: Ninguno.
-->

# Constitución — Grafo Transaccional para Investigación PLAFT

## I. Propósito del Proyecto

El propósito principal del proyecto es construir un grafo transaccional para la
investigación PLAFT, que permita a los analistas investigar clientes, cuentas,
transacciones, contrapartes y otras entidades relacionadas, comprender conexiones y
patrones de movimiento de dinero, identificar estructuras relevantes y documentar
evidencia trazable que sustente cada investigación.

El grafo DEBERÁ funcionar como representación analítica integrada de relaciones financieras
y transaccionales relevantes para PLAFT. El flujo conceptual principal DEBERÁ ser:

Fuentes de datos → validación → construcción del grafo → análisis de relaciones y patrones
→ investigación PLAFT → evidencia → caso investigado.

La generación de variables estructurales DEBERÁ mantenerse como capacidad analítica
secundaria y reutilizable. Puede enriquecer investigaciones y modelos, pero NO define por
sí sola el objetivo del proyecto.

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

- **Ingesta de fuentes**: carga y recepción de fuentes primarias.
- **Validación y calidad**: verificación de esquemas, reglas de calidad e integridad.
- **Normalización y mapeo físico-conceptual**: estandarización semántica de datos.
- **Construcción del grafo transaccional**: creación de nodos, relaciones y atributos.
- **Persistencia y versionado**: almacenamiento reproducible del grafo y artefactos.
- **Graph Analytics**: cómputo de métricas, conectividad y estructuras.
- **Detección de patrones y señales**: identificación de ciclos, cadenas, hubs,
  intermediarios, concentraciones y otras señales.
- **Investigación de casos**: análisis guiado por caso y sujeto investigado.
- **Gestión y trazabilidad de evidencia**: vinculación de hallazgos con soporte verificable.
- **Visualización y exploración**: navegación funcional para investigación.
- **Consultas analíticas**: acceso estructurado y reproducible para analistas.
- **Generación opcional de variables para ML**: publicación selectiva y reutilizable.
- **Integraciones futuras con GraphRAG y asistentes PLAFT**: capacidades avanzadas con
  controles de evidencia y acceso.

Cada capa DEBERÁ tener responsabilidades claramente definidas. Una capa NO DEBERÁ depender
directamente de componentes internos de una capa distinta de su dependencia inmediata.

La incorporación de entidades, relaciones o atributos NO DEBERÁ justificarse únicamente por
generación de variables. También puede justificarse por utilidad para investigación,
trazabilidad, evidencia, explicabilidad, navegación o consultas futuras (incluyendo GraphRAG).

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
- PEP, ROS y fuentes regulatorias complementarias
- Dispositivos, canales, IP, comercios y otras trazas transaccionales
- Resultados de modelos ML

La incorporación de nuevas fuentes de datos NO DEBERÁ requerir rediseñar la arquitectura.
Todo nuevo dataset DEBERÁ cumplir los estándares de calidad definidos en el Principio VI.

## V. Modelo del Grafo

El grafo representa entidades financieras y sus relaciones. Toda entidad y relación
DEBERÁ conservar trazabilidad hasta el registro de origen que la generó.

El modelo conceptual DEBERÁ estar centrado en investigación y soportar progresivamente,
como mínimo, las siguientes entidades:

- Cliente
- Cuenta
- Persona
- Empresa
- Producto
- Transacción
- Caso
- Alerta
- ROS
- PEP
- Documento
- Beneficiario final
- Apoderado
- Dispositivo
- Dirección IP
- Canal
- Comercio
- País
- Otras entidades relevantes para PLAFT.

Las relaciones DEBERÁN representar hechos del negocio y conservar procedencia,
temporalidad y contexto de cálculo e investigación.

Una transferencia PUEDE representarse como relación o entidad según necesidades de
trazabilidad, atributos y análisis, respetando ADR vigentes. Ninguna reinterpretación de
modelado DEBERÁ invalidar decisiones arquitectónicas aprobadas sin evaluación formal de
impacto en ADR.

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
- versión de las variables producidas (si aplica);
- versión del caso y evidencia generada (si aplica).

Todo resultado DEBERÁ ser completamente reproducible a partir de los insumos y parámetros
registrados. Todo nodo y relación DEBERÁ mantener referencia directa al dato de origen.

## VIII. Variables Analíticas

Las variables estructurales se mantienen como instrumentos analíticos derivados del grafo.
NO constituyen el entregable principal del negocio. Las variables DEBERÁN clasificarse al
menos en las siguientes categorías:

- **Centralidad**: grado de entrada y salida, PageRank, betweenness, eigenvector centrality.
- **Conectividad**: cantidad de contrapartes, profundidad de red, componentes conectados.
- **Comunidades**: membresía, tamaño de comunidad, modularidad local.
- **Flujo de dinero**: monto recibido y enviado, velocidad de circulación, concentración.
- **Exposición a nodos con señales PLAFT**: cercanía y dependencia respecto a nodos
  alertados, PEP, ROS o investigados.
- **Riesgo de vecinos**: exposición directa a nodos de riesgo conocido.
- **Riesgo propagado**: exposición indirecta a nodos de riesgo en niveles superiores.
- **Anomalías estructurales**: patrones atípicos respecto al comportamiento esperado.
- **Patrones transaccionales**: frecuencia, regularidad, estacionalidad, dispersión,
  ciclos, cadenas, hubs e intermediarios.

Las variables DEBERÁN ser reproducibles y trazables. Solo las variables con caso de uso
explícito para modelamiento DEBERÁN publicarse en SageMaker Feature Store. NO todas las
métricas del grafo DEBERÁN convertirse obligatoriamente en features.

## IX. Machine Learning

Machine Learning es una capacidad complementaria. El proyecto NO DEBERÁ diseñarse
exclusivamente alrededor de Feature Store ni del entrenamiento de modelos.

Las variables DEBERÁN poder utilizarse como features reutilizables para modelos supervisados
y no supervisados. Las decisiones de riesgo DEBERÁN considerar múltiples fuentes de
información. Ningún sistema descendente DEBERÁ depender exclusivamente de las variables del
grafo para emitir alertas o decisiones de riesgo.

Los resultados de modelos ML PUEDEN incorporarse como señales o atributos del grafo cuando
mejoren la investigación y mantengan trazabilidad.

## X. Investigación PLAFT y Evidencia

El entregable principal de negocio DEBERÁ ser un caso investigado con evidencia trazable,
no un conjunto de variables aisladas.

Todo hallazgo relevante producido por Graph Analytics DEBERÁ vincularse con evidencia
verificable. La evidencia DEBERÁ conservar, cuando corresponda:

- cliente o entidad investigada;
- nodos involucrados;
- relaciones involucradas;
- transacciones relacionadas;
- período analizado y fecha de corte;
- algoritmo o regla aplicada;
- parámetros utilizados;
- datasets fuente;
- versión del grafo;
- timestamp de ejecución.

El sistema DEBERÁ distinguir explícitamente:

dato fuente → hecho representado en el grafo → métrica o patrón o señal → evidencia →
interpretación del analista → resultado del caso.

Una señal analítica NUNCA DEBERÁ confundirse con una conclusión PLAFT definitiva.

## XI. Casos Investigados

La entidad de investigación y caso NO DEBERÁ tratarse únicamente como fuente histórica.
DEBERÁ poder agrupar, como mínimo:

- sujeto investigado;
- motivo de investigación;
- fecha de apertura;
- período analizado;
- hallazgos;
- señales;
- evidencia;
- entidades relacionadas;
- estado de investigación;
- observaciones del analista;
- resultado o conclusión;
- trazabilidad de acciones por usuario.

Los casos históricos PUEDEN reutilizarse para enriquecer nuevas investigaciones.

## XII. Explicabilidad

Toda variable generada por el sistema DEBERÁ poder explicar:

- qué datos utilizó para su cálculo;
- qué algoritmo o lógica fue aplicada;
- qué relaciones del grafo participaron;
- qué transacciones originaron el resultado.

La explicabilidad constituye un requisito funcional obligatorio, no una característica
opcional. Todo componente que produzca variables DEBERÁ exponer su trazabilidad de forma
que sea comprensible para un analista PLAFT o auditor.

La explicabilidad DEBERÁ extenderse también a hallazgos de investigación y evidencia,
incluyendo el vínculo entre patrones detectados y transacciones fuente.

## XIII. Seguridad

Los datos productivos ÚNICAMENTE PODRÁN procesarse dentro de la infraestructura autorizada
por el banco. El repositorio NO DEBERÁ contener credenciales, secretos, tokens ni información
sensible de ningún tipo.

Los datos utilizados para desarrollo local DEBERÁN ser sintéticos o anonimizados en su
totalidad. El repositorio DEBERÁ incluir un `.gitignore` que excluya explícitamente datos
sensibles, credenciales y entornos locales. El incumplimiento de este principio invalida la
contribución afectada.

## XIV. Calidad del Software

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

## XV. Evolución

La hoja de ruta del proyecto contempla las siguientes fases. La arquitectura DEBERÁ
soportar todas estas etapas sin requerir rediseño:

| Fase | Objetivo |
|------|----------|
| 1 | Base de datos e ingesta: contratos, calidad, temporalidad y trazabilidad de fuentes reales. |
| 2 | Grafo transaccional: construcción, persistencia y reproducción del grafo base. |
| 3 | Graph Analytics: métricas, comunidades, ciclos, cadenas, hubs, intermediarios y patrones. |
| 4 | Investigación PLAFT: casos, expansión de redes, filtros temporales y priorización de hallazgos. |
| 5 | Evidencia y explicabilidad: vínculo reproducible entre hallazgos, grafo y registros fuente. |
| 6 | Enriquecimiento: KYC, documentos, beneficiarios finales, PEP, ROS, listas y otras fuentes. |
| 7 | GraphRAG: consultas sobre grafo, evidencia y documentación autorizada. |
| 8 | Asistente inteligente PLAFT: asistencia conversacional con evidencia y controles de acceso. |

Capacidad transversal: Variables para ML. Las métricas y señales reutilizables podrán
publicarse para modelos PLAFT cuando exista un caso de uso que lo justifique.

Ninguna decisión técnica en la fase actual DEBERÁ impedir la incorporación de fases
posteriores. Toda decisión que limite la extensibilidad DEBERÁ justificarse mediante un ADR.

## XVI. Métricas del Proyecto

Como mínimo, cada ejecución del sistema DEBERÁ registrar las siguientes métricas
operacionales del grafo y de investigación:

- número de nodos totales y por tipo;
- número de relaciones totales y por tipo;
- densidad del grafo;
- modularidad global;
- número de comunidades detectadas;
- distribución de grados (entrada y salida);
- tiempo de construcción del grafo;
- tiempo de detección de patrones y señales;
- tiempo de respuesta a consultas;
- número de hallazgos por caso y por tipología de patrón;
- cobertura de hallazgos con evidencia trazable;
- cantidad de variables generadas por categoría (cuando aplique).

Estas métricas DEBERÁN almacenarse junto a los artefactos del grafo y estar disponibles
para monitoreo y comparación entre ejecuciones.

## XVII. Gobernanza

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

## XVIII. Principios de Diseño

El proyecto se regirá por los siguientes principios rectores:

- **El grafo sirve a la investigación PLAFT**: toda decisión sobre nodos, relaciones,
  métricas, persistencia, visualización, variables o integraciones DEBERÁ evaluarse primero
  por su capacidad de mejorar investigación, trazabilidad, evidencia o comprensión de
  relaciones relevantes para PLAFT.
- **El negocio guía la arquitectura**: toda decisión técnica parte de una necesidad del
  negocio PLAFT.
- **La trazabilidad prevalece sobre la complejidad**: ante la duda, se prioriza la
  trazabilidad del dato sobre la elegancia técnica.
- **La reproducibilidad es obligatoria**: toda ejecución DEBE poder replicarse con los
  mismos insumos y producir los mismos resultados.
- **La simplicidad tiene prioridad sobre la optimización prematura**: no se optimizará lo
  que no ha demostrado ser un cuello de botella.
- **La explicabilidad es un requisito funcional**: toda variable y hallazgo DEBEN poder
  justificarse ante un analista o auditor.
- **Escala desde el diseño**: toda funcionalidad DEBERÁ diseñarse para operar correctamente
  a escala de millones de transacciones.
- **Sin bloqueos para GraphRAG**: ninguna decisión técnica DEBERÁ impedir la futura
  incorporación de capacidades de GraphRAG o asistentes inteligentes.

Las respuestas futuras generadas mediante GraphRAG DEBERÁN citar o identificar evidencia
trazable y DEBERÁN abstenerse cuando no exista evidencia suficiente.

---

**Versión**: 4.0.0 | **Ratificada**: 2026-08-05 | **Última enmienda**: 2026-08-10
