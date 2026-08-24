# Demo — Nave ML Platform · Viernes 22/08/2026 · 2pm

**Audiencia:** Cliente Nave  
**Duración:** 30 minutos  
**Quién presenta:** Santiago Castro (Nubiral)  
**Ambiente:** Cuenta sandbox Nubiral `015319782619` · SageMaker Studio · dominio `d-7v1pspekpoad`

---

## Mensaje central

> "Nave hoy ejecuta modelos abriendo un notebook a mano.
> Les vamos a mostrar que con agentes de IA, ese mismo modelo
> queda en un pipeline reproducible en AWS — en horas, no en semanas."

---

## Preparación previa (jueves a la noche, antes de cerrar)

- [ ] `terraform apply` corrido y verde
- [ ] Bucket S3 creado con los tags de la política
- [ ] User profile de SageMaker creado y `InService`
- [ ] Pipeline ejecutado al menos una vez exitosamente (no en vivo)
- [ ] MLflow con al menos 2 experimentos registrados
- [ ] Tener grabado un video de backup del pipeline corriendo (por si la red falla en vivo)
- [ ] Ensayo completo de punta a punta cronometrado (objetivo: ≤ 28 min)

---

## Guión

### 0 · Apertura (2 min)

**Decir:**
> "Nave tiene modelos que hoy funcionan. El problema no es que no funcionen: es que
> dependen de que alguien abra un notebook y lo corra a mano. Si esa persona se va de
> vacaciones, el modelo no corre. Si alguien pregunta con qué datos se generó una
> predicción de hace tres meses, nadie puede responder. En el sistema financiero eso
> no es un problema técnico — es un hallazgo de auditoría.
> Hoy les mostramos cómo se ve eso resuelto."

---

### 1 · El notebook original (3 min)

**Mostrar:** `legacy/modelo-demo/nave_notebook_ejemplo.ipynb` en JupyterLab o VS Code

**Decir:**
> "Este notebook simula lo que hoy tiene Nave: un modelo de scoring que alguien
> escribió, que funciona, pero que nadie sabe exactamente qué hace, con qué versiones
> de librerías, ni qué pasa si el ambiente cambia."

**Puntos a señalar en el notebook:**
- Dependencias sin versión fijada (`import sklearn`)
- Datos hardcodeados con rutas locales
- Sin tests, sin logging, sin manejo de errores
- Funciona — pero solo en la máquina de quien lo escribió

---

### 2 · Agente notebook-archaeologist (8 min) — EN VIVO

**Abrir Claude Code en la terminal**

```
/inventariar legacy/modelo-demo/nave_notebook_ejemplo.ipynb
```

**Qué muestra el agente:**
- Lee el notebook célula por célula
- Extrae: features de entrada, lógica de preprocesamiento, algoritmo usado, versiones de librerías, formato de salida
- Genera la ficha en `docs/inventario/modelo-demo.md`

**Decir mientras corre:**
> "Lo que están viendo es el agente leyendo el código. Esto normalmente toma una
> reunión de dos horas con quien escribió el notebook — si todavía está en la empresa.
> El agente lo hace en dos minutos y deja todo por escrito."

**Mostrar la ficha generada** y leerla en voz alta brevemente.

---

### 3 · Agente ml-pipeline-builder (8 min) — EN VIVO

```
/migrar modelo-demo
```

**Qué genera el agente:**
- `ml/src/modelo-demo/preprocessing.py`
- `ml/src/modelo-demo/train.py`
- `ml/src/modelo-demo/evaluate.py`
- `ml/pipelines/modelo-demo/pipeline.py`

**Decir mientras corre:**
> "El agente toma la ficha que acabamos de generar y produce el pipeline de SageMaker.
> Esto — modularizar el notebook, escribir los tests, armar los steps — normalmente
> son tres o cuatro días de un Data Scientist. El agente lo hace en minutos."

**Mostrar el `pipeline.py` generado** y señalar los steps: `@step` de SageMaker.

---

### 4 · Pipeline corriendo en SageMaker Studio (5 min)

**Abrir SageMaker Studio → Pipelines**

Mostrar la ejecución del pipeline (puede ser la del día anterior, no necesariamente en vivo):
- `ProcessingStep` → preprocesamiento
- `TrainingStep` → entrenamiento del modelo
- `TransformStep` → predicciones batch

**Decir:**
> "Ya no hay notebook. Hay un pipeline reproducible: cualquiera lo puede re-ejecutar,
> da siempre el mismo resultado sobre los mismos datos, y deja trazabilidad completa
> de cada ejecución."

---

### 5 · MLflow (3 min)

**Abrir MLflow UI** (desde Studio o puerto forwarded)

Mostrar:
- Lista de experimentos
- Parámetros registrados (hiperparámetros)
- Métricas (accuracy, etc.)
- Artefactos (modelo serializado)

**Decir:**
> "Cada ejecución queda registrada. Saben exactamente qué código, qué datos y qué
> parámetros generaron cada predicción. Eso es lo que le responde a Compliance cuando
> pregunta."

---

### 6 · Cierre y próximos pasos (3 min)

**Decir:**
> "Lo que vieron hoy es un prototipo construido en 2 días en nuestra cuenta de sandbox,
> con datos de ejemplo. El MVP real — con el primer modelo de Nave migrado, agendado
> y corriendo solo en la cuenta de Nave — son 6 semanas con este mismo equipo y estos
> mismos agentes."

**Mostrar la tabla del plan** (del `PLAN_DE_TRABAJO_MVP_1.md`):

| Semana | Entregable |
|--------|-----------|
| S1 | Inventario de modelos de Nave — primera vez escrito en un solo lugar |
| S2 | Especificación validada del primer modelo |
| S3 | Demo en vivo del agente tomando el notebook de Nave real |
| S4 | Pipeline con paridad aprobada: "produce exactamente las mismas predicciones" |
| S5 | El modelo corre solo, sin que nadie abra un notebook |
| S6 | El segundo modelo migrado en días, no semanas |

> "El número que vende el proyecto es el de la semana 6: el primer modelo tardó
> 5 semanas. El segundo tardó días. Esa capacidad de repetirlo es lo que están comprando."

---

## Preguntas esperadas y respuestas

| Pregunta | Respuesta |
|----------|-----------|
| "¿Esto funciona con nuestros datos reales?" | "Sí. La semana 1 del MVP es exactamente eso: inventariar los notebooks de Nave y elegir el primero. El prototipo usó datos públicos para no bloquear la demo con accesos." |
| "¿Qué pasa con el modelo actual mientras migramos?" | "No se toca. La migración es iso-funcional: el notebook original sigue corriendo hasta que la paridad esté aprobada. No se apaga nada." |
| "¿Cuánto cuesta esto en AWS?" | "El sandbox de hoy corrió en instancias `ml.m5.large`. Para el MVP completo hacemos la estimación de costo en la semana 1, una vez que sabemos cuántos modelos son y con qué frecuencia corren." |
| "¿Necesitamos cambiar los modelos?" | "No. Migramos la plomería, no el modelo. El modelo migrado produce exactamente las mismas predicciones que el notebook actual." |
| "¿Compliance lo va a aprobar?" | "Precisamente por eso la migración es iso-funcional: no es un modelo nuevo que necesita validación. Es el mismo modelo con mejor infraestructura." |

---

## Contingencias

| Problema | Plan B |
|----------|--------|
| La red falla y el agente no corre en vivo | Reproducir desde el video grabado el jueves |
| El pipeline tarda mucho en iniciarse | Mostrar la ejecución ya completada del jueves |
| MLflow no levanta | Mostrar los logs de CloudWatch como alternativa |
| Algo falla en vivo | "Esto es un sandbox de 2 días — les mostramos el video de la ejecución completa del jueves" |
