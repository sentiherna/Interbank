"""
monitoring_builder.py — Agente de construccion de pipelines de monitoreo SageMaker via Amazon Bedrock

Tercer agente de la fabrica: arma el pipeline de monitoreo de un modelo ya migrado y
registrado (ver notebook_archaeologist.py y pipeline_builder.py). Sigue el mismo patron que
usa NaranjaX en produccion (03-monitoring-pipeline): no se apoya solo en un Model Monitor
schedule generico, sino en un pipeline propio que re-consulta datos con un rezago (lag) de
periodos —el tiempo que tarda en aparecer el resultado real (ground truth)— y mide deriva de
datos y caida de performance contra la misma metrica y umbral definidos en la ficha.

Lee la ficha generada por notebook-archaeologist y produce:
  - ml/src/<modelo>/monitoring/create_dataset.py   (re-consulta el periodo con rezago)
  - ml/src/<modelo>/monitoring/compute_drift.py    (deriva de datos + caida de performance)
  - ml/pipelines/<modelo>/monitoring_pipeline.py   (orquesta todo + dispara reentrenamiento)

El monitoring_pipeline.py generado:
  - Consulta el modelo APROBADO vigente en el Model Registry (mismo patron que
    02-inference-pipeline: AWS Lambda GetApprovedModel).
  - Re-ejecuta la inferencia sobre el periodo con rezago y la compara contra el resultado
    real ya disponible.
  - Publica metricas de deriva y performance a Amazon CloudWatch.
  - Si la metrica cae por debajo del umbral de la ficha, dispara una regla de Amazon
    EventBridge que arranca el pipeline de entrenamiento (reentrenamiento automatizado).
    Si no, solo deja registro del chequeo.

Uso desde la terminal de SageMaker Studio:
    python ml/agents/monitoring_builder.py --ficha <ruta_ficha> --modelo <nombre> [--lag N]

Ejemplo:
    python ml/agents/monitoring_builder.py \
        --ficha docs/inventario/nave_notebook_ejemplo.md \
        --modelo modelo-riesgo \
        --lag 3
"""

import argparse
import json
import sys
from pathlib import Path

import boto3
from botocore.config import Config


# --- Configuracion -----------------------------------------------------------

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION   = "us-east-1"

BUCKET       = "ar3306-nave-aceleradores-ml-data-sandbox"
ROLE_ARN     = "arn:aws:iam::015319782619:role/ar3306-nave-aceleradores-sagemaker-execution-role"
ACCOUNT_ID   = "015319782619"
RETRAIN_PIPELINE_NAME_SUFFIX = "-training-pipeline"  # nombre del pipeline de train a re-disparar

SYSTEM_PROMPT = f"""Sos un agente experto en MLOps que genera codigo Python de produccion para Amazon SageMaker,
especializado en pipelines de monitoreo de modelos ya migrados y registrados.

Recibis la ficha de un modelo (generada por notebook-archaeologist, ya migrado por
pipeline-builder) y producis exactamente 2 archivos Python.

Reglas generales:
- No inventes metricas nuevas: usa la misma metrica y el mismo umbral de la seccion
  "Metrica de aceptacion y umbral" de la ficha, ahora aplicados a datos nuevos.
- El bucket S3 es: {BUCKET}
- El execution role ARN es: {ROLE_ARN}
- Region: {REGION}
- Nunca hardcodees credenciales ni ARNs de cuentas en el codigo de los modulos.
- Los modulos reciben paths de S3, el periodo de ejecucion y el rezago (lag) como argumentos
  de linea de comandos (argparse). Nunca hardcodees el periodo.

Reglas especificas por modulo:

- create_dataset.py:
  - Re-ejecuta, para el periodo con rezago (periodo_ejecucion - lag), la misma logica de
    consulta y join que arma la ficha en "Fuente de datos" — no una logica nueva.
  - El resultado de este periodo YA tiene el resultado real (ground truth) disponible,
    a diferencia de la inferencia en tiempo real. Ese es el motivo del lag: sin ground
    truth no hay con qué comparar la prediccion.
  - Guarda el dataset resultante en S3 bajo un prefijo "monitoring/data-raw/<periodo>".

- compute_drift.py:
  - Recibe: (a) las predicciones que el modelo ya genero para ese periodo (via el pipeline
    de inferencia) y (b) el resultado real de create_dataset.py.
  - Calcula la metrica de aceptacion de la ficha sobre datos reales (no de referencia) y la
    compara contra el umbral. Si la ficha tiene predicciones de referencia del notebook
    original, reutiliza la funcion ya existente en el toolkit interno para no reimplementar
    comparaciones de dataframes:
      from utils import compare_dataframes, analyse_dif
  - Calcula tambien deriva de datos: distribucion de cada feature en el periodo actual vs.
    el periodo de entrenamiento (KS-test o PSI por columna; si no está claro cuál usar,
    dejalo como funcion `compute_psi(reference, current)` con un TODO de calibración).
  - Escribe un unico monitoring_report.json con esta forma minima:
    {{"periodo": "<periodo>", "metrics": {{"<metrica>": {{"value": <float>, "umbral": <float>}}}},
      "drift": {{"<feature>": <float, ...>}}, "alerta": <bool>}}
  - Publica el valor de la metrica principal y el indicador de deriva a Amazon CloudWatch
    con boto3 (cloudwatch.put_metric_data), namespace f"MLOps/{{modelo}}", para que puedan
    graficarse en un dashboard sin depender del pipeline.

Responde UNICAMENTE con bloques de codigo en este formato exacto (nada antes, nada despues):

### create_dataset.py
```python
<codigo>
```

### compute_drift.py
```python
<codigo>
```
"""

SYSTEM_PROMPT_PIPELINE = f"""Sos un agente experto en MLOps que genera codigo Python de produccion para Amazon SageMaker.

Recibis la ficha de un modelo y los modulos ya generados (create_dataset, compute_drift).
Generas UNICAMENTE el monitoring_pipeline.py que orquesta esos modulos con el SageMaker
Python SDK, siguiendo el patron de pipeline de monitoreo propio (no un Model Monitor
schedule generico) que ya usa NaranjaX en produccion.

Reglas generales:
- El bucket S3 es: {BUCKET}
- El execution role ARN es: {ROLE_ARN}
- Region: {REGION}
- El pipeline recibe como ParameterString: PeriodoEjecucion y Lag (rezago en periodos hasta
  que el ground truth esta disponible). Nunca los hardcodees.
- Lee el bucket, el role y el nombre del pipeline de entrenamiento a re-disparar desde
  variables de entorno, con fallback a los valores por defecto.

=== REGLAS CRITICAS (romper cualquiera causa error en ejecucion) ===

REGLA 1 — Usar PipelineSession, NO sagemaker.Session:
  from sagemaker.workflow.pipeline_context import PipelineSession
  sagemaker_session = PipelineSession(boto_session=boto3.Session(region_name=REGION))

REGLA 2 — Obtener el modelo aprobado vigente, mismo patron que el pipeline de inferencia:
  from sagemaker.lambda_helper import Lambda
  from sagemaker.workflow.lambda_step import LambdaStep

  get_approved_model = Lambda(
      function_arn="arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:GetApprovedModel",  # REVISAR ARN real
  )
  step_get_model = LambdaStep(
      name="GetApprovedModel",
      lambda_func=get_approved_model,
      inputs={{"model_package_group_name": f"{{modelo}}-package-group"}},
      outputs=[],
  )
  # El monitoreo SIEMPRE se corre contra el modelo aprobado vigente, nunca contra el ultimo
  # entrenado: si un modelo fue rechazado por el gate, no debe monitorearse en produccion.

REGLA 3 — Orden de steps, con el lag como parametro explicito:
  1. ProcessingStep (create_dataset.py) — recibe PeriodoEjecucion y Lag como argumentos.
  2. TransformStep — scorea ese periodo con el modelo del step 2 (Batch Transform, igual
     que el pipeline de inferencia). Usa model_name=step_get_model.properties.Outputs["ModelName"].
  3. ProcessingStep (compute_drift.py) — recibe las predicciones del TransformStep y el
     dataset con ground truth del ProcessingStep 1.

REGLA 4 — Property file y gate de reentrenamiento (ConditionStep), igual patron que el gate
del pipeline de entrenamiento — reutiliza el mismo enfoque, no inventes uno nuevo:
  from sagemaker.workflow.properties import PropertyFile
  from sagemaker.workflow.functions import JsonGet
  from sagemaker.workflow.condition_step import ConditionStep
  from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo

  monitoring_report = PropertyFile(name="MonitoringReport", output_name="monitoring", path="monitoring_report.json")
  # step_drift (ProcessingStep de compute_drift.py) debe declarar property_files=[monitoring_report]

  metric_value = JsonGet(
      step_name=step_drift.name,
      property_file=monitoring_report,
      json_path="metrics.<nombre_metrica>.value",
  )
  condition_ok = ConditionGreaterThanOrEqualTo(left=metric_value, right=<umbral_de_la_ficha>)

REGLA 5 — Si el modelo cae por debajo del umbral, disparar reentrenamiento via EventBridge,
NUNCA reentrenar sincronicamente dentro de este mismo pipeline:
  from sagemaker.workflow.lambda_step import LambdaStep
  from sagemaker.lambda_helper import Lambda

  trigger_retrain = Lambda(
      function_arn="arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TriggerRetrainingPipeline",  # REVISAR ARN real
  )
  step_trigger_retrain = LambdaStep(
      name="TriggerRetraining",
      lambda_func=trigger_retrain,
      inputs={{
          "pipeline_name": f"{{modelo}}{RETRAIN_PIPELINE_NAME_SUFFIX}",
          "reason": "metric_below_threshold",
      }},
      outputs=[],
  )
  # Esta Lambda es la que hace event_bridge_client.put_events(...) o directamente
  # sagemaker_client.start_pipeline_execution(...) sobre el pipeline de entrenamiento.
  # El pipeline de monitoreo NUNCA debe importar ni ejecutar el pipeline de entrenamiento
  # directamente: solo lo dispara de forma asincronica.

  step_gate = ConditionStep(
      name="PerformanceGate",
      conditions=[condition_ok],
      if_steps=[],                       # todo OK: no hace falta reentrenar
      else_steps=[step_trigger_retrain],  # cae la metrica: dispara reentrenamiento
  )

REGLA 6 — El pipeline debe correr con Pipeline Schedule (EventBridge Scheduler), no manual:
  Documenta en un comentario al final del archivo el comando para asociar un schedule
  periodico (ej: mensual) usando sagemaker.workflow.triggers.PipelineSchedule, ya que este
  pipeline no tiene sentido si se dispara solo a mano.

Responde UNICAMENTE con este bloque (nada antes, nada despues):

### monitoring_pipeline.py
```python
<codigo>
```
"""


# --- Funciones ---------------------------------------------------------------

def load_ficha(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=REGION,
        config=Config(read_timeout=300, connect_timeout=10, retries={"max_attempts": 1}),
    )


def call_bedrock_modules(ficha_content: str, modelo: str, lag: int) -> str:
    """Genera create_dataset.py y compute_drift.py."""
    client = _bedrock_client()

    user_message = f"""Genera los 2 modulos Python (create_dataset, compute_drift) para monitorear el
siguiente modelo ya migrado y registrado.
Nombre del modelo: {modelo}
Rezago (lag) por defecto hasta que el ground truth esta disponible: {lag} periodo(s)

<ficha>
{ficha_content}
</ficha>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 6000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["content"][0]["text"]


def call_bedrock_pipeline(ficha_content: str, modelo: str, lag: int) -> str:
    """Genera monitoring_pipeline.py separado para evitar truncamiento."""
    client = _bedrock_client()

    user_message = f"""Genera el monitoring_pipeline.py de SageMaker para el siguiente modelo.
Nombre del modelo: {modelo}
Rezago (lag) por defecto: {lag} periodo(s)

<ficha>
{ficha_content}
</ficha>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 6000,
        "system": SYSTEM_PROMPT_PIPELINE,
        "messages": [{"role": "user", "content": user_message}],
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["content"][0]["text"]


def parse_and_save(raw: str, modelo: str) -> None:
    """Extrae los bloques de codigo y los guarda en las rutas correctas."""
    files = {
        "create_dataset.py":      f"ml/src/{modelo}/monitoring/create_dataset.py",
        "compute_drift.py":       f"ml/src/{modelo}/monitoring/compute_drift.py",
        "monitoring_pipeline.py": f"ml/pipelines/{modelo}/monitoring_pipeline.py",
    }

    for filename, output_path in files.items():
        marker = f"### {filename}"
        if marker not in raw:
            print(f"WARN: no se encontro el bloque '{marker}' en la respuesta")
            continue

        start = raw.index(marker) + len(marker)
        code_start = raw.index("```python", start) + len("```python")
        code_end   = raw.index("```", code_start)
        code       = raw[code_start:code_end].strip()

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code + "\n", encoding="utf-8")
        print(f"  Guardado: {output_path}")


# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ML Monitoring Pipeline Builder via Bedrock")
    parser.add_argument("--ficha",  required=True, help="Ruta a la ficha .md del modelo")
    parser.add_argument("--modelo", required=True, help="Nombre del modelo (ej: modelo-riesgo)")
    parser.add_argument(
        "--lag", type=int, default=1,
        help="Rezago en periodos hasta que el ground truth esta disponible (default: 1)",
    )
    args = parser.parse_args()

    if not Path(args.ficha).exists():
        print(f"ERROR: No se encontro la ficha: {args.ficha}", file=sys.stderr)
        sys.exit(1)

    print(f"Leyendo ficha: {args.ficha}")
    ficha = load_ficha(args.ficha)
    print(f"   {len(ficha.split())} palabras en la ficha")

    print(f"\nLlamada 1/2 — generando modulos (create_dataset, compute_drift)...")
    raw_modules = call_bedrock_modules(ficha, args.modelo, args.lag)
    print("Guardando modulos generados:")
    parse_and_save(raw_modules, args.modelo)

    print(f"\nLlamada 2/2 — generando monitoring_pipeline.py...")
    raw_pipeline = call_bedrock_pipeline(ficha, args.modelo, args.lag)
    print("Guardando pipeline:")
    parse_and_save(raw_pipeline, args.modelo)

    print(f"\nDone. Pipeline de monitoreo listo en ml/pipelines/{args.modelo}/monitoring_pipeline.py")
    print(f"Modulos en ml/src/{args.modelo}/monitoring/")
    print(f"\nRecorda asociarle un schedule periodico (EventBridge Scheduler / PipelineSchedule):")
    print(f"no tiene sentido si solo se dispara a mano.")


if __name__ == "__main__":
    main()
