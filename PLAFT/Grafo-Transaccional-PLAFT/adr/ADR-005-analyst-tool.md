# ADR-005: Tecnología para la Herramienta de Investigación del Analista

**Estado**: Propuesto | **Fecha**: 2026-08-06

---

## Contexto

El MVP requiere una herramienta interna que permita a analistas PLAFT investigar clientes
sospechosos mediante una interfaz visual. La herramienta debe cumplir:

- Operar exclusivamente en infraestructura interna autorizada (no pública).
- Autenticar y autorizar a los analistas.
- Visualizar subgrafos con nodos y relaciones diferenciados.
- Filtrar por múltiples criterios.
- Registrar toda acción en log de auditoría.
- Consumir artefactos S3 persistidos, no reconstruir el grafo en tiempo real.
- Ser mantenible por el equipo de Data Science del banco.

---

## Opciones evaluadas

### Opción A: Streamlit + SageMaker Studio App

Aplicación Streamlit desplegada como SageMaker Studio Application o como job de
SageMaker Processing de larga duración.

| Criterio | Evaluación |
|----------|-----------|
| Compatibilidad AWS | Alta (SageMaker Studio Apps o instancias EC2 internas) |
| Desarrollo | Python puro; curva baja para el equipo Data Science |
| Visualización de grafos | pyvis, streamlit-agraph, networkx (subgrafos pequeños) |
| Autenticación | IAM SSO + SageMaker Studio IAM; requiere configuración adicional |
| Autorización por cliente | Implementada en código (access_control.py) |
| Auditoría | Implementada en código (audit_log.py) |
| Diferenciación nodos/relaciones | Forma + etiqueta + color en pyvis |
| Despliegue | SageMaker Studio App o instancia EC2 interna |
| Mantenimiento | Equipo Python existente |
| Restricción de acceso a internet | Cumple si desplegada en VPC privada |

### Opción B: Aplicación web Flask/FastAPI + JavaScript (D3.js / Cytoscape.js)

Backend Python con API REST + frontend JavaScript para visualización de grafos.

| Criterio | Evaluación |
|----------|-----------|
| Compatibilidad AWS | Alta (ECS, EC2, o Lambda + S3) |
| Desarrollo | Requiere desarrollo frontend adicional |
| Visualización de grafos | Cytoscape.js o D3.js: muy rica y personalizable |
| Autenticación | Cognito, Active Directory u otro IdP corporativo |
| Auditoría | En backend Python |
| Despliegue | Contenedor Docker en ECS o EC2 interno |
| Mantenimiento | Requiere habilidades frontend + backend |
| Tiempo al MVP | Mayor que Streamlit |

### Opción C: Amazon QuickSight Embedded

Dashboard de BI embebido para visualización de datos.

| Criterio | Evaluación |
|----------|-----------|
| Compatibilidad AWS | Nativa |
| Visualización de grafos | Muy limitada (no es un viz de grafos) |
| Filtros interactivos | Estándar de BI |
| Trazabilidad individual de nodos | No disponible nativamente |
| Adecuación para investigación de grafos | Baja |

---

## Decisión

**Opción A: Streamlit** como tecnología para el MVP de la herramienta de investigación.

**Justificación**:
- El equipo posee habilidades Python; no requiere contratar skills de frontend.
- Streamlit permite llegar al MVP funcional en menor tiempo.
- La visualización de subgrafos pequeños (< 500 nodos en pantalla) con pyvis o
  streamlit-agraph es adecuada para el caso de uso del analista.
- El despliegue en VPC privada garantiza que la herramienta no sea accesible desde
  internet.
- Streamlit sobre SageMaker Studio App o instancia EC2 interna es compatible con la
  infraestructura AWS aprobada.

**Para versiones futuras**: si la herramienta requiere visualizaciones más ricas o mayor
rendimiento, migrar a Opción B (Flask + Cytoscape.js) sin necesidad de reescribir la
lógica de negocio (que permanece en módulos Python compartidos).

---

## Restricciones de despliegue

- La aplicación debe estar en una VPC privada sin exposición a internet.
- El acceso requiere autenticación corporativa (SSO o IAM).
- Los roles IAM de la aplicación deben tener permisos de mínimo privilegio (solo lectura
  sobre los buckets S3 autorizados y las tablas Glue correspondientes).
- La herramienta no debe tener permisos de escritura sobre datos del grafo.

---

## Pendiente de validación (Fase 0)

- Confirmar mecanismo de autenticación corporativa disponible (SSO/SAML/Cognito).
- Validar si SageMaker Studio Apps permite despliegue de Streamlit en la cuenta del banco.
- Confirmar que la VPC permite acceso de analistas a la aplicación desde sus estaciones.

---

## Consecuencias

- La herramienta se construye como un módulo Python separado (`src/plaft_graph/tool/`).
- La lógica de acceso a datos (consultas S3, Athena) está en módulos compartidos,
  reutilizables independientemente de la tecnología de UI.
- Si en el futuro se migra a Flask/Cytoscape, solo la capa de presentación (`tool/app.py`)
  necesita reescribirse.

---

## Referencias

- plan.md Capa 12 (Herramienta de Investigación)
- spec.md FR-027 a FR-038
- research.md Decisión 3
