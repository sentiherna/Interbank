"""
pipeline_builder.py — Agente de construccion de pipelines SageMaker via Amazon Bedrock

Lee la ficha generada por notebook-archaeologist y produce:
  - ml/src/<modelo>/preprocessing.py
  - ml/src/<modelo>/train.py       (parametrizable, apto para HPO)
  - ml/src/<modelo>/evaluate.py    (metrica de gate + test de paridad, si hay referencia)
  - ml/pipelines/<modelo>/pipeline.py

El pipeline.py generado incluye, cuando la ficha lo justifica:
  - HyperparameterTuner (HPO) en lugar de un TrainingStep simple, si hay rangos definidos.
  - Data Quality y Model Quality checks (SageMaker Clarify / QualityCheckStep).
  - Explicabilidad del modelo (SHAP) via ClarifyCheckStep.
  - Gate de aprobacion automatico (ConditionStep + FailStep) contra el umbral de la ficha:
    solo si el modelo lo supera se registra en el Model Registry y se habilita el transform.

Uso desde la terminal de SageMaker Studio:
    python ml/agents/pipeline_builder.py --ficha <ruta_ficha> --modelo <nombre>

Ejemplo:
    python ml/agents/pipeline_builder.py \
        --ficha docs/inventario/nave_notebook_ejemplo.md \
        --modelo modelo-riesgo
"""

import argparse
import json
import os
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

SYSTEM_PROMPT = f"""Sos un agente experto en MLOps que genera codigo Python de produccion para Amazon SageMaker.

Recibes la ficha de un modelo (generada por notebook-archaeologist) y produces exactamente 4 archivos Python.
El codigo debe ser correcto, ejecutable y seguir las convenciones del SageMaker Python SDK.

Reglas:
- No cambies la logica del modelo. La migracion es iso-funcional.
- Usa el decorador @step del SageMaker SDK donde corresponda.
- El bucket S3 es: {BUCKET}
- El execution role ARN es: {ROLE_ARN}
- Region: {REGION}
- Nunca hardcodees credenciales ni ARNs de cuentas en el codigo de los modulos.
- Los modulos (preprocessing, train, evaluate) reciben paths de S3 como argumentos.
- El pipeline.py lee el bucket y el role de variables de entorno o parametros.

Reglas especificas por modulo:

- train.py:
  - Si la ficha indica un espacio de busqueda de hiperparametros, NO hardcodees los valores:
    recibilos como argumentos de linea de comandos (argparse), con el valor actual de la
    ficha como default. Asi el mismo train.py sirve para un training simple o para correr
    dentro de un HyperparameterTuner sin modificarlo.
  - Si la ficha dice "Fijos, no se detecto busqueda", usa los hiperparametros tal cual estan,
    igual como argumentos con esos defaults (permite overridearlos a futuro sin tocar codigo).

- evaluate.py:
  - Debe calcular la metrica de aceptacion que indica la ficha (seccion "Metrica de
    aceptacion y umbral") y escribirla en un evaluation.json con esta forma minima:
    {{"metrics": {{"<nombre_metrica>": {{"value": <float>}}}}, "umbral": <float o null>}}
  - Si la ficha referencia predicciones de referencia del notebook original (para test de
    paridad), evaluate.py debe compararlas contra las predicciones del modelo migrado
    reutilizando la funcion ya existente en el toolkit interno:
      from utils import compare_dataframes, analyse_dif
    No reimplementes esta logica de comparacion. Si la ficha no tiene predicciones de
    referencia, omiti el test de paridad y dejalo comentado con un TODO.

Responde UNICAMENTE con bloques de codigo en este formato exacto (nada antes, nada despues):

### preprocessing.py
```python
<codigo>
```

### train.py
```python
<codigo>
```

### evaluate.py
```python
<codigo>
```
"""

SYSTEM_PROMPT_PIPELINE = f"""Sos un agente experto en MLOps que genera codigo Python de produccion para Amazon SageMaker.

Recibes la ficha de un modelo y los modulos ya generados (preprocessing, train, evaluate).
Genera UNICAMENTE el pipeline.py que orquesta esos modulos con el SageMaker Python SDK.

Reglas generales:
- El bucket S3 es: {BUCKET}
- El execution role ARN es: {ROLE_ARN}
- Region: {REGION}
- El pipeline debe tener, en este orden: ProcessingStep (preprocess) → entrenamiento
  (TrainingStep simple o HyperparameterTuner, segun REGLA 5) → ProcessingStep (evaluate) →
  gate de aprobacion (REGLA 8) → ModelStep + RegisterModel → TransformStep.
- Lee el bucket y el role de variables de entorno con fallback a los valores por defecto.
- Usa la metrica y el umbral de la seccion "Metrica de aceptacion y umbral" de la ficha
  para el gate. Si la ficha dice "[DEFINIR con el dueno del modelo]", igual arma el gate
  pero dejalo con un umbral placeholder claramente marcado como TODO — nunca lo omitas
  silenciosamente, porque sin gate cualquier modelo se registraria automaticamente.

=== REGLAS CRITICAS (romper cualquiera causa error en ejecucion) ===

REGLA 1 — Usar PipelineSession, NO sagemaker.Session:
  from sagemaker.workflow.pipeline_context import PipelineSession
  sagemaker_session = PipelineSession(boto_session=boto3.Session(region_name=REGION))
  # Sin PipelineSession, model.create() se ejecuta en tiempo real en lugar de
  # capturarse como step argument, y el pipeline falla con TypeError.

REGLA 2 — Importar ParameterString explicitamente:
  from sagemaker.workflow.parameters import ParameterString
  # Este import NO viene incluido con Pipeline ni con PipelineSession.

REGLA 3 — ModelStep con nombre explicito y SKLearnModel:
  from sagemaker.sklearn import SKLearnModel
  from sagemaker.workflow.model_step import ModelStep

  model = SKLearnModel(
      name="<nombre-del-modelo>-model",  # OBLIGATORIO: sin name, el SDK llama urlparse()
      # sobre el Properties object (model_data) y falla con AttributeError: 'Properties'
      # object has no attribute 'decode'
      model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
      role=ROLE,
      entry_point="train.py",
      framework_version="1.2-1",
      py_version="py3",
      sagemaker_session=sagemaker_session,
  )
  step_create_model = ModelStep(
      name="CreateModelStep",
      step_args=model.create(instance_type="ml.m5.large"),
  )

REGLA 4 — TransformStep usa properties.ModelName, NUNCA model.name:
  transformer = Transformer(
      model_name=step_create_model.properties.ModelName,  # referencia lazy al step
      # model.name es None en tiempo de definicion del pipeline
      ...
  )

REGLA 5 — HPO solo si la ficha trae rangos de hiperparametros:
  from sagemaker.tuner import HyperparameterTuner, ContinuousParameter, IntegerParameter

  Si la ficha indica rangos ("Hiperparametros y espacio de busqueda"), reemplaza el
  TrainingStep simple por un TuningStep:
      tuner = HyperparameterTuner(
          estimator=estimator,
          objective_metric_name="<metrica_de_aceptacion_de_la_ficha>",
          hyperparameter_ranges={{...}},  # uno por hiperparametro con rango en la ficha
          metric_definitions=[{{"Name": "<metrica>", "Regex": r".*<metrica>:\\s*([0-9.]+).*"}}],
          max_jobs=10,
          max_parallel_jobs=2,
      )
      step_tuning = TuningStep(name="HPOStep", tuner=tuner, inputs={{...}})
  El mejor modelo se referencia con:
      step_tuning.get_top_model_s3_uri(top_k=0, s3_bucket=BUCKET, prefix=<prefix>)
  Si la ficha dice "Fijos, no se detecto busqueda", usa un TrainingStep normal con
  estimator.fit(...) — no agregues HPO donde no hay rangos que buscar.

REGLA 6 — Data Quality y Model Quality checks con Clarify/QualityCheckStep:
  from sagemaker.workflow.quality_check_step import QualityCheckStep, DataQualityCheckConfig, ModelQualityCheckConfig
  from sagemaker.workflow.check_job_config import CheckJobConfig

  check_job_config = CheckJobConfig(role=ROLE, sagemaker_session=sagemaker_session)

  data_quality_check_config = DataQualityCheckConfig(
      baseline_dataset=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
      dataset_format=DatasetFormat.csv(header=True),
      output_s3_uri=Join(on="/", values=["s3:/", BUCKET, project_path, "monitoring", "data-quality"]),
  )
  step_data_quality = QualityCheckStep(
      name="DataQualityCheck",
      skip_check=False,
      register_new_baseline=True,
      quality_check_config=data_quality_check_config,
      check_job_config=check_job_config,
  )
  # Analogo con ModelQualityCheckConfig sobre la salida del TransformStep, para
  # comparar la calidad del modelo migrado contra la baseline.

REGLA 7 — Explicabilidad con SageMaker Clarify (SHAP):
  from sagemaker.clarify import SHAPConfig, DataConfig
  from sagemaker.workflow.clarify_check_step import ClarifyCheckStep, ModelExplainabilityCheckConfig

  shap_config = SHAPConfig(baseline=[<fila_baseline>], num_samples=100, agg_method="mean_abs")
  model_explainability_config = ModelExplainabilityCheckConfig(
      data_config=DataConfig(
          s3_data_input_path=step_process.properties.ProcessingOutputConfig.Outputs["train_sample"].S3Output.S3Uri,
          s3_output_path=Join(on="/", values=["s3:/", BUCKET, project_path, "explainability"]),
          label="<target_col>",
          headers=[<features>],
      ),
      model_config=ModelConfig(model_name=step_create_model.properties.ModelName, instance_type="ml.m5.xlarge", instance_count=1),
      explainability_config=shap_config,
  )
  step_explainability = ClarifyCheckStep(
      name="ModelExplainabilityCheck",
      clarify_check_config=model_explainability_config,
      check_job_config=check_job_config,
      skip_check=True,        # no bloquea el pipeline por defecto: informa, no gatea
      register_new_baseline=True,
  )

REGLA 8 — Gate de aprobacion automatico (ConditionStep + FailStep), NUNCA lo omitas:
  from sagemaker.workflow.condition_step import ConditionStep
  from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
  from sagemaker.workflow.fail_step import FailStep
  from sagemaker.workflow.properties import PropertyFile
  from sagemaker.workflow.functions import JsonGet

  evaluation_report = PropertyFile(name="EvaluationReport", output_name="evaluation", path="evaluation.json")
  # step_eval (ProcessingStep de evaluate.py) debe declarar property_files=[evaluation_report]

  metric_value = JsonGet(
      step_name=step_eval.name,
      property_file=evaluation_report,
      json_path="metrics.<nombre_metrica>.value",
  )
  condition = ConditionGreaterThanOrEqualTo(left=metric_value, right=<umbral_de_la_ficha>)

  step_fail = FailStep(
      name="ModelBelowThreshold",
      error_message=Join(on=" ", values=["El modelo no supera el umbral de aceptacion:", metric_value]),
  )
  step_gate = ConditionStep(
      name="ApprovalGate",
      conditions=[condition],
      if_steps=[step_create_model, step_register, step_transform],  # solo si pasa el gate
      else_steps=[step_fail],
  )
  # El pipeline final expone step_gate (y sus dependencias previas), NUNCA registres o
  # transformes fuera de este condicional: es lo que reemplaza la aprobacion manual.

Responde UNICAMENTE con este bloque (nada antes, nada despues):

### pipeline.py
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


def call_bedrock_modules(ficha_content: str, modelo: str) -> str:
    """Genera preprocessing.py, train.py y evaluate.py."""
    client = _bedrock_client()

    user_message = f"""Genera los 3 modulos Python (preprocessing, train, evaluate) para migrar el siguiente modelo.
Nombre del modelo: {modelo}

<ficha>
{ficha_content}
</ficha>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8000,
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


def call_bedrock_pipeline(ficha_content: str, modelo: str) -> str:
    """Genera pipeline.py separado para evitar truncamiento."""
    client = _bedrock_client()

    user_message = f"""Genera el pipeline.py de SageMaker para el siguiente modelo.
Nombre del modelo: {modelo}

<ficha>
{ficha_content}
</ficha>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8000,
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
    """Extrae los 4 bloques de codigo y los guarda en las rutas correctas."""
    files = {
        "preprocessing.py": f"ml/src/{modelo}/preprocessing.py",
        "train.py":         f"ml/src/{modelo}/train.py",
        "evaluate.py":      f"ml/src/{modelo}/evaluate.py",
        "pipeline.py":      f"ml/pipelines/{modelo}/pipeline.py",
    }

    for filename, output_path in files.items():
        marker = f"### {filename}"
        if marker not in raw:
            print(f"WARN: no se encontro el bloque '{marker}' en la respuesta")
            continue

        start = raw.index(marker) + len(marker)
        # Buscar el bloque ```python ... ```
        code_start = raw.index("```python", start) + len("```python")
        code_end   = raw.index("```", code_start)
        code       = raw[code_start:code_end].strip()

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code + "\n", encoding="utf-8")
        print(f"  Guardado: {output_path}")


# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ML Pipeline Builder via Bedrock")
    parser.add_argument("--ficha",  required=True, help="Ruta a la ficha .md del modelo")
    parser.add_argument("--modelo", required=True, help="Nombre del modelo (ej: modelo-riesgo)")
    args = parser.parse_args()

    if not Path(args.ficha).exists():
        print(f"ERROR: No se encontro la ficha: {args.ficha}", file=sys.stderr)
        sys.exit(1)

    print(f"Leyendo ficha: {args.ficha}")
    ficha = load_ficha(args.ficha)
    print(f"   {len(ficha.split())} palabras en la ficha")

    print(f"\nLlamada 1/2 — generando modulos (preprocessing, train, evaluate)...")
    raw_modules = call_bedrock_modules(ficha, args.modelo)
    print("Guardando modulos generados:")
    parse_and_save(raw_modules, args.modelo)

    print(f"\nLlamada 2/2 — generando pipeline.py...")
    raw_pipeline = call_bedrock_pipeline(ficha, args.modelo)
    print("Guardando pipeline:")
    parse_and_save(raw_pipeline, args.modelo)

    print(f"\nDone. Pipeline listo en ml/pipelines/{args.modelo}/pipeline.py")
    print(f"Modulos en ml/src/{args.modelo}/")


if __name__ == "__main__":
    main()