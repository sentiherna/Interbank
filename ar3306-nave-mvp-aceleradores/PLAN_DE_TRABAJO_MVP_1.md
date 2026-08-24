# Plan de trabajo — MVP Plataforma de ML de Nave

**Situación:** Nave tiene modelos corriendo hoy en notebooks, ejecutados a mano. No hay plataforma.
**Equipo:** 1 Tech Lead + 1 Data Scientist, apalancados en agentes de IA (Claude Code)
**Duración estimada:** **6 semanas** de calendario · ~12 persona-semanas de esfuerzo
**Modo de entrega:** incremento mostrable cada semana (no big bang)

---

## 1. La respuesta corta

**6 semanas** para: inventario de los modelos existentes, zona de experimentación operativa, y **un
modelo migrado de notebook manual a pipeline automatizado con paridad demostrada**.

Sin agentes, el mismo alcance con el mismo equipo son **12 a 16 semanas**. La aceleración real está
entre **2x y 2.5x en calendario** — no 10x. Cualquiera que prometa 10x no está contando el tiempo
que se va en accesos, datos y decisiones.

**Advertencia sobre esta estimación:** hoy no sabemos cuántos modelos son, de qué tipo, ni si
todavía corren del lado de Galicia. La Semana 1 existe precisamente para cerrar eso. Si el
inventario revela un deadline de salida de Galicia, el plan se reordena.

---

## 2. Dónde acelera el agente y dónde no

La parte honesta de la estimación, y la que conviene mostrarle a Nave para alinear expectativas.

| Actividad | Aceleración | Por qué |
|---|---|---|
| **Arqueología de notebooks** (entender qué hace el código existente) | **4–5x** | Leer código ajeno y documentarlo es exactamente donde un agente rinde. |
| Scaffolding de IaC (stacks CDK, roles, buckets, Studio) | **3–5x** | Código estructurado y repetitivo con convenciones claras. |
| Refactor notebook → módulo + tests | **3–5x** | Transformación mecánica sobre código que ya existe y funciona. |
| Boilerplate del pipeline de SageMaker | **3–4x** | Patrón conocido, mucho código ceremonial. |
| Documentación, inventario, fichas de modelo | **4x** | Normalmente se posterga; con agente sale junto con el código. |
| Code review de seguridad y convenciones | **3x** | El agente revisa el 100% de los diffs, no una muestra. |
| **Segundo modelo migrado en adelante** | **5–8x** | Acá está el verdadero premio: la fábrica ya existe. |
| Debugging del test de paridad | **1.5x** | Si las predicciones no coinciden, hay que entender por qué. Trabajo de detective. |
| Decisiones de negocio (criticidad, tolerancias, orden) | **1x** | El agente no decide por el dueño del modelo. |
| **Esperar accesos a la cuenta AWS** | **1x** | El agente no acelera al equipo de infra. |
| **Esperar el dato y a las personas** | **1x** | Ni al equipo de Data, ni a quien hoy corre los notebooks. |

> **Conclusión operativa:** en un cliente corporativo el camino crítico **no es escribir código**.
> Por eso la Semana 0 (§4) arranca en paralelo y destraba todo lo demás.

---

## 3. Estructura del equipo

| Rol | Dedicación | Foco |
|---|---|---|
| **Tech Lead** | Full-time | Infraestructura CDK, pipeline, **y construir los agentes** (§5). Opera Claude Code con más profundidad. |
| **Data Scientist** | Full-time | Arqueología de los notebooks, test de paridad, criterio de métrica. Usa los agentes, no los construye. |
| *Dueño de los modelos (Nave)* | ~4 hs/semana | **La dependencia más crítica.** Es quien sabe qué hace cada notebook y por qué. Sin acceso a esta persona, el descubrimiento se vuelve adivinanza. |
| *Referente de infra/cloud (Nave)* | Puntual, semanas 0–1 | Cuenta AWS, permisos, cuotas. |

**Inversión clave:** el TL dedica ~30% de las semanas 1 y 2 a construir los agentes. Parece tiempo
perdido y se recupera con creces desde la semana 3 — y sobre todo en la semana 6.

---

## 4. Semana 0 — Destrabar (en paralelo, antes o durante S1)

No consume al equipo técnico full-time, pero **define si el plan se cumple**.

| Ítem | Responsable | Bloquea |
|---|---|---|
| **Acceso a los notebooks y a quien los ejecuta hoy** | Nave + TL | Todo el descubrimiento |
| Cuenta AWS de trabajo y accesos vía Identity Center | Infra Nave | Semana 1 |
| Confirmar si hay deadline de salida de Galicia | Nave | El orden completo del plan |
| Verificar cuotas de instancias de SageMaker | TL | Semana 3 |
| Repo creado con el CLAUDE.md cargado | TL | Semana 1 |

---

## 5. Plan semana a semana

Cada semana cierra con algo que se le puede mostrar a alguien.

### Semana 1 — Inventario y zona de experimentación

**DS:** recorre los notebooks existentes con el agente de arqueología. Por cada modelo: qué hace,
quién lo consume, con qué frecuencia se corre, qué datos usa, qué riesgo regulatorio tiene, qué pasa
si deja de correr.
**TL:** stacks CDK (`security`, `studio`, `data`), Domain de SageMaker, Spaces con auto-shutdown,
roles y buckets. Construye `cdk-infra` y `security-reviewer`.

🎯 **Mostrable:** **el inventario de modelos de Nave** — probablemente la primera vez que existe
escrito en un solo lugar — más un DS entrando a Studio a consultar datos reales.

> Este entregable tiene valor propio aunque el proyecto se frenara acá. También es lo que permite
> elegir el primer modelo con criterio en lugar de por intuición.

---

### Semana 2 — Congelar la referencia

**DS + TL:** se elige el primer modelo (dolor alto, lógica acotada, bajo riesgo regulatorio). Se
congela un dataset de referencia, se ejecuta el notebook original tal cual está y se guardan sus
predicciones. Se capturan las versiones exactas de las librerías.
**TL:** dataset versionado en particiones inmutables, MLflow configurado, arranca
`ml-pipeline-builder`.

🎯 **Mostrable:** la especificación escrita del modelo, validada con su dueño. Suele ser la semana
que más conversación genera: es común que nadie tuviera esto documentado.

---

### Semana 3 — De notebook a código productivo

**DS + TL con `ml-pipeline-builder`:** modularizar `preprocessing.py`, `train.py`, `evaluate.py` en
`ml/src/` con sus tests. Definir el pipeline de SageMaker con el decorador `@step`.

🎯 **Mostrable:** **la demo más impactante.** Mostrar en vivo al agente tomando el notebook y
generando el módulo, los tests y el pipeline. Es donde se ve el diferencial.

---

### Semana 4 — Pipeline completo y paridad

**TL:** el pipeline corre entero: processing → training → transform → métricas → **test de paridad**
→ gate → registro en Model Registry.
**DS:** ejecuta la comparación contra las predicciones de referencia y persigue cualquier
divergencia hasta explicarla.

🎯 **Mostrable:** **el momento que define el MVP.** "El pipeline produce exactamente las mismas
predicciones que el notebook que hoy se corre a mano." Esa frase es la que le da confianza al
negocio para dejar de depender de una persona.

⚠️ Es la semana con más riesgo de sorpresas. Las divergencias por versiones de librerías son
habituales y llevan tiempo de detective.

---

### Semana 5 — Automatizar y entregar

**TL:** agendamiento con EventBridge replicando la cadencia actual, alerta cuando falla, salida en
la tabla que el negocio ya consume, costos estimados.
**DS:** README del modelo y plan de corte acordado con el dueño (el notebook no se apaga hasta que
haya corridas automáticas exitosas en paralelo).

🎯 **Mostrable:** el modelo corre solo, en horario, sin que nadie abra un notebook. Y si falla,
alguien se entera.

---

### Semana 6 — La prueba de fuego

**Ambos:** tomar el **segundo modelo del inventario** y recorrer todo el camino con la fábrica de
agentes. Cronometrarlo. Cerrar el paquete: documentación, backlog de Fase 2 priorizado, CLAUDE.md
actualizado.

🎯 **Mostrable:** **el número que vende la vertical.** "El primer modelo tardó 5 semanas. El segundo
tardó días." Un modelo lo migra cualquiera; la capacidad de repetirlo es lo que estamos vendiendo.

---

## 6. Vista de conjunto

```
        S0        S1        S2        S3        S4        S5        S6
        │         │         │         │         │         │         │
Infra   ████──────████                                    ██
Descub. ████──────████──────██
Migrac.                     ████──────████──────████
Paridad                               ██────────████
Automat.                                                  ████
Agentes           ███───────███───────██                            ████
                  │         │         │         │         │         │
                  ▲         ▲         ▲         ▲         ▲         ▲
              Inventario  Especifi-  Demo del  Paridad   Corre    Speedup
              de modelos   cación     agente   aprobada   solo    medido
```

---

## 7. Riesgos y mitigaciones

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | **Nadie recuerda del todo qué hace el notebook** | Alta | Alto | Es lo normal, no una excepción. Por eso la arqueología es un paso formal con entregable escrito, y no se migra nada sin la especificación validada por el dueño. |
| R2 | **El test de paridad no cierra** | Alta | Medio | Casi siempre son versiones de librerías o el orden de operaciones. Se pinnean versiones desde el inicio (§5.2 del CLAUDE.md) y se define de antemano la tolerancia aceptable. |
| R3 | **Accesos y cuotas de AWS demoran** | Alta | Alto | Pedirlos en Semana 0 con la lista exacta por escrito. El atraso más común y el más evitable. |
| R4 | **Hay deadline de salida de Galicia que no conocíamos** | Media | Alto | Se confirma en Semana 0. Si existe, manda sobre el orden de migración y hay que replanificar antes de arrancar, no después. |
| R5 | **El dueño de los modelos no está disponible** | Media | Alto | Comprometer 4 hs semanales en Semana 0, con nombre y apellido. Sin esa persona el descubrimiento es adivinanza. |
| R6 | **Presión por "aprovechar y mejorar el modelo"** | Alta | Medio | La migración es iso-funcional. Las mejoras se anotan en un backlog visible y se hacen después, con la plataforma que permite compararlas limpiamente. |
| R7 | **Aparecen más modelos de los esperados** | Media | Bajo | Buen problema: fortalece el argumento de la fábrica. Se prioriza el inventario y se migra por olas. |

---

## 8. Cómo medir que la aceleración fue real

Sin estas métricas, "aceleramos con IA" es marketing. Con ellas, es un dato.

| Métrica | Cómo se mide | Objetivo |
|---|---|---|
| **Time-to-first-query** | Desde que un DS pide acceso hasta que consulta datos en Studio | < 1 día |
| **Time-to-second-migration** | Duración del modelo #2 vs el #1 | **≤ 20% del primero** |
| Paridad | Predicciones del pipeline vs el notebook original | Coincidencia dentro de la tolerancia acordada |
| Ejecuciones manuales eliminadas | Corridas de notebook a mano por mes | A cero para el modelo migrado |
| Cobertura de review automático | % de PRs de infra revisados por el agente | 100% |
| Costo del ambiente | Gasto mensual de la zona de experimentación | Dentro del budget definido |

---

## 9. Después de la semana 6

El backlog de Fase 2 está en el §11 del CLAUDE.md. Los dos primeros habilitan el corte definitivo y
no se pueden saltear:

1. **Aislamiento de red (VPC-only)** — ~2 semanas. *Bloquea el uso de datos productivos.*
2. **Ambientes separados + CI/CD** — ~3 semanas. *Bloquea apagar el notebook original.*
3. **Migrar el resto del inventario** — con la fábrica ya construida, por olas.

A partir de ahí, cada modelo nuevo o migrado debería costar **días, no semanas** — que es el punto
de haber construido una plataforma en lugar de haber migrado un modelo.

---

## 10. Supuestos de esta estimación

Si alguno no se cumple, la estimación cambia y hay que rehacerla:

- TL y DS **dedicados full-time**, sin partirse con la migración del datalake en paralelo.
- Acceso a los notebooks y a quien los ejecuta hoy, desde la Semana 0.
- Cuenta AWS disponible y con permisos para crear recursos en Semana 1.
- Los modelos son de complejidad razonable (no un ensamble de 40 modelos con lógica de negocio
  entrelazada).
- Sin requerimiento de aislamiento de red durante el MVP (solo datos anonimizados).
- Sin deadline externo de salida de Galicia que comprima el cronograma.
- El equipo ya tiene manejo de Python y AWS; **no** se asume experiencia previa en SageMaker.
