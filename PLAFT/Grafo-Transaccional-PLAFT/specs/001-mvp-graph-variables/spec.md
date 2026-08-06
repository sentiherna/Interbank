<!-- Sync Impact Report
Version change: v1.1 → v2.0
Motivo del bump MAJOR: expansión sustancial del alcance del MVP.
  - El MVP produce dos resultados: (1) variables estructurales para modelos analíticos
    del banco, y (2) herramienta de consulta y visualización para analistas PLAFT que
    investigan clientes sospechosos.
  - La población objetivo cambia a un subgrafo centrado exclusivamente en clientes
    sospechosos y sus contrapartes directas (profundidad configurable).
  - Alertas PLAFT, ROS, Condición PEP y Casos Investigados se incorporan al MVP; ya no
    se postergan a Fase 2.
  - Se añade el Catálogo Documental como nueva fuente de datos del MVP.
  - Nuevo modelo del grafo: 9 tipos de nodos y 8 tipos de relaciones.
  - Nueva User Story 4 (Investigación de Cliente Sospechoso — P1).
  - Las 8 categorías de variables son objetivo del MVP; Riesgo de Vecinos y Riesgo
    Propagado se calculan desde el MVP a partir de señales de riesgo integradas.
  - Se añade sección Seguridad y Auditoría (SA-001 a SA-007).
  - Se añaden RNF-010 (Seguridad) y RNF-011 (Auditoría).
  - Exclusiones actualizadas: interfaz, visualización, alertas, ROS, PEP, casos y
    catálogo documental eliminados de las exclusiones.
Secciones añadidas: Población Objetivo del MVP, Modelo del Grafo, Seguridad y Auditoría,
  User Story 4 (Investigación de Cliente Sospechoso), FR-001–FR-043 (reordenados),
  SC-009–SC-018, RNF-010/011.
Secciones modificadas: Resumen Ejecutivo, Objetivo, Alcance del MVP, Pipeline del MVP,
  User Story 1 (subgrafo sospechosos), User Story 3 (8 categorías en MVP), User Story 5→6
  (Explicabilidad ampliada), User Story 6→7 (Reproducibilidad), Edge Cases, Key Entities,
  Exclusiones, Assumptions.
Secciones sin cambios materiales: User Story 2 (Persistencia), User Story 4→5 (Consumo).
Follow-up TODOs: ADR para elección tecnológica de la herramienta de visualización.
-->

# Feature Specification: MVP — Plataforma Analítica PLAFT basada en Grafos

**Feature Directory**: `specs/001-mvp-graph-variables`

**Created**: 2026-08-06

**Updated**: 2026-08-06

**Version**: v2.0

**Status**: Draft

**Constitución aplicable**: v3.0.0

---

## Resumen Ejecutivo

Los analistas PLAFT de Interbank requieren herramientas para investigar clientes
sospechosos y comprender sus redes de relaciones financieras. Actualmente, esta
investigación depende de consultas manuales a múltiples sistemas que no están integrados
y que no ofrecen una visión estructural de las relaciones entre clientes, cuentas y
transferencias.

Este MVP construye una plataforma analítica que produce dos resultados principales:

1. **Variables estructurales reutilizables**: generadas mediante Graph Analytics sobre
   un subgrafo de clientes sospechosos, para enriquecer modelos PLAFT y otros modelos
   analíticos del banco.
2. **Herramienta de investigación para analistas**: que permite seleccionar un cliente
   sospechoso, visualizar sus relaciones financieras, consultar señales de riesgo
   (alertas, ROS, PEP, casos) y acceder al catálogo de documentos disponibles.

El grafo es el mecanismo de cómputo y el núcleo de la plataforma. La plataforma pertenece
a la capa de Data Science del banco y no a un modelo específico.

## Objetivo

Construir el MVP de la Plataforma Analítica PLAFT basada en Grafos, que permita:

1. Seleccionar la población de clientes sospechosos según criterios configurables.
2. Construir y persistir un subgrafo financiero centrado en clientes sospechosos y sus
   contrapartes directas, con versionado completo.
3. Integrar señales de riesgo: Alertas PLAFT, ROS, Condición PEP y Casos Investigados.
4. Integrar el catálogo de documentos asociados a los clientes.
5. Ejecutar algoritmos de Graph Analytics sobre el subgrafo.
6. Generar las 8 categorías de variables estructurales, incluyendo Riesgo de Vecinos y
   Riesgo Propagado calculados a partir de las señales de riesgo integradas.
7. Proveer una herramienta interna para que los analistas PLAFT investiguen clientes
   sospechosos, visualicen sus relaciones y consulten variables y documentos.

## Población Objetivo del MVP

El MVP no construye el grafo de toda la cartera. Opera exclusivamente sobre un **subgrafo
centrado en clientes sospechosos** y las contrapartes necesarias para comprender sus
relaciones.

Un cliente se considera sospechoso cuando cumple al menos una de las siguientes
condiciones, verificables en los datos disponibles:

- Posee una Alerta PLAFT activa o histórica.
- Posee un ROS (Reporte de Operación Sospechosa).
- Está identificado como PEP (Persona Expuesta Políticamente).
- Posee un Caso Investigado asociado.
- Aparece en una lista de clientes objetivo provista por el equipo PLAFT.
- Cumple una regla de selección configurable y documentada.

**Expansión del subgrafo**: el grafo incluye al cliente sospechoso más sus contrapartes
directas. La profundidad de expansión es un parámetro configurable; el valor por defecto
del MVP es 1 salto. El diseño DEBE permitir ampliar a 2 o más niveles sin rediseño.

Para cada contraparte incorporada, el sistema registra sus relaciones con el cliente
sospechoso y, cuando esté disponible, sus propias señales de riesgo.

## Alcance del MVP

**Incluido en esta versión**:

- Selección de la población de clientes sospechosos mediante criterios configurables.
- Ingesta de los datasets: Clientes sospechosos, Clientes o contrapartes relacionadas,
  Cuentas, Transferencias, Productos, Alertas PLAFT, ROS, Indicadores PEP, Casos
  Investigados y Catálogo Documental.
- Validación de calidad de datos (esquema, tipos, duplicados, integridad referencial,
  consistencia temporal, dominios).
- Construcción del subgrafo financiero con los nodos y relaciones definidos en el Modelo.
- Persistencia del grafo con versionado completo y trazabilidad.
- Graph Analytics: ejecución de algoritmos estructurales (Degree, PageRank, Betweenness,
  Closeness, Eigenvector Centrality, Louvain, Label Propagation, Connected Components,
  Shortest Paths, Community Detection).
- Generación de las 8 categorías de variables estructurales: Centralidad, Conectividad,
  Comunidades, Flujo de dinero, Patrones transaccionales, Anomalías estructurales,
  Riesgo de Vecinos y Riesgo Propagado.
- Persistencia de variables con trazabilidad y versionado completos.
- Herramienta interna de investigación para analistas PLAFT.
- Registro de auditoría de consultas realizadas por analistas.
- Reproducibilidad completa de cualquier ejecución histórica.

**Fuera del alcance de esta versión**: ver sección *Exclusiones del MVP*.

---

## Modelo del Grafo

El grafo representa un subgrafo financiero centrado en clientes sospechosos. Toda entidad
y relación DEBE conservar trazabilidad hasta el registro de origen.

**Nodos**:

| Nodo | Descripción |
|------|-------------|
| Cliente | Único tipo de nodo para clientes. Incluye atributos de rol: `es_cliente_objetivo`, `es_contraparte`, `motivos_seleccion`, `nivel_expansion`. Un cliente puede actuar simultáneamente como cliente objetivo y contraparte de otro cliente objetivo. |
| Cuenta | Cuenta bancaria. Puede tener más de un titular. |
| Producto | Producto financiero contratado. |
| Alerta PLAFT | Alerta generada por el sistema PLAFT para un cliente. |
| ROS | Reporte de Operación Sospechosa asociado a un cliente. |
| Condición PEP | Registro que identifica a un cliente como Persona Expuesta Políticamente. No constituye evidencia automática de operación sospechosa. |
| Caso Investigado | Caso de investigación PLAFT asociado a un cliente. |
| Documento | Registro del catálogo documental; metadatos y referencia, sin contenido en esta versión. |

**Relaciones**:

| Relación | Origen | Destino | Descripción |
|----------|--------|---------|-------------|
| `ES_TITULAR_DE` | Cliente | Cuenta | Titularidad; una cuenta puede tener múltiples titulares. |
| `POSEE` | Cliente | Producto | El cliente contrata un producto financiero. |
| `TRANSFIERE_A` | Cuenta | Cuenta | Transferencia dirigida con atributos completos. |
| `TIENE_ALERTA` | Cliente | Alerta PLAFT | El cliente posee una alerta PLAFT. |
| `TIENE_ROS` | Cliente | ROS | El cliente posee un Reporte de Operación Sospechosa. |
| `TIENE_CONDICION_PEP` | Cliente | Condición PEP | El cliente está identificado como PEP. |
| `TIENE_CASO` | Cliente | Caso Investigado | El cliente posee un caso de investigación. |
| `TIENE_DOCUMENTO` | Cliente | Documento | El cliente posee documentación en el catálogo. |

**Atributos de `TRANSFIERE_A`**: `id_transaccion` (clave de identidad; múltiples
transferencias entre las mismas cuentas NO se deduplicarán si poseen identificadores
distintos), `cuenta_origen`, `cuenta_destino`, `cliente_origen` (si resoluble),
`cliente_destino` (si resoluble), `fecha_hora`, `monto`, `moneda`, `canal`, `estado`,
`periodo`, `dataset_origen`, `registro_fuente`.

**Atributos del nodo Documento**: identificador, identificador del cliente, tipo
documental, nombre, fecha del documento, fecha de incorporación, referencia en S3,
sistema de origen, estado, versión, checksum (cuando esté disponible).

---

## Pipeline del MVP

El pipeline del MVP describe el flujo completo desde la selección de clientes sospechosos
hasta el consumo de variables y la consulta analítica:

```
S3 (datos de entrada)
        ↓
Selección de Clientes Sospechosos
        ↓
   Validación
        ↓
Construcción del Subgrafo
        ↓
 Persistencia del Grafo
        ↓
   Graph Analytics
        ↓
Generación de Variables
        ↓
Persistencia de Variables
        ↓
SageMaker Feature Store ←———→ Modelos Analíticos
        ↑
Herramienta de Investigación (Analistas PLAFT)
```

**Ejecución en esta versión**: el pipeline de construcción y análisis será ejecutado
mediante Amazon SageMaker Processing como jobs independientes y monitoreables. La
herramienta de investigación operará en infraestructura interna autorizada. La elección
tecnológica definitiva se documentará mediante un ADR.

**Evolución planificada**: el pipeline de construcción podrá orquestarse en versiones
posteriores mediante Amazon SageMaker Pipelines.

**Características del pipeline**:

- La Persistencia del Grafo desacopla la construcción del análisis: Graph Analytics y
  Generación de Variables pueden ejecutarse múltiples veces sobre el mismo grafo.
- La herramienta de investigación consume el grafo persistido directamente, sin requerir
  reconstrucción para cada consulta del analista.
- Los metadatos de cada etapa permiten reproducir el pipeline completo desde cualquier
  punto.
- Toda consulta del analista queda registrada en el log de auditoría.

---

## User Scenarios & Testing

<!--
  Historias priorizadas como viajes de usuario ordenados por importancia.
  Cada historia es independientemente testeable y entrega valor por sí sola.
-->

### User Story 1 — Construcción del Subgrafo de Clientes Sospechosos (Priority: P1)

Como Data Scientist, quiero seleccionar la población de clientes sospechosos y construir
automáticamente el subgrafo financiero centrado en dichos clientes e incorporando sus
contrapartes directas, con todas las señales de riesgo y documentación disponibles, para
disponer de una representación estructural de sus relaciones y contexto de riesgo.

**Por qué P1**: Sin el subgrafo construido correctamente no es posible calcular variables
ni proveer la herramienta de investigación. Es el cimiento de toda la plataforma.

**Independent Test**: Se puede probar de forma independiente suministrando una lista de
clientes sospechosos con los datasets de soporte y verificando que el subgrafo contiene
los nodos y relaciones esperados con trazabilidad completa.

**Acceptance Scenarios**:

1. **Given** una lista de clientes sospechosos y los datasets validados,
   **When** se ejecuta el proceso de construcción,
   **Then** el sistema genera un subgrafo con cada cliente sospechoso como nodo central,
   sus contrapartes directas, relaciones de titularidad, transferencias, alertas, ROS,
   PEP, casos y documentos; cada elemento con referencia directa a su registro de origen.

2. **Given** un cliente sospechoso sin transferencias registradas,
   **When** se construye el subgrafo,
   **Then** el cliente aparece con sus señales de riesgo asociadas; el proceso no falla.

3. **Given** un cliente con múltiples cuentas compartidas entre titulares,
   **When** se construye el subgrafo,
   **Then** cada relación de titularidad se modela independientemente.

4. **Given** una ejecución completada,
   **When** se consultan los metadatos,
   **Then** están disponibles: versión del código, criterio de selección de sospechosos,
   versión del dataset, profundidad de expansión, parámetros y timestamp.

---

### User Story 2 — Persistencia del Grafo (Priority: P1)

Como Data Scientist, quiero persistir el subgrafo generado con versionado completo, para
reutilizarlo en ejecuciones de Graph Analytics y en la herramienta de investigación sin
reconstruirlo desde cero.

**Por qué P1**: La persistencia desacopla la construcción del análisis. Sin ella, cada
ejecución de Graph Analytics y cada consulta del analista requieren reconstruir el grafo.

**Independent Test**: Se puede probar construyendo un subgrafo de prueba, persistiéndolo,
recuperándolo y verificando que la estructura es idéntica a la almacenada.

**Acceptance Scenarios**:

1. **Given** un subgrafo construido a partir de la población de sospechosos,
   **When** se ejecuta el proceso de persistencia,
   **Then** el grafo se almacena con identificador de versión único, timestamp y
   referencia a los datasets y criterio de selección utilizados.

2. **Given** un grafo persistido con su identificador de versión,
   **When** se recupera para una ejecución de Graph Analytics o para la herramienta,
   **Then** el grafo recuperado es estructuralmente idéntico al almacenado.

3. **Given** múltiples versiones del grafo almacenadas,
   **When** se solicita una versión específica,
   **Then** el sistema retorna exactamente esa versión.

4. **Given** una versión del grafo recuperada,
   **When** se ejecuta Graph Analytics sobre ella,
   **Then** los resultados son equivalentes a los que se obtendrían reconstruyendo el
   grafo con los mismos datos y parámetros.

**Trazabilidad y Versionado**: cada versión persiste con identificador único, timestamp,
versión del código, criterio de selección, referencia a datasets (nombre y versión) y
parámetros de construcción.

---

### User Story 3 — Graph Analytics y Generación de Variables (Priority: P1)

Como Data Scientist, quiero ejecutar algoritmos de Graph Analytics sobre el subgrafo y
generar las 8 categorías de variables estructurales —incluyendo Riesgo de Vecinos y
Riesgo Propagado a partir de señales de riesgo integradas— para disponer de features
reutilizables para modelos PLAFT y otros modelos analíticos del banco.

**Por qué P1**: La generación de variables es el propósito central de la plataforma. Las
variables de riesgo requieren las señales integradas en el subgrafo desde el MVP.

**Independent Test**: Dado un subgrafo persistido con señales de riesgo integradas, se
puede verificar que el sistema produce las 8 categorías con diferenciación por tipo de
señal y trazabilidad completa.

**Acceptance Scenarios**:

1. **Given** un subgrafo persistido con alertas, ROS, PEP y casos integrados,
   **When** se ejecuta el cálculo de métricas,
   **Then** el sistema produce variables en las 8 categorías: Centralidad, Conectividad,
   Comunidades, Flujo de dinero, Patrones transaccionales, Anomalías estructurales,
   Riesgo de Vecinos y Riesgo Propagado.

2. **Given** variables de Riesgo de Vecinos calculadas,
   **When** se consulta una variable de esta categoría,
   **Then** el sistema diferencia el origen de la señal: alerta PLAFT, ROS, PEP o caso.

3. **Given** variables calculadas para un cliente,
   **When** se consulta cualquier variable,
   **Then** el sistema indica: datos utilizados, algoritmo aplicado, relaciones y señales
   que originaron el resultado.

4. **Given** dos ejecuciones con los mismos datos y parámetros,
   **When** se comparan los resultados,
   **Then** las variables generadas son idénticas.

---

### User Story 4 — Investigación de Cliente Sospechoso (Priority: P1)

Como analista PLAFT, quiero seleccionar un cliente sospechoso y visualizar sus relaciones
financieras, contrapartes, alertas, ROS, condición PEP, casos investigados y documentos
disponibles, para comprender su contexto de riesgo y fundamentar una investigación.

**Por qué P1**: Esta historia es el producto funcional más directo del MVP para el usuario
final. Sin esta capacidad la plataforma no entrega valor directo al proceso de
investigación PLAFT.

**Independent Test**: Dado un cliente sospechoso con relaciones en el grafo, se verifica
que la herramienta muestra correctamente su subgrafo, señales de riesgo, variables y
documentos, y que la consulta queda registrada en el log de auditoría.

**Acceptance Scenarios**:

1. **Given** un identificador de cliente sospechoso válido,
   **When** el analista lo selecciona en la herramienta,
   **Then** el sistema muestra el cliente como nodo central y sus relaciones directas:
   cuentas, productos, transferencias, contrapartes, alertas, ROS, PEP, casos y
   documentos disponibles.

2. **Given** el subgrafo del cliente visible,
   **When** el analista observa las transferencias,
   **Then** cada transferencia muestra dirección, monto, fecha, moneda, canal y cuenta
   contraparte; diferenciando entradas y salidas.

3. **Given** las contrapartes del cliente visibles,
   **When** el analista revisa una contraparte,
   **Then** la herramienta indica si posee alerta, ROS, condición PEP o caso investigado,
   cuando la información esté disponible.

4. **Given** el subgrafo visible,
   **When** el analista aplica filtros (período, tipo de relación, monto, dirección,
   condición de riesgo),
   **Then** el sistema actualiza la vista sin reconstruir el grafo.

5. **Given** un nodo o relación seleccionado,
   **When** el analista consulta su trazabilidad,
   **Then** el sistema retorna la referencia directa al registro de origen (dataset,
   identificador de fila y clave fuente).

6. **Given** el subgrafo visible,
   **When** el analista consulta los documentos del cliente,
   **Then** el sistema lista los documentos disponibles con metadatos y referencia
   autorizada en S3.

7. **Given** el subgrafo visible,
   **When** el analista consulta las variables estructurales del cliente,
   **Then** la herramienta muestra las 8 categorías de variables con valor y explicación.

8. **Given** un cliente sin relaciones o documentos en el grafo,
   **When** el analista lo consulta,
   **Then** el sistema informa la ausencia con mensaje descriptivo, sin lanzar error.

9. **Given** el subgrafo visible,
   **When** el analista visualiza los nodos y relaciones,
   **Then** los tipos se distinguen claramente sin depender exclusivamente del color; la
   versión del grafo y fecha de corte de los datos están siempre visibles.

10. **Given** cualquier acción del analista,
    **When** la acción se completa,
    **Then** queda registrada en el log de auditoría: usuario, cliente consultado,
    timestamp, filtros aplicados, versión del grafo, documentos consultados y
    exportaciones realizadas.

---

### User Story 5 — Consumo de Variables por Modelos Analíticos (Priority: P2)

Como modelo PLAFT, quiero consumir variables estructurales generadas por la plataforma,
para enriquecer mis inputs y mejorar la capacidad predictiva sin calcular las variables
internamente.

**Por qué P2**: El consumo externo depende de que P1 esté resuelto, pero el formato de
acceso debe diseñarse desde el inicio para garantizar reutilización.

**Independent Test**: Se puede verificar de forma independiente que las variables
exportadas son consumibles en formato estándar por un proceso externo de scoring.

**Acceptance Scenarios**:

1. **Given** variables calculadas para un período determinado,
   **When** un proceso externo solicita las variables de un cliente,
   **Then** el sistema retorna las variables en formato estructurado con metadatos de
   versión, categoría y timestamp de generación.

2. **Given** múltiples modelos solicitando variables del mismo cliente y versión,
   **When** los modelos consumen las variables,
   **Then** todos reciben exactamente el mismo resultado.

3. **Given** un cliente sin actividad en una categoría específica,
   **When** se solicita la variable correspondiente,
   **Then** el sistema retorna un valor nulo o valor por defecto documentado, sin error.

---

### User Story 6 — Explicabilidad y Trazabilidad (Priority: P2)

Como analista PLAFT o auditor, quiero poder explicar por qué una variable toma un
determinado valor para un cliente sospechoso —indicando los datos, relaciones y señales
que la originaron— para fundamentar decisiones ante equipos de revisión y auditoría.

**Por qué P2**: La explicabilidad es un requisito funcional obligatorio (Constitución
v3.0.0, Principio X). Permite que analistas y auditores justifiquen las señales del
sistema.

**Independent Test**: Dado un cliente con variables calculadas, se puede verificar que
el sistema retorna la explicación completa de cada variable con trazabilidad al dato.

**Acceptance Scenarios**:

1. **Given** una variable con valor inusual para un cliente,
   **When** el analista solicita su explicación,
   **Then** el sistema indica: datos utilizados, algoritmo aplicado, relaciones y señales
   que originaron el resultado.

2. **Given** una variable de Riesgo de Vecinos,
   **When** se consulta su explicación,
   **Then** el sistema diferencia la contribución por tipo de señal: alertas, ROS, PEP y
   casos, con los valores individuales.

3. **Given** cualquier nodo o relación en el grafo,
   **When** se consulta su trazabilidad,
   **Then** el sistema retorna la referencia directa al registro de origen.

---

### User Story 7 — Reproducibilidad de Ejecuciones Históricas (Priority: P3)

Como auditor, quiero poder reconstruir exactamente un subgrafo histórico y sus variables
asociadas, para verificar la reproducibilidad y exactitud de los resultados en cualquier
punto del tiempo pasado.

**Por qué P3**: La reproducibilidad es obligatoria (Constitución, Principio XVI), pero
puede validarse una vez que los procesos P1 y P2 estén operativos.

**Independent Test**: Dado el registro de una ejecución pasada, se puede re-ejecutar con
los mismos parámetros y verificar que grafo y variables son idénticos a los originales.

**Acceptance Scenarios**:

1. **Given** el identificador de una ejecución pasada,
   **When** el auditor solicita reproducirla,
   **Then** el sistema utiliza exactamente la misma versión de código, criterio de
   selección, datos y parámetros que registró la ejecución original.

2. **Given** una reproducción completada,
   **When** se comparan el grafo y variables resultantes con los originales,
   **Then** los resultados son idénticos.

3. **Given** los metadatos de cualquier ejecución,
   **When** se consultan,
   **Then** están disponibles: versión del código, criterio de selección, versión de
   datos, parámetros, timestamp, versión del grafo y versión de variables producidas.

---

### Edge Cases

- **Cliente sospechoso sin transacciones**: aparece como nodo central con sus señales de
  riesgo; las variables de conectividad y flujo retornan valor nulo o cero documentado;
  el proceso no falla.
- **Cuentas compartidas entre varios titulares**: cada relación de titularidad se modela
  independientemente; la multiplicidad se refleja en el grafo.
- **Cliente con múltiples señales de riesgo simultáneas**: el sistema integra todas las
  señales; las variables de riesgo diferencian por tipo y reflejan el conjunto completo.
- **Contraparte que también es cliente sospechoso**: se modela con ambos roles y el
  analista puede ver sus señales de riesgo propias.
- **Relaciones duplicadas en los datos de origen**: el sistema elimina duplicados y los
  registra; no crea múltiples relaciones para el mismo par salvo instancias temporalmente
  distintas.
- **Ciclos en el grafo**: los algoritmos de Graph Analytics manejan ciclos correctamente
  sin entrar en bucles infinitos ni producir resultados indefinidos.
- **Múltiples productos por cliente**: cada producto genera una relación independiente.
- **Transacciones anuladas**: no se integran como relaciones activas en el grafo.
- **Datos incompletos**: un registro con campos obligatorios ausentes es rechazado en
  validación; el proceso se detiene y registra el error con detalle.
- **Inconsistencias temporales**: transacciones con fecha posterior al corte de extracción
  son rechazadas con registro de error.
- **Documento sin referencia válida en S3**: el documento se registra con sus metadatos y
  estado; la ausencia de referencia válida se indica al analista sin lanzar error.
- **Analista consulta cliente fuera del subgrafo autorizado**: el sistema rechaza la
  consulta, no muestra datos y registra el intento en el log de auditoría.

---

## Requirements

### Functional Requirements

**Selección de población**

- **FR-001**: El sistema DEBE seleccionar la población de clientes sospechosos mediante
  al menos los siguientes criterios: poseer alerta PLAFT, poseer ROS, estar identificado
  como PEP, poseer caso investigado, aparecer en lista provista por PLAFT o cumplir una
  regla de selección configurable y documentada.
- **FR-002**: El sistema DEBE aceptar como entrada los datasets: Clientes sospechosos,
  Clientes o contrapartes relacionadas, Cuentas, Transferencias, Productos, Alertas PLAFT,
  ROS, Indicadores PEP, Casos Investigados y Catálogo Documental.
- **FR-003**: El sistema DEBE admitir la incorporación futura de nuevos datasets y
  criterios de selección sin requerir cambios en la arquitectura de capas existentes.

**Validación**

- **FR-004**: El sistema DEBE validar en cada dataset ingestado: esquema, tipos de datos,
  columnas obligatorias, duplicados, integridad referencial, consistencia temporal y
  pertenencia a dominios válidos.
- **FR-005**: El sistema DEBE detener la ejecución ante errores críticos de calidad y
  registrar el motivo de forma detallada y legible.
- **FR-006**: El sistema NO DEBE ocultar errores de validación ni continuar procesando
  datos inválidos.

**Construcción del subgrafo**

- **FR-007**: El sistema DEBE construir el subgrafo partiendo de los clientes sospechosos
  e incorporando contrapartes a la profundidad configurada (por defecto: 1 salto).
- **FR-008**: El sistema DEBE soportar un único tipo de nodo **Cliente** con los atributos
  de rol: `es_cliente_objetivo`, `es_contraparte`, `motivos_seleccion`, `nivel_expansion`,
  `tiene_alerta`, `tiene_ros`, `es_pep`, `tiene_caso`. Adicionalmente: Cuenta, Producto,
  Alerta PLAFT, ROS, Condición PEP, Caso Investigado y Documento.
- **FR-009**: El sistema DEBE soportar las relaciones: ES_TITULAR_DE, POSEE,
  TRANSFIERE_A, TIENE_ALERTA, TIENE_ROS, TIENE_CONDICION_PEP, TIENE_CASO y
  TIENE_DOCUMENTO.
- **FR-010**: Cada nodo y relación DEBEN conservar referencia directa al registro de
  origen: dataset, identificador de fila o clave del registro fuente.
- **FR-011**: La relación TRANSFIERE_A DEBE conservar todos los atributos definidos en el
  Modelo del Grafo.
- **FR-012**: El catálogo documental DEBE integrarse como nodos Documento con los
  metadatos mínimos definidos: identificador, cliente, tipo, nombre, fecha del documento,
  fecha de incorporación, referencia en S3, sistema de origen, estado, versión y checksum
  cuando esté disponible.
- **FR-013**: El sistema DEBE controlar la profundidad de expansión del subgrafo mediante
  un parámetro configurable.

**Persistencia del grafo versionado**

- **FR-014**: El sistema DEBE persistir el grafo con identificador de versión único,
  timestamp, criterio de selección, versión del código y referencia a los datasets.
- **FR-015**: El sistema DEBE permitir recuperar cualquier versión persistida por su
  identificador, garantizando integridad estructural completa.

**Graph Analytics**

- **FR-016**: El sistema DEBE ejecutar los siguientes algoritmos **obligatorios** del MVP:
  in-degree, out-degree, grado total, cantidad de transferencias recibidas y enviadas,
  monto recibido y enviado, cantidad de contrapartes únicas, PageRank, Connected
  Components, Louvain Community Detection, distancia mínima dirigida a clientes con
  señales de riesgo, y exposición directa e indirecta a señales de riesgo. Los algoritmos
  **experimentales** (Betweenness Centrality, Closeness Centrality, Eigenvector Centrality,
  Label Propagation, cálculos masivos de Shortest Paths) se ejecutarán condicionados a
  pruebas de escala y se documentarán mediante ADR.
- **FR-017**: Los resultados de Graph Analytics DEBEN ser el insumo directo de la capa de
  Generación de Variables.
- **FR-018**: El sistema DEBE manejar correctamente grafos con ciclos en todos los
  algoritmos de Graph Analytics.
- **FR-019**: Los resultados de Graph Analytics DEBEN persistirse junto al grafo para
  regenerar variables sin re-ejecutar los algoritmos.

**Generación de variables**

- **FR-020**: El sistema DEBE generar variables por entidad en las 8 categorías:
  Centralidad, Conectividad, Comunidades, Flujo de dinero, Patrones transaccionales,
  Anomalías estructurales, Riesgo de Vecinos y Riesgo Propagado.
- **FR-021**: Las variables de Riesgo de Vecinos y Riesgo Propagado DEBEN calcularse a
  partir de: Alertas PLAFT, ROS, Condición PEP y Casos Investigados; diferenciando el
  origen de la señal en el valor de cada variable.
- **FR-022**: Las variables de riesgo DEBEN incluir al menos: cantidad de contrapartes
  directas con ROS, monto enviado a clientes PEP, monto recibido de clientes con alerta
  PLAFT, proporción de contrapartes investigadas, distancia mínima a cliente con ROS,
  exposición ponderada a señales de riesgo, cantidad de señales diferentes en la comunidad
  y porcentaje del flujo vinculado con clientes sospechosos.
- **FR-023**: Cada variable DEBE exponer: nombre, categoría, valor, datos de origen,
  algoritmo o lógica aplicada, relaciones participantes y transacciones o señales
  generadoras.
- **FR-024**: Las variables DEBEN ser reproducibles dado el mismo grafo y parámetros.

**Persistencia de resultados**

- **FR-025**: El sistema DEBE persistir las variables con versionado explícito en formato
  consumible por modelos externos y por la herramienta de investigación.
- **FR-026**: El sistema DEBE registrar por ejecución: versión del código, criterio de
  selección, versión de datos, parámetros, timestamp, versión del grafo y versión de las
  variables producidas.

**Herramienta de investigación**

- **FR-027**: La herramienta DEBE permitir buscar un cliente sospechoso por identificador.
- **FR-028**: La herramienta DEBE visualizar el subgrafo del cliente: cuentas, productos,
  transferencias, contrapartes, alertas, ROS, PEP, casos y documentos.
- **FR-029**: La herramienta DEBE diferenciar tipos de nodos y relaciones visualmente sin
  depender exclusivamente del color.
- **FR-030**: La herramienta DEBE permitir filtrar relaciones por: período, tipo, monto,
  dirección de transferencia y condición de riesgo de la contraparte; sin reconstruir el
  grafo.
- **FR-031**: La herramienta DEBE mostrar para cada transferencia: dirección, monto,
  fecha, moneda, canal y cuenta contraparte, diferenciando entradas y salidas.
- **FR-032**: La herramienta DEBE indicar para cada contraparte visible sus señales de
  riesgo disponibles (alerta, ROS, PEP, caso).
- **FR-033**: La herramienta DEBE permitir expandir visualmente relaciones de contrapartes
  que ya pertenezcan a la versión persistida del subgrafo y para las cuales el analista
  tenga autorización. La herramienta NO DEBE incorporar nuevos clientes ni consultar
  relaciones fuera del subgrafo autorizado durante una consulta interactiva.
- **FR-034**: La herramienta DEBE mostrar las variables estructurales del cliente con
  valor y explicación de cálculo.
- **FR-035**: La herramienta DEBE permitir consultar el catálogo documental del cliente:
  listar documentos con metadatos y referencia autorizada.
- **FR-036**: La herramienta DEBE mostrar la versión del grafo y fecha de corte de los
  datos en todo momento.
- **FR-037**: La herramienta DEBE permitir exportar un resumen de la consulta en formato
  estructurado.
- **FR-038**: La herramienta NO DEBE exponer datos de clientes fuera del subgrafo
  autorizado ni documentación sin permisos del analista.

**Consultas y trazabilidad**

- **FR-039**: El sistema DEBE permitir consultar todas las relaciones de un cliente dado
  su identificador.
- **FR-040**: El sistema DEBE permitir consultar la explicación de cualquier variable,
  retornando dato de origen, algoritmo, relaciones y señales generadoras.

**Reproducibilidad**

- **FR-041**: El sistema DEBE permitir reconstruir exactamente un subgrafo histórico dado
  el identificador de una ejecución pasada.
- **FR-042**: Las ejecuciones reproducidas con los mismos insumos DEBEN producir
  resultados idénticos.

**Métricas operacionales**

- **FR-043**: El sistema DEBE registrar por ejecución: número de nodos y relaciones por
  tipo, densidad del subgrafo, modularidad global, número de comunidades, distribución
  de grados, tiempos de construcción y generación de variables, y cantidad de variables
  generadas por categoría.

### Key Entities

- **Cliente**: único tipo de nodo para clientes. Cada nodo incluye atributos de rol
  (`es_cliente_objetivo`, `es_contraparte`, `motivos_seleccion`, `nivel_expansion`) y
  resúmenes de señales de riesgo (`tiene_alerta`, `tiene_ros`, `es_pep`, `tiene_caso`). Un
  cliente puede actuar simultáneamente como cliente objetivo y contraparte de otro cliente.
- **Cuenta**: cuenta bancaria; puede tener múltiples titulares.
- **Producto**: producto financiero contratado.
- **Alerta PLAFT**: alerta generada por el sistema PLAFT; nodo con metadatos del evento.
- **ROS**: Reporte de Operación Sospechosa; nodo con metadatos del reporte.
- **Condición PEP**: registro que identifica a un cliente como PEP; incluye vigencia y
  categoría.
- **Caso Investigado**: caso de investigación PLAFT; incluye estado, período y resultado.
- **Documento**: registro del catálogo documental con metadatos y referencia a S3; sin
  contenido ni extracción automática en esta versión.
- **Variable Estructural**: métrica calculada sobre el subgrafo; clasificada por categoría,
  versionada, trazable y diferenciada por tipo de señal en las categorías de riesgo.
- **Ejecución**: instancia completa del pipeline; incluye criterio de selección, código,
  datos, parámetros, grafo, variables y métricas operacionales.

---

## Seguridad y Auditoría

- **SA-001**: La herramienta DEBE operar exclusivamente dentro de la infraestructura
  autorizada por el banco. ESTÁ PROHIBIDO el acceso desde redes externas no autorizadas.
- **SA-002**: El sistema DEBE registrar por cada acción del analista: usuario, cliente
  consultado, timestamp, filtros utilizados, versión del grafo, versión de datos,
  documentos consultados y exportaciones realizadas.
- **SA-003**: El sistema DEBE aplicar el principio de mínimo privilegio: cada analista
  accede únicamente al subgrafo y documentos para los que posee autorización.
- **SA-004**: La herramienta NO DEBE exponer datos de clientes fuera del subgrafo
  autorizado ni información documental sin permisos.
- **SA-005**: Los intentos de consultar clientes o documentos no autorizados DEBEN
  registrarse en el log de auditoría y generar respuesta de acceso denegado.
- **SA-006**: El repositorio NO DEBE contener credenciales, tokens, secretos ni datos
  sensibles de producción.
- **SA-007**: Los datos para desarrollo y pruebas DEBEN ser sintéticos o anonimizados.

---

## Requisitos No Funcionales

- **RNF-001 Escalabilidad**: el sistema DEBE operar a escala de millones de transacciones
  sin degradación que impida su uso en producción.
- **RNF-002 Reproducibilidad**: toda ejecución DEBE poder replicarse con los mismos
  insumos y producir los mismos resultados.
- **RNF-003 Trazabilidad**: todo nodo, relación, variable y consulta DEBE mantener
  referencia directa al dato de origen.
- **RNF-004 Tolerancia a fallos**: los errores NO DEBEN propagarse silenciosamente; el
  sistema DEBE fallar de forma controlada con registro del motivo.
- **RNF-005 Observabilidad**: toda ejecución DEBE generar logs estructurados y métricas
  operacionales consultables.
- **RNF-006 Explicabilidad**: toda variable DEBE poder justificarse ante un analista o
  auditor sin conocimiento técnico del sistema.
- **RNF-007 Mantenibilidad**: cada capa funcional DEBE poder modificarse independientemente
  sin afectar otras capas no adyacentes.
- **RNF-008 Versionado**: el grafo, los datasets y las variables DEBEN estar versionados
  para identificar y recuperar cualquier estado pasado.
- **RNF-009 Extensibilidad**: la arquitectura DEBE permitir incorporar nuevos tipos de
  nodos, relaciones, datasets, categorías de variables y profundidades de expansión sin
  rediseño.
- **RNF-010 Seguridad**: el sistema DEBE implementar controles de acceso basados en el
  principio de mínimo privilegio para datos y documentos.
- **RNF-011 Auditoría**: toda interacción del analista DEBE quedar registrada de forma
  inmutable y consultable.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: El sistema construye un subgrafo completo a partir de la población de
  clientes sospechosos y los datasets definidos sobre datos sintéticos de prueba.
- **SC-002**: Las 8 categorías de variables están disponibles para el 100% de los
  clientes sospechosos del subgrafo.
- **SC-003**: Toda variable puede ser explicada indicando datos de origen, algoritmo,
  relaciones y señales participantes, verificable por un analista PLAFT.
- **SC-004**: Toda ejecución es reproducible: mismos insumos y parámetros producen
  resultados idénticos.
- **SC-005**: Los errores críticos de calidad detienen el proceso en el 100% de los casos
  y generan registro de error legible.
- **SC-006**: El sistema registra metadatos completos de ejecución en el 100% de los
  casos.
- **SC-007**: Las variables son consumibles por un proceso externo de scoring en formato
  estándar sin transformación adicional.
- **SC-008**: El sistema opera correctamente ante los 12 casos borde definidos sin fallos
  no controlados.
- **SC-009**: El 100% de los clientes sospechosos de prueba puede consultarse desde la
  herramienta de investigación.
- **SC-010**: Cada cliente muestra correctamente sus relaciones directas, señales de
  riesgo y documentos disponibles.
- **SC-011**: Las transferencias visualizadas coinciden con los registros fuente en monto,
  fecha, dirección, moneda y canal.
- **SC-012**: Alertas, ROS, PEP y casos están vinculados correctamente a sus clientes.
- **SC-013**: Los documentos aparecen con referencia, tipo, estado y metadatos completos.
- **SC-014**: El analista puede aplicar todos los filtros definidos sin reconstruir el
  grafo.
- **SC-015**: Toda entidad y relación mantiene trazabilidad al registro de origen.
- **SC-016**: Toda consulta del analista queda registrada con los campos de auditoría
  requeridos.
- **SC-017**: El sistema rechaza y registra los intentos de acceso a información no
  autorizada.
- **SC-018**: La herramienta permite explicar las variables de cualquier cliente
  sospechoso en términos comprensibles para un analista.

---

## Exclusiones del MVP

Las siguientes capacidades están explícitamente fuera del alcance de esta versión:

- GraphRAG y recuperación aumentada por grafo.
- Large Language Models (LLM) y embeddings.
- OCR, extracción automática de texto y análisis semántico de documentos.
- Neo4j u otras bases de datos de grafos externas.
- Análisis multimodal.
- Aplicación pública o exposición a internet.
- Entrenamiento de modelos supervisados (la plataforma genera features; el entrenamiento
  es responsabilidad de los equipos de modelos).

---

## Assumptions

- Los datasets de entrada estarán disponibles en Amazon S3 en la infraestructura aprobada.
- Los identificadores de cliente, cuenta y transacción son únicos y estables entre
  datasets.
- Las señales de riesgo (alertas, ROS, PEP, casos) provienen de fuentes autorizadas; el
  MVP no valida la veracidad de las señales, solo las integra como input.
- La lista de clientes objetivo provista por PLAFT se considera input válido de selección.
- Los documentos del catálogo existen en las ubicaciones referenciadas en S3; el MVP
  registra la referencia y metadatos, no verifica la integridad del contenido.
- Las variables calculadas no constituyen por sí solas una decisión de riesgo; son inputs
  para modelos supervisados y para el juicio del analista.
- La herramienta de investigación será desplegada en infraestructura interna autorizada;
  la elección tecnológica definitiva se documentará mediante un ADR.
- El MVP operará sobre datos sintéticos o anonimizados durante el desarrollo. El
  procesamiento de datos reales requiere despliegue en la infraestructura AWS aprobada.
- Los permisos de acceso de analistas a clientes y documentos serán provistos por el
  sistema de control de acceso del banco; el MVP los consume pero no los gestiona.
