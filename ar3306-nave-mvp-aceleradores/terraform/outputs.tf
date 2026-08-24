output "sagemaker_user_profile_arn" {
  description = "ARN del user profile de SageMaker para la demo"
  value       = aws_sagemaker_user_profile.demo.arn
}

output "sagemaker_execution_role_arn" {
  description = "ARN del rol de ejecución de SageMaker — usar en pipeline.py"
  value       = aws_iam_role.sagemaker_execution.arn
}

output "ml_data_bucket_name" {
  description = "Nombre del bucket S3 para datos de ML — usar en pipeline.py"
  value       = aws_s3_bucket.ml_data.id
}

output "ml_data_bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.ml_data.arn
}
