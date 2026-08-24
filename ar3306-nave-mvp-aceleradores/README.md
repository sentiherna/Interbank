# nave-mlplatform — MVP

Plataforma de ML para Nave. Migración de notebooks manuales a pipelines reproducibles en Amazon SageMaker, acelerada con agentes de IA (Claude Code).

## Contexto

Nave se está desacoplando de Grupo Galicia y construye su plataforma de datos propia en AWS. Hoy los modelos de ML corren en notebooks ejecutados a mano. Este repo es la propuesta de Nubiral para resolver eso.

Documento de arquitectura: [CLAUDE.md](CLAUDE.md)  
Plan de trabajo (6 semanas): [PLAN_DE_TRABAJO_MVP_1.md](PLAN_DE_TRABAJO_MVP_1.md)  
Demo del viernes: [DEMO.md](DEMO.md)

## Estructura

```
.
├── CLAUDE.md                        # Reglas operativas del repo (Claude Code las lee al iniciar)
├── DEMO.md                          # Guión de la demo del 22/08
├── TAGGING_POLICY.md                # Política de tags para la cuenta sandbox de Nubiral
├── .claude/
│   ├── agents/                      # Sub-agentes de Claude Code
│   │   ├── notebook-archaeologist.md
│   │   └── ml-pipeline-builder.md
│   └── settings.json                # Hooks (format, guardrails)
├── terraform/                       # Infraestructura en AWS
│   ├── main.tf                      # User profile SageMaker + bucket S3
│   ├── providers.tf
│   ├── variables.tf
│   ├── locals.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example     # Copiar a terraform.tfvars (no commitear)
├── ml/
│   ├── pipelines/modelo-demo/       # pipeline.py con @step
│   ├── src/modelo-demo/             # preprocessing.py, train.py, evaluate.py
│   └── tests/
├── legacy/modelo-demo/              # Notebook original + predicciones de referencia
├── notebooks/                       # Exploración nueva
└── docs/                            # ADRs, inventario de modelos
```

## Arrancar

```bash
# 1. Infraestructura
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con los valores del proyecto
terraform init
terraform plan
terraform apply

# 2. Claude Code (agentes)
# Instalar Claude Code y abrir el repo — lee CLAUDE.md automáticamente
claude

# 3. Demo rápida
/inventariar legacy/modelo-demo/nave_notebook_ejemplo.ipynb
/migrar modelo-demo
```

## Cuenta AWS

| Campo | Valor |
|-------|-------|
| Sandbox | `015319782619` (Nubiral) |
| Región | `us-east-1` |
| Dominio SageMaker existente | `d-7v1pspekpoad` |

## Equipo

| Rol | Persona |
|-----|---------|
| Tech Lead | santiago.castro@nubiral.com |
