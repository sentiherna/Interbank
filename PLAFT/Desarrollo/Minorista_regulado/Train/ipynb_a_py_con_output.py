import json
import sys
from pathlib import Path

def comment_block(text, prefix="# "):
    lines = str(text).splitlines()
    return "\n".join(prefix + line for line in lines)

def extract_text_output(output):
    output_type = output.get("output_type")

    if output_type == "stream":
        text = output.get("text", "")
        if isinstance(text, list):
            text = "".join(text)
        return text

    if output_type in ("execute_result", "display_data"):
        data = output.get("data", {})

        if "text/plain" in data:
            text = data["text/plain"]
            if isinstance(text, list):
                text = "".join(text)
            return text

        # Si solo tiene gráfico/HTML/etc.
        tipos = ", ".join(data.keys())
        return f"[Output no textual: {tipos}]"

    if output_type == "error":
        ename = output.get("ename", "")
        evalue = output.get("evalue", "")
        traceback = output.get("traceback", [])

        # Limpiar códigos ANSI básicos
        traceback_text = "\n".join(traceback)

        return (
            f"{ename}: {evalue}\n"
            f"{traceback_text}"
        )

    return ""

def convert_ipynb_to_py(ipynb_path, py_path=None):
    ipynb_path = Path(ipynb_path)

    if py_path is None:
        py_path = ipynb_path.with_suffix(".py")
    else:
        py_path = Path(py_path)

    with open(ipynb_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    partes = []

    partes.append(
        "# Archivo generado desde Jupyter Notebook\n"
        f"# Origen: {ipynb_path.name}\n"
    )

    for i, cell in enumerate(notebook.get("cells", []), start=1):
        cell_type = cell.get("cell_type")
        source = cell.get("source", [])

        if isinstance(source, list):
            source = "".join(source)

        if cell_type == "markdown":
            partes.append(
                f"\n# %% [markdown]\n"
                f"# --- CELDA MARKDOWN {i} ---\n"
                f"{comment_block(source)}\n"
            )

        elif cell_type == "code":
            execution_count = cell.get("execution_count")

            partes.append(
                f"\n# %%\n"
                f"# --- CELDA DE CÓDIGO {i} ---\n"
                f"# execution_count: {execution_count}\n"
            )

            partes.append(source.rstrip() + "\n")

            outputs = cell.get("outputs", [])

            if outputs:
                partes.append("\n# --- OUTPUT ---\n")

                for j, output in enumerate(outputs, start=1):
                    texto = extract_text_output(output)

                    if texto:
                        partes.append(
                            f"# Output {j}:\n"
                            f"{comment_block(texto)}\n"
                        )

                partes.append("# --- FIN OUTPUT ---\n")

    contenido = "\n".join(partes)

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"Archivo generado: {py_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso:\n"
            "python ipynb_a_py_con_output.py archivo.ipynb\n"
            "o\n"
            "python ipynb_a_py_con_output.py archivo.ipynb salida.py"
        )
        sys.exit(1)

    entrada = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else None

    convert_ipynb_to_py(entrada, salida)