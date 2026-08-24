import os
import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, TransformStep
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.parameters import ParameterString
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.estimator import Estimator
from sagemaker.transformer import Transformer
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.inputs import TrainingInput, TransformInput
from sagemaker.workflow.model_step import ModelStep
from sagemaker.sklearn import SKLearnModel
from sagemaker.workflow.properties import PropertyFile

# Configuración de entorno
BUCKET = os.environ.get('SAGEMAKER_BUCKET', 'ar3306-nave-aceleradores-ml-data-sandbox')
ROLE = os.environ.get('SAGEMAKER_ROLE', 'arn:aws:iam::015319782619:role/ar3306-nave-aceleradores-sagemaker-execution-role')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# PipelineSession es OBLIGATORIO para ModelStep: intercepta model.create()
# y lo captura como step argument en lugar de ejecutarlo en tiempo real.
sagemaker_session = PipelineSession(boto_session=boto3.Session(region_name=REGION))

# Parámetros del pipeline
input_data_path = ParameterString(
    name="InputDataPath",
    default_value=f"s3://{BUCKET}/modelo-riesgo/input/clientes_activos.csv"
)

model_approval_status = ParameterString(
    name="ModelApprovalStatus",
    default_value="PendingManualApproval"
)

processing_instance_type = ParameterString(
    name="ProcessingInstanceType",
    default_value="ml.m5.xlarge"
)

training_instance_type = ParameterString(
    name="TrainingInstanceType",
    default_value="ml.m5.xlarge"
)

transform_instance_type = ParameterString(
    name="TransformInstanceType",
    default_value="ml.m5.xlarge"
)


def create_pipeline():
    """
    Crea el pipeline de SageMaker para el modelo de scoring de riesgo.
    
    Pipeline estructura:
    1. ProcessingStep: Preprocesamiento de datos (imputación, encoding, scaling)
    2. TrainingStep: Entrenamiento del GradientBoostingClassifier
    3. TransformStep: Generación de scores de riesgo para clientes activos
    """
    
    # ====================
    # STEP 1: PREPROCESSING
    # ====================
    sklearn_processor = SKLearnProcessor(
        framework_version="1.2-1",
        instance_type=processing_instance_type,
        instance_count=1,
        role=ROLE,
        sagemaker_session=sagemaker_session,
        base_job_name="modelo-riesgo-preprocessing"
    )
    
    step_process = ProcessingStep(
        name="PreprocessingStep",
        processor=sklearn_processor,
        inputs=[
            ProcessingInput(
                source=input_data_path,
                destination="/opt/ml/processing/input",
                input_name="input-data"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train",
                source="/opt/ml/processing/train",
                destination=f"s3://{BUCKET}/modelo-riesgo/preprocessing/train"
            ),
            ProcessingOutput(
                output_name="test",
                source="/opt/ml/processing/test",
                destination=f"s3://{BUCKET}/modelo-riesgo/preprocessing/test"
            ),
            ProcessingOutput(
                output_name="inference",
                source="/opt/ml/processing/inference",
                destination=f"s3://{BUCKET}/modelo-riesgo/preprocessing/inference"
            )
        ],
        code="preprocessing.py",
        job_arguments=[
            "--input-path", "/opt/ml/processing/input/clientes_activos.csv",
            "--train-output", "/opt/ml/processing/train",
            "--test-output", "/opt/ml/processing/test",
            "--inference-output", "/opt/ml/processing/inference"
        ]
    )
    
    # ====================
    # STEP 2: TRAINING
    # ====================
    sklearn_estimator = SKLearn(
        entry_point="train.py",
        framework_version="1.2-1",
        instance_type=training_instance_type,
        instance_count=1,
        role=ROLE,
        sagemaker_session=sagemaker_session,
        base_job_name="modelo-riesgo-training",
        hyperparameters={
            "n-estimators": 200,
            "learning-rate": 0.05,
            "max-depth": 4,
            "subsample": 0.8,
            "random-state": 42
        },
        output_path=f"s3://{BUCKET}/modelo-riesgo/models",
        code_location=f"s3://{BUCKET}/modelo-riesgo/code"
    )
    
    step_train = TrainingStep(
        name="TrainingStep",
        estimator=sklearn_estimator,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv"
            ),
            "test": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    # ====================
    # STEP 3: CREAR MODELO (necesario antes del Transform)
    # SKLearnModel resuelve la imagen correcta sin llamar metodos que fallen
    # con Properties objects en tiempo de definicion del pipeline.
    # ====================
    model = SKLearnModel(
        name="modelo-riesgo-model",
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        role=ROLE,
        entry_point="train.py",
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=sagemaker_session,
    )

    step_create_model = ModelStep(
        name="CreateModelStep",
        step_args=model.create(instance_type="ml.m5.large"),
    )

    # ====================
    # STEP 4: BATCH TRANSFORM (SCORING)
    # ====================
    transformer = Transformer(
        model_name=step_create_model.properties.ModelName,
        instance_type=transform_instance_type,
        instance_count=1,
        output_path=f"s3://{BUCKET}/modelo-riesgo/scoring/output",
        accept="text/csv",
        assemble_with="Line",
        base_transform_job_name="modelo-riesgo-scoring"
    )
    
    step_transform = TransformStep(
        name="BatchScoringStep",
        transformer=transformer,
        inputs=TransformInput(
            data=step_process.properties.ProcessingOutputConfig.Outputs["inference"].S3Output.S3Uri,
            content_type="text/csv",
            split_type="Line"
        )
    )
    
    # ====================
    # PIPELINE DEFINITION
    # ====================
    pipeline = Pipeline(
        name="modelo-riesgo-pipeline",
        parameters=[
            input_data_path,
            model_approval_status,
            processing_instance_type,
            training_instance_type,
            transform_instance_type
        ],
        steps=[
            step_process,
            step_train,
            step_create_model,
            step_transform
        ],
        sagemaker_session=sagemaker_session
    )
    
    return pipeline


if __name__ == "__main__":
    # Crear y registrar el pipeline
    pipeline = create_pipeline()
    
    # Upsert (crear o actualizar) el pipeline
    pipeline.upsert(role_arn=ROLE)
    
    print(f"Pipeline '{pipeline.name}' creado/actualizado exitosamente")
    print(f"Bucket S3: {BUCKET}")
    print(f"Region: {REGION}")
    
    # Iniciar ejecución del pipeline
    execution = pipeline.start()
    print(f"Ejecución del pipeline iniciada: {execution.arn}")
    print(f"Puede monitorear el progreso en la consola de SageMaker Studio")
