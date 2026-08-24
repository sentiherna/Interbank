# ─────────────────────────────────────────────
# Dominio SageMaker existente — referenciado por variable
# (data source aws_sagemaker_domain no existe en el provider)
# ─────────────────────────────────────────────
locals {
  sagemaker_domain_id = var.sagemaker_domain_id
}

data "aws_caller_identity" "current" {}

# ─────────────────────────────────────────────
# IAM — Rol de ejecución de SageMaker
# ─────────────────────────────────────────────
resource "aws_iam_role" "sagemaker_execution" {
  name = "${var.project}-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full" {
  role       = aws_iam_role.sagemaker_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project}-s3-access"
  role = aws_iam_role.sagemaker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.ml_data.arn,
        "${aws_s3_bucket.ml_data.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.project}-bedrock-access"
  role = aws_iam_role.sagemaker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
      Resource = [
        "arn:aws:bedrock:us-east-1::foundation-model/*",
        "arn:aws:bedrock:us-east-1:${data.aws_caller_identity.current.account_id}:inference-profile/*",
        "arn:aws:bedrock:*::foundation-model/*"
      ]
    }]
  })
}

# ─────────────────────────────────────────────
# SageMaker — User profile para la demo
# ─────────────────────────────────────────────
resource "aws_sagemaker_user_profile" "demo" {
  domain_id         = local.sagemaker_domain_id
  user_profile_name = "${var.project}-demo"

  user_settings {
    execution_role = aws_iam_role.sagemaker_execution.arn
  }
}

# ─────────────────────────────────────────────
# S3 — Bucket de datos de ML
# ─────────────────────────────────────────────
resource "aws_s3_bucket" "ml_data" {
  bucket = "${var.project}-ml-data-sandbox"
}

resource "aws_s3_bucket_versioning" "ml_data" {
  bucket = aws_s3_bucket.ml_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ml_data" {
  bucket = aws_s3_bucket.ml_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ml_data" {
  bucket                  = aws_s3_bucket.ml_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Carpetas lógicas dentro del bucket
resource "aws_s3_object" "prefix_data" {
  bucket  = aws_s3_bucket.ml_data.id
  key     = "data/"
  content = ""
}

resource "aws_s3_object" "prefix_models" {
  bucket  = aws_s3_bucket.ml_data.id
  key     = "models/"
  content = ""
}

resource "aws_s3_object" "prefix_pipelines" {
  bucket  = aws_s3_bucket.ml_data.id
  key     = "pipelines/"
  content = ""
}
