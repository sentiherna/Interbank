variable "owner" {
  type        = string
  description = "Email @nubiral.com del responsable del proyecto"
}

variable "project" {
  type        = string
  description = "Nombre del proyecto en formato CRM: <crm-id>-<nombre> (kebab-case)"
}

variable "created_by" {
  type        = string
  description = "Email @nubiral.com del creador de los recursos"
}

variable "team" {
  type        = string
  description = "POD de Nubiral (ej: pod7)"
}

variable "deadline" {
  type        = string
  description = "Fecha límite del proyecto en formato YYYY-MM-DD"
}

variable "sagemaker_domain_id" {
  type        = string
  default     = "d-7v1pspekpoad"
  description = "ID del dominio SageMaker existente en la cuenta sandbox de Nubiral"
}
