import os
import ast
import glob
import tarfile
import yaml
import json
import pickle
import boto3
import tempfile
import joblib

import math
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from sagemaker.experiments import Experiment
from botocore.exceptions import ClientError

def open_yaml(path):
    with open(path, "r") as stream:
        try:
            doc = yaml.safe_load(stream)
            return doc
        except yaml.YAMLError as exc:
            print(exc)
            
def create_if_not_exists_sm_experiment(experiment_name, experiment_description=None, experiment_tags=None):
    client = boto3.client('sagemaker')
    try:
        resp = client.describe_experiment(ExperimentName = experiment_name) 
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFound':
            experiment = Experiment.create(experiment_name=experiment_name, 
                                       description=experiment_description,
                                      tags = experiment_tags)
            resp = client.describe_experiment(ExperimentName = experiment_name)
            print(resp)
        else:
            # Código a ejecutar para otras excepciones de botocore
            print("Se produjo una excepción diferente:", str(e))
    else:
        print('Experiment Name already exists')
        print(resp)

def download_s3_file(s3_path):
    s3 = boto3.client('s3')
    cmpnts = s3_path.split("/")
    bucket = cmpnts[2]
    key = "/".join(cmpnts[3:])
    local_file = "/tmp/{}".format(cmpnts[-1])

    s3.download_file(bucket, key, local_file)

    return local_file

class S3Paths():
    def __init__(self, bucket='nx-analitica-avanzada-data-dev', config=None):
        if config is None:
            self.config = open_yaml(Path(__file__).parent.parent / 'config' / 'config.yaml')
        else:
            self.config = config         
        self.bucket = bucket
        self.prefix = self.config['proyect']['vertical'] +  "/" + self.config['proyect']['name'] + "/" + self.config['proyect']['version'] + "/" + self.config.get('iteration', {}).get('version', 'v0')
        self.datasets_raw_prefix = f'{self.prefix}/datasets_raw'
        self.datasets_join_prefix = f'{self.prefix}/datasets_join'
        self.datasets_preprocess_prefix = f'{self.prefix}/dataset_preprocess'
        self.datasets_concat_prefix = f'{self.prefix}/datasets_concat'
        self.datasets_join_pr_prefix = f'{self.prefix}/datasets_join_pr'
        self.datasets_transform_prefix = f'{self.prefix}/datasets_transform'
        self.code_prefix = f'{self.prefix}/code'
        self.model_prefix = f'{self.prefix}/models'
        self.eval_prefix = f'{self.prefix}/eval'
        self.queries_prefix = f'{self.prefix}/queries'
        self.prefix_name = (self.config['proyect']['vertical'][0] + ''.join([s[0] for s in self.config['proyect']['name'].split('_')]) + '.' + self.config['proyect']['version'] + '.' + self.config.get('iteration', {}).get('version', '0.0')).replace('.', '-')
        
    def create_new_prefix(self, prefix):
        setattr(self, f'{prefix}_prefix', f'{self.prefix}/{prefix}')
    
    def get_path(self, prefix):
        return f"s3://{self.bucket}/{getattr(self, f'{prefix}_prefix')}"

# Aquí puedes añadir más funciones si es necesario...


