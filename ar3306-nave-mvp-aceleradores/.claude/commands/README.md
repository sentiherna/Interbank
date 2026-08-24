# Slash commands para Claude Code

## /inventariar

```
Activar el agente notebook-archaeologist sobre el notebook en <ruta>.
Leer el notebook de punta a punta y producir la ficha en docs/inventario/<nombre>.md.
Reportar qué quedó marcado como [AMBIGUO].
```

## /migrar

```
Activar el agente ml-pipeline-builder sobre el modelo <nombre>.
Leer la ficha en docs/inventario/<nombre>.md y generar:
- ml/src/<nombre>/{preprocessing,train,evaluate}.py
- ml/pipelines/<nombre>/pipeline.py
- ml/tests/<nombre>/test_*.py
La migración es iso-funcional: no cambiar lógica, features ni hiperparámetros.
```
