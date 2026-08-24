# CLAUDE.md — Plataforma de ML de Nave · **MVP**

> Contexto operativo del repositorio. Claude Code lo lee al iniciar cada sesión. Lo que está acá es
> **regla**, no sugerencia. Si una regla queda desactualizada, se corrige en el mismo PR.
>
> | | |
> |---|---|
> | Alcance | **MVP** — no es la plataforma final (ver §3) |
> | Autoría de la arquitectura | **Propuesta de Nubiral.** Nave no tiene plataforma de ML armada. |
> | Última revisión | 2026-08-18 |
> | `[DEFINIR]` | marca lo que hay que cerrar con Nave |

---

## 1. Situación real de partida

Nave se está desacoplando de Grupo Galicia y arma su plataforma de datos propia en AWS.

**En Machine Learning, hoy Nave tiene modelos funcionando y no tiene plataforma que los sostenga.**
Los modelos viven en notebooks y se ejecutan a mano. No existe una zona de experimentación, ni
pipelines, ni registro de modelos, ni ambiente definido. La arquitectura de este repositorio es
**nuestra propuesta**, no un diseño heredado: podemos y debemos mejorarla con lo que vayamos
aprendiendo.

### 1.1 Por qué esto es urgente y no solo deseable

Un modelo que se ejecuta abriendo un notebook a mano tiene cuatro problemas que no se ven hasta que
duelen:

| Problema | Consecuencia real |
|---|---|
| **No es reproducible** | Nadie puede responder con qué datos y con qué código se generó una predicción de hace tres meses. En una entidad financiera, esa pregunta llega. |
| **Depende de una persona** | Si quien corre el notebook se va de vacaciones o de la empresa, el modelo deja de funcionar. Es riesgo de continuidad operativa, no un problema técnico. |
| **No es auditable** | No hay traza de ejecución, ni versionado, ni aprobación. Es hallazgo de auditoría casi asegurado. |
| **No escala** | Cada modelo nuevo multiplica el trabajo manual en lugar de aprovechar el anterior. |

> Este es el argumento central frente a Nave. No estamos proponiendo modernizar por gusto: estamos
> sacando de la ejecución manual algo que ya está en producción de hecho.

### 1.2 Lo que todavía no sabemos

Tres incógnitas que **el descubrimiento de la Semana 1 tiene que cerrar** (§6):

1. **Qué modelos son.** Si alguno participa en decisiones de crédito o riesgo, cambia el encuadre
   regulatorio (§2.3) y el orden de migración.
2. **Dónde y cómo corren hoy.** En la cuenta de Nave o todavía del lado de Galicia. Si es lo
   segundo, hay un deadline externo que manda sobre el plan.
3. **Cuántos son.** Define cuánto pesa el argumento de escala y qué tan agresiva conviene ser con la
   fábrica de agentes.

**No inventar respuestas a estas preguntas.** Mientras no estén cerradas, se marcan como
`[DEFINIR]` en cualquier documento o código que dependa de ellas.

---

## 2. Estrategia: migración iso-funcional

La decisión de diseño más importante del MVP, y la que hay que defender frente a cualquier presión
por "aprovechar y mejorar el modelo":

> **Migramos la plomería, no el modelo.** El modelo migrado debe producir **las mismas predicciones**
> que el notebook actual sobre los mismos datos. Cero cambios de lógica, features o hiperparámetros
> durante la migración.

### 2.1 Por qué

- **Reduce el riesgo regulatorio a casi cero.** No es un modelo nuevo que requiere validación y
  aprobación: es el mismo modelo con mejor infraestructura. Si alguno resulta ser de riesgo
  crediticio, esto es lo que salva el MVP.
- **Hace el éxito verificable.** "¿Funcionó la migración?" tiene una respuesta binaria: las
  predicciones coinciden o no coinciden.
- **Separa los debates.** Mejorar el modelo es una conversación legítima — pero después, y con la
  plataforma que permite compararlo contra el actual de forma limpia.

### 2.2 El test de paridad

Es **el entregable central de cada migración**, no un extra:

1. Se toma un conjunto de datos de referencia congelado.
2. Se ejecuta el notebook original y se guardan sus predicciones.
3. Se ejecuta el pipeline migrado sobre exactamente los mismos datos.
4. Se comparan predicción por predicción.

**Criterio de aceptación:** coincidencia exacta, o dentro de una tolerancia numérica documentada y
justificada (diferencias de versión de librería, orden de operaciones en punto flotante). Cualquier
divergencia sistemática es un bug de migración, no "ruido".

Si el test de paridad no pasa, **la migración no está terminada** — por más que el pipeline corra
lindo de punta a punta.

### 2.3 Riesgo regulatorio

Nave opera en el sistema financiero argentino: aplican la **Ley 25.326 de Protección de Datos
Personales** y la normativa **BCRA de riesgo tecnológico y ciberseguridad** (auditabilidad,
segregación de ambientes, gestión de accesos).

La migración iso-funcional mantiene el perfil de riesgo del modelo sin cambios, que es exactamente
el argumento a usar con Compliance. Pero **si algún modelo participa en decisiones que afectan al
cliente** (crédito, límites, condiciones), hay que confirmar antes de tocarlo si existe un comité de
modelos con potestad de aprobación.

> `[DEFINIR]` Validar con Riesgos/Compliance de Nave: ¿qué modelos están alcanzados y quién aprueba?

---

## 3. Alcance del MVP

### ✅ Dentro

- **Inventario y assessment** de los modelos que hoy corren en notebooks
- **Zona de experimentación**: dominio de SageMaker Studio, Spaces self-service, una cuenta (`dev`)
- **Un modelo migrado end-to-end**: pipeline reproducible, agendado, **con test de paridad aprobado**
- Registro del modelo y gate de calidad
- Tracking de experimentos (MLflow)
- 4 subagentes de Claude Code funcionando (§8.1)

### ❌ Fuera — **no lo construyas, no lo propongas**

Multi-cuenta dev/stg/prod · CI/CD completo · Feature Store · Model Monitor y detección de drift ·
explicabilidad automatizada · A/B testing · re-entrenamiento automático · **mejoras al modelo** ·
integración con Lake Formation.

Va al backlog de §9. Es buena arquitectura y hay que hacerlo — pero ahora mata la velocidad.

### ⚠️ Deuda técnica asumida conscientemente

No es olvido, es decisión. Se documenta para que nadie se sorprenda después:

| Deuda | Mitigación durante el MVP | Cuándo se paga |
|---|---|---|
| Sin aislamiento de red (VPC-only) | Solo datos muestreados y anonimizados. **Ningún dato con PII entra al ambiente.** | Antes de que el modelo migrado tome decisiones reales. Innegociable. |
| Sin ambiente productivo separado | El notebook original sigue siendo la fuente de verdad hasta que la paridad esté aprobada. **No se apaga nada.** | Antes del corte definitivo. |
| Sin monitoreo de drift | Ventana corta, con el modelo original disponible como respaldo. | Fase 2. |
| Sin explicabilidad formalizada | La migración no cambia el perfil del modelo (§2). | Antes de cualquier modelo nuevo o modificado. |

### 3.1 Cómo elegir el primer modelo a migrar

Del inventario, el mejor candidato **no es el más importante**: es el que maximiza aprendizaje y
minimiza riesgo.

Buscar: dolor operativo alto (se corre seguido y a mano), lógica acotada, dato accesible, y **bajo
riesgo regulatorio**. Evitar como primer caso: el modelo más crítico del negocio, o uno que participe
en decisiones de crédito — esos se migran segundos, cuando el camino ya está probado.

---

## 4. Arquitectura propuesta

### 4.1 El flujo

```
Notebook actual  ──arqueología──> especificación del modelo (features, lógica, dependencias)
                 └──ejecución──>  predicciones de referencia ──┐
                                                               │
Athena / S3 (dataset versionado)                               │
   └─> Studio Space          ← exploración                     │
   └─> SageMaker Pipeline    ← ejecución reproducible          │
         ProcessingStep      → train / validation / test        │
         TrainingStep        → modelo                           │
         TransformStep       → predicciones                     │
         ProcessingStep      → métricas + TEST DE PARIDAD ◄─────┘
         ConditionStep       → ¿paridad OK y métricas OK? ── no ──> FIN, no se registra
                │ sí
         ModelStep           → Model Registry
                              └─> inferencia agendada (§4.3)

Transversal: IAM Identity Center · KMS · Secrets Manager · MLflow · CloudWatch · EventBridge
```

**Tres piezas que existen por ser una migración** y que no estarían en una plataforma greenfield:

1. **Arqueología del notebook** — extraer la especificación de lo que hoy corre, antes de tocarlo.
2. **Test de paridad** como paso del pipeline (§2.2).
3. **Agendamiento (EventBridge)** — hoy alguien lo ejecuta a mano cada semana; el pipeline necesita
   un disparador y una alerta cuando falla.

### 4.2 El gate de calidad se define contra el modelo actual

Ventaja poco obvia de migrar en lugar de empezar de cero: **no hay que inventar un umbral**. El
modelo que corre hoy es el baseline. El criterio es "no empeorar", que es objetivo, defendible ante
negocio y no requiere una discusión de tres semanas.

### 4.3 Inferencia: replicar la cadencia actual, no rediseñarla

Si el notebook se corre una vez por semana y el resultado se deja en una tabla, **el pipeline hace
exactamente eso** (batch transform + EventBridge). No se levanta un endpoint real-time salvo que
exista un requerimiento de latencia por escrito de negocio. Rediseñar el consumo durante la
migración rompe la iso-funcionalidad y agrega riesgo gratis.

---

## 5. Stack

| Capa | Herramienta |
|---|---|
| IaC | **AWS CDK (Python)** — decisión tomada, no mezclar con Terraform |
| Plataforma ML | **Amazon SageMaker AI**: Studio (Domain + Spaces), Pipelines, Training, Processing, Model Registry |
| Agendamiento | **EventBridge Scheduler** disparando el pipeline |
| Tracking | **MLflow gestionado en SageMaker** |
| Lenguaje | **Python 3.11+** |
| Datos | **Parquet** entre pasos (nunca CSV), consulta vía **Athena** |
| Testing | `pytest`, `ruff` (format + lint) |
| Dependencias | `[DEFINIR]` `uv` o `poetry`, con lockfile commiteado |

### 5.1 Frontera CDK ↔ SageMaker SDK (causa #1 de código roto — leer)

- **CDK define infraestructura que persiste**: Domain, Spaces, buckets, roles IAM, KMS, Model
  Package Groups, schedule de EventBridge.
- **El SageMaker Python SDK define el pipeline de ML**: steps, estimadores, lógica. Se versiona como
  código Python y se hace `upsert()`. **No se define en CDK.**
- **El puente son los parámetros**: CDK exporta nombres/ARNs a SSM Parameter Store y el pipeline los
  lee. **Nunca hardcodear un ARN.**

### 5.2 Reproducir el entorno del notebook original

Riesgo específico de migración: el notebook corre con las versiones que tenía instaladas quien lo
escribió. Antes de migrar, **capturar las versiones exactas de las librerías** y pinnearlas. Una
diferencia de versión de `scikit-learn` puede cambiar las predicciones lo suficiente como para que
el test de paridad falle sin que haya un error de lógica.

---

## 6. El descubrimiento (Semana 1)

Primer entregable del MVP, y el que destraba todo lo demás. Por cada modelo encontrado:

| Campo | Qué registrar |
|---|---|
| Nombre y propósito | Qué decide o informa, y quién lo consume |
| Criticidad | Qué pasa si deja de correr una semana |
| **Riesgo regulatorio** | ¿Participa en decisiones que afectan a un cliente? |
| Ejecución | Quién lo corre, con qué frecuencia, cuánto tarda, dónde |
| Ubicación | Cuenta de Nave o infraestructura de Galicia (¿hay deadline?) |
| Datos de entrada | Fuentes, accesibles desde Athena o no |
| Dependencias | Librerías y versiones |
| Salida | Dónde se deja el resultado y quién lo lee |
| Dueño | Persona de referencia |

**Resultado:** un inventario priorizado y la elección justificada del primer modelo a migrar. Es un
entregable con valor propio aunque el MVP se frenara ahí.

---

## 7. Cómo trabajamos

### 7.1 El notebook original es evidencia, no base de código

Durante la migración el notebook cumple tres funciones: documenta la lógica, genera las predicciones
de referencia, y **sigue corriendo en producción hasta que la paridad esté aprobada**. No se
modifica, no se refactoriza y no se apaga antes de tiempo.

### 7.2 El camino de la migración

```
Notebook original
   ├─ 1. Arqueología     → especificación escrita de qué hace (agente + revisión humana)
   ├─ 2. Congelamiento   → dataset de referencia + predicciones de referencia
   ├─ 3. Modularización  → ml/src/<modelo>/ {preprocessing, train, evaluate}.py + tests
   ├─ 4. Pipeline        → ml/pipelines/<modelo>/pipeline.py con @step
   ├─ 5. Paridad         → comparación contra las predicciones de referencia
   └─ 6. Agendamiento    → EventBridge + alerta de fallo
```

Preferir el decorador `@step` del SageMaker Python SDK: reduce mucho la fricción y mantiene el
código legible.

### 7.3 Estructura del repo

```
.
├── CLAUDE.md
├── .claude/{agents,commands,settings.json}
├── infra/                        # AWS CDK (Python)
│   ├── app.py
│   └── stacks/{security,studio,data,serving}_stack.py
├── ml/
│   ├── pipelines/<modelo>/       # pipeline.py + config.yaml
│   ├── src/<modelo>/             # preprocessing.py, train.py, evaluate.py
│   └── tests/
├── legacy/<modelo>/              # notebook original + especificación + refs de paridad
├── notebooks/                    # exploración nueva
└── docs/{adr,inventario}/
```

**Nombres:** `nave-{dominio}-{modelo}-{ambiente}-{recurso}`. Minúsculas, guiones, sin acentos.
**Tags obligatorios:** `Project` · `Environment` · `Owner` · `CostCenter` · `DataClassification` ·
`ManagedBy=cdk`.

### 7.4 Definition of Done

**Cambio de infra (CDK):** `cdk synth` sin errores · `cdk diff` pegado en el PR · tags puestos · sin
`"*"` en Action/Resource de IAM · cifrado con KMS.

**Modelo migrado:** especificación escrita y validada con el dueño del modelo · **test de paridad
aprobado y documentado** · pipeline re-ejecutable de punta a punta · agendado con alerta de fallo ·
corridas en MLflow · README de una página (qué hace, con qué datos, limitaciones) · costo mensual
estimado · plan de corte acordado con el dueño.

### 7.5 Git

Ramas `feat/`, `fix/`, `chore/`, `exp/`. Conventional Commits. PRs chicos.
**Nunca commitear** credenciales, datos de clientes, ni outputs de notebooks con datos reales
(`jupyter nbconvert --clear-output --inplace` antes del commit).

---

## 8. La fábrica de agentes

El activo que sobrevive al MVP. Viven en `.claude/agents/`, versionados en este repo.

### 8.1 Los cuatro del MVP

| Agente | Qué hace |
|---|---|
| **`notebook-archaeologist`** | Lee un notebook existente y produce la especificación: features, lógica, dependencias con versiones, fuentes de datos, formato de salida. **Es el que convierte una migración incierta en una tarea acotada.** |
| **`ml-pipeline-builder`** | Toma esa especificación y genera los módulos en `ml/src/`, sus tests y el pipeline. El caballo de batalla del segundo modelo en adelante. |
| **`cdk-infra`** | Genera y modifica stacks CDK siguiendo §5.1 y §7.3. Verifica con `cdk synth` y `cdk diff`. |
| **`security-reviewer`** | Revisa el diff: IAM amplio, buckets sin cifrar, secretos, tags faltantes. Corre sobre todo PR de infra. |

### 8.2 Slash commands (`.claude/commands/`)

`/inventariar <ruta>` — corre `notebook-archaeologist` y agrega la ficha al inventario
`/migrar <modelo>` — ejecuta el flujo de §7.2 sobre un modelo del inventario
`/verificar-paridad <modelo>` — corre la comparación y reporta divergencias
`/revisar-seguridad` — corre `security-reviewer` sobre el diff actual

### 8.3 Hooks (`.claude/settings.json`)

PreToolUse en Bash: bloquear `cdk deploy` fuera de `dev` · PostToolUse en Edit/Write: `ruff format`
sobre `.py` modificados · PreToolUse en Write: rechazar contenido que matchee patrones de secretos.

> **Guardrail:** los agentes generan PRs, no commits a `main`. La verificación (tests, `cdk synth`,
> paridad) es trabajo del agente, no del revisor.

---

## 9. Reglas para el agente (Claude Code)

### Siempre

- **Leer antes de escribir**: buscar el patrón que ya existe en el repo y seguirlo.
- **Respetar §2: la migración es iso-funcional.** Si detectás una mejora posible al modelo,
  **anotala en `docs/mejoras.md` y seguí** — no la implementes.
- **Respetar el alcance de §3.** Si algo está fuera del MVP, mencionalo como Fase 2 y seguí.
- **Preguntar cuando la decisión es de negocio**: tolerancia del test de paridad, criticidad de un
  modelo, cadencia de ejecución.
- Type hints y docstrings en `ml/src/` e `infra/`. Tests junto al código.
- **Declarar los supuestos** cuando asumiste algo que no estaba en contexto.

### Nunca

- Ejecutar `cdk deploy` fuera de `dev` sin confirmación explícita.
- **Modificar, refactorizar o apagar el notebook original.** Es la fuente de verdad hasta que la
  paridad esté aprobada.
- Cambiar features, hiperparámetros o lógica del modelo durante la migración.
- Declarar una migración terminada sin test de paridad aprobado.
- Borrar o modificar recursos con datos: buckets, tablas, model package groups.
- Crear políticas IAM permisivas "para que funcione y después lo ajustamos". Nunca se ajusta.
- **Inventar** respuestas a las incógnitas de §1.2, ni nombres de recursos, ARNs, IDs de cuenta o
  tablas. Si no está en el repo o en la conversación, preguntar.
- Escribir credenciales o datos con PII en archivos, logs o commits.
- Deshabilitar un test o un check de lint para que pase el pipeline.
- Afirmar que algo funciona sin haberlo verificado.

---

## 10. Reglas que no se relajan ni en MVP

**Datos.** Solo muestras anonimizadas mientras no haya aislamiento de red. Buckets: KMS, versionado,
acceso público bloqueado. Datasets en particiones inmutables con fecha.

**IAM.** Un rol de ejecución por modelo y ambiente. Prohibido `Action: "*"` o `Resource: "*"` salvo
excepción justificada en el PR. Acceso humano vía IAM Identity Center.

**Secretos.** Secrets Manager. Nunca en el notebook, nunca en `config.yaml`, nunca en un commit.

**Costos.** Auto-shutdown de Spaces por inactividad (obligatorio) · `max_jobs` acotado · Spot con
checkpointing para entrenamiento · AWS Budgets con alerta al 80% por `CostCenter`. Toda propuesta de
arquitectura en un PR incluye una línea de costo mensual estimado.

---

## 11. Backlog Fase 2

1. **Aislamiento de red (VPC-only)** — *bloquea datos productivos*
2. **Ambientes separados + CI/CD** — *bloquea el corte definitivo del notebook*
3. **Migrar el resto del inventario** — con la fábrica ya construida
4. **Model Monitor** — baseline, data capture, alarmas con dueño
5. **Gobierno del modelo** — Model Cards, Clarify, runbooks
6. **Mejoras a los modelos** — ahora sí, con la plataforma que permite compararlas limpiamente
7. **Linaje dato→modelo** integrado con el catálogo del datalake
8. **Agentes de migración de fuentes y tableros**

---

## 12. Decisiones abiertas

| # | Tema | Bloquea |
|---|---|---|
| **D1** | **Qué modelos son y cuál es su riesgo regulatorio** | §2.3, elección del primero |
| **D2** | **Dónde corren hoy — ¿hay deadline de salida de Galicia?** | Todo el cronograma |
| **D3** | **Cuántos son** | Dimensionamiento de la fábrica |
| D4 | Cuenta AWS del MVP: ¿nueva o heredada de la landing zone de Galicia? | Semana 1 |
| D5 | ¿Existe comité de modelos y quién aprueba? | Corte definitivo |
| D6 | Tolerancia numérica aceptable del test de paridad | §2.2 |
| D7 | Gestor de dependencias (`uv` vs `poetry`) | Bootstrapping |

---

## 13. Contribuir a este archivo

Si trabajando en el repo encontrás que una regla está desactualizada, es ambigua, o que el agente se
equivocó por falta de contexto: **corregila en el mismo PR**. Este documento es el activo más
valioso del repo — es lo que hace que cada persona nueva, humana o agente, arranque con el contexto
correcto.
