# Progreso Demo — Nave ML Platform con Aceleradores IA
**Fecha inicio:** 2026-08-20  
**Demo:** Viernes 2026-08-22 · 2pm  
**Objetivo:** mostrar migración notebook → pipeline SageMaker acelerada con agentes IA via Bedrock

---

## Estado actual

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Infra Terraform | **Completo** | User profile + S3 + IAM + Bedrock |
| SageMaker Studio | **Corriendo** | Space `nave-demo-space` InService |
| Notebook de demo | **Corriendo** | 5000 clientes sintéticos, AUC ~0.5 |
| Agente notebook-archaeologist | **Funcionando** | Genera ficha via Bedrock Claude Sonnet 4.5 |
| Agente pipeline-builder | **Funcionando** | Genera 4 módulos Python via Bedrock |
| Pipeline SageMaker | **Pendiente** | `pipeline.py` generado, falta ejecutar |

---

## 1. Infraestructura (Terraform)

### Cuenta AWS
- **Cuenta sandbox Nubiral:** `015319782619`
- **Región:** `us-east-1`
- **Dominio SageMaker existente:** `d-7v1pspekpoad` (no se recreó)

### Recursos desplegados por Terraform

| Recurso | Nombre/ID |
|---------|-----------|
| IAM Role | `ar3306-nave-aceleradores-sagemaker-execution-role` |
| IAM Policy: SageMaker | `AmazonSageMakerFullAccess` (managed) |
| IAM Policy: S3 | `ar3306-nave-aceleradores-s3-access` (inline, scoped) |
| IAM Policy: Bedrock | `ar3306-nave-aceleradores-bedrock-access` (inline) |
| S3 Bucket | `ar3306-nave-aceleradores-ml-data-sandbox` |
| S3 Prefijos | `data/`, `models/`, `pipelines/` |
| S3 Versioning | Habilitado |
| S3 Encryption | AES256 |
| S3 Public Access Block | Bloqueado |
| SageMaker User Profile | `ar3306-nave-aceleradores-demo` |

### Política Bedrock (ARNs cubiertos)
```hcl
Actions: bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream
Resources:
  - arn:aws:bedrock:us-east-1::foundation-model/*
  - arn:aws:bedrock:us-east-1:015319782619:inference-profile/*
  - arn:aws:bedrock:*::foundation-model/*
```

### Problemas resueltos durante el despliegue

| Problema | Causa | Fix |
|---------|-------|-----|
| `terraform init` falla con DNS | Go runtime en Windows no usa DNS del sistema | `$env:GODEBUG="netdns=go"` |
| `aws_sagemaker_domain` data source no existe | Provider v5 no lo soporta | Reemplazado por `locals` + variable |
| SCP bloquea `CreateApp` | Tag `owner/project/team/etc` requerido | Activar `TagPropagation=ENABLED` en el dominio |
| `CreateApp` bloquea por inference-profile ARN | Policy solo cubría `foundation-model/*` | Agregar `inference-profile/*` al resource |

---

## 2. SageMaker Studio

### Space
- **Nombre:** `nave-demo-space`
- **Tipo:** JupyterLab · Private
- **Estado:** InService
- **Instancia:** `ml.t3.medium`
- **Image:** `arn:aws:sagemaker:us-east-1:885854791233:image/sagemaker-distribution-cpu`
- **Owner:** `ar3306-nave-aceleradores-demo`

### Cómo levantar el Space (si está Stopped)
```python
import boto3
sm = boto3.client('sagemaker', region_name='us-east-1')
sm.create_app(
    DomainId='d-7v1pspekpoad',
    SpaceName='nave-demo-space',
    AppType='JupyterLab',
    AppName='default',
    ResourceSpec={
        'SageMakerImageArn': 'arn:aws:sagemaker:us-east-1:885854791233:image/sagemaker-distribution-cpu',
        'InstanceType': 'ml.t3.medium'
    },
    Tags=[
        {'Key': 'owner',     'Value': 'santiago.castro@nubiral.com'},
        {'Key': 'project',   'Value': 'ar3306-nave-aceleradores'},
        {'Key': 'createdBy', 'Value': 'santiago.castro@nubiral.com'},
        {'Key': 'team',      'Value': 'pod7'},
        {'Key': 'deadline',  'Value': '2026-12-31'},
    ]
)
```

---

## 3. Notebook de demo

### Archivo
`legacy/modelo-demo/nave_notebook_ejemplo.ipynb`

### Qué hace
Simula un notebook real de Nave: modelo de scoring de riesgo (GradientBoostingClassifier) que predice `default_90d` para una cartera de clientes.

### Características del notebook (intencionalmente "malo" para la demo)
- Dependencias sin versiones (`import sklearn`)
- Ruta hardcodeada: `/data/clientes_activos.csv` (fallback a datos sintéticos)
- Sin logging, sin manejo de errores, sin tests
- Mezcla entrenamiento y scoring en el mismo script
- Guarda en rutas locales

### Datos
- **5000 clientes sintéticos** generados con `np.random.seed(42)`
- Features: edad, antiguedad_meses, saldo_promedio_90d, cant_productos, dias_ultimo_movimiento, ratio_utilizacion_credito, cant_cuotas_atrasadas, segmento
- Target: `default_90d` (tasa de default ~8%)
- Output: `/tmp/output/scoring_semanal.csv`

---

## 4. Agentes de IA via Bedrock

### Modelo usado
```
us.anthropic.claude-sonnet-4-5-20250929-v1:0
```
(inference profile — requerido para modelos Claude nuevos en Bedrock)

### Agente 1: notebook-archaeologist
**Script:** `ml/agents/notebook_archaeologist.py`  
**Input:** notebook `.ipynb`  
**Output:** ficha Markdown estructurada en `docs/inventario/`

```bash
python ml/agents/notebook_archaeologist.py \
    --notebook legacy/modelo-demo/nave_notebook_ejemplo.ipynb \
    --output docs/inventario/modelo-demo.md
```

**Ficha generada:** `docs/inventario/nave_notebook_ejemplo.md`  
Contiene: features, preprocesamiento, algoritmo, dependencias, fuente de datos, salida, riesgo regulatorio, ambigüedades.

### Agente 2: pipeline-builder
**Script:** `ml/agents/pipeline_builder.py`  
**Input:** ficha Markdown  
**Output:** 4 archivos Python de SageMaker

```bash
python ml/agents/pipeline_builder.py \
    --ficha docs/inventario/nave_notebook_ejemplo.md \
    --modelo modelo-riesgo
```

**Diseño:** 2 llamadas separadas a Bedrock (evita truncamiento por límite de tokens):
- Llamada 1 (6000 tokens): `preprocessing.py` + `train.py` + `evaluate.py`
- Llamada 2 (4000 tokens): `pipeline.py`

---

## 5. Archivos generados por los agentes

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `docs/inventario/nave_notebook_ejemplo.md` | 104 | Ficha completa del modelo |
| `ml/src/modelo-riesgo/preprocessing.py` | 152 | Imputación, encoding, scaling → S3 |
| `ml/src/modelo-riesgo/train.py` | 147 | GradientBoostingClassifier → modelo en S3 |
| `ml/src/modelo-riesgo/evaluate.py` | 199 | Métricas AUC, clasificación, scoring |
| `ml/pipelines/modelo-riesgo/pipeline.py` | 213 | Orquestación ProcessingStep→TrainingStep→TransformStep |

### Estructura del pipeline generado
```
pipeline = Pipeline(
    name = "modelo-riesgo-pipeline",
    steps = [
        ProcessingStep  → preprocessing.py  (SKLearnProcessor, ml.m5.xlarge)
        TrainingStep    → train.py           (SKLearn estimator, ml.m5.xlarge)
        TransformStep   → batch scoring      (ml.m5.xlarge)
    ]
)
pipeline.upsert(role_arn=ROLE)
execution = pipeline.start()
```

---

## 6. Pendiente para completar la demo

### Crítico (antes del viernes)
- [ ] **Subir datos de prueba al bucket S3**
  ```bash
  aws s3 cp /tmp/output/scoring_semanal.csv \
      s3://ar3306-nave-aceleradores-ml-data-sandbox/modelo-riesgo/input/clientes_activos.csv
  ```
- [ ] **Ejecutar el pipeline** desde Studio:
  ```bash
  cd ar3306-nave-mvp-aceleradores
  python ml/pipelines/modelo-riesgo/pipeline.py
  ```
- [ ] **Verificar ejecución** en SageMaker → Pipelines → `modelo-riesgo-pipeline`
- [ ] **Ensayo completo** de la demo de punta a punta

### Nice-to-have
- [ ] MLflow configurado (tracking de experimentos)
- [ ] Video de backup del pipeline corriendo

---

## 7. Lecciones aprendidas / fixes aplicados

| Tema | Fix |
|------|-----|
| Terraform DNS en Windows | `$env:GODEBUG="netdns=go"` antes de cualquier comando |
| SageMaker Studio SCP tags | TagPropagation ENABLED en el dominio |
| Bedrock model EOL | Usar inference profile con prefijo `us.` |
| Bedrock timeout con output largo | Separar en 2 llamadas + `read_timeout=300` |
| Git en Studio sin identidad | `git config user.email/name` antes del primer commit |
| Git conflict en Studio | `git stash` → `git pull --rebase` → `git stash pop` |

---

## 8. Comandos de referencia

### Terraform (desde Windows)
```powershell
cd terraform
$env:GODEBUG="netdns=go"
terraform plan
terraform apply -auto-approve
```

### Verificar Space (estado)
```python
import boto3
sm = boto3.client('sagemaker', region_name='us-east-1')
r = sm.describe_app(DomainId='d-7v1pspekpoad', SpaceName='nave-demo-space', AppType='JupyterLab', AppName='default')
print(r['Status'])
```

### Flujo completo de agentes (desde Studio)
```bash
# 1. Arqueología del notebook
python ml/agents/notebook_archaeologist.py \
    --notebook legacy/modelo-demo/nave_notebook_ejemplo.ipynb

# 2. Generación del pipeline
python ml/agents/pipeline_builder.py \
    --ficha docs/inventario/nave_notebook_ejemplo.md \
    --modelo modelo-riesgo

# 3. Ejecutar el pipeline
python ml/pipelines/modelo-riesgo/pipeline.py
```
