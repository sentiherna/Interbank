# Política de Tagging — Cuenta Sandbox Nubiral

## Índice

- [1. Resumen Ejecutivo](#1-resumen-ejecutivo)
- [2. Tags Obligatorios](#2-tags-obligatorios)
- [3. Implementación en Terraform](#3-implementación-en-terraform)
- [4. Validación y Cumplimiento](#4-validación-y-cumplimiento)
- [5. Referencias](#5-referencias)

---

## 1. Resumen Ejecutivo

Este documento define la política de tagging para todos los recursos AWS desplegados en la **cuenta sandbox de Nubiral** (`015319782619`, región `us-east-1`).

Aplica a **cualquier proyecto** desplegado en esta cuenta. Cada proyecto llena sus propios valores según la tabla de §2.

| Campo | Valor fijo |
|-------|-----------|
| **Cuenta AWS** | `015319782619` |
| **Propietario** | Nubiral |
| **Región** | `us-east-1` |
| **Escenario de Tagging** | Escenario 1 — Consumo Interno (NUB-ALI-POL-001 v1.1) |

> **Control automático activo**: la cuenta rechaza la creación de recursos que no incluyan todos los tags obligatorios. No es posible omitir ninguno.

---

## 2. Tags Obligatorios

### 2.1 Estructura

```hcl
# Proyecto: ar3306-nave-aceleradores
locals {
  tags = {
    owner     = "santiago.castro@nubiral.com"
    project   = "ar3306-nave-aceleradores"
    createdBy = "santiago.castro@nubiral.com"
    team      = "pod7"
    deadline  = "2026-12-31"
  }
}
```

### 2.2 Descripción de cada tag

| Tag | Descripción | Valor — Proyecto Nave |
|-----|-------------|----------------------|
| `owner` | Email del responsable del recurso | `santiago.castro@nubiral.com` |
| `project` | Identificador del proyecto (kebab-case) | `ar3306-nave-aceleradores` |
| `createdBy` | Email de quien crea el recurso | `santiago.castro@nubiral.com` |
| `team` | POD de Nubiral | `pod7` |
| `deadline` | Fecha límite del proyecto | `2026-12-31` |

### 2.3 Tags del proyecto Nave

Estos son los valores definitivos — no hay placeholders pendientes:

```hcl
locals {
  tags = {
    owner     = "santiago.castro@nubiral.com"
    project   = "ar3306-nave-aceleradores"
    createdBy = "santiago.castro@nubiral.com"
    team      = "pod7"
    deadline  = "2026-12-31"
  }
}
```

---

## 3. Implementación en Terraform

### 3.1 Definición central

Los tags se definen una sola vez en `variables.tf` o en un `locals` block del módulo raíz y se propagan a todos los recursos.

```hcl
# terraform/locals.tf
locals {
  tags = {
    owner     = var.owner
    project   = var.project
    createdBy = var.created_by
    team      = var.team
    deadline  = var.deadline
  }
}
```

```hcl
# terraform/variables.tf
variable "owner"      { type = string }
variable "project"    { type = string }
variable "created_by" { type = string }
variable "team"       { type = string }
variable "deadline"   { type = string }
```

```hcl
# terraform/terraform.tfvars
owner       = "santiago.castro@nubiral.com"
project     = "ar3306-nave-aceleradores"
created_by  = "santiago.castro@nubiral.com"
team        = "pod7"
deadline    = "2026-12-31"
```

### 3.2 Aplicación en recursos

Pasar `local.tags` al argumento `tags` de cada recurso:

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${var.project_id}-data-sandbox"
  tags   = local.tags
}

resource "aws_sagemaker_domain" "studio" {
  domain_name = "${var.project_id}-studio"
  # ... resto de la config
  tags = local.tags
}
```

### 3.3 Tags heredados (default_tags)

Para aplicar los tags automáticamente a **todos** los recursos sin declararlos uno por uno, usar el bloque `default_tags` en el provider:

```hcl
# terraform/providers.tf
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = local.tags
  }
}
```

> Con `default_tags` activo, Terraform aplica los tags a todos los recursos del provider. Solo se necesita declarar `tags` explícitamente si algún recurso requiere tags adicionales.

---

## 4. Validación y Cumplimiento

### 4.1 Validación pre-deploy

```bash
# Ver qué tags se van a aplicar
terraform plan | grep -A 10 "tags"

# Verificar que el plan no tiene recursos sin tags
terraform plan -out=tfplan
terraform show -json tfplan | jq '[.resource_changes[].change.after.tags] | map(select(. == null))'
```

### 4.2 Validación post-deploy

```bash
# Ver tags de un bucket S3 específico
aws s3api get-bucket-tagging \
  --bucket <nombre-del-bucket> \
  --region us-east-1

# Buscar todos los recursos del proyecto por tag
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=project_id,Values=<crm-id> \
  --region us-east-1
```

### 4.3 Auditoría periódica

**Frecuencia recomendada**: al inicio de cada proyecto y mensual durante su ejecución.

**Checklist**:
- [ ] Todos los recursos tienen los 5 tags obligatorios
- [ ] No hay recursos huérfanos sin tags (creados manualmente por consola)
- [ ] La fecha `deadline` está vigente y actualizada
- [ ] El `project_id` coincide con el CRM de Nubiral

---

## 5. Referencias

### 5.1 Documentos Nubiral

- **NUB-ALI-POL-001** — Política de Tagging de Recursos en Nube AWS
- **NUB-ALI-REF-002** — AWS Códigos Marketplace PRM

### 5.2 Contactos

| Tema | Contacto |
|------|----------|
| Política de Tagging / PODs | PMO — lorena.censori@nubiral.com |
| Product Codes APN | Alianzas — laura.luengas@nubiral.com |

### 5.3 AWS

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/whitepapers/latest/tagging-best-practices/tagging-best-practices.html)
- [Terraform AWS Provider — default_tags](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags)
- [AWS Resource Groups & Tag Editor](https://console.aws.amazon.com/resource-groups/tag-editor)

---

**Última actualización**: 2026-08-19  
**Aplica a**: Cuenta sandbox Nubiral `015319782619`  
**Referencia normativa**: NUB-ALI-POL-001 v1.1 — Escenario 1 (Consumo Interno)
