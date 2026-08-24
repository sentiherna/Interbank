from sagemaker.workflow.steps import ProcessingStep, ModelStep, LambdaStep, ConditionStep
from sagemaker.workflow.condition_step import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.model_step import ModelMetrics, MetricsSource
from sagemaker.workflow import Pipeline
from sagemaker.workflow.execution_variables import ExecutionVariables
from sagemaker import get_execution_role
from sagemaker.s3 import S3Uploader
from sagemaker.workflow.lambda_step import Lambda
from sagemaker.workflow.fail_step import FailStep

# Configuración de los pasos del pipeline
step_eval = ProcessingStep(
    name=f'{base_name}-EvaluateBestModel',
    step_args=processor_args,
    property_files=[evaluation_report],
    cache_config=cache_config,
)

model_metrics = ModelMetrics(
    model_data_statistics=MetricsSource(
        s3_uri=model_quality_check_step.properties.CalculatedBaselineStatistics,




