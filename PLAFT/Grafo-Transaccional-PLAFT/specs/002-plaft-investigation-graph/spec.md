# Feature Specification: Grafo Transaccional para Investigacion PLAFT

**Feature Branch**: `[002-plaft-investigation-graph]`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Construir un grafo transaccional para investigacion PLAFT cuyo entregable principal sea un caso investigado con evidencia reproducible, manteniendo las variables como capacidad secundaria y reutilizando infraestructura existente cuando sea compatible con la constitucion 4.0.0."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Investigar un caso con evidencia trazable (Priority: P1)

Como analista PLAFT, necesito iniciar una investigacion sobre un sujeto y recorrer sus relaciones transaccionales para consolidar evidencia verificable que sustente un caso investigado.

**Why this priority**: Este es el entregable principal de negocio y define el valor directo para investigacion PLAFT.

**Independent Test**: Puede probarse de forma independiente cargando un caso, ejecutando la investigacion y verificando que el resultado incluya hallazgos y evidencia trazable hasta la fuente.

**Acceptance Scenarios**:

1. **Given** un sujeto investigado con datos fuente disponibles, **When** el analista ejecuta la investigacion del caso, **Then** obtiene un caso investigado con relaciones relevantes y evidencia verificable.
2. **Given** hallazgos de patrones sobre el grafo, **When** se documenta el caso, **Then** cada hallazgo queda vinculado con su soporte y contexto de analisis.

---

### User Story 2 - Documentar y cerrar una investigacion (Priority: P1)

Como analista PLAFT, necesito registrar mis hallazgos, observaciones, evidencia y conclusion para obtener un expediente reproducible de la investigacion realizada.

**Why this priority**: La investigacion no finaliza con la deteccion automatica de patrones. El resultado de negocio requiere que el analista pueda interpretar los hallazgos, documentar sus conclusiones y conservar la evidencia que sustenta el caso.

**Independent Test**: Puede probarse de forma independiente tomando una investigacion con hallazgos y evidencia disponibles, registrando la interpretacion y conclusion del analista y verificando que el expediente resultante conserve toda la trazabilidad.

**Acceptance Scenarios**:

1. **Given** una investigacion con hallazgos y evidencia, **When** el analista documenta su interpretacion y conclusion, **Then** el sistema conserva el expediente del caso con trazabilidad de evidencia, usuario, fechas, parametros y fuentes utilizadas.

---

### User Story 3 - Explorar relaciones y patrones para soporte analitico (Priority: P2)

Como analista PLAFT, necesito explorar conexiones, cadenas y concentraciones de transacciones para entender el comportamiento de la red y priorizar lineas de investigacion.

**Why this priority**: Permite convertir datos dispersos en contexto investigable y acelera el analisis del caso.

**Independent Test**: Puede probarse consultando una entidad y validando que el sistema devuelve conexiones y patrones relevantes para analisis.

**Acceptance Scenarios**:

1. **Given** un conjunto de entidades y transacciones validado, **When** el analista consulta relaciones del sujeto, **Then** visualiza conexiones y patrones con contexto temporal y de negocio.
2. **Given** varios patrones detectados, **When** el analista prioriza una hipotesis, **Then** puede sustentar la priorizacion con evidencia asociada.

---

### User Story 4 - Reutilizar resultados para monitoreo y modelos (Priority: P3)

Como equipo de analitica y riesgo, necesitamos reutilizar de forma selectiva resultados estructurales del grafo para enriquecer procesos de monitoreo y modelamiento sin desplazar el objetivo investigativo.

**Why this priority**: Aporta valor incremental y continuidad con capacidades existentes sin alterar el foco de negocio.

**Independent Test**: Puede probarse verificando que las metricas seleccionadas del grafo quedan disponibles como salida reutilizable junto con su trazabilidad.

**Acceptance Scenarios**:

1. **Given** un caso investigado y metricas estructurales calculadas, **When** se solicita reutilizacion analitica, **Then** solo las metricas seleccionadas y trazables se publican como artefactos reutilizables.

---

### Edge Cases

- Que ocurre cuando el sujeto investigado no tiene relaciones transaccionales en el periodo analizado.
- Como se maneja evidencia contradictoria entre distintas fuentes para un mismo hecho.
- Que sucede cuando una investigacion requiere datos fuera de la ventana temporal permitida.
- Como responde el sistema cuando faltan atributos criticos para interpretar un patron detectado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir registrar una investigacion asociada a un sujeto, motivo y periodo de analisis.
- **FR-002**: El sistema DEBE construir una representacion integrada de entidades y relaciones transaccionales relevantes para PLAFT.
- **FR-003**: El sistema DEBE permitir explorar conexiones directas e indirectas entre entidades para una investigacion.
- **FR-004**: El sistema DEBE identificar patrones transaccionales relevantes para investigacion (por ejemplo cadenas, ciclos, hubs, intermediarios y concentraciones).
- **FR-005**: El sistema DEBE vincular cada hallazgo con evidencia verificable y trazable hasta su origen.
- **FR-006**: El sistema DEBE conservar para cada evidencia el contexto de analisis (periodo, parametros, fecha de ejecucion y version de resultados).
- **FR-007**: El sistema DEBE producir un expediente de caso investigado que consolide sujeto, hallazgos y evidencia, y DEBE permitir al analista registrar su interpretacion, observaciones, conclusion y resultado del caso.
- **FR-008**: El sistema DEBE distinguir explicitamente entre dato fuente, hecho representado, senal analitica, evidencia e interpretacion del analista.
- **FR-009**: El sistema DEBE detener y reportar la ejecucion cuando la calidad de datos incumpla reglas criticas definidas para investigacion.
- **FR-010**: El sistema DEBE permitir incorporar nuevas fuentes de datos relevantes sin redefinir el alcance funcional del proceso investigativo.
- **FR-011**: El sistema DEBE permitir generar salidas estructurales reutilizables para analitica avanzada como capacidad secundaria, manteniendo trazabilidad.
- **FR-012**: El sistema DEBE registrar metadatos suficientes para reproducir un caso investigado y sus evidencias.

### Key Entities *(include if feature involves data)*

- **Caso Investigado**: Resultado principal de negocio que agrupa sujeto, hipotesis, hallazgos, evidencia, conclusiones y estado del caso.
- **Sujeto Investigado**: Persona o entidad foco de la investigacion PLAFT, con identificadores y contexto de riesgo.
- **Entidad de Grafo**: Nodo relevante para investigacion (cliente, cuenta, contraparte, alerta, documento u otra entidad aplicable).
- **Relacion Transaccional**: Vinculo entre entidades que representa un hecho financiero con atributos de temporalidad y contexto.
- **Hallazgo Analitico**: Resultado de analisis sobre estructura o flujo de la red que puede apoyar una hipotesis investigativa.
- **Evidencia**: Soporte verificable asociado a hallazgos, con trazabilidad al origen y metadatos de reproduccion.
- **Artefacto Reutilizable**: Salida estructural derivada del grafo para uso analitico complementario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los casos investigados generados incluye evidencia trazable para cada hallazgo relevante.
- **SC-002**: Al menos el 95% de las investigaciones solicitadas se completan con un resultado de caso en una sola ejecucion operativa sin reproceso manual.
- **SC-003**: El 100% de los resultados de investigacion permiten reconstruir insumos, periodo y parametros utilizados.
- **SC-004**: Al menos el 90% de los analistas participantes en la validacion considera que la salida consolida de manera suficiente las relaciones, hallazgos y evidencias disponibles en las fuentes integradas al sistema para apoyar la investigacion.
- **SC-005**: El 100% de las senales reportadas en un caso queda claramente clasificado como senal analitica y no como conclusion definitiva.
- **SC-006**: Al menos el 80% de los casos priorizados por analistas muestra reduccion del tiempo de armado de evidencia frente al proceso base vigente.

## Assumptions

- Existe una definicion institucional de caso investigado y de criterios minimos de evidencia aceptable.
- Los analistas PLAFT cuentan con autorizacion para consultar las fuentes requeridas para investigacion.
- El proyecto reutiliza capacidades ya disponibles de ingesta, validacion y trazabilidad cuando sean compatibles con la constitucion vigente.
- La priorizacion inicial cubre fuentes principales (clientes, cuentas, transferencias, alertas y casos) y permite extensiones posteriores.
- Las salidas reutilizables para analitica avanzada son complementarias y no sustituyen el entregable principal de caso investigado.
