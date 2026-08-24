"""Audita un PDF metodologico contra Train usando GitHub Models.

Genera un unico archivo ``reporte_final.md``. Requiere GITHUB_TOKEN en el
entorno o en el archivo indicado por ``--env-file``.
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

try:
    import truststore
except ImportError:
    truststore = None

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

if truststore is not None:
    truststore.inject_into_ssl()

MODEL_ID = "openai/gpt-5.5"
API_URL = "https://models.github.ai/inference/chat/completions"
ARTIFACT_SUFFIXES = {".ipynb", ".py"}
CHUNK_SIZE = 42_000
SYSTEM_PROMPT = """Sos un auditor tecnico especializado en modelos PLAFT. Trabajas solo
con evidencia del PDF y de los artefactos entregados. Responde en espanol y Markdown.
Usa exclusivamente estos estados: CUMPLE, PARCIAL, NO EVIDENCIADO, NO APLICA y NO CUMPLE.
Nunca inventes metricas, periodos, parametros, nombres, resultados o referencias.
Una coincidencia conceptual no prueba el valor declarado. Toda evidencia de Train debe
citar ruta relativa y celda de notebook o linea de script. Si el codigo y el documento
se contradicen, declara NO CUMPLE o PARCIAL y explica la contradiccion."""


def load_environment(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def call_api(token: str, prompt: str, max_tokens: int) -> str:
    payload = {"model": MODEL_ID, "max_tokens": max_tokens, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]}
    request = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json",
    }, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub Models devolvio HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"No fue posible conectar con GitHub Models: {error.reason}") from error
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Respuesta inesperada de GitHub Models") from error


def split_text(text: str) -> list[str]:
    chunks = []
    while len(text) > CHUNK_SIZE:
        cut = text.rfind("\n\n", 0, CHUNK_SIZE)
        cut = cut if cut >= CHUNK_SIZE // 2 else CHUNK_SIZE
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def extract_pdf(path: Path) -> str:
    if fitz is None:
        raise RuntimeError("Falta PyMuPDF. Instala con: pip install pymupdf")
    pages = []
    with fitz.open(path) as document:
        for number, page in enumerate(document, 1):
            text = page.get_text("text").strip()
            pages.append(f"\n## Pagina {number}\n{text or '[Sin texto extraible]'}")
    return "\n".join(pages)


def load_artifact(path: Path, train_dir: Path) -> str:
    relative = path.relative_to(train_dir).as_posix()
    if path.suffix.lower() == ".ipynb":
        notebook = json.loads(path.read_text(encoding="utf-8"))
        entries = []
        for number, cell in enumerate(notebook.get("cells", []), 1):
            source = "".join(cell.get("source", []))
            if source.strip():
                entries.append(f"### {relative} | Celda {number} ({cell.get('cell_type', '')})\n{source}")
        return "\n\n".join(entries)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(f"{relative} | Linea {n}: {line}" for n, line in enumerate(lines, 1))


def artifact_paths(train_dir: Path) -> list[Path]:
    return sorted(path for path in train_dir.rglob("*") if path.is_file() and path.suffix.lower() in ARTIFACT_SUFFIXES)


def analyse_document(token: str, document_text: str, max_tokens: int) -> str:
    parts = []
    for number, chunk in enumerate(split_text(document_text), 1):
        parts.append(call_api(token, f"""Extrae todos los requisitos verificables del fragmento {number} del PDF.
Incluye pagina, seccion, valores exactos y evidencia tecnica requerida para datos, target,
temporalidad, muestreo, faltantes, variables, modelo, HPO, metricas, validacion,
explicabilidad, gobierno y resultados. No evalues aun.

<DOCUMENTO>\n{chunk}\n</DOCUMENTO>""", max_tokens))
    return "\n\n".join(parts)


def analyse_artifacts(token: str, paths: list[Path], train_dir: Path, max_tokens: int) -> str:
    reviews = []
    for path in paths:
        content = load_artifact(path, train_dir)
        fragments = []
        for number, chunk in enumerate(split_text(content), 1):
            fragments.append(call_api(token, f"""Realiza arqueologia tecnica del fragmento {number} del artefacto.
Identifica objetivo, entradas/salidas, fuente, target, horizonte, particiones,
preprocesamiento, variables, algoritmo, HPO, metricas, validaciones, artefactos,
dependencias y ambiguedades. Cita ruta, celda o linea exacta.

<ARTEFACTO>\n{chunk}\n</ARTEFACTO>""", max_tokens))
        reviews.append(f"## {path.relative_to(train_dir).as_posix()}\n" + "\n\n".join(fragments))
    return "\n\n".join(reviews)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audita un PDF contra Train con GPT-5.5 y genera un unico reporte")
    parser.add_argument("--document", required=True)
    parser.add_argument("--train-dir", required=True)
    parser.add_argument("--output-dir", default="docs/auditoria_documento_train")
    parser.add_argument("--env-file", default="C:\\Users\\b46637\\OneDrive - Interbank\\PLAFT\\Interbank\\PLAFT\\Desarrollo\\Minorista_regulado\\Documentacion\\github.env")
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()
    document = Path(args.document)
    train_dir = Path(args.train_dir)
    if not document.is_file():
        parser.error(f"No se encontro el PDF: {document}")
    if not train_dir.is_dir():
        parser.error(f"No se encontro Train: {train_dir}")
    load_environment(Path(args.env_file))
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("No se encontro GITHUB_TOKEN en el entorno ni en --env-file")
    paths = artifact_paths(train_dir)
    if not paths:
        parser.error("No se encontraron .ipynb ni .py en Train")
    document_text = extract_pdf(document)
    if not document_text.strip():
        parser.error("El PDF no tiene texto extraible")
    print(f"Modelo API: {MODEL_ID}")
    print(f"Artefactos: {len(paths)}")
    requirements = analyse_document(token, document_text, args.max_tokens)
    archaeology = analyse_artifacts(token, paths, train_dir, args.max_tokens)
    final_prompt = f"""Genera UN SOLO REPORTE FINAL de auditoria comparando el documento contra TODOS los artefactos.
No generes fichas separadas ni archivos adicionales. Debe contener exactamente:
# Reporte final de auditoria del modelo PLAFT
## Dictamen ejecutivo
## Matriz de trazabilidad
| ID | Pagina/seccion | Requisito declarado | Estado | Evidencia en Train | Hallazgo/accion |
## Hallazgos criticos
## Evidencia faltante
## Inventario de referencias

El dictamen ejecutivo debe decir claramente si la documentacion es CONSISTENTE o NO CONSISTENTE.
Cada evidencia debe tener ruta y celda/linea concreta. Usa solo la evidencia proporcionada.

<REQUISITOS>\n{requirements}\n</REQUISITOS>
<ARQUEOLOGIA TRAIN>\n{archaeology}\n</ARQUEOLOGIA TRAIN>"""
    report = call_api(token, final_prompt, args.max_tokens)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "reporte_final.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Reporte final generado: {report_path}")


if __name__ == "__main__":
    main()
