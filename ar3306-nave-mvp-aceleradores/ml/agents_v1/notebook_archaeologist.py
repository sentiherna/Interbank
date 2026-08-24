"""
notebook_archaeologist.py — Agente de arqueología de notebooks vía Amazon Bedrock

Uso desde la terminal de SageMaker Studio:
    python notebook_archaeologist.py --notebook <ruta_al_notebook> [--output <ruta_salida>]

Ejemplo:
    python notebook_archaeologist.py \
        --notebook legacy/modelo-demo/nave_notebook_ejemplo.ipynb \
        --output docs/inventario/modelo-demo.md
"""

import argparse
import json
import sys
from pathlib import Path

import boto3


# ─── Configuración ────────────────────────────────────────────────────────────

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION = "us-east-1"

SYSTEM_PROMPT = """Sos un agente de arqueología de notebooks de Machine Learning.
Tu trabajo es leer un notebook que alguien escribió y producir una ficha estructurada
que permita a otro agente migrarlo a SageMaker sin ambigüedades.

Reglas:
- No modificás el notebook. Solo leés.
- No asumís nada que no esté en el código. Si algo no está claro, lo marcás como [AMBIGUO].
- No mejorás el modelo. Documentás lo que existe.
- Si encontrás una mejora posible, la anotás en la sección "Mejoras potenciales" y seguís.

Producí la ficha en formato Markdown con exactamente esta estructura:

# Ficha del modelo: <nombre>

## Qué hace
<Una o dos oraciones. Qué decide o informa, quién lo consume.>

## Features de entrada
| Feature | Tipo | Descripción |
|---------|------|-------------|

## Preprocesamiento
<Paso a paso: imputación, encoding, scaling, feature engineering>

## Algoritmo
<Nombre, hiperparámetros usados, si están fijos o variados>

## Hiperparámetros y espacio de búsqueda
<Para cada hiperparámetro relevante: valor actual y, si tiene sentido tunearlo, un rango
razonable (ej: learning_rate: 0.01–0.3). Si el notebook no varía hiperparámetros, indicar
"Fijos, no se detectó búsqueda" — el agente de pipelines usará esto para decidir si arma
un HyperparameterTuner o un entrenamiento simple.>

## Métrica de aceptación y umbral
<Métrica que decide si el modelo migrado es aceptable (ej: AUC, RMSE, F1) y contra qué se
compara: el modelo original (test de paridad) y/o un umbral mínimo de negocio. Si no está
definido en el notebook, marcar "[DEFINIR con el dueño del modelo]" — sin esto, el pipeline
no puede armar el gate de aprobación automático.>

## Dependencias
| Librería | Versión detectada | Versión a pinnear |
|----------|-------------------|-------------------|

## Fuente de datos
<De dónde vienen los datos: ruta, query, formato>

## Salida
<Qué produce: predicciones, probabilidades, scores. Formato y dónde se guardan. Si el
notebook ya generó predicciones de referencia (para comparar contra el modelo migrado),
indicar dónde están — se usan como baseline del test de paridad.>

## Riesgo regulatorio
[DEFINIR con el dueño del modelo] ¿Participa en decisiones que afectan a un cliente?

## Ambigüedades pendientes
- [AMBIGUO] <si las hay>

## Mejoras potenciales (no implementar ahora)
- <si las hay>
"""


# ─── Funciones ────────────────────────────────────────────────────────────────

def load_notebook(path: str) -> str:
    """Lee un .ipynb y extrae el código fuente de todas las celdas."""
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells_text = []
    for i, cell in enumerate(nb.get("cells", []), 1):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))
        if source.strip():
            cells_text.append(f"### Celda {i} ({cell_type})\n{source}")

    return "\n\n".join(cells_text)


def call_bedrock(notebook_content: str) -> str:
    """Llama a Claude vía Bedrock y retorna la ficha generada."""
    client = boto3.client("bedrock-runtime", region_name=REGION)

    user_message = f"""Analizá el siguiente notebook y generá la ficha de arqueología completa.

<notebook>
{notebook_content}
</notebook>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def save_output(content: str, output_path: str) -> None:
    """Guarda la ficha en el archivo de destino."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"\nFicha guardada en: {output_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Notebook Archaeologist vía Bedrock")
    parser.add_argument("--notebook", required=True, help="Ruta al notebook .ipynb")
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta de salida para la ficha .md (default: docs/inventario/<nombre>.md)",
    )
    args = parser.parse_args()

    notebook_path = args.notebook
    if not Path(notebook_path).exists():
        print(f"ERROR: No se encontro el notebook: {notebook_path}", file=sys.stderr)
        sys.exit(1)

    # Nombre base para el output
    notebook_name = Path(notebook_path).stem
    output_path = args.output or f"docs/inventario/{notebook_name}.md"

    print(f"Leyendo notebook: {notebook_path}")
    notebook_content = load_notebook(notebook_path)
    print(f"   {len(notebook_content.split())} palabras extraidas de {notebook_path}")

    print(f"\nLlamando a Claude ({MODEL_ID}) via Bedrock...")
    ficha = call_bedrock(notebook_content)

    print("\n" + "-" * 60)
    print(ficha)
    print("-" * 60)

    save_output(ficha, output_path)


if __name__ == "__main__":
    main()