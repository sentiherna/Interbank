"""
pipeline_builder.py — Agente de construccion de pipelines SageMaker via Amazon Bedrock

Lee la ficha generada por notebook-archaeologist y produce:
  - ml/src/<modelo>/preprocessing.py
  - ml/src/<modelo>/train.py
  - ml/src/<modelo>/evaluate.py
  - ml/pipelines/<modelo>/pipeline.py

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
- El pipeline debe tener: ProcessingStep, TrainingStep, ModelStep, TransformStep (en ese orden).
- Lee el bucket y el role de variables de entorno con fallback a los valores por defecto.

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
  pipeline = Pipeline(
      steps=[step_process, step_train, step_create_model, step_transform],
      ...
  )

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
        "max_tokens": 4000,
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
