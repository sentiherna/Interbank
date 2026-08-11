# Research: Grafo Transaccional para Investigacion PLAFT

**Feature**: `002-plaft-investigation-graph`  
**Date**: 2026-08-10  
**Plan**: [plan.md](plan.md)

---

## Decision 1: Mantener arquitectura existente y extender por dominios investigativos

**Decision**

Reutilizar la base actual en `src/graph_plaft/` (config, ingestion, validation,
observability, schemas y tests) y extenderla con dominios nuevos `patterns`,
`investigation` y `evidence`.

**Rationale**

- Evita duplicidad funcional en ingesta, validacion y mapeo.
- Conserva estabilidad de componentes ya validados.
- Alinea el esfuerzo nuevo al objetivo de negocio: caso investigado con evidencia.

**Alternatives considered**

- Crear una nueva raiz de codigo (`src/plaft_graph/`): descartado por duplicacion y riesgo
  de deriva de comportamiento.
- Reescribir pipeline completo con nuevo naming: descartado por costo alto sin ganancia.

---

## Decision 2: Flujo principal investigacion-first

**Decision**

Adoptar como flujo oficial:

Fuentes -> Ingesta -> Validacion -> Mapeo -> Grafo -> Persistencia -> Analytics ->
Patrones/Senales -> Investigacion -> Hallazgos -> Evidencia -> Interpretacion -> Expediente.

**Rationale**

- Cumple el principio rector de la constitucion 4.0.0.
- Evita sesgo de diseno hacia variables como salida principal.
- Facilita auditabilidad y explicabilidad de decisiones analiticas.

**Alternatives considered**

- Flujo centrado en variables + Feature Store: descartado por desalineacion con proposito.
- Flujo sin paso explicito de hallazgos/evidencia: descartado por perdida de trazabilidad.

---

## Decision 3: Feature Store como capacidad secundaria y opcional

**Decision**

Mantener publicacion a Feature Store solo para metricas seleccionadas con caso de uso
explicito de modelamiento.

**Rationale**

- La plataforma debe operar investigacion completa incluso sin Feature Store.
- Reduce acoplamiento con componentes de ML no necesarios para cerrar casos.

**Alternatives considered**

- Publicar todas las metricas del grafo: descartado por sobrecarga y bajo valor incremental.
- Deshabilitar totalmente Feature Store: descartado porque existe valor analitico secundario.

---

## Decision 4: Integracion progresiva de datos reales sin reescritura de logica

**Decision**

Usar la misma interfaz de carga y validacion para CSV locales controlados y para S3.
Formalizar mapeos fisico-conceptuales por fuente, iniciando por `clientes.csv`
(`cod_cli -> cliente_id`).

**Rationale**

- Permite evolucion local -> AWS con bajo riesgo.
- Evita bifurcacion de codigo por entorno.
- Mejora control de calidad contractual en cada nueva fuente.

**Alternatives considered**

- Pipeline separado para datos reales: descartado por duplicidad.
- Migrar directo todo a S3 desde el inicio: descartado por alto riesgo operativo temprano.

---

## Decision 5: Modelar explicitamente CasoInvestigado, HallazgoAnalitico y Evidencia

**Decision**

Introducir entidades de dominio investigativo como primer ciudadano del modelo de datos
funcional del sistema.

**Rationale**

- El expediente es el entregable principal de negocio.
- Hallazgos y evidencia permiten separar senal automatica de conclusion humana.
- Fortalece reproducibilidad y auditoria.

**Alternatives considered**

- Guardar solo resultados agregados de analytics: descartado por falta de contexto.
- Usar casos historicos como unico repositorio de casos: descartado por no cubrir casos
  nuevos creados dentro de la plataforma.

---

## Decision 6: Mantener AWS como plataforma oficial con desarrollo local reproducible

**Decision**

Disenar la ejecucion oficial en AWS (S3, SageMaker Processing, Glue, Athena, MLflow
compatible) y conservar modo local para validacion rapida con sinteticos.

**Rationale**

- Cumple principios de plataforma autorizada.
- Habilita iteracion tecnica rapida sin exponer datos sensibles.

**Alternatives considered**

- Solo AWS sin modo local: descartado por friccion de desarrollo.
- Solo local con emulacion: descartado por brecha con operacion real.

---

## Decision 7: Estrategia de pruebas incremental sobre base existente

**Decision**

Extender la suite actual con pruebas de investigacion, hallazgos, evidencia y cierre de
caso, manteniendo checks de calidad (`ruff`, `mypy`, `pytest`).

**Rationale**

- Aprovecha cobertura existente en contratos y validacion.
- Reduce regresiones durante incorporacion de dominios nuevos.

**Alternatives considered**

- Crear suite separada solo para feature 002: descartado por duplicidad y fragmentacion.

---

## Open items gestionados como ADR (no bloqueantes para plan)

- Tecnologia final de visualizacion interactiva para analista (mantener ADR si requiere
  validacion corporativa adicional).
- Estrategia de aceleracion para algoritmos de alto costo en grafos muy grandes.
- Politica operativa de retencion de expedientes y evidencia en produccion.

No quedan items marcados como NEEDS CLARIFICATION para cerrar Fase 0 de planificacion.

---

## Nota de ejecucion Phase 1 (T006)

Se confirma que la implementacion de la feature 002 no debe duplicar infraestructura ya
existente de proyecto 001. Las adaptaciones de Phase 1 se limitan a:

- configuracion de fuentes reales progresivas;
- ampliacion de mapeos fisico-conceptuales para fuentes prioritarias;
- actualizacion documental de reutilizacion.

No se aprueba crear una segunda implementacion de ingesta, validacion o mapeo.
