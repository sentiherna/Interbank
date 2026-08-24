# Ficha del modelo: Scoring de Riesgo — Nave

## Qué hace
Genera un score de probabilidad de default (mora a 90 días) para clientes activos de un banco. El equipo de riesgo consume el archivo semanal para decisiones de gestión de cartera.

## Features de entrada
| Feature | Tipo | Descripción |
|---------|------|-------------|
| edad | Numérico (entero) | Edad del cliente en años |
| antiguedad_meses | Numérico (entero) | Antigüedad del cliente en meses |
| saldo_promedio_90d | Numérico (float) | Saldo promedio de los últimos 90 días |
| cant_productos | Numérico (entero) | Cantidad de productos contratados |
| dias_ultimo_movimiento | Numérico (entero) | Días transcurridos desde el último movimiento |
| ratio_utilizacion_credito | Numérico (float) | Ratio de utilización de crédito (0-1) |
| cant_cuotas_atrasadas | Numérico (entero) | Cantidad de cuotas atrasadas |
| segmento | Categórico | Segmento del cliente: RETAIL, PYME o CORPORATIVO |

## Preprocesamiento
1. **Imputación de nulos**: Se imputan valores faltantes en features numéricos con la mediana de cada columna (acordado con equipo de riesgo en julio 2024)
2. **Encoding categórico**: La variable `segmento` se codifica manualmente con mapping:
   - RETAIL → 0
   - PYME → 1
   - CORPORATIVO → 2
   - Valores nulos → 0 (asignados a RETAIL)
3. **Scaling**: StandardScaler aplicado sobre todas las features (numéricas + segmento_encoded)
4. **Feature engineering**: No hay transformaciones adicionales ni variables derivadas

## Algoritmo
**Nombre:** GradientBoostingClassifier (scikit-learn)

**Hiperparámetros fijos** (según exploración de diciembre 2023, no modificar sin consultar al equipo de riesgo):
- n_estimators: 200
- learning_rate: 0.05
- max_depth: 4
- subsample: 0.8
- random_state: 42

**Target:** `default_90d` (binario: 1 = entró en mora en últimos 90 días, 0 = no)

## Dependencias
| Librería | Versión detectada | Versión a pinnear |
|----------|-------------------|-------------------|
| pandas | [AMBIGUO] | pandas==1.5.3 |
| numpy | [AMBIGUO] | numpy==1.24.3 |
| scikit-learn | [AMBIGUO] | scikit-learn==1.2.2 |
| pickle | stdlib | - |

**Nota:** Las versiones exactas no están especificadas en el notebook. Se recomienda verificar las versiones del ambiente actual antes de migrar.

## Fuente de datos
**Origen:** `/data/clientes_activos.csv`

**Proceso upstream:** CSV generado por proceso de extracción ejecutado por el área de Infraestructura los domingos. Contacto: Martín (según comentario en código).

**Formato:** CSV con 10 columnas (cliente_id + 8 features + target)

**Fallback:** Si el archivo no existe, el notebook genera datos sintéticos con `np.random.seed(42)` y 5000 registros para demostración.

**[AMBIGUO]:** No hay especificación del esquema de validación del CSV ni manejo de errores si la estructura difiere.

## Salida
**Formato:** CSV con 3 columnas
- `cliente_id`: identificador del cliente
- `score_riesgo`: probabilidad de default (float entre 0 y 1)
- `riesgo_alto`: flag binario (1 si score_riesgo >= 0.6, 0 en caso contrario)

**Ubicación:** `/tmp/output/scoring_semanal.csv` (nota: en el notebook original menciona `/data/output/` pero guarda en `/tmp/output/`)

**Artefactos adicionales:** 
- Modelo serializado con pickle en `/tmp/models/modelo_riesgo_v1.pkl` (contiene dict con 'model' y 'scaler')

**Frecuencia:** Generación semanal (lunes a la mañana según documentación)

## Riesgo regulatorio
**[DEFINIR con el dueño del modelo]** ¿Participa en decisiones que afectan a un cliente?

**Contexto identificado:** El score alimenta al "equipo de riesgo" para "decisiones de gestión de cartera". Esto sugiere potencial impacto en:
- Límites de crédito
- Tasas de interés
- Cobranzas
- Aprobaciones de productos

**Requiere confirmación urgente:** Si se usa para decisiones automatizadas que afectan a clientes (ej: bajar límite de crédito, denegar productos), podría caer bajo regulaciones de riesgo de modelos y requerir gobernanza adicional.

## Ambigüedades pendientes
- [AMBIGUO] **Discrepancia en rutas de output:** El markdown menciona `/data/output/scoring_semanal.csv` pero el código guarda en `/tmp/output/`. Confirmar ruta correcta en producción.
- [AMBIGUO] **Versionado de dependencias:** No hay especificación de versiones de librerías. Verificar ambiente actual antes de migrar.
- [AMBIGUO] **Validación del CSV de entrada:** No hay chequeos de esquema, tipos de datos, ni rangos válidos para features.
- [AMBIGUO] **Umbral de riesgo_alto (0.6):** No hay documentación sobre cómo se definió este umbral ni si está calibrado con el negocio.
- [AMBIGUO] **Proceso de re-entrenamiento:** No está claro si el modelo se re-entrena semanalmente o solo se aplica scoring con modelo fijo.
- [AMBIGUO] **Manejo de datos nuevos:** ¿Qué pasa si aparecen nuevos valores de `segmento` no mapeados en el encoding?
- [AMBIGUO] **Train/test split:** Se hace split en el código pero el modelo final se entrena solo con train. ¿Se valida en producción con test o es solo para monitoreo?

## Mejoras potenciales (no implementar ahora)
- **Logging estructurado:** Agregar logging de métricas (AUC, distribución de scores) para monitoreo en el tiempo
- **Validación de esquema:** Implementar validación con pandera o great_expectations antes de procesar
- **Manejo robusto de categorías:** Usar scikit-learn OrdinalEncoder o OneHotEncoder en lugar de mapping manual
- **Monitoreo de drift:** Trackear distribución de features y scores para detectar data drift
- **Versionado de modelos:** Usar MLflow o similar en lugar de pickle manual con nombre versionado
- **Threshold optimization:** Calibrar el umbral 0.6 con matriz de costos del negocio (falsos positivos vs falsos negativos)
- **Feature importance:** Agregar análisis de importancia de variables para interpretabilidad
- **Separación de train/inference:** El notebook mezcla entrenamiento y scoring. En producción idealmente son jobs separados
- **Manejo de clientes nuevos:** Definir estrategia para clientes sin historial suficiente (cold start)
- **Documentación de cambios en hiperparámetros:** Los params vienen de diciembre 2023, establecer proceso formal para actualizarlos