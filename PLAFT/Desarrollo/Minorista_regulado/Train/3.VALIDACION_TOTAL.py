# Archivo generado desde Jupyter Notebook
# Origen: 3.VALIDACION_TOTAL.ipynb


# %%
# --- CELDA DE CÓDIGO 1 ---
# execution_count: 2

bucket_name ='ibk-discovery-comercial-us-east-1-654654352211-data'
model_prefix = 'discovery/comercial/sanherna/PLAFT/PJ/MINORISTA'


# %%
# --- CELDA DE CÓDIGO 2 ---
# execution_count: 3

# === Conexion Athena estilo Cruce + fallback awswrangler ===
import os
import re
import sys
from pathlib import Path

import boto3
import awswrangler as wr
import pandas as pd

EXPLICIT_CREDENTIALS_SH = Path(r"c:/Users/b46637/OneDrive - Interbank/conexion_aws/athena_conection_test/credentials.sh")


def _find_dir_with_athena_client(preferred_dir: Path | None = None) -> Path | None:
    cwd = Path.cwd().resolve()
    search_roots = []

    if preferred_dir is not None:
        search_roots.append(preferred_dir)

    search_roots.extend([cwd, *cwd.parents])

    home = Path.home()
    search_roots.extend([
        home / "OneDrive - Interbank" / "conexion_aws" / "athena_conection_test",
        Path("c:/Users/b46637/OneDrive - Interbank/conexion_aws/athena_conection_test"),
    ])

    visited = set()
    for root in search_roots:
        if root in visited:
            continue
        visited.add(root)

        if not root.exists():
            continue
        if (root / "athena_client.py").exists() and (root / "athena_config.json").exists():
            return root
    return None


def _load_credentials_from_sh(sh_path: Path) -> list[str]:
    if not sh_path.exists():
        return []

    loaded_keys: list[str] = []
    pattern = re.compile(r'^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$')

    for line in sh_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue

        key, raw_val = match.groups()
        value = raw_val.strip().strip('"').strip("'")
        if key and value:
            os.environ[key] = value
            loaded_keys.append(key)

    return loaded_keys


def _build_session(aws_region: str) -> boto3.Session:
    aws_profile = os.getenv("AWS_PROFILE")
    if aws_profile:
        return boto3.Session(profile_name=aws_profile, region_name=aws_region)
    return boto3.Session(region_name=aws_region)


def _session_is_valid(sess: boto3.Session) -> tuple[bool, str | None]:
    try:
        sts = sess.client("sts")
        _ = sts.get_caller_identity()
        return True, None
    except Exception as exc:
        return False, str(exc)


ATHENA_MODE = "wrangler"
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "disc_comercial")
ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "primary")
ATHENA_OUTPUT = os.getenv(
    "ATHENA_OUTPUT",
    "s3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/athena_results/"
 )
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

client = None

credentials_file = EXPLICIT_CREDENTIALS_SH if EXPLICIT_CREDENTIALS_SH.exists() else None
if credentials_file is None:
    print(f"⚠ No se encontró credentials.sh en ruta fija: {EXPLICIT_CREDENTIALS_SH}")

preferred_dir = credentials_file.parent if credentials_file is not None else None
athena_dir = _find_dir_with_athena_client(preferred_dir=preferred_dir)
loaded_cred_keys: list[str] = []

if credentials_file is not None:
    loaded_cred_keys = _load_credentials_from_sh(credentials_file)
    if loaded_cred_keys:
        print(f"✓ Credenciales cargadas desde: {credentials_file}")
elif athena_dir is not None:
    fallback_sh = athena_dir / "credentials.sh"
    loaded_cred_keys = _load_credentials_from_sh(fallback_sh)
    if loaded_cred_keys:
        print(f"✓ Credenciales cargadas desde: {fallback_sh}")

try:
    session = _build_session(AWS_REGION)
except Exception:
    session = boto3.Session(region_name=AWS_REGION)

ok_session, session_error = _session_is_valid(session)
if not ok_session and session_error and "ExpiredToken" in session_error and loaded_cred_keys:
    print("⚠ Se detectó token expirado en credentials.sh. Reintentando con credenciales locales (perfil/default)...")
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
        os.environ.pop(key, None)
    session = _build_session(AWS_REGION)

if athena_dir is not None:
    if str(athena_dir) not in sys.path:
        sys.path.append(str(athena_dir))
    try:
        from athena_client import AthenaClient

        if credentials_file is None:
            credentials_file = athena_dir / "credentials.sh"

        client = AthenaClient(
            credentials_file=str(credentials_file),
            config_file=str(athena_dir / "athena_config.json"),
        )
        ATHENA_MODE = "athena_client"
        print(f"✓ AthenaClient cargado desde: {athena_dir}")
    except Exception as exc:
        print(f"⚠ No se pudo inicializar AthenaClient ({exc}). Se usará awswrangler.")
else:
    print("⚠ No se encontró athena_client.py + athena_config.json. Se usará awswrangler.")


def athena_query(query: str, database: str = ATHENA_DATABASE) -> pd.DataFrame:
    if ATHENA_MODE == "athena_client" and client is not None:
        return client.query(query)
    return wr.athena.read_sql_query(
        sql=query,
        database=database,
        ctas_approach=False,
        boto3_session=session,
        workgroup=ATHENA_WORKGROUP,
        s3_output=ATHENA_OUTPUT,
    )


def s3_read_csv(path: str, sep: str = "|", **kwargs) -> pd.DataFrame:
    return wr.s3.read_csv(path=path, sep=sep, boto3_session=session, **kwargs)


def test_aws_connection(sample_s3_path: str | None = None) -> None:
    sts = session.client("sts")
    ident = sts.get_caller_identity()
    print(f"✓ AWS Account: {ident.get('Account')} | ARN: {ident.get('Arn')}")

    if sample_s3_path:
        _ = wr.s3.read_csv(path=sample_s3_path, sep='|', boto3_session=session, nrows=1)
        print(f"✓ Lectura S3 OK: {sample_s3_path}")


print(f"Modo Athena activo: {ATHENA_MODE}")
print(f"DB: {ATHENA_DATABASE} | WG: {ATHENA_WORKGROUP}")
print(f"credentials.sh en uso: {credentials_file}")
print("Helper Athena: athena_query(query)")
print("Helper S3 CSV: s3_read_csv('s3://bucket/prefix/file.txt', sep='|')")
print("Diagnóstico opcional: test_aws_connection()")


# --- OUTPUT ---

# Output 1:
# ✓ Credenciales cargadas desde: c:\Users\b46637\OneDrive - Interbank\conexion_aws\athena_conection_test\credentials.sh
# ⚠ No se encontró athena_client.py + athena_config.json. Se usará awswrangler.
# Modo Athena activo: wrangler
# DB: disc_comercial | WG: primary
# credentials.sh en uso: c:\Users\b46637\OneDrive - Interbank\conexion_aws\athena_conection_test\credentials.sh
# Helper Athena: athena_query(query)
# Helper S3 CSV: s3_read_csv('s3://bucket/prefix/file.txt', sep='|')
# Diagnóstico opcional: test_aws_connection()

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 3 ---
# execution_count: 4

!pip install scikit-learn


# --- OUTPUT ---

# Output 1:
# Defaulting to user installation because normal site-packages is not writeable
# Requirement already satisfied: scikit-learn in c:\users\b46637\appdata\roaming\python\python314\site-packages (1.8.0)
# Requirement already satisfied: numpy>=1.24.1 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn) (2.5.2)
# Requirement already satisfied: scipy>=1.10.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn) (1.18.0)
# Requirement already satisfied: joblib>=1.3.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn) (1.5.3)
# Requirement already satisfied: threadpoolctl>=3.2.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn) (3.6.0)

# Output 2:
# 
# [notice] A new release of pip is available: 25.3 -> 26.2.1
# [notice] To update, run: C:\Program Files\Python314\python.exe -m pip install --upgrade pip

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 4 ---
# execution_count: 5

import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline
from numpy import loadtxt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_curve, roc_auc_score 
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

from sklearn import linear_model
from sklearn.neural_network import MLPClassifier
import pylab as pl

from collections import Counter
from sklearn.datasets import make_classification


# %%
# --- CELDA DE CÓDIGO 5 ---
# execution_count: 6

# Función para comprimir datos #######################################################
def reduce_mem_usage(df, verbose=True):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage().sum() / 1024**2    
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)  
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)    
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose: print('Mem. usage decreased to {:5.2f} Mb ({:.1f}% reduction)'.format(end_mem, 100 * (start_mem - end_mem) / start_mem))
    return df


# %%
# --- CELDA DE CÓDIGO 6 ---
# execution_count: 7

import numpy as np


# %%
# --- CELDA DE CÓDIGO 7 ---
# execution_count: 8

###Tabla_Deciles

def Tabla_Deciles(objective,probas,n=10):
    data={'Objective':objective}
    df_deciles=pd.DataFrame(data,columns=['Objective'])
    df_deciles['probas']=probas
    df_deciles['Rangos']=pd.qcut(df_deciles['probas'],n,duplicates='drop')
    cross_tab=pd.crosstab(df_deciles['Rangos'],df_deciles['Objective'],rownames=['Rangos'],colnames=['Objective'])
    a=0;b=1
    cross_tab['Efectividad']=(cross_tab[1]/cross_tab[[0,1]].sum(axis=1))
    cross_tab['%CumSum_{}'.format(a)]=cross_tab[a].cumsum()/cross_tab[a].sum()
    cross_tab['%CumSum_{}'.format(b)]=cross_tab.loc[::-1,b].cumsum()[::-1]/cross_tab[b].sum()
    cross_tab['CumSum_{}'.format(a)]=cross_tab[a].cumsum()
    cross_tab['CumSum_{}'.format(b)]=cross_tab.loc[::-1,b].cumsum()[::-1]
    return cross_tab


# %% [markdown]
# --- CELDA MARKDOWN 8 ---
# # MODELOS


# %%
# --- CELDA DE CÓDIGO 9 ---
# execution_count: 8

from sagemaker.tuner import HyperparameterTuner
#Solo variables importantes
nombre_exportado = HyperparameterTuner.attach('hpo-plaft-pj-minoris-260803-2126').best_training_job()
print(nombre_exportado)


# --- OUTPUT ---

# Output 1:
# ModuleNotFoundError: No module named 'sagemaker'
# [31m---------------------------------------------------------------------------[39m
# [31mModuleNotFoundError[39m                       Traceback (most recent call last)
# [36mCell[39m[36m [39m[32mIn[8][39m[32m, line 1[39m
# [32m----> [39m[32m1[39m [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01msagemaker[39;00m[34;01m.[39;00m[34;01mtuner[39;00m[38;5;250m [39m[38;5;28;01mimport[39;00m HyperparameterTuner
# [32m      2[39m [38;5;66;03m#Solo variables importantes[39;00m
# [32m      3[39m nombre_exportado = HyperparameterTuner.attach([33m'[39m[33mhpo-plaft-pj-minoris-260803-2126[39m[33m'[39m).best_training_job()
# 
# [31mModuleNotFoundError[39m: No module named 'sagemaker'

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 10 ---
# execution_count: 9

#!pip install xgboost --prefer-binary


# %%
# --- CELDA DE CÓDIGO 11 ---
# execution_count: 10

!pip install --force-reinstall "xgboost==1.7.6"


# --- OUTPUT ---

# Output 1:
# Defaulting to user installation because normal site-packages is not writeable
# Collecting xgboost==1.7.6
#   Using cached xgboost-1.7.6-py3-none-win_amd64.whl.metadata (1.9 kB)
# Collecting numpy (from xgboost==1.7.6)
#   Using cached numpy-2.5.2-cp314-cp314-win_amd64.whl.metadata (6.6 kB)
# Collecting scipy (from xgboost==1.7.6)
#   Using cached scipy-1.18.0-cp314-cp314-win_amd64.whl.metadata (61 kB)
# Using cached xgboost-1.7.6-py3-none-win_amd64.whl (70.9 MB)
# Using cached numpy-2.5.2-cp314-cp314-win_amd64.whl (12.6 MB)
# Using cached scipy-1.18.0-cp314-cp314-win_amd64.whl (37.3 MB)
# Installing collected packages: numpy, scipy, xgboost
# 
#   Attempting uninstall: numpy
# 
#     Found existing installation: numpy 2.5.2
# 
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#     Uninstalling numpy-2.5.2:
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#       Successfully uninstalled numpy-2.5.2
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#    ---------------------------------------- 0/3 [numpy]
#   Attempting uninstall: scipy
#    ---------------------------------------- 0/3 [numpy]
#     Found existing installation: scipy 1.18.0
#    ---------------------------------------- 0/3 [numpy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#     Uninstalling scipy-1.18.0:
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#       Successfully uninstalled scipy-1.18.0
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#    ------------- -------------------------- 1/3 [scipy]
#   Attempting uninstall: xgboost
#    ------------- -------------------------- 1/3 [scipy]
#     Found existing installation: xgboost 1.7.6
#    ------------- -------------------------- 1/3 [scipy]
#     Uninstalling xgboost-1.7.6:
#    ------------- -------------------------- 1/3 [scipy]
#       Successfully uninstalled xgboost-1.7.6
#    ------------- -------------------------- 1/3 [scipy]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    -------------------------- ------------- 2/3 [xgboost]
#    ---------------------------------------- 3/3 [xgboost]
# 
# Successfully installed numpy-2.5.2 scipy-1.18.0 xgboost-1.7.6

# Output 2:
#   WARNING: The scripts f2py.exe and numpy-config.exe are installed in 'C:\Users\b46637\AppData\Roaming\Python\Python314\Scripts' which is not on PATH.
#   Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
# ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
# numba 0.65.1 requires numpy<2.5,>=1.22, but you have numpy 2.5.2 which is incompatible.
# 
# [notice] A new release of pip is available: 25.3 -> 26.2.1
# [notice] To update, run: C:\Program Files\Python314\python.exe -m pip install --upgrade pip

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 12 ---
# execution_count: 11

import xgboost as xgb

print(xgb.__version__)


# --- OUTPUT ---

# Output 1:
# 1.7.6

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 13 ---
# execution_count: 12

import boto3
import tarfile
import xgboost as xgb
import os

# Parámetros
# Parámetros
bucket_name = 'ibk-discovery-comercial-us-east-1-654654352211-data'
model_prefix = 'discovery/comercial/sanherna/PLAFT/PJ/MINORISTA'
nombre_exportado = 'hpo-plaft-pj-minoris-260803-2126-022-10aa0dbf'

# Descargar model.tar.gz desde S3
s3 = boto3.client('s3')

with open('model.tar.gz', 'wb') as f:
    s3.download_fileobj(
        bucket_name,
        f'{model_prefix}/MODEL/output/{nombre_exportado}/output/model.tar.gz',
        f
    )

# Extraer el archivo tar.gz
with tarfile.open('model.tar.gz', 'r:gz') as tar:
    tar.extractall(path='model')

# Cargar el modelo con XGBoost
model_path = os.path.join('model', 'xgboost-model')
model = xgb.Booster()
model.load_model(model_path)

# ¡Listo! Ya podés usar model.predict(...) con DMatrix


# --- OUTPUT ---

# Output 1:
# C:\Users\b46637\AppData\Local\Temp\ipykernel_40756\2417049600.py:24: DeprecationWarning: Python 3.14 will, by default, filter extracted tar archives and reject files or modify their metadata. Use the filter argument to control this behavior.
#   tar.extractall(path='model')

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 14 ---
# execution_count: 13

import pandas as pd

import pandas as pd

# ===============================================================
# 1. Parámetros de tu bucket y prefijo
# ===============================================================
bucket_name ='ibk-discovery-comercial-us-east-1-654654352211-data'
model_prefix = 'discovery/comercial/sanherna/PLAFT/PJ/MINORISTA'

# Ejemplo completo:
# bucket_name  = "sagemaker-us-east-1-123456789012"
# model_prefix = "risk-fraud-model/2025-12-05"

# ===============================================================
# 2. Rutas en S3
# ===============================================================
base_s3_path = f"s3://{bucket_name}/{model_prefix}/data_dev_model"

headers_path      = f"{base_s3_path}/headers_total.csv"
train_path        = f"{base_s3_path}/train_total.csv"
val_path          = f"{base_s3_path}/validation_total.csv"
test_path         = f"{base_s3_path}/test_total.csv"
extras_val_path   = f"{base_s3_path}/extras_validation_total.csv"
extras_test_path  = f"{base_s3_path}/extras_test_total.csv"

# ===============================================================
# 3. Cargar headers (orden y tipos)
# ===============================================================
headers = pd.read_csv(headers_path)
column_order = headers['variables'].tolist()

print(f"Se cargaron {len(column_order)} variables desde S3")
print("Primeras 10 variables:", column_order[:10])

# ===============================================================
# 4. Cargar train / val / test SIN header, pero CON nombres correctos
# ===============================================================
df_train = pd.read_csv(train_path, header=None, names=column_order)
df_val   = pd.read_csv(val_path,   header=None, names=column_order)
df_test  = pd.read_csv(test_path,  header=None, names=column_order)

print(f"\nShapes cargados desde S3:")
print(f"  Train : {df_train.shape}")
print(f"  Val   : {df_val.shape}")
print(f"  Test  : {df_test.shape}")

# ===============================================================
# 5. Cargar extras (num_documento, mes_base, tipo_alerta_n2)
# ===============================================================
extras_val  = pd.read_csv(extras_val_path)
extras_test = pd.read_csv(extras_test_path)

# Pegamos las columnas de reporting al dataframe original
df_val  = pd.concat([df_val.reset_index(drop=True), 
                     extras_val[['key_value','cod_cli' ,'cod_mes','tipo_alerta_n2','trx_riesgo_cliente']]], axis=1)

df_test = pd.concat([df_test.reset_index(drop=True), 
                     extras_test[['key_value','cod_cli' , 'cod_mes','tipo_alerta_n2','trx_riesgo_cliente']]], axis=1)

# ===============================================================
# 6. Verificación final
# ===============================================================
print("\nListo! Todo cargado correctamente desde S3")
print(f"df_val  ahora tiene {df_val.shape[1]} columnas (incluye num_documento y mes_base)")
print(f"df_test ahora tiene {df_test.shape[1]} columnas")

# Ejemplo rápido de uso
display(df_val[['key_value', 'cod_cli' ,'cod_mes', 'target','tipo_alerta_n2','trx_riesgo_cliente']].head())


# --- OUTPUT ---

# Output 1:
# Se cargaron 33 variables desde S3
# Primeras 10 variables: ['target', 'cnt_trx_cargostot_3m', 'mto_pas_soles', 'rat_pastot_x_ingtot_6m', 'cnt_trx_abonospromtot_3m', 'imp_trx_abonosefect_6m', 'num_antiguedad', 'imp_trx_cargosefe_6m', 'ratio_cargos_1m_vs_6m', 'cnt_meses_sinegresos_12m']
# 
# Shapes cargados desde S3:
#   Train : (173600, 33)
#   Val   : (324253, 33)
#   Test  : (1509824, 33)
# 
# Listo! Todo cargado correctamente desde S3
# df_val  ahora tiene 38 columnas (incluye num_documento y mes_base)
# df_test ahora tiene 38 columnas

# Output 2:
#                                            key_value     cod_cli   cod_mes  \
# 0  3B020DB4DC631ED9192290632AD8627B2A9495500B2783...  21602930.0  202508.0   
# 1  2820FF155EBE1FF50F339495F0BDE21578CCE6AFD934D9...   7321045.0  202508.0   
# 2  3194E86A626832BA5994B2318E2D0A0774892E5D769D76...  19639492.0  202508.0   
# 3  566A75C788AB628F0A7BAE537CBBBD49F613E1FEAA85A4...  21010838.0  202509.0   
# 4  6A5C84509F82D207D3F611E0FBBBA19AA144C80E686E3E...  18466306.0  202509.0   
# 
#    target tipo_alerta_n2 trx_riesgo_cliente  
# 0     0.0       SIN_INFO           SIN_INFO  
# 1     0.0       SIN_INFO           SIN_INFO  
# 2     0.0       SIN_INFO           SIN_INFO  
# 3     0.0       SIN_INFO           SIN_INFO  
# 4     0.0       SIN_INFO           SIN_INFO  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 15 ---
# execution_count: 14

#df_test_1= df_test[(df_test.tipo_alerta_n2 =='AUTOMATICA')&(df_test.trx_riesgo_cliente !='A')]


# %%
# --- CELDA DE CÓDIGO 16 ---
# execution_count: 15

#df_test_1= df_test[(df_test.tipo_alerta_n2 !='SIN_INFO')]


# %%
# --- CELDA DE CÓDIGO 17 ---
# execution_count: 16

import xgboost as xgb
import pandas as pd

# Tu DataFrame de test
df_test_3 = df_test.copy()
#test_data_0825_2= test_data_0825_1[(test_data_0825_1.tipo_alerta_n2 !='0')]




# Variables a excluir (no estuvieron en el entrenamiento)
cols_excluir = ['key_value', 'cod_cli', 'cod_mes', 'tipo_alerta_n2','trx_riesgo_cliente']

# Seleccionamos solo las columnas usadas en entrenamiento
X_test = df_test_3.drop(columns=cols_excluir, errors='ignore')

# Asegurarnos de no tener la columna target si existiera
X_test = X_test.drop(columns=['target'], errors='ignore')

# Crear DMatrix para XGBoost con soporte para categóricas
dtest = xgb.DMatrix(X_test, enable_categorical=True)


# %%
# --- CELDA DE CÓDIGO 18 ---
# execution_count: 17

df_test_3['prob'] = model.predict(dtest)


# %%
# --- CELDA DE CÓDIGO 19 ---
# execution_count: 18

import pandas as pd
from sklearn.metrics import roc_auc_score

# ---------------------------------------------------
# Función para calcular Gini
# ---------------------------------------------------
def gini(actual, pred):
    auc = roc_auc_score(actual, pred)
    return 2*auc - 1

# ---------------------------------------------------
# Calcular Gini por mes usando 'codmes' y 'target_m'
# ---------------------------------------------------
gini_por_mes = df_test_3.groupby('cod_mes').apply(
    lambda x: gini(x['target'], x['prob'])
)

# Mostrar resultados
print("Gini por mes:")
print(gini_por_mes)


# --- OUTPUT ---

# Output 1:
# Gini por mes:
# cod_mes
# 202508.0    0.950945
# 202509.0    0.944097
# 202510.0    0.898831
# 202511.0    0.927584
# 202512.0    0.902826
# 202601.0    0.963558
# 202602.0    0.940175
# 202603.0    0.918342
# 202604.0    0.967561
# dtype: float64

# Output 2:
# C:\Users\b46637\AppData\Local\Temp\ipykernel_40756\29427415.py:14: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
#   gini_por_mes = df_test_3.groupby('cod_mes').apply(

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 20 ---
# execution_count: 19

gini_promedio = gini_por_mes.mean()

print(f"\nGini promedio de todos los meses: {gini_promedio:.4f}")


# --- OUTPUT ---

# Output 1:
# 
# Gini promedio de todos los meses: 0.9349

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 21 ---
# execution_count: 20

from sklearn.metrics import confusion_matrix
import pandas as pd

# -------------------------------------------------
# Configuración
# -------------------------------------------------
MES = 202508
THRESHOLD = 0.99296  # tu umbral definido
cols_excluir = ['key_value', 'cod_cli' ,'cod_mes', 'cod_cli' , 'tipo_alerta_n2', 'target','trx_riesgo_cliente']

# -------------------------------------------------
# Filtrar datos del mes
# -------------------------------------------------
test_data = df_test[df_test.cod_mes == float(MES)].copy()

if test_data.empty:
    print(f"⚠️ No hay datos para el mes {MES}")
else:
    # Preparar X_test
    X_test = test_data.drop(columns=cols_excluir, errors='ignore')
    dtest = xgb.DMatrix(X_test, enable_categorical=True)

    # Predicciones
    test_data['prob'] = model.predict(dtest)

    # Verdaderos / predichos
    y_true = test_data['target'].values
    y_score = test_data['prob'].values
    y_pred = (y_score >= THRESHOLD).astype(int)

    # Matriz de confusión
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"\n=== Matriz de Confusión Mes {MES} ===")
    print(pd.DataFrame(
        cm,
        index=["Real 0", "Real 1"],
        columns=["Pred 0", "Pred 1"]
    ))
    print(f"\nTP: {tp} | FP: {fp} | FN: {fn} | TN: {tn}")
    print(f"Precision: {tp / (tp + fp):.4f}")
    print(f"Recall:    {tp / (tp + fn):.4f}")


# --- OUTPUT ---

# Output 1:
# 
# === Matriz de Confusión Mes 202508 ===
#         Pred 0  Pred 1
# Real 0  161080     217
# Real 1      91      27
# 
# TP: 27 | FP: 217 | FN: 91 | TN: 161080
# Precision: 0.1107
# Recall:    0.2288

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 22 ---
# execution_count: 21

#validation


# %%
# --- CELDA DE CÓDIGO 23 ---
# execution_count: 22

import xgboost as xgb
import pandas as pd

# Tu DataFrame de test
df_val_3 = df_val.copy()
#test_data_0825_2= test_data_0825_1[(test_data_0825_1.tipo_alerta_n2 !='0')]




# Variables a excluir (no estuvieron en el entrenamiento)
cols_excluir = ['key_value', 'cod_cli', 'cod_mes', 'tipo_alerta_n2','trx_riesgo_cliente']

# Seleccionamos solo las columnas usadas en entrenamiento
X_test = df_val_3.drop(columns=cols_excluir, errors='ignore')

# Asegurarnos de no tener la columna target si existiera
X_test = X_test.drop(columns=['target'], errors='ignore')

# Crear DMatrix para XGBoost con soporte para categóricas
dtest = xgb.DMatrix(X_test, enable_categorical=True)


# %%
# --- CELDA DE CÓDIGO 24 ---
# execution_count: 23

df_val_3['prob'] = model.predict(dtest)


# %%
# --- CELDA DE CÓDIGO 25 ---
# execution_count: 24

import pandas as pd
from sklearn.metrics import roc_auc_score

# ---------------------------------------------------
# Función para calcular Gini
# ---------------------------------------------------
def gini(actual, pred):
    auc = roc_auc_score(actual, pred)
    return 2*auc - 1

# ---------------------------------------------------
# Calcular Gini por mes usando 'codmes' y 'target_m'
# ---------------------------------------------------
gini_por_mes = df_val_3.groupby('cod_mes').apply(
    lambda x: gini(x['target'], x['prob'])
)

# Mostrar resultados
print("Gini por mes:")
print(gini_por_mes)


# --- OUTPUT ---

# Output 1:
# Gini por mes:
# cod_mes
# 202508.0    0.950945
# 202509.0    0.944097
# dtype: float64

# Output 2:
# C:\Users\b46637\AppData\Local\Temp\ipykernel_40756\1839909994.py:14: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
#   gini_por_mes = df_val_3.groupby('cod_mes').apply(

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 26 ---
# execution_count: 25

#df_test_1= df_test[(df_test.tipo_alerta_n2 =='AUTOMATICA')&(df_test.trx_riesgo_cliente !='A')]


# %%
# --- CELDA DE CÓDIGO 27 ---
# execution_count: 26

#df_test_1= df_test[(df_test.tipo_alerta_n2 =='AUTOMATICA')]


# %%
# --- CELDA DE CÓDIGO 28 ---
# execution_count: 27

meses = [202508, 202509, 202510, 202511, 202512,202601,202602,202603,202604]
tablas_quintiles = {}

for mes in meses:

    test_data = df_test[df_test.cod_mes == float(mes)].copy()

    # Predicción (asumiendo que ya tienes `predictions`)
    cols_excluir = ['key_value', 'cod_cli' ,'cod_mes',  'cod_cli' ,'tipo_alerta_n2','trx_riesgo_cliente']
    X_test = test_data.drop(columns=cols_excluir, errors='ignore')
    X_test = X_test.drop(columns=['target'], errors='ignore')
    dtest = xgb.DMatrix(X_test, enable_categorical=True)

    test_data['prob'] = model.predict(dtest)

    # Filtro indicado
    test_data_alerta = test_data[
        test_data.tipo_alerta_n2 != 0
    ].copy()

    if test_data_alerta.empty:
        continue

    # Tabla QUINTILES
    tablas_quintiles[mes] = Tabla_Deciles(
        test_data_alerta['target'],
        test_data_alerta['prob'],
        n=5
    )


# %%
# --- CELDA DE CÓDIGO 29 ---
# execution_count: 28

tablas_quintiles[202508]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (-0.000787, 0.0239]  32283    0     0.000000   0.200146   1.000000     32283   
# (0.0239, 0.08]       32282    1     0.000031   0.400286   1.000000     64565   
# (0.08, 0.142]        32282    1     0.000031   0.600427   0.991525     96847   
# (0.142, 0.278]       32290    0     0.000000   0.800616   0.983051    129137   
# (0.278, 0.998]       32160  116     0.003594   1.000000   0.983051    161297   
# 
# Objective            CumSum_1  
# Rangos                         
# (-0.000787, 0.0239]       118  
# (0.0239, 0.08]            118  
# (0.08, 0.142]             117  
# (0.142, 0.278]            116  
# (0.278, 0.998]            116  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 30 ---
# execution_count: 29

tablas_quintiles[202509]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (-0.000322, 0.0244]  32568    0     0.000000   0.200124   1.000000     32568   
# (0.0244, 0.0807]     32567    0     0.000000   0.400242   1.000000     65135   
# (0.0807, 0.143]      32568    0     0.000000   0.600366   1.000000     97703   
# (0.143, 0.279]       32564    3     0.000092   0.800466   1.000000    130267   
# (0.279, 0.998]       32472   96     0.002948   1.000000   0.969697    162739   
# 
# Objective            CumSum_1  
# Rangos                         
# (-0.000322, 0.0244]        99  
# (0.0244, 0.0807]           99  
# (0.0807, 0.143]            99  
# (0.143, 0.279]             99  
# (0.279, 0.998]             96  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 31 ---
# execution_count: 30

tablas_quintiles[202510]


# --- OUTPUT ---

# Output 1:
# Objective             0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                        
# (-0.000715, 0.025]  32955    0     0.000000   0.200153      1.000     32955   
# (0.025, 0.082]      32954    1     0.000030   0.400300      1.000     65909   
# (0.082, 0.144]      32951    3     0.000091   0.600429      0.992     98860   
# (0.144, 0.283]      32974    6     0.000182   0.800697      0.968    131834   
# (0.283, 0.999]      32815  115     0.003492   1.000000      0.920    164649   
# 
# Objective           CumSum_1  
# Rangos                        
# (-0.000715, 0.025]       125  
# (0.025, 0.082]           125  
# (0.082, 0.144]           124  
# (0.144, 0.283]           121  
# (0.283, 0.999]           115  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 32 ---
# execution_count: 31

tablas_quintiles[202511]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (-0.000724, 0.0259]  33264    0     0.000000   0.200079   1.000000     33264   
# (0.0259, 0.0836]     33263    0     0.000000   0.400153   1.000000     66527   
# (0.0836, 0.148]      33262    1     0.000030   0.600220   1.000000     99789   
# (0.148, 0.288]       33262    1     0.000030   0.800288   0.984127    133051   
# (0.288, 0.999]       33203   61     0.001834   1.000000   0.968254    166254   
# 
# Objective            CumSum_1  
# Rangos                         
# (-0.000724, 0.0259]        63  
# (0.0259, 0.0836]           63  
# (0.0836, 0.148]            63  
# (0.148, 0.288]             62  
# (0.288, 0.999]             61  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 33 ---
# execution_count: 32

tablas_quintiles[202512]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (-0.000693, 0.0261]  34267    0     0.000000   0.200023     1.0000     34267   
# (0.0261, 0.0828]     34266    0     0.000000   0.400041     1.0000     68533   
# (0.0828, 0.145]      34265    1     0.000029   0.600053     1.0000    102798   
# (0.145, 0.284]       34266    0     0.000000   0.800070     0.9375    137064   
# (0.284, 0.999]       34251   15     0.000438   1.000000     0.9375    171315   
# 
# Objective            CumSum_1  
# Rangos                         
# (-0.000693, 0.0261]        16  
# (0.0261, 0.0828]           16  
# (0.0828, 0.145]            16  
# (0.145, 0.284]             15  
# (0.284, 0.999]             15  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 34 ---
# execution_count: 33

tablas_quintiles[202603]


# --- OUTPUT ---

# Output 1:
# Objective             0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                        
# (-0.000804, 0.029]  34086    0     0.000000   0.200151      1.000     34086   
# (0.029, 0.0845]     34085    0     0.000000   0.400297      1.000     68171   
# (0.0845, 0.148]     34080    5     0.000147   0.600413      1.000    102251   
# (0.148, 0.293]      34084    1     0.000029   0.800553      0.960    136335   
# (0.293, 0.999]      33966  119     0.003491   1.000000      0.952    170301   
# 
# Objective           CumSum_1  
# Rangos                        
# (-0.000804, 0.029]       125  
# (0.029, 0.0845]          125  
# (0.0845, 0.148]          125  
# (0.148, 0.293]           120  
# (0.293, 0.999]           119  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 35 ---
# execution_count: 34

tablas_quintiles[202604]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (-0.000876, 0.0296]  34555    0     0.000000   0.200585   1.000000     34555   
# (0.0296, 0.0852]     34447    0     0.000000   0.400543   1.000000     69002   
# (0.0852, 0.15]       34500    1     0.000029   0.600809   1.000000    103502   
# (0.15, 0.296]        34500    1     0.000029   0.801075   0.995726    138002   
# (0.296, 0.999]       34269  232     0.006724   1.000000   0.991453    172271   
# 
# Objective            CumSum_1  
# Rangos                         
# (-0.000876, 0.0296]       234  
# (0.0296, 0.0852]          234  
# (0.0852, 0.15]            234  
# (0.15, 0.296]             233  
# (0.296, 0.999]            232  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 36 ---
# execution_count: 35

df_test_2= df_test[(df_test.cod_mes ==202604)]


# %%
# --- CELDA DE CÓDIGO 37 ---
# execution_count: 36

#solo alarmas


# %%
# --- CELDA DE CÓDIGO 38 ---
# execution_count: 37

df_test_1= df_test[(df_test.tipo_alerta_n2 =='AUTOMATICA')&(df_test.trx_riesgo_cliente !='A')]


# %%
# --- CELDA DE CÓDIGO 39 ---
# execution_count: 38

meses = [202508, 202509, 202510, 202511, 202512,202601,202602,202603,202604]
tablas_quintiles = {}

for mes in meses:

    test_data = df_test_1[df_test_1.cod_mes == float(mes)].copy()

    # Predicción (asumiendo que ya tienes `predictions`)
    cols_excluir = ['key_value', 'cod_cli' ,'cod_mes',  'cod_cli' ,'tipo_alerta_n2','trx_riesgo_cliente']
    X_test = test_data.drop(columns=cols_excluir, errors='ignore')
    X_test = X_test.drop(columns=['target'], errors='ignore')
    dtest = xgb.DMatrix(X_test, enable_categorical=True)

    test_data['prob'] = model.predict(dtest)

    # Filtro indicado
    test_data_alerta = test_data[
        test_data.tipo_alerta_n2 != 0
    ].copy()

    if test_data_alerta.empty:
        continue

    # Tabla QUINTILES
    tablas_quintiles[mes] = Tabla_Deciles(
        test_data_alerta['target'],
        test_data_alerta['prob'],
        n=5
    )


# %%
# --- CELDA DE CÓDIGO 40 ---
# execution_count: 39

tablas_quintiles[202508]


# --- OUTPUT ---

# Output 1:
# Objective         0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                    
# (0.00263, 0.224]   39    0     0.000000   0.245283   1.000000        39   
# (0.224, 0.69]      34    4     0.105263   0.459119   1.000000        73   
# (0.69, 0.892]      34    5     0.128205   0.672956   0.882353       107   
# (0.892, 0.977]     28   10     0.263158   0.849057   0.735294       135   
# (0.977, 0.997]     24   15     0.384615   1.000000   0.441176       159   
# 
# Objective         CumSum_1  
# Rangos                      
# (0.00263, 0.224]        34  
# (0.224, 0.69]           34  
# (0.69, 0.892]           30  
# (0.892, 0.977]          25  
# (0.977, 0.997]          15  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 41 ---
# execution_count: 40

tablas_quintiles[202509]


# --- OUTPUT ---

# Output 1:
# Objective         0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                    
# (0.00208, 0.392]   55    0     0.000000   0.215686   1.000000        55   
# (0.392, 0.815]     53    1     0.018519   0.423529   1.000000       108   
# (0.815, 0.932]     53    1     0.018519   0.631373   0.941176       161   
# (0.932, 0.977]     51    3     0.055556   0.831373   0.882353       212   
# (0.977, 0.998]     43   12     0.218182   1.000000   0.705882       255   
# 
# Objective         CumSum_1  
# Rangos                      
# (0.00208, 0.392]        17  
# (0.392, 0.815]          17  
# (0.815, 0.932]          16  
# (0.932, 0.977]          15  
# (0.977, 0.998]          12  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 42 ---
# execution_count: 41

tablas_quintiles[202510]


# --- OUTPUT ---

# Output 1:
# Objective                     0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                      
# (0.014100000000000001, 0.24]   53    0     0.000000   0.226496   1.000000   
# (0.24, 0.734]                  53    0     0.000000   0.452991   1.000000   
# (0.734, 0.905]                 48    4     0.076923   0.658120   1.000000   
# (0.905, 0.979]                 47    6     0.113208   0.858974   0.866667   
# (0.979, 0.999]                 33   20     0.377358   1.000000   0.666667   
# 
# Objective                     CumSum_0  CumSum_1  
# Rangos                                            
# (0.014100000000000001, 0.24]        53        30  
# (0.24, 0.734]                      106        30  
# (0.734, 0.905]                     154        30  
# (0.905, 0.979]                     201        26  
# (0.979, 0.999]                     234        20  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 43 ---
# execution_count: 42

tablas_quintiles[202511]


# --- OUTPUT ---

# Output 1:
# Objective                       0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                        
# (0.0070999999999999995, 0.246]   36    0     0.000000   0.229299   1.000000   
# (0.246, 0.753]                   32    3     0.085714   0.433121   1.000000   
# (0.753, 0.905]                   32    3     0.085714   0.636943   0.842105   
# (0.905, 0.971]                   31    4     0.114286   0.834395   0.684211   
# (0.971, 0.997]                   26    9     0.257143   1.000000   0.473684   
# 
# Objective                       CumSum_0  CumSum_1  
# Rangos                                              
# (0.0070999999999999995, 0.246]        36        19  
# (0.246, 0.753]                        68        19  
# (0.753, 0.905]                       100        16  
# (0.905, 0.971]                       131        13  
# (0.971, 0.997]                       157         9  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 44 ---
# execution_count: 43

tablas_quintiles[202512]


# --- OUTPUT ---

# Output 1:
# Objective         0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                    
# (0.00502, 0.155]   57    0     0.000000   0.202847        1.0        57   
# (0.155, 0.582]     56    0     0.000000   0.402135        1.0       113   
# (0.582, 0.851]     57    0     0.000000   0.604982        1.0       170   
# (0.851, 0.939]     56    0     0.000000   0.804270        1.0       226   
# (0.939, 0.997]     55    2     0.035088   1.000000        1.0       281   
# 
# Objective         CumSum_1  
# Rangos                      
# (0.00502, 0.155]         2  
# (0.155, 0.582]           2  
# (0.582, 0.851]           2  
# (0.851, 0.939]           2  
# (0.939, 0.997]           2  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 45 ---
# execution_count: 44

tablas_quintiles[202601]


# --- OUTPUT ---

# Output 1:
# Objective                       0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                        
# (0.0019199999999999998, 0.246]   26    0         0.00   0.254902   1.000000   
# (0.246, 0.858]                   21    4         0.16   0.460784   1.000000   
# (0.858, 0.956]                   22    3         0.12   0.676471   0.833333   
# (0.956, 0.983]                   20    5         0.20   0.872549   0.708333   
# (0.983, 0.997]                   13   12         0.48   1.000000   0.500000   
# 
# Objective                       CumSum_0  CumSum_1  
# Rangos                                              
# (0.0019199999999999998, 0.246]        26        24  
# (0.246, 0.858]                        47        24  
# (0.858, 0.956]                        69        20  
# (0.956, 0.983]                        89        17  
# (0.983, 0.997]                       102        12  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 46 ---
# execution_count: 45

tablas_quintiles[202602]


# --- OUTPUT ---

# Output 1:
# Objective                         0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                          
# (-0.00025600000000000004, 0.193]  105    0     0.000000   0.204678   1.000000   
# (0.193, 0.644]                    105    0     0.000000   0.409357   1.000000   
# (0.644, 0.871]                    103    1     0.009615   0.610136   1.000000   
# (0.871, 0.955]                    103    2     0.019048   0.810916   0.909091   
# (0.955, 0.999]                     97    8     0.076190   1.000000   0.727273   
# 
# Objective                         CumSum_0  CumSum_1  
# Rangos                                                
# (-0.00025600000000000004, 0.193]       105        11  
# (0.193, 0.644]                         210        11  
# (0.644, 0.871]                         313        11  
# (0.871, 0.955]                         416        10  
# (0.955, 0.999]                         513         8  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 47 ---
# execution_count: 46

tablas_quintiles[202603]


# --- OUTPUT ---

# Output 1:
# Objective           0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                      
# (-0.000717, 0.153]   24    0     0.000000   0.214286      1.000        24   
# (0.153, 0.658]       24    0     0.000000   0.428571      1.000        48   
# (0.658, 0.897]       23    1     0.041667   0.633929      1.000        71   
# (0.897, 0.961]       19    5     0.208333   0.803571      0.875        90   
# (0.961, 0.998]       22    2     0.083333   1.000000      0.250       112   
# 
# Objective           CumSum_1  
# Rangos                        
# (-0.000717, 0.153]         8  
# (0.153, 0.658]             8  
# (0.658, 0.897]             8  
# (0.897, 0.961]             7  
# (0.961, 0.998]             2  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 48 ---
# execution_count: 47

tablas_quintiles[202604]


# --- OUTPUT ---

# Output 1:
# Objective         0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                    
# (0.00586, 0.799]   54    5     0.084746   0.293478   1.000000        54   
# (0.799, 0.926]     45   14     0.237288   0.538043   0.954545        99   
# (0.926, 0.969]     35   23     0.396552   0.728261   0.827273       134   
# (0.969, 0.985]     29   30     0.508475   0.885870   0.618182       163   
# (0.985, 0.998]     21   38     0.644068   1.000000   0.345455       184   
# 
# Objective         CumSum_1  
# Rangos                      
# (0.00586, 0.799]       110  
# (0.799, 0.926]         105  
# (0.926, 0.969]          91  
# (0.969, 0.985]          68  
# (0.985, 0.998]          38  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 49 ---
# execution_count: 48

#from pathlib import Path
#output_path = Path(r"/PLAFT/Desarrollo/Desarrollo/PJ/MINORISTA/Artefactos/Inferencia/alertas_ordenadas_automaticas_sinriegoalto.csv")
#df_test_2.to_csv(output_path, index=False, encoding="utf-8-sig")
#print(f"✓ CSV exportado: {output_path} | Filas: {len(df_test_2):,}")


# %%
# --- CELDA DE CÓDIGO 50 ---
# execution_count: 49

meses = [202508, 202509, 202510, 202511,202512]
tablas_quintiles = {}

for mes in meses:

    test_data = df_test[df_test.cod_mes == float(mes)].copy()

    # Predicción (asumiendo que ya tienes `predictions`)
    cols_excluir = ['key_value', 'cod_mes', 'cod_cli' , 'tipo_alerta_n2','trx_riesgo_cliente']
    X_test = test_data.drop(columns=cols_excluir, errors='ignore')
    X_test = X_test.drop(columns=['target'], errors='ignore')
    dtest = xgb.DMatrix(X_test, enable_categorical=True)

    test_data['prob'] = model.predict(dtest)

    # Filtro indicado
    test_data_alerta = test_data[
        test_data.tipo_alerta_n2 != 0
    ].copy()

    if test_data_alerta.empty:
        continue

    # Tabla QUINTILES
    tablas_quintiles[mes] = Tabla_Deciles(
        test_data_alerta['target'],
        test_data_alerta['prob'],
        n=1000
    )


# %%
# --- CELDA DE CÓDIGO 51 ---
# execution_count: 50

tablas_quintiles[202508]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (0.0001134, 0.001799]  162    0     0.000000   0.001004   1.000000       162   
# (0.001799, 0.002104]   161    0     0.000000   0.002003   1.000000       323   
# (0.002104, 0.00231]    162    0     0.000000   0.003007   1.000000       485   
# (0.00231, 0.0025]      161    0     0.000000   0.004005   1.000000       646   
# (0.0025, 0.002665]     162    0     0.000000   0.005009   1.000000       808   
# ...                    ...  ...          ...        ...        ...       ...   
# (0.9824, 0.9859]       155    7     0.043210   0.996262   0.423729    160694   
# (0.9859, 0.9891]       155    6     0.037267   0.997223   0.364407    160849   
# (0.9891, 0.9915]       158    4     0.024691   0.998202   0.313559    161007   
# (0.9915, 0.9942]       148   13     0.080745   0.999120   0.279661    161155   
# (0.9942, 0.9982]       142   20     0.123457   1.000000   0.169492    161297   
# 
# Objective              CumSum_1  
# Rangos                           
# (0.0001134, 0.001799]       118  
# (0.001799, 0.002104]        118  
# (0.002104, 0.00231]         118  
# (0.00231, 0.0025]           118  
# (0.0025, 0.002665]          118  
# ...                         ...  
# (0.9824, 0.9859]             50  
# (0.9859, 0.9891]             43  
# (0.9891, 0.9915]             37  
# (0.9915, 0.9942]             33  
# (0.9942, 0.9982]             20  
# 
# [953 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 52 ---
# execution_count: 51

tablas_quintiles[202509]


# --- OUTPUT ---

# Output 1:
# Objective                0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                 
# (0.00066803, 0.0017963]  163    0     0.000000   0.001002   1.000000   
# (0.0017963, 0.0021272]   163    0     0.000000   0.002003   1.000000   
# (0.0021272, 0.0023114]   163    0     0.000000   0.003005   1.000000   
# (0.0023114, 0.0025096]   163    0     0.000000   0.004006   1.000000   
# (0.0025096, 0.0026912]   163    0     0.000000   0.005008   1.000000   
# ...                      ...  ...          ...        ...        ...   
# (0.98266, 0.98605]       157    6     0.036810   0.996178   0.363636   
# (0.98605, 0.9889]        159    4     0.024540   0.997155   0.303030   
# (0.9889, 0.99194]        156    7     0.042945   0.998114   0.262626   
# (0.99194, 0.99425]       158    5     0.030675   0.999084   0.191919   
# (0.99425, 0.99826]       149   14     0.085890   1.000000   0.141414   
# 
# Objective                CumSum_0  CumSum_1  
# Rangos                                       
# (0.00066803, 0.0017963]       163        99  
# (0.0017963, 0.0021272]        326        99  
# (0.0021272, 0.0023114]        489        99  
# (0.0023114, 0.0025096]        652        99  
# (0.0025096, 0.0026912]        815        99  
# ...                           ...       ...  
# (0.98266, 0.98605]         162117        36  
# (0.98605, 0.9889]          162276        30  
# (0.9889, 0.99194]          162432        26  
# (0.99194, 0.99425]         162590        19  
# (0.99425, 0.99826]         162739        14  
# 
# [953 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 53 ---
# execution_count: 52

tablas_quintiles[202510]


# --- OUTPUT ---

# Output 1:
# Objective              0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  CumSum_0  \
# Rangos                                                                         
# (0.0001848, 0.001803]  165    0     0.000000   0.001002      1.000       165   
# (0.001803, 0.002128]   185    0     0.000000   0.002126      1.000       350   
# (0.002128, 0.002322]   145    0     0.000000   0.003006      1.000       495   
# (0.002322, 0.002509]   165    0     0.000000   0.004009      1.000       660   
# (0.002509, 0.002706]   164    0     0.000000   0.005005      1.000       824   
# ...                    ...  ...          ...        ...        ...       ...   
# (0.9823, 0.9865]       161    3     0.018293   0.996283      0.408    164037   
# (0.9865, 0.9892]       158    7     0.042424   0.997243      0.384    164195   
# (0.9892, 0.9922]       159    6     0.036364   0.998208      0.328    164354   
# (0.9922, 0.9946]       149   16     0.096970   0.999113      0.280    164503   
# (0.9946, 0.9988]       146   19     0.115152   1.000000      0.152    164649   
# 
# Objective              CumSum_1  
# Rangos                           
# (0.0001848, 0.001803]       125  
# (0.001803, 0.002128]        125  
# (0.002128, 0.002322]        125  
# (0.002322, 0.002509]        125  
# (0.002509, 0.002706]        125  
# ...                         ...  
# (0.9823, 0.9865]             51  
# (0.9865, 0.9892]             48  
# (0.9892, 0.9922]             41  
# (0.9922, 0.9946]             35  
# (0.9946, 0.9988]             19  
# 
# [954 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 54 ---
# execution_count: 53

tablas_quintiles[202511]


# --- OUTPUT ---

# Output 1:
# Objective                            0.0  1.0  Efectividad  %CumSum_0  \
# Rangos                                                                  
# (0.00027484499999999996, 0.0018404]  167    0     0.000000   0.001004   
# (0.0018404, 0.00212757]              176    0     0.000000   0.002063   
# (0.00212757, 0.00233758]             156    0     0.000000   0.003001   
# (0.00233758, 0.00254109]             167    0     0.000000   0.004006   
# (0.00254109, 0.00269707]             166    0     0.000000   0.005004   
# ...                                  ...  ...          ...        ...   
# (0.983804, 0.986936]                 165    1     0.006024   0.996096   
# (0.986936, 0.989622]                 164    3     0.017964   0.997083   
# (0.989622, 0.992577]                 162    4     0.024096   0.998057   
# (0.992577, 0.994978]                 161    5     0.030120   0.999026   
# (0.994978, 0.998688]                 162    5     0.029940   1.000000   
# 
# Objective                            %CumSum_1  CumSum_0  CumSum_1  
# Rangos                                                              
# (0.00027484499999999996, 0.0018404]   1.000000       167        63  
# (0.0018404, 0.00212757]               1.000000       343        63  
# (0.00212757, 0.00233758]              1.000000       499        63  
# (0.00233758, 0.00254109]              1.000000       666        63  
# (0.00254109, 0.00269707]              1.000000       832        63  
# ...                                        ...       ...       ...  
# (0.983804, 0.986936]                  0.285714    165605        18  
# (0.986936, 0.989622]                  0.269841    165769        17  
# (0.989622, 0.992577]                  0.222222    165931        14  
# (0.992577, 0.994978]                  0.158730    166092        10  
# (0.994978, 0.998688]                  0.079365    166254         5  
# 
# [957 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 55 ---
# execution_count: 54

tablas_quintiles[202512]


# --- OUTPUT ---

# Output 1:
# Objective                 0.0  1.0  Efectividad  %CumSum_0  %CumSum_1  \
# Rangos                                                                  
# (0.000306404, 0.0018335]  172    0     0.000000   0.001004     1.0000   
# (0.0018335, 0.00212757]   175    0     0.000000   0.002026     1.0000   
# (0.00212757, 0.00235251]  167    0     0.000000   0.003000     1.0000   
# (0.00235251, 0.0025563]   172    0     0.000000   0.004004     1.0000   
# (0.0025563, 0.00275162]   178    0     0.000000   0.005043     1.0000   
# ...                       ...  ...          ...        ...        ...   
# (0.983961, 0.987089]      171    0     0.000000   0.996013     0.1875   
# (0.987089, 0.990061]      172    0     0.000000   0.997017     0.1875   
# (0.990061, 0.992578]      170    1     0.005848   0.998010     0.1875   
# (0.992578, 0.994863]      169    2     0.011696   0.998996     0.1250   
# (0.994863, 0.998899]      172    0     0.000000   1.000000     0.0000   
# 
# Objective                 CumSum_0  CumSum_1  
# Rangos                                        
# (0.000306404, 0.0018335]       172        16  
# (0.0018335, 0.00212757]        347        16  
# (0.00212757, 0.00235251]       514        16  
# (0.00235251, 0.0025563]        686        16  
# (0.0025563, 0.00275162]        864        16  
# ...                            ...       ...  
# (0.983961, 0.987089]        170632         3  
# (0.987089, 0.990061]        170804         3  
# (0.990061, 0.992578]        170974         3  
# (0.992578, 0.994863]        171143         2  
# (0.994863, 0.998899]        171315         0  
# 
# [954 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 56 ---
# execution_count: 55

import pandas as pd
import numpy as np

def metricas_top_k(df, target_col, score_col, k_list):
    """
    Calcula Recall@K y Precision@K para distintos valores de K
    """
    df = df.sort_values(score_col, ascending=False).reset_index(drop=True)
    total_positivos = df[target_col].sum()

    resultados = []

    for k in k_list:
        top_k = df.head(k)
        tp_k = top_k[target_col].sum()

        recall_k = tp_k / total_positivos if total_positivos > 0 else 0
        precision_k = tp_k / k if k > 0 else 0

        resultados.append({
            "K": k,
            "score_min": top_k[score_col].min(),
            "TP": tp_k,
            "Recall": recall_k,
            "Precision": precision_k
        })

    return pd.DataFrame(resultados)


# %%
# --- CELDA DE CÓDIGO 57 ---
# execution_count: 56

meses = [202508, 202509, 202510, 202511, 202512,202604]
k_list = [100, 200, 500, 1000, 2000]

resultados_meses = {}

for mes in meses:

    test_data = df_test[df_test.cod_mes == float(mes)].copy()

    cols_excluir = ['key_value', 'cod_mes',  'cod_cli' ,'tipo_alerta_n2', 'target','trx_riesgo_cliente']
    X_test = test_data.drop(columns=cols_excluir, errors='ignore')

    dtest = xgb.DMatrix(X_test, enable_categorical=True)
    test_data['prob'] = model.predict(dtest)

    # Solo alertas nuevas
    test_data_alerta = test_data[
        test_data.tipo_alerta_n2 != 0
    ].copy()

    if test_data_alerta.empty:
        continue

    tabla_k = metricas_top_k(
        test_data_alerta,
        target_col="target",
        score_col="prob",
        k_list=k_list
    )

    tabla_k["mes"] = mes
    resultados_meses[mes] = tabla_k


# %%
# --- CELDA DE CÓDIGO 58 ---
# execution_count: 57

df_metricas = pd.concat(
    resultados_meses.values(),
    ignore_index=True
)

df_metricas


# --- OUTPUT ---

# Output 1:
#        K  score_min     TP    Recall  Precision     mes
# 0    100   0.995190   16.0  0.135593     0.1600  202508
# 1    200   0.993580   26.0  0.220339     0.1300  202508
# 2    500   0.988720   37.0  0.313559     0.0740  202508
# 3   1000   0.977754   60.0  0.508475     0.0600  202508
# 4   2000   0.951468   80.0  0.677966     0.0400  202508
# 5    100   0.995521    7.0  0.070707     0.0700  202509
# 6    200   0.993716   15.0  0.151515     0.0750  202509
# 7    500   0.988662   26.0  0.262626     0.0520  202509
# 8   1000   0.978254   41.0  0.414141     0.0410  202509
# 9   2000   0.951332   57.0  0.575758     0.0285  202509
# 10   100   0.995548   13.0  0.104000     0.1300  202510
# 11   200   0.994050   25.0  0.200000     0.1250  202510
# 12   500   0.989141   41.0  0.328000     0.0820  202510
# 13  1000   0.978402   60.0  0.480000     0.0600  202510
# 14  2000   0.952777   68.0  0.544000     0.0340  202510
# 15   100   0.996077    4.0  0.063492     0.0400  202511
# 16   200   0.994509    6.0  0.095238     0.0300  202511
# 17   500   0.989622   14.0  0.222222     0.0280  202511
# 18  1000   0.980174   18.0  0.285714     0.0180  202511
# 19  2000   0.956427   29.0  0.460317     0.0145  202511
# 20   100   0.996219    0.0  0.000000     0.0000  202512
# 21   200   0.994539    0.0  0.000000     0.0000  202512
# 22   500   0.990255    3.0  0.187500     0.0060  202512
# 23  1000   0.981310    5.0  0.312500     0.0050  202512
# 24  2000   0.958077   10.0  0.625000     0.0050  202512
# 25   100   0.995932   19.0  0.081197     0.1900  202604
# 26   200   0.994669   28.0  0.119658     0.1400  202604
# 27   500   0.990601   60.0  0.256410     0.1200  202604
# 28  1000   0.982765   97.0  0.414530     0.0970  202604
# 29  2000   0.961614  148.0  0.632479     0.0740  202604

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 59 ---
# execution_count: 58

def optimal_threshold_topk(
    df,
    score_col="prob",
    target_col="target",
    k=1000,
    n_groups=5
):
    df = df.sort_values(score_col, ascending=False).reset_index(drop=True)

    # Total positivos reales (para recall)
    total_positivos = (df[target_col] == 1).sum()

    # Nos quedamos solo con los top K
    df_topk = df.iloc[:k].copy()

    group_size = k // n_groups
    resultados = []

    acumulado = pd.DataFrame()

    for g in range(1, n_groups + 1):
        inicio = (g - 1) * group_size
        fin = g * group_size

        acumulado = df_topk.iloc[:fin]

        tp = (acumulado[target_col] == 1).sum()
        fp = fin - tp
        fn = total_positivos - tp

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0 else 0
        )

        threshold = acumulado[score_col].min()

        resultados.append({
            "grupo": g,
            "casos_hasta": fin,
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1
        })

    return pd.DataFrame(resultados)


# %%
# --- CELDA DE CÓDIGO 60 ---
# execution_count: 59

resultados_mes = {}

for mes in meses:
    df_mes = df_test[df_test.cod_mes == mes].copy()
    df_mes = df_mes[df_mes.tipo_alerta_n2 != 0]

    if df_mes.empty:
        continue

    X = df_mes.drop(
        columns=["key_value", "cod_mes", 'cod_cli' , "tipo_alerta_n2", "target","trx_riesgo_cliente"],
        errors="ignore"
    )

    dtest = xgb.DMatrix(X)
    df_mes["prob"] = model.predict(dtest)

    tabla = optimal_threshold_topk(
        df_mes,
        score_col="prob",
        target_col="target",
        k=1000,
        n_groups=5
    )

    resultados_mes[mes] = tabla


# %%
# --- CELDA DE CÓDIGO 61 ---
# execution_count: 60

for mes, tabla in resultados_mes.items():
    print(f"\nMes {mes}")
    display(tabla.sort_values("f1", ascending=False).head(1))


# --- OUTPUT ---

# Output 1:
# 
# Mes 202508

# Output 2:
#    grupo  casos_hasta  threshold  precision    recall        f1
# 0      1          200    0.99358       0.13  0.220339  0.163522

# Output 3:
# 
# Mes 202509

# Output 4:
#    grupo  casos_hasta  threshold  precision    recall        f1
# 0      1          200   0.993716      0.075  0.151515  0.100334

# Output 5:
# 
# Mes 202510

# Output 6:
#    grupo  casos_hasta  threshold  precision  recall        f1
# 0      1          200    0.99405      0.125     0.2  0.153846

# Output 7:
# 
# Mes 202511

# Output 8:
#    grupo  casos_hasta  threshold  precision    recall        f1
# 1      2          400   0.991373     0.0275  0.174603  0.047516

# Output 9:
# 
# Mes 202512

# Output 10:
#    grupo  casos_hasta  threshold  precision  recall        f1
# 4      5         1000    0.98131      0.005  0.3125  0.009843

# Output 11:
# 
# Mes 202604

# Output 12:
#    grupo  casos_hasta  threshold  precision    recall        f1
# 2      3          600   0.989226   0.118333  0.303419  0.170264

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 62 ---
# execution_count: 61

df_optimos = []

for mes, tabla in resultados_mes.items():
    best = tabla.sort_values("f1", ascending=False).iloc[0]
    best["mes"] = mes
    df_optimos.append(best)

df_optimos = pd.DataFrame(df_optimos)
df_optimos


# --- OUTPUT ---

# Output 1:
#    grupo  casos_hasta  threshold  precision    recall        f1       mes
# 0    1.0        200.0   0.993580   0.130000  0.220339  0.163522  202508.0
# 0    1.0        200.0   0.993716   0.075000  0.151515  0.100334  202509.0
# 0    1.0        200.0   0.994050   0.125000  0.200000  0.153846  202510.0
# 1    2.0        400.0   0.991373   0.027500  0.174603  0.047516  202511.0
# 4    5.0       1000.0   0.981310   0.005000  0.312500  0.009843  202512.0
# 2    3.0        600.0   0.989226   0.118333  0.303419  0.170264  202604.0

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 63 ---
# execution_count: 62

threshold_final = df_optimos["threshold"].quantile(0.25)
threshold_final


# --- OUTPUT ---

# Output 1:
# np.float64(0.989762544631958)

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 64 ---
# execution_count: 63

!pip install shap


# --- OUTPUT ---

# Output 1:
# Defaulting to user installation because normal site-packages is not writeable
# Requirement already satisfied: shap in c:\users\b46637\appdata\roaming\python\python314\site-packages (0.51.0)
# Requirement already satisfied: numpy>=2 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (2.5.2)
# Requirement already satisfied: scipy in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (1.18.0)
# Requirement already satisfied: scikit-learn in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (1.8.0)
# Requirement already satisfied: pandas in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (2.3.3)
# Requirement already satisfied: tqdm>=4.27.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (4.67.3)
# Requirement already satisfied: packaging>20.9 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (24.2)
# Requirement already satisfied: slicer==0.0.8 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (0.0.8)
# Requirement already satisfied: numba in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (0.65.1)
# Requirement already satisfied: llvmlite in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (0.47.0)
# Requirement already satisfied: cloudpickle in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (3.1.2)
# Requirement already satisfied: typing-extensions in c:\users\b46637\appdata\roaming\python\python314\site-packages (from shap) (4.15.0)
# Requirement already satisfied: colorama in c:\users\b46637\appdata\roaming\python\python314\site-packages (from tqdm>=4.27.0->shap) (0.4.6)
# Collecting numpy>=2 (from shap)
#   Downloading numpy-2.4.6-cp314-cp314-win_amd64.whl.metadata (6.6 kB)
# Requirement already satisfied: python-dateutil>=2.8.2 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from pandas->shap) (2.9.0.post0)
# Requirement already satisfied: pytz>=2020.1 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from pandas->shap) (2026.1.post1)
# Requirement already satisfied: tzdata>=2022.7 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from pandas->shap) (2025.3)
# Requirement already satisfied: six>=1.5 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from python-dateutil>=2.8.2->pandas->shap) (1.17.0)
# Requirement already satisfied: joblib>=1.3.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn->shap) (1.5.3)
# Requirement already satisfied: threadpoolctl>=3.2.0 in c:\users\b46637\appdata\roaming\python\python314\site-packages (from scikit-learn->shap) (3.6.0)
# Downloading numpy-2.4.6-cp314-cp314-win_amd64.whl (12.5 MB)
#    ---------------------------------------- 0.0/12.5 MB ? eta -:--:--
#    ---------------------------------------- 0.0/12.5 MB ? eta -:--:--
#     --------------------------------------- 0.3/12.5 MB ? eta -:--:--
#     --------------------------------------- 0.3/12.5 MB ? eta -:--:--
#    - -------------------------------------- 0.5/12.5 MB 941.3 kB/s eta 0:00:13
#    -- ------------------------------------- 0.8/12.5 MB 1.0 MB/s eta 0:00:12
#    --- ------------------------------------ 1.0/12.5 MB 1.1 MB/s eta 0:00:11
#    ----- ---------------------------------- 1.6/12.5 MB 1.2 MB/s eta 0:00:09
#    ----- ---------------------------------- 1.8/12.5 MB 1.3 MB/s eta 0:00:09
#    ------ --------------------------------- 2.1/12.5 MB 1.3 MB/s eta 0:00:08
#    -------- ------------------------------- 2.6/12.5 MB 1.4 MB/s eta 0:00:07
#    --------- ------------------------------ 2.9/12.5 MB 1.4 MB/s eta 0:00:07
#    ---------- ----------------------------- 3.4/12.5 MB 1.5 MB/s eta 0:00:07
#    ------------ --------------------------- 3.9/12.5 MB 1.5 MB/s eta 0:00:06
#    ------------- -------------------------- 4.2/12.5 MB 1.6 MB/s eta 0:00:06
#    --------------- ------------------------ 4.7/12.5 MB 1.6 MB/s eta 0:00:05
#    ---------------- ----------------------- 5.2/12.5 MB 1.7 MB/s eta 0:00:05
#    ------------------- -------------------- 6.0/12.5 MB 1.8 MB/s eta 0:00:04
#    --------------------- ------------------ 6.6/12.5 MB 1.8 MB/s eta 0:00:04
#    ---------------------- ----------------- 7.1/12.5 MB 1.9 MB/s eta 0:00:03
#    ------------------------- -------------- 7.9/12.5 MB 2.0 MB/s eta 0:00:03
#    -------------------------- ------------- 8.4/12.5 MB 2.0 MB/s eta 0:00:03
#    ---------------------------- ----------- 8.9/12.5 MB 2.0 MB/s eta 0:00:02
#    ------------------------------ --------- 9.4/12.5 MB 2.1 MB/s eta 0:00:02
#    -------------------------------- ------- 10.2/12.5 MB 2.1 MB/s eta 0:00:02
#    ---------------------------------- ----- 10.7/12.5 MB 2.2 MB/s eta 0:00:01
#    ------------------------------------- -- 11.5/12.5 MB 2.2 MB/s eta 0:00:01
#    ---------------------------------------  12.3/12.5 MB 2.3 MB/s eta 0:00:01
#    ---------------------------------------- 12.5/12.5 MB 2.3 MB/s  0:00:05
# Installing collected packages: numpy
#   Attempting uninstall: numpy
#     Found existing installation: numpy 2.5.2
#     Uninstalling numpy-2.5.2:
#       Successfully uninstalled numpy-2.5.2
# Successfully installed numpy-2.4.6

# Output 2:
#   WARNING: The scripts f2py.exe and numpy-config.exe are installed in 'C:\Users\b46637\AppData\Roaming\Python\Python314\Scripts' which is not on PATH.
#   Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
# 
# [notice] A new release of pip is available: 25.3 -> 26.2.1
# [notice] To update, run: C:\Program Files\Python314\python.exe -m pip install --upgrade pip

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 65 ---
# execution_count: 64

import shap
import pandas as pd
import numpy as np

# ===============================
# Dataset de referencia (ej: 202508)
# ===============================
df_ref = df_test[
    (df_test.cod_mes == 202508) 
    #&(df_test.tipo_alerta_n2 != '0')
].copy()

cols_excluir = ['key_value', 'cod_mes', 'cod_cli' , 'tipo_alerta_n2', 'target','trx_riesgo_cliente']
X_ref = df_ref.drop(columns=cols_excluir, errors='ignore')

# SHAP explainer (XGBoost)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_ref)

# Summary plot
shap.summary_plot(shap_values, X_ref, plot_type="bar")


# --- OUTPUT ---

# Output 1:
# C:\Users\b46637\AppData\Roaming\Python\Python313\site-packages\tqdm\auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html
#   from .autonotebook import tqdm as notebook_tqdm

# Output 2:
# <Figure size 800x950 with 1 Axes>

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 66 ---
# execution_count: 68

variable_names = X_test.columns

# Importancia global SHAP: promedio de los valores absolutos por variable.
average_shap_values = np.abs(shap_values).mean(axis=0)
shap_mean_values = shap_values.mean(axis=0)
total_importance = average_shap_values.sum()

if total_importance == 0:
    raise ValueError("La suma de las importancias SHAP es cero.")

# Normalizar como porcentaje de contribución para que sume 100%.
importance_pct = average_shap_values / total_importance * 100

variable_importance = [
    (variable_name, importance, shap_mean)
    for variable_name, importance, shap_mean in zip(
        variable_names,
        importance_pct,
        shap_mean_values
    )
]

variable_importance.sort(key=lambda item: item[1], reverse=True)

# Ajustar solo el residuo de redondeo para garantizar suma exacta de 100%.
variable_importance = [
    (variable, round(importance, 6), shap_mean)
    for variable, importance, shap_mean in variable_importance
]
residuo = 100 - sum(item[1] for item in variable_importance)
ultima_variable, ultima_importancia, ultimo_shap = variable_importance[-1]
variable_importance[-1] = (
    ultima_variable,
    round(ultima_importancia + residuo, 6),
    ultimo_shap
)

variables_mas_importantes = variable_importance
print(f"Suma de importancia (%): {sum(item[1] for item in variables_mas_importantes):.6f}")


# --- OUTPUT ---

# Output 1:
# Suma de importancia (%): 100.000008

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 67 ---
# execution_count: 69

import csv

# Nombre del archivo CSV de salida
output_csv = 'importancia_variables.csv'

# Escribe los datos en el archivo CSV
with open(output_csv, 'w', newline='') as csvfile:
    
    # Define el escritor CSV
    csv_writer = csv.writer(csvfile)
    
    # Escribe el encabezado
    csv_writer.writerow(['Variable', 'Importancia', 'Valor Absoluto SHAP'])
    
    # Escribe los datos de cada variable
    for variable in variables_mas_importantes:
        csv_writer.writerow([variable[0], variable[1], variable[2]])


# %%
# --- CELDA DE CÓDIGO 68 ---
# execution_count: 70

variables_mas_importantes


# --- OUTPUT ---

# Output 1:
# [('rat_pastot_x_ingtot_6m', np.float32(12.582718), np.float32(-0.37739804)),
#  ('mto_fact_declarado_sunat', np.float32(12.362029), np.float32(-0.4796663)),
#  ('mto_pas_soles', np.float32(10.484087), np.float32(-0.35750833)),
#  ('cnt_trx_cargostot_3m', np.float32(9.65748), np.float32(-0.40517455)),
#  ('imp_trx_abonosefect_6m', np.float32(9.640982), np.float32(-0.44454706)),
#  ('cnt_alerta_hist', np.float32(6.767946), np.float32(-0.25740096)),
#  ('imp_trx_cargosefe_6m', np.float32(6.061638), np.float32(-0.2504466)),
#  ('mto_del_ext_12m', np.float32(5.042963), np.float32(-0.25013897)),
#  ('num_antiguedad', np.float32(4.354103), np.float32(-0.13734435)),
#  ('cnt_meses_sinegresos_12m', np.float32(3.872816), np.float32(-0.08155555)),
#  ('cnt_trx_abonospromtot_3m', np.float32(3.848639), np.float32(-0.014913195)),
#  ('cod_ubigeo_cd', np.float32(3.246591), np.float32(-0.108468585)),
#  ('cod_sectorista_id', np.float32(2.545484), np.float32(-0.08682539)),
#  ('rat_mntcrgsefetot_1m', np.float32(2.25881), np.float32(-0.009472523)),
#  ('ratio_cargos_1m_vs_6m', np.float32(1.957896), np.float32(-0.07314386)),
#  ('rat_ing_ext_x_ing_tot_12m', np.float32(0.906231), np.float32(-0.040596467)),
#  ('rat_cntros_x_cnttrxegr_3m', np.float32(0.682815), np.float32(-0.03222288)),
#  ('cnt_ros_hist', np.float32(0.600724), np.float32(-0.024996847)),
#  ('rat_trx_abonosefectot_1m', np.float32(0.540644), np.float32(0.0037226833)),
#  ('share_cp_egresos', np.float32(0.531494), np.float32(-0.019737437)),
#  ('rat_trx_abonosefectot_3m', np.float32(0.501184), np.float32(-0.023074685)),
#  ('avg_trx_cargostot_3m', np.float32(0.383475), np.float32(-0.017747687)),
#  ('avg_cpmenegr_12m', np.float32(0.332519), np.float32(-0.011816502)),
#  ('cnt_noticias', np.float32(0.259659), np.float32(-0.012070532)),
#  ('mto_al_ext_12m', np.float32(0.150394), np.float32(-0.006863172)),
#  ('flg_alerta_12m', np.float32(0.107723), np.float32(-0.004580547)),
#  ('share_cp_ingresos', np.float32(0.082537), np.float32(-0.003558771)),
#  ('flg_vrcn_abonos_5m_1m', np.float32(0.068465), np.float32(-0.00042817421)),
#  ('ratio_egresos_exterior', np.float32(0.056584), np.float32(-0.0020168591)),
#  ('max_mto_cpegrmen_12m', np.float32(0.043191), np.float32(-0.0008172366)),
#  ('avg_cp_men_ing_12m', np.float32(0.038519), np.float32(-0.0016701525)),
#  ('cnt_trx_sinenv_alext_12m', np.float32(0.029667), np.float32(-0.0012866604))]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 69 ---
# execution_count: None




# %%
# --- CELDA DE CÓDIGO 70 ---
# execution_count: None


# ============================================================
# PRECISIÓN TOP20% y RECALL TOP20% — Train / Validation / Test
# Universo completo (todos los registros, no solo alertas)
# Ref: §13.4, §13.5, §13.6 DOCUMENTO_METODOLOGICO v2.1
# ============================================================

import pandas as pd
import numpy as np
import xgboost as xgb

PERIODOS_TRAIN = [202501, 202502, 202503, 202504, 202505, 202506, 202507]
PERIODOS_VAL   = [202508, 202509]
PERIODOS_TEST  = [202510, 202511, 202512, 202601, 202602, 202603, 202604]

COLS_EXCLUIR = ['key_value', 'cod_mes', 'cod_cli', 'tipo_alerta_n2',
                'trx_riesgo_cliente', 'target']

def _predecir(df_subset, modelo):
    X = df_subset.drop(columns=COLS_EXCLUIR, errors='ignore')
    dm = xgb.DMatrix(X, enable_categorical=True)
    return modelo.predict(dm)

def metricas_top_pct(df, prob_col, target_col, pct=0.20):
    """
    Calcula Precisión y Recall sobre el top `pct`% de registros por score.
    """
    df = df.sort_values(prob_col, ascending=False).reset_index(drop=True)
    k = max(1, int(np.ceil(len(df) * pct)))
    top = df.head(k)
    tp              = int(top[target_col].sum())
    total_positivos = int(df[target_col].sum())
    precision       = round(tp / k, 6) if k > 0 else 0.0
    recall          = round(tp / total_positivos, 6) if total_positivos > 0 else 0.0
    return {
        "n_total"        : len(df),
        "k_top20pct"     : k,
        "total_positivos": total_positivos,
        "tp_top20pct"    : tp,
        "precision_top20": round(precision * 100, 2),   # en %
        "recall_top20"   : round(recall    * 100, 2),   # en %
        "lift_top20"     : round(precision / (total_positivos / len(df)), 2)
                           if total_positivos > 0 else None,
    }

# ── Calcular por mes para cada conjunto ─────────────────────────────────────
def calcular_conjunto(df_base, periodos, nombre_conjunto):
    filas = []
    for mes in periodos:
        sub = df_base[df_base['cod_mes'] == float(mes)].copy()
        if sub.empty or sub['target'].sum() == 0:
            continue
        sub['prob'] = _predecir(sub, model)
        m = metricas_top_pct(sub, 'prob', 'target', pct=0.20)
        m['mes']       = mes
        m['conjunto']  = nombre_conjunto
        filas.append(m)
    return filas

filas_train = calcular_conjunto(df_train, PERIODOS_TRAIN, 'TRAIN')
filas_val   = calcular_conjunto(df_val,   PERIODOS_VAL,   'VALIDATION')
filas_test  = calcular_conjunto(df_test,  PERIODOS_TEST,  'TEST')

df_top20 = pd.DataFrame(filas_train + filas_val + filas_test)
df_top20 = df_top20[['conjunto','mes','n_total','total_positivos',
                      'k_top20pct','tp_top20pct',
                      'precision_top20','recall_top20','lift_top20']]

print("=" * 75)
print("PRECISIÓN TOP20% y RECALL TOP20% — universo completo")
print("=" * 75)
print(df_top20.to_string(index=False))

# ── Resumen por conjunto (promedio) ─────────────────────────────────────────
resumen = (
    df_top20.groupby('conjunto')[['precision_top20','recall_top20','lift_top20']]
    .mean()
    .round(2)
    .reindex(['TRAIN','VALIDATION','TEST'])
    .reset_index()
)
print()
print("RESUMEN PROMEDIO POR CONJUNTO:")
print(resumen.to_string(index=False))
print()
print("▶ Copiar a §13.4 (Train), §13.5 (Validation), §13.6 (Test) del documento v2.1")


# %%
# --- CELDA DE CÓDIGO 71 ---
# execution_count: 17

#concilia con piloto


# %%
# --- CELDA DE CÓDIGO 72 ---
# execution_count: 32

df_test_3.head()


# --- OUTPUT ---

# Output 1:
#    target  cnt_trx_cargostot_3m  mto_pas_soles  rat_pastot_x_ingtot_6m  \
# 0     0.0                   0.0           0.00                0.021352   
# 1     0.0                   0.0           0.00                0.021352   
# 2     0.0                 212.0       25384.81                0.200318   
# 3     0.0                 201.0      314865.94                0.882499   
# 4     0.0                  15.0         652.00                0.224897   
# 
#    cnt_trx_abonospromtot_3m  imp_trx_abonosefect_6m  num_antiguedad  \
# 0                      0.00                     0.0             0.0   
# 1                      0.00                     0.0            27.0   
# 2                     32.00                     0.0             2.0   
# 3                     39.33                     0.0             4.0   
# 4                     15.00                     0.0             0.0   
# 
#    imp_trx_cargosefe_6m  ratio_cargos_1m_vs_6m  cnt_meses_sinegresos_12m  ...  \
# 0                   0.0               4580.909                      12.0  ...   
# 1                   0.0               4580.909                      12.0  ...   
# 2                 900.0              92422.420                       5.0  ...   
# 3                   0.0               4580.909                       0.0  ...   
# 4                   0.0               4580.909                      11.0  ...   
# 
#    share_cp_ingresos  mto_fact_declarado_sunat  cod_ubigeo_cd  \
# 0                0.0                       3.0            3.0   
# 1                0.0                       3.0            3.0   
# 2                0.0                       3.0            3.0   
# 3                0.0                       1.0            3.0   
# 4                0.0                       3.0            3.0   
# 
#    cod_sectorista_id                                          key_value  \
# 0                3.0  3B020DB4DC631ED9192290632AD8627B2A9495500B2783...   
# 1                2.0  2820FF155EBE1FF50F339495F0BDE21578CCE6AFD934D9...   
# 2                3.0  3194E86A626832BA5994B2318E2D0A0774892E5D769D76...   
# 3                3.0  6981440E76CCD482BE3D65197D2A85581859FA641A42B7...   
# 4                3.0  ED6F89C0D3A75FF3F831AFBECCE36318F82E0E2C82DB41...   
# 
#       cod_cli   cod_mes  tipo_alerta_n2  trx_riesgo_cliente      prob  
# 0  21602930.0  202508.0        SIN_INFO            SIN_INFO  0.128483  
# 1   7321045.0  202508.0        SIN_INFO            SIN_INFO  0.006566  
# 2  19639492.0  202508.0        SIN_INFO            SIN_INFO  0.165856  
# 3  18329162.0  202604.0        SIN_INFO            SIN_INFO  0.012824  
# 4  22031580.0  202603.0        SIN_INFO            SIN_INFO  0.167192  
# 
# [5 rows x 39 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 73 ---
# execution_count: 33

import pandas as pd

# ============================================================
# Conciliación df_test_3 (mes 202604) vs bases externas (piloto)
# Cruce inner por cod_cli (df_test_3) == codunico (csv)
# ============================================================

path_csv_1 = r"C:\Users\b46637\OneDrive - Interbank\PLAFT\PJ\Minorista\OLD\inferencia\desarrollo\df_6_razones_sospechosas_20260409 1.csv"
path_csv_2 = r"C:\Users\b46637\OneDrive - Interbank\PLAFT\PJ\Minorista\OLD\inferencia\desarrollo\df_6_razones_sospechosas_20260416.csv"

df_ext_1 = pd.read_csv(path_csv_1)
df_ext_2 = pd.read_csv(path_csv_2)

def normalizar_id(serie):
    # quita ".0" de floats y espacios, para poder cruzar ids numéricos como texto
    return (
        pd.to_numeric(serie, errors='coerce')
        .astype('Int64')
        .astype(str)
        .str.strip()
    )

df_test_202604 = df_test_3[df_test_3.cod_mes == 202604].copy()
df_test_202604['cod_cli'] = normalizar_id(df_test_202604['cod_cli'])

def conciliar(df_test_mes, df_ext, nombre_base):
    df_ext_ = df_ext.copy()
    df_ext_['codunico'] = normalizar_id(df_ext_['codunico'])

    merged = df_test_mes.merge(
        df_ext_[['codunico', 'score']],
        left_on='cod_cli',
        right_on='codunico',
        how='inner'
    )
    merged['base'] = nombre_base
    return merged[['cod_cli', 'cod_mes', 'target', 'prob', 'score', 'base']].rename(
        columns={'score': 'prob_piloto'}
    )

conciliado_1 = conciliar(df_test_202604, df_ext_1, 'df_6_razones_sospechosas_20260409 1')
conciliado_2 = conciliar(df_test_202604, df_ext_2, 'df_6_razones_sospechosas_20260409')

df_conciliado = pd.concat([conciliado_1, conciliado_2], ignore_index=True)
df_conciliado['diff_prob'] = df_conciliado['prob'] - df_conciliado['prob_piloto']

print(f"Coincidencias base 1: {len(conciliado_1)}")
print(f"Coincidencias base 2: {len(conciliado_2)}")

df_conciliado


# --- OUTPUT ---

# Output 1:
# Coincidencias base 1: 63
# Coincidencias base 2: 32

# Output 2:
#      cod_cli   cod_mes  target      prob  prob_piloto  \
# 0   21905298  202604.0     0.0  0.980542     0.990190   
# 1   21736268  202604.0     0.0  0.991169     0.986006   
# 2   21943372  202604.0     0.0  0.993966     0.990866   
# 3   21977712  202604.0     0.0  0.994761     0.990966   
# 4   21896636  202604.0     0.0  0.989835     0.984005   
# ..       ...       ...     ...       ...          ...   
# 90  21975560  202604.0     0.0  0.993066     0.995165   
# 91  22063468  202604.0     0.0  0.996656     0.996018   
# 92  22109646  202604.0     0.0  0.997101     0.996661   
# 93  22054536  202604.0     0.0  0.992231     0.994452   
# 94  21985478  202604.0     0.0  0.994885     0.996643   
# 
#                                    base  diff_prob  
# 0   df_6_razones_sospechosas_20260409 1  -0.009648  
# 1   df_6_razones_sospechosas_20260409 1   0.005163  
# 2   df_6_razones_sospechosas_20260409 1   0.003100  
# 3   df_6_razones_sospechosas_20260409 1   0.003795  
# 4   df_6_razones_sospechosas_20260409 1   0.005829  
# ..                                  ...        ...  
# 90    df_6_razones_sospechosas_20260409  -0.002099  
# 91    df_6_razones_sospechosas_20260409   0.000638  
# 92    df_6_razones_sospechosas_20260409   0.000440  
# 93    df_6_razones_sospechosas_20260409  -0.002221  
# 94    df_6_razones_sospechosas_20260409  -0.001757  
# 
# [95 rows x 7 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 74 ---
# execution_count: 34

len(df_ext_1)


# --- OUTPUT ---

# Output 1:
# 120

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 75 ---
# execution_count: 35

len(df_ext_2)


# --- OUTPUT ---

# Output 1:
# 64

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 76 ---
# execution_count: 36

len(df_test_202604)


# --- OUTPUT ---

# Output 1:
# 172505

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 77 ---
# execution_count: 37

print("cod_cli dtype original:", df_test_3['cod_cli'].dtype)
print(df_test_3['cod_cli'].head(10).tolist())

print("\ncodunico dtype original:", df_ext_1['codunico'].dtype)
print(df_ext_1['codunico'].head(10).tolist())

ids_test = set(normalizar_id(df_test_202604['cod_cli']))
ids_ext_1 = set(normalizar_id(df_ext_1['codunico']))
ids_ext_2 = set(normalizar_id(df_ext_2['codunico']))

no_match_1 = ids_ext_1 - ids_test
no_match_2 = ids_ext_2 - ids_test

print(f"\ncodunico base 1 sin match: {len(no_match_1)} de {len(ids_ext_1)}")
print(list(no_match_1)[:10])

print(f"\ncodunico base 2 sin match: {len(no_match_2)} de {len(ids_ext_2)}")
print(list(no_match_2)[:10])

# ¿Los ids "sin match" existen en otro mes de df_test, o en val? (df_train no tiene cod_cli)
ids_test_todos = set(normalizar_id(df_test['cod_cli']))
ids_val_todos  = set(normalizar_id(df_val['cod_cli']))

faltantes = no_match_1 | no_match_2
en_test_otro_mes = faltantes & ids_test_todos
en_val = faltantes & ids_val_todos
en_ningun_lado = faltantes - ids_test_todos - ids_val_todos

print(f"\nTotal ids sin match (unión base1+base2): {len(faltantes)}")
print(f"  presentes en df_test (otro mes): {len(en_test_otro_mes)}")
print(f"  presentes en df_val: {len(en_val)}")
print(f"  no existen en ninguna base cargada: {len(en_ningun_lado)}")


# --- OUTPUT ---

# Output 1:
# cod_cli dtype original: float64
# [21602930.0, 7321045.0, 19639492.0, 18329162.0, 22031580.0, 21010838.0, 18466306.0, 20499696.0, 17190538.0, 20557890.0]
# 
# codunico dtype original: int64
# [21927707, 21881108, 21932484, 21936243, 21971477, 21947688, 22024447, 22011612, 22054719, 21875153]
# 
# codunico base 1 sin match: 61 de 120
# ['19503433', '22087071', '19782535', '21917811', '21396713', '21994351', '21927707', '21933273', '21977847', '21936243']
# 
# codunico base 2 sin match: 35 de 64
# ['21973099', '22040445', '21882591', '21980449', '22104261', '22065925', '22190173', '22069441', '22109913', '22036611']
# 
# Total ids sin match (unión base1+base2): 96
#   presentes en df_test (otro mes): 0
#   presentes en df_val: 0
#   no existen en ninguna base cargada: 96

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 78 ---
# execution_count: 38

df_ext_1_id = df_ext_1.copy()
df_ext_1_id['codunico'] = normalizar_id(df_ext_1_id['codunico'])
df_ext_1_id['base'] = 'df_6_razones_sospechosas_20260409 1'

df_ext_2_id = df_ext_2.copy()
df_ext_2_id['codunico'] = normalizar_id(df_ext_2_id['codunico'])
df_ext_2_id['base'] = 'df_6_razones_sospechosas_20260409'

df_faltantes_1 = df_ext_1_id[df_ext_1_id['codunico'].isin(no_match_1)]
df_faltantes_2 = df_ext_2_id[df_ext_2_id['codunico'].isin(no_match_2)]

df_ids_faltantes = pd.concat([df_faltantes_1, df_faltantes_2], ignore_index=True)[
    ['base', 'codunico', 'num_documento', 'codmes', 'score', 'orden']
].sort_values(['base', 'codunico'])

df_ids_faltantes


# --- OUTPUT ---

# Output 1:
#                                    base  codunico  num_documento  codmes  \
# 95    df_6_razones_sospechosas_20260409  20053187            NaN  202604   
# 78    df_6_razones_sospechosas_20260409  21292833            NaN  202604   
# 85    df_6_razones_sospechosas_20260409  21542789            NaN  202604   
# 84    df_6_razones_sospechosas_20260409  21809989            NaN  202604   
# 89    df_6_razones_sospechosas_20260409  21882591            NaN  202604   
# ..                                  ...       ...            ...     ...   
# 8   df_6_razones_sospechosas_20260409 1  22087071            NaN  202604   
# 49  df_6_razones_sospechosas_20260409 1  22088439            NaN  202604   
# 42  df_6_razones_sospechosas_20260409 1  22100457            NaN  202604   
# 21  df_6_razones_sospechosas_20260409 1  22114799            NaN  202604   
# 6   df_6_razones_sospechosas_20260409 1  22118157            NaN  202604   
# 
#        score  orden  
# 95  0.993225    576  
# 78  0.995093    503  
# 85  0.994345    536  
# 84  0.994379    534  
# 89  0.993730    551  
# ..       ...    ...  
# 8   0.991783    733  
# 49  0.985206    892  
# 42  0.986146    873  
# 21  0.989969    782  
# 6   0.992175    717  
# 
# [96 rows x 6 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 79 ---
# execution_count: 39

# Verificación: comparando con formato 10 dígitos con ceros a la izquierda
# (el resultado numérico es el mismo, el padding no cambia la igualdad)

def normalizar_id_padded(serie, ancho=10):
    return (
        pd.to_numeric(serie, errors='coerce')
        .astype('Int64')
        .astype(str)
        .str.zfill(ancho)
    )

ids_test_padded = set(normalizar_id_padded(df_test_202604['cod_cli']))
ids_ext_1_padded = set(normalizar_id_padded(df_ext_1['codunico']))
ids_ext_2_padded = set(normalizar_id_padded(df_ext_2['codunico']))

no_match_1_padded = ids_ext_1_padded - ids_test_padded
no_match_2_padded = ids_ext_2_padded - ids_test_padded

print(f"codunico base 1 sin match (formato 10 dígitos): {len(no_match_1_padded)} de {len(ids_ext_1_padded)}")
print(f"codunico base 2 sin match (formato 10 dígitos): {len(no_match_2_padded)} de {len(ids_ext_2_padded)}")
print("\n→ El padding con ceros no cambia el resultado: la comparación numérica ya era equivalente.")


# --- OUTPUT ---

# Output 1:
# codunico base 1 sin match (formato 10 dígitos): 61 de 120
# codunico base 2 sin match (formato 10 dígitos): 35 de 64
# 
# → El padding con ceros no cambia el resultado: la comparación numérica ya era equivalente.

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 80 ---
# execution_count: 40

import awswrangler as wr

parquet_path = 's3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/PLAFT/PJ/MINORISTA/DATA_INFERENCIA/data_pn_total_expandido_new_v2.parquet'

df_inferencia = wr.s3.read_parquet(path=parquet_path, boto3_session=session)

print(f"Shape: {df_inferencia.shape}")
print(f"\nColumnas: {df_inferencia.columns.tolist()}")


# --- OUTPUT ---

# Output 1:
# Shape: (1684424, 65)
# 
# Columnas: ['target', 'key_value', 'cod_cli', 'codmes_lag1', 'cod_mes', 'mto_pas_soles', 'imp_trx_abonosefect_6m', 'imp_trx_cargosefe_6m', 'avg_trx_cargostot_3m', 'max_trx_abonos_3m', 'cnt_trx_cargostot_3m', 'cnt_trx_abonospromtot_3m', 'rat_trx_abonosefectot_1m', 'rat_trx_abonosefectot_3m', 'rat_trx_abonosefectot_9m', 'rat_mntcrgsefetot_1m', 'num_edad_constitucion', 'num_antiguedad', 'desc_nivel_rsg_lsb_tot', 'cnt_meses_siningresos_12m', 'cnt_meses_sinegresos_12m', 'desc_provincia', 'desc_departamento', 'cod_ubigeo_cd', 'cod_sectorista_id', 'cod_ciiu_v4', 'flg_casos_hist', 'flg_vrcn_abonos_5m_1m', 'flg_vrcn_efe_cargos_5m_1m', 'cnt_ro_debajo_umbral', 'mto_fact_declarado_sunat', 'avg_cp_men_ing_12m', 'avg_cpmenegr_12m', 'max_mto_cpmening_12m', 'max_mto_cpegrmen_12m', 'flg_al_ext_12m', 'flg_del_ext_12m', 'cnt_trx_sinenv_alext_12m', 'cnt_trx_al_ext_1000_12m', 'mto_al_ext_12m', 'mto_del_ext_12m', 'flg_pep', 'cod_rsg_pep', 'flg_activo_pep', 'cnt_noticias', 'flg_ros_12m', 'flg_alerta_12m', 'cnt_alerta_hist', 'cnt_ros_hist', 'flg_kyc_12m', 'flg_kyc_hist', 'cnt_kyc_hist', 'rat_abonos_1m_vs_6m', 'ratio_cargos_1m_vs_6m', 'share_cp_egresos', 'share_cp_ingresos', 'rat_cntros_x_cnttrxegr_3m', 'alertas_por_antiguedad', 'rat_ing_tot_x_factura_6m', 'rat_pastot_x_ingtot_6m', 'ratio_egresos_exterior', 'rat_ing_ext_x_ing_tot_12m', 'gap_riesgo_pep_lsb', 'tipo_alerta_n2', 'trx_riesgo_cliente']

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 81 ---
# execution_count: 41

print(df_inferencia['cod_mes'].dtype)
print(sorted(df_inferencia['cod_mes'].unique()))


# --- OUTPUT ---

# Output 1:
# Int64
# [np.int64(202501), np.int64(202502), np.int64(202503), np.int64(202504), np.int64(202505), np.int64(202506), np.int64(202507), np.int64(202508), np.int64(202509), np.int64(202510), np.int64(202511), np.int64(202512), np.int64(202601), np.int64(202602), np.int64(202603), np.int64(202604)]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 82 ---
# execution_count: 42

import xgboost as xgb

# ============================================================
# Filtrar mes 04/2026 (202604) desde el parquet de inferencia
# y correr predict con el modelo ya cargado
# ============================================================

df_inf_202604 = df_inferencia[df_inferencia.cod_mes == 202604].copy()
print(f"Registros mes 202604: {len(df_inf_202604)}")

cols_excluir_inf = ['key_value', 'cod_cli', 'codmes_lag1', 'cod_mes',
                     'tipo_alerta_n2', 'trx_riesgo_cliente', 'target']
X_inf = df_inf_202604.drop(columns=cols_excluir_inf, errors='ignore')

# Alinear columnas al orden/nombres con los que se entrenó el modelo
X_inf = X_inf.reindex(columns=model.feature_names)

dinf = xgb.DMatrix(X_inf, enable_categorical=True)
df_inf_202604['prob'] = model.predict(dinf)

df_inf_202604[['key_value', 'cod_cli', 'cod_mes', 'prob']].head()


# --- OUTPUT ---

# Output 1:
# Registros mes 202604: 172505

# Output 2:
#                                                 key_value     cod_cli  \
# 174600  BE8F55650C2645322D5927060AB1E3F7D0C1C04AD143F2...  0021177767   
# 174601  94891434745D9CEBC00BBCB0961B1BF2EADEB4DDE6C3C7...  0018245247   
# 174602  15F0954CDE12201B2D1423A65C27FF95E8C5B3A8F087FA...  0020872103   
# 174603  F94FD7BE09D13724DC6B0E64E289BDA4AF0DC028847C5E...  0021424893   
# 174607  C4CED63F016FF22E97BDB3AF4178A112881B08A7231C32...  0018298046   
# 
#         cod_mes      prob  
# 174600   202604  0.159011  
# 174601   202604  0.050120  
# 174602   202604  0.113093  
# 174603   202604  0.946854  
# 174607   202604  0.717317  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 83 ---
# execution_count: 43

# ============================================================
# Cruce inner por cliente contra las bases piloto (score)
# ============================================================

df_inf_202604['cod_cli_norm'] = normalizar_id(df_inf_202604['cod_cli'])

def conciliar_inferencia(df_inf, df_ext, nombre_base):
    df_ext_ = df_ext.copy()
    df_ext_['codunico'] = normalizar_id(df_ext_['codunico'])

    merged = df_inf.merge(
        df_ext_[['codunico', 'score']],
        left_on='cod_cli_norm',
        right_on='codunico',
        how='inner'
    )
    merged['base'] = nombre_base
    return merged[['cod_cli', 'cod_mes', 'prob', 'score', 'base']].rename(
        columns={'score': 'prob_piloto'}
    )

conciliado_inf_1 = conciliar_inferencia(df_inf_202604, df_ext_1, 'df_6_razones_sospechosas_20260409 1')
conciliado_inf_2 = conciliar_inferencia(df_inf_202604, df_ext_2, 'df_6_razones_sospechosas_20260409')

df_conciliado_inf = pd.concat([conciliado_inf_1, conciliado_inf_2], ignore_index=True)
df_conciliado_inf['diff_prob'] = df_conciliado_inf['prob'] - df_conciliado_inf['prob_piloto']

print(f"Coincidencias base 1: {len(conciliado_inf_1)} de {len(df_ext_1)}")
print(f"Coincidencias base 2: {len(conciliado_inf_2)} de {len(df_ext_2)}")

df_conciliado_inf


# --- OUTPUT ---

# Output 1:
# Coincidencias base 1: 120 de 120
# Coincidencias base 2: 64 de 64

# Output 2:
#         cod_cli  cod_mes      prob  prob_piloto  \
# 0    0022019634   202604  0.356221     0.987842   
# 1    0022020085   202604  0.980361     0.985621   
# 2    0022075591   202604  0.968376     0.990449   
# 3    0021933273   202604  0.990602     0.984897   
# 4    0022087071   202604  0.991136     0.991783   
# ..          ...      ...       ...          ...   
# 179  0022100843   202604  0.998879     0.995144   
# 180  0021969602   202604  0.995637     0.994969   
# 181  0021809989   202604  0.995286     0.994379   
# 182  0022113091   202604  0.996662     0.996402   
# 183  0022018823   202604  0.994598     0.995109   
# 
#                                     base  diff_prob  
# 0    df_6_razones_sospechosas_20260409 1  -0.631621  
# 1    df_6_razones_sospechosas_20260409 1  -0.005260  
# 2    df_6_razones_sospechosas_20260409 1  -0.022073  
# 3    df_6_razones_sospechosas_20260409 1   0.005705  
# 4    df_6_razones_sospechosas_20260409 1  -0.000647  
# ..                                   ...        ...  
# 179    df_6_razones_sospechosas_20260409   0.003735  
# 180    df_6_razones_sospechosas_20260409   0.000668  
# 181    df_6_razones_sospechosas_20260409   0.000907  
# 182    df_6_razones_sospechosas_20260409   0.000260  
# 183    df_6_razones_sospechosas_20260409  -0.000511  
# 
# [184 rows x 6 columns]

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 84 ---
# execution_count: 57

# ============================================================
# Piloto original vs df_inf_202604 completo
# ============================================================

# El nuevo ranking considera todos los clientes de df_inf_202604,
# sin excluir por tipo_alerta_n2.
df_modelo_ranking = df_inf_202604.copy()

# Nuevo orden: 1 = probabilidad mas alta de todo df_inf_202604.
df_modelo_ranking['rank_modelo'] = (
    df_modelo_ranking['prob']
    .rank(ascending=False, method='first')
    .astype(int)
)

n_universo = len(df_modelo_ranking)
n_piloto = len(df_ext_1) + len(df_ext_2)


def comparar_piloto_con_modelo(df_ext, nombre_base):
    df_ext_ = df_ext.copy()
    df_ext_['codunico'] = normalizar_id(df_ext_['codunico'])

    # left merge conserva todos los clientes enviados en el piloto.
    comp = df_ext_[['codunico', 'orden', 'score']].merge(
        df_modelo_ranking[
            ['cod_cli_norm', 'cod_cli', 'prob', 'rank_modelo', 'tipo_alerta_n2']
        ],
        left_on='codunico',
        right_on='cod_cli_norm',
        how='left'
    )

    return comp[
        [
            'codunico', 'cod_cli', 'orden', 'score', 'prob',
            'rank_modelo', 'tipo_alerta_n2'
        ]
    ].rename(
        columns={
            'codunico': 'cod_cli_piloto',
            'cod_cli': 'cod_cli_modelo',
            'orden': 'orden_piloto_original',
            'score': 'prob_piloto'
        }
    ).assign(base=nombre_base)


comp_1 = comparar_piloto_con_modelo(
    df_ext_1,
    'df_6_razones_sospechosas_20260409 1'
)
comp_2 = comparar_piloto_con_modelo(
    df_ext_2,
    'df_6_razones_sospechosas_20260416'
)
df_comparacion_orden = pd.concat([comp_1, comp_2], ignore_index=True)

# Ranking piloto consecutivo, respetando el orden original del piloto.
df_comparacion_orden['rank_piloto'] = (
    df_comparacion_orden['orden_piloto_original']
    .rank(ascending=True, method='first')
    .astype(int)
)

df_comparacion_orden['estado_cruce'] = np.where(
    df_comparacion_orden['rank_modelo'].notna(),
    'Incluido en ranking completo',
    'No encontrado en df_inf_202604'
)

df_comparacion_orden['dif_prob'] = (
    df_comparacion_orden['prob'] - df_comparacion_orden['prob_piloto']
)
df_comparacion_orden['dif_orden'] = (
    df_comparacion_orden['rank_modelo'] - df_comparacion_orden['rank_piloto']
)

print(f"Universo completo de df_inf_202604: {n_universo}")
print(f"Clientes enviados en el piloto original: {n_piloto}")
print(df_comparacion_orden['estado_cruce'].value_counts(dropna=False))

df_comparacion_orden.sort_values('rank_piloto')


# --- OUTPUT ---

# Output 1:
# Universo completo de df_inf_202604: 172505
# Clientes enviados en el piloto original: 184
# estado_cruce
# Incluido en ranking completo    184
# Name: count, dtype: int64

# Output 2:
#     cod_cli_piloto cod_cli_modelo  orden_piloto_original  prob_piloto  \
# 120       21948529     0021948529                    398     0.997276   
# 121       22190173     0022190173                    418     0.997007   
# 122       22118647     0022118647                    429     0.996746   
# 123       22109646     0022109646                    434     0.996661   
# 124       21985478     0021985478                    436     0.996643   
# 125       22066220     0022066220                    437     0.996615   
# 126       22104261     0022104261                    439     0.996533   
# 127       21931341     0021931341                    441     0.996446   
# 128       22113091     0022113091                    445     0.996402   
# 129       21454964     0021454964                    450     0.996226   
# 130       21885882     0021885882                    454     0.996189   
# 131       22041620     0022041620                    457     0.996142   
# 132       22063468     0022063468                    461     0.996018   
# 133       22015147     0022015147                    463     0.995937   
# 134       22004920     0022004920                    465     0.995907   
# 135       22039884     0022039884                    473     0.995789   
# 136       22089643     0022089643                    476     0.995762   
# 137       22013932     0022013932                    478     0.995756   
# 138       21973119     0021973119                    480     0.995691   
# 139       22164362     0022164362                    481     0.995681   
# 140       22162461     0022162461                    483     0.995664   
# 141       22000021     0022000021                    486     0.995618   
# 142       22021405     0022021405                    488     0.995566   
# 143       22109913     0022109913                    490     0.995507   
# 144       22069441     0022069441                    495     0.995299   
# 145       22070723     0022070723                    497     0.995208   
# 146       21998214     0021998214                    499     0.995198   
# 147       21975560     0021975560                    500     0.995165   
# 148       22100843     0022100843                    501     0.995144   
# 149       22018823     0022018823                    502     0.995109   
# 150       21292833     0021292833                    503     0.995093   
# 151       21985472     0021985472                    505     0.995013   
# 152       22061098     0022061098                    506     0.995003   
# 153       21969602     0021969602                    508     0.994969   
# 154       22066040     0022066040                    510     0.994923   
# 155       21788462     0021788462                    513     0.994765   
# 156       22040445     0022040445                    517     0.994661   
# 157       21980314     0021980314                    519     0.994614   
# 158       22059912     0022059912                    520     0.994592   
# 159       21940749     0021940749                    523     0.994572   
# 160       21980449     0021980449                    524     0.994568   
# 161       21996385     0021996385                    525     0.994563   
# 162       22109298     0022109298                    526     0.994515   
# 163       22014274     0022014274                    528     0.994490   
# 164       22054536     0022054536                    529     0.994452   
# 165       21982407     0021982407                    530     0.994451   
# 166       21945684     0021945684                    531     0.994447   
# 167       22067710     0022067710                    532     0.994408   
# 168       21809989     0021809989                    534     0.994379   
# 169       21542789     0021542789                    536     0.994345   
# 170       22098441     0022098441                    538     0.994191   
# 171       21723312     0021723312                    541     0.994151   
# 172       22036611     0022036611                    544     0.993914   
# 173       22169827     0022169827                    546     0.993879   
# 174       21882591     0021882591                    551     0.993730   
# 175       21973099     0021973099                    556     0.993686   
# 176       22065925     0022065925                    558     0.993633   
# 177       21954811     0021954811                    563     0.993521   
# 178       22001484     0022001484                    564     0.993508   
# 179       22071869     0022071869                    565     0.993479   
# 180       22063317     0022063317                    566     0.993419   
# 181       22091878     0022091878                    568     0.993390   
# 182       22088286     0022088286                    572     0.993271   
# 183       20053187     0020053187                    576     0.993225   
# 0         21927707     0021927707                    693     0.992935   
# 1         21881108     0021881108                    694     0.992926   
# 2         21932484     0021932484                    695     0.992924   
# 3         21936243     0021936243                    696     0.992869   
# 4         21971477     0021971477                    697     0.992842   
# 5         21947688     0021947688                    699     0.992784   
# 6         22024447     0022024447                    703     0.992667   
# 7         22011612     0022011612                    706     0.992573   
# 8         22054719     0022054719                    708     0.992469   
# 9         21875153     0021875153                    709     0.992458   
# 10        22090236     0022090236                    714     0.992238   
# 11        22063180     0022063180                    715     0.992206   
# 12        22118157     0022118157                    717     0.992175   
# 13        22051568     0022051568                    721     0.992116   
# 14        22013457     0022013457                    724     0.992051   
# 15        22087071     0022087071                    733     0.991783   
# 16        21396713     0021396713                    734     0.991764   
# 17        22083646     0022083646                    741     0.991478   
# 18        22068291     0022068291                    742     0.991414   
# 19        21945557     0021945557                    744     0.991323   
# 20        22039891     0022039891                    748     0.991206   
# 21        21977712     0021977712                    752     0.990966   
# 22        21983768     0021983768                    754     0.990953   
# 23        21972361     0021972361                    755     0.990942   
# 24        21703889     0021703889                    758     0.990899   
# 25        21943372     0021943372                    762     0.990866   
# 26        22015059     0022015059                    765     0.990699   
# 27        22106528     0022106528                    767     0.990649   
# 28        22052223     0022052223                    770     0.990456   
# 29        22075591     0022075591                    771     0.990449   
# 30        22049402     0022049402                    774     0.990201   
# 31        21905298     0021905298                    775     0.990190   
# 32        21905327     0021905327                    776     0.990126   
# 33        21999217     0021999217                    778     0.990123   
# 34        21949472     0021949472                    779     0.989997   
# 35        22072563     0022072563                    780     0.989995   
# 36        22114799     0022114799                    782     0.989969   
# 37        21932428     0021932428                    784     0.989893   
# 38        21878966     0021878966                    786     0.989732   
# 39        21906060     0021906060                    790     0.989491   
# 40        22044922     0022044922                    795     0.989304   
# 41        22001025     0022001025                    796     0.989274   
# 42        19378420     0019378420                    798     0.989195   
# 43        21906046     0021906046                    799     0.989183   
# 44        22014979     0022014979                    800     0.989156   
# 45        14878020     0014878020                    802     0.989097   
# 46        19782535     0019782535                    803     0.989067   
# 47        21938517     0021938517                    805     0.989022   
# 48        22001399     0022001399                    807     0.988948   
# 49        22040402     0022040402                    808     0.988931   
# 50        21942502     0021942502                    809     0.988913   
# 51        21540756     0021540756                    810     0.988911   
# 52        21908418     0021908418                    811     0.988832   
# 53        21724301     0021724301                    812     0.988817   
# 54        21791332     0021791332                    813     0.988743   
# 55        21692378     0021692378                    816     0.988714   
# 56        21964445     0021964445                    818     0.988666   
# 57        21948379     0021948379                    819     0.988627   
# 58        20392042     0020392042                    823     0.988457   
# 59        21866473     0021866473                    826     0.988367   
# 60        17269518     0017269518                    827     0.988275   
# 61        21977847     0021977847                    828     0.988263   
# 62        21898069     0021898069                    830     0.988150   
# 63        16754084     0016754084                    831     0.988096   
# 64        21918315     0021918315                    832     0.988073   
# 65        21692406     0021692406                    833     0.987900   
# 66        21060605     0021060605                    835     0.987854   
# 67        22019634     0022019634                    836     0.987842   
# 68        21918062     0021918062                    838     0.987752   
# 69        21983786     0021983786                    840     0.987713   
# 70        21940721     0021940721                    842     0.987672   
# 71        21480293     0021480293                    844     0.987508   
# 72        21809596     0021809596                    845     0.987454   
# 73        21918930     0021918930                    847     0.987388   
# 74        22085208     0022085208                    848     0.987339   
# 75        21976682     0021976682                    849     0.987227   
# 76        17356462     0017356462                    851     0.987177   
# 77        22054188     0022054188                    852     0.987146   
# 78        22014546     0022014546                    853     0.987132   
# 79        21816207     0021816207                    854     0.987061   
# 80        21908270     0021908270                    855     0.987059   
# 81        22038761     0022038761                    858     0.986786   
# 82        21864573     0021864573                    859     0.986751   
# 83        22022981     0022022981                    863     0.986611   
# 84        11871738     0011871738                    867     0.986505   
# 85        22058820     0022058820                    868     0.986461   
# 86        21834137     0021834137                    870     0.986337   
# 87        22100457     0022100457                    873     0.986146   
# 88        21917811     0021917811                    874     0.986140   
# 89        21736268     0021736268                    878     0.986006   
# 90        22075302     0022075302                    879     0.985966   
# 91        22097386     0022097386                    880     0.985958   
# 92        20580041     0020580041                    881     0.985790   
# 93        17243383     0017243383                    882     0.985705   
# 94        22133044     0022133044                    884     0.985675   
# 95        22020085     0022020085                    885     0.985621   
# 96        21968274     0021968274                    889     0.985370   
# 97        20249161     0020249161                    890     0.985325   
# 98        19688327     0019688327                    891     0.985260   
# 99        22088439     0022088439                    892     0.985206   
# 100       21884121     0021884121                    893     0.985112   
# 101       21994351     0021994351                    894     0.985034   
# 102       21933273     0021933273                    897     0.984897   
# 103       21998466     0021998466                    899     0.984872   
# 104       21970800     0021970800                    900     0.984769   
# 105       21727657     0021727657                    901     0.984759   
# 106       22042318     0022042318                    902     0.984665   
# 107       21724767     0021724767                    904     0.984515   
# 108       21650523     0021650523                    905     0.984513   
# 109       21538263     0021538263                    906     0.984496   
# 110       17900869     0017900869                    907     0.984415   
# 111       21778202     0021778202                    908     0.984304   
# 112       22111510     0022111510                    909     0.984276   
# 113       21739662     0021739662                    910     0.984272   
# 114       21841312     0021841312                    911     0.984249   
# 115       19503433     0019503433                    912     0.984230   
# 116       21649033     0021649033                    913     0.984086   
# 117       17768246     0017768246                    914     0.984048   
# 118       21896636     0021896636                    915     0.984005   
# 119       19886797     0019886797                    916     0.983969   
# 
#          prob  rank_modelo   tipo_alerta_n2  \
# 120  0.996114           95         SIN_INFO   
# 121  0.995481          135         SIN_INFO   
# 122  0.997100           34         SIN_INFO   
# 123  0.997101           33         SIN_INFO   
# 124  0.994885          179         SIN_INFO   
# 125  0.996892           48         SIN_INFO   
# 126  0.997185           31         SIN_INFO   
# 127  0.994504          209         SIN_INFO   
# 128  0.996662           63         SIN_INFO   
# 129  0.995840          105  SEMI AUTOMATICA   
# 130  0.995498          131  SEMI AUTOMATICA   
# 131  0.987681          699         SIN_INFO   
# 132  0.996656           64         SIN_INFO   
# 133  0.993315          295         SIN_INFO   
# 134  0.994510          208         SIN_INFO   
# 135  0.994729          194         SIN_INFO   
# 136  0.998492            3         SIN_INFO   
# 137  0.993147          309         SIN_INFO   
# 138  0.996902           46           MANUAL   
# 139  0.997175           32         SIN_INFO   
# 140  0.995517          129         SIN_INFO   
# 141  0.995263          156         SIN_INFO   
# 142  0.993316          294         SIN_INFO   
# 143  0.992217          374         SIN_INFO   
# 144  0.997089           36         SIN_INFO   
# 145  0.998174           10         SIN_INFO   
# 146  0.992356          364         SIN_INFO   
# 147  0.993066          317         SIN_INFO   
# 148  0.998879            2         SIN_INFO   
# 149  0.994598          202         SIN_INFO   
# 150  0.583673        13806         SIN_INFO   
# 151  0.994129          232         SIN_INFO   
# 152  0.994494          210         SIN_INFO   
# 153  0.995637          121         SIN_INFO   
# 154  0.998056           15         SIN_INFO   
# 155  0.995169          162  SEMI AUTOMATICA   
# 156  0.252419        41059         SIN_INFO   
# 157  0.994119          234         SIN_INFO   
# 158  0.995866          103         SIN_INFO   
# 159  0.996253           84         SIN_INFO   
# 160  0.996671           62         SIN_INFO   
# 161  0.995441          139         SIN_INFO   
# 162  0.979788         1145         SIN_INFO   
# 163  0.993569          274         SIN_INFO   
# 164  0.992231          372         SIN_INFO   
# 165  0.993794          254         SIN_INFO   
# 166  0.995370          146         SIN_INFO   
# 167  0.998083           13         SIN_INFO   
# 168  0.995286          153         SIN_INFO   
# 169  0.995353          147           MANUAL   
# 170  0.998221            9         SIN_INFO   
# 171  0.991232          438         SIN_INFO   
# 172  0.995759          113         SIN_INFO   
# 173  0.992824          335         SIN_INFO   
# 174  0.993366          291  SEMI AUTOMATICA   
# 175  0.996862           50         SIN_INFO   
# 176  0.998160           11         SIN_INFO   
# 177  0.993502          280         SIN_INFO   
# 178  0.984919          859         SIN_INFO   
# 179  0.997897           18         SIN_INFO   
# 180  0.995656          119         SIN_INFO   
# 181  0.994589          204           MANUAL   
# 182  0.992584          349         SIN_INFO   
# 183  0.991110          449         SIN_INFO   
# 0    0.994161          229         SIN_INFO   
# 1    0.991689          407           MANUAL   
# 2    0.991829          401           MANUAL   
# 3    0.990435          508         SIN_INFO   
# 4    0.992341          366         SIN_INFO   
# 5    0.995770          112         SIN_INFO   
# 6    0.994734          193  SEMI AUTOMATICA   
# 7    0.990785          481         SIN_INFO   
# 8    0.990910          464         SIN_INFO   
# 9    0.994171          228         SIN_INFO   
# 10   0.411647        22081         SIN_INFO   
# 11   0.883592         4861         SIN_INFO   
# 12   0.993117          311         SIN_INFO   
# 13   0.983149          974         SIN_INFO   
# 14   0.993577          272           MANUAL   
# 15   0.991136          447         SIN_INFO   
# 16   0.995057          166         SIN_INFO   
# 17   0.987503          711         SIN_INFO   
# 18   0.975681         1359         SIN_INFO   
# 19   0.986317          780         SIN_INFO   
# 20   0.989050          606         SIN_INFO   
# 21   0.994761          188         SIN_INFO   
# 22   0.998223            7         SIN_INFO   
# 23   0.988960          610         SIN_INFO   
# 24   0.969099         1652         SIN_INFO   
# 25   0.993966          241         SIN_INFO   
# 26   0.992265          371         SIN_INFO   
# 27   0.992409          361         SIN_INFO   
# 28   0.967892         1715         SIN_INFO   
# 29   0.968376         1688         SIN_INFO   
# 30   0.989489          580         SIN_INFO   
# 31   0.980542         1097         SIN_INFO   
# 32   0.994242          222       AUTOMATICA   
# 33   0.988138          673         SIN_INFO   
# 34   0.993690          261         SIN_INFO   
# 35   0.988778          628         SIN_INFO   
# 36   0.971068         1569         SIN_INFO   
# 37   0.985931          807         SIN_INFO   
# 38   0.995742          115  SEMI AUTOMATICA   
# 39   0.995486          133         SIN_INFO   
# 40   0.364029        26552         SIN_INFO   
# 41   0.989597          572         SIN_INFO   
# 42   0.987362          722         SIN_INFO   
# 43   0.993027          321         SIN_INFO   
# 44   0.985448          832         SIN_INFO   
# 45   0.988509          652         SIN_INFO   
# 46   0.881525         4931         SIN_INFO   
# 47   0.986623          760         SIN_INFO   
# 48   0.979090         1181         SIN_INFO   
# 49   0.985066          851         SIN_INFO   
# 50   0.990274          516         SIN_INFO   
# 51   0.990090          531           MANUAL   
# 52   0.995681          117         SIN_INFO   
# 53   0.991010          457         SIN_INFO   
# 54   0.992197          376         SIN_INFO   
# 55   0.994113          235         SIN_INFO   
# 56   0.988626          639         SIN_INFO   
# 57   0.993443          288         SIN_INFO   
# 58   0.982432         1017         SIN_INFO   
# 59   0.994662          199         SIN_INFO   
# 60   0.951179         2387         SIN_INFO   
# 61   0.940706         2813         SIN_INFO   
# 62   0.994529          206         SIN_INFO   
# 63   0.985691          818         SIN_INFO   
# 64   0.994384          215         SIN_INFO   
# 65   0.993170          307         SIN_INFO   
# 66   0.988073          678         SIN_INFO   
# 67   0.356221        27709         SIN_INFO   
# 68   0.993815          252         SIN_INFO   
# 69   0.996299           82         SIN_INFO   
# 70   0.977661         1260         SIN_INFO   
# 71   0.995639          120         SIN_INFO   
# 72   0.994198          226         SIN_INFO   
# 73   0.992918          331           MANUAL   
# 74   0.971507         1552         SIN_INFO   
# 75   0.983429          956         SIN_INFO   
# 76   0.922149         3510         SIN_INFO   
# 77   0.991991          390         SIN_INFO   
# 78   0.984913          860         SIN_INFO   
# 79   0.995623          122         SIN_INFO   
# 80   0.993670          265         SIN_INFO   
# 81   0.950980         2401         SIN_INFO   
# 82   0.988512          651         SIN_INFO   
# 83   0.990070          537         SIN_INFO   
# 84   0.893457         4506         SIN_INFO   
# 85   0.890917         4604         SIN_INFO   
# 86   0.989098          602         SIN_INFO   
# 87   0.239077        43606         SIN_INFO   
# 88   0.991346          433         SIN_INFO   
# 89   0.991169          444         SIN_INFO   
# 90   0.969265         1643         SIN_INFO   
# 91   0.979670         1151         SIN_INFO   
# 92   0.986676          757         SIN_INFO   
# 93   0.966546         1772           MANUAL   
# 94   0.979394         1163         SIN_INFO   
# 95   0.980361         1110         SIN_INFO   
# 96   0.994070          237         SIN_INFO   
# 97   0.989048          607         SIN_INFO   
# 98   0.984591          886         SIN_INFO   
# 99   0.985231          843         SIN_INFO   
# 100  0.955340         2223         SIN_INFO   
# 101  0.995222          158         SIN_INFO   
# 102  0.990602          496         SIN_INFO   
# 103  0.923669         3453         SIN_INFO   
# 104  0.958095         2109         SIN_INFO   
# 105  0.993656          268           MANUAL   
# 106  0.390422        23767         SIN_INFO   
# 107  0.991081          452         SIN_INFO   
# 108  0.990868          468         SIN_INFO   
# 109  0.987986          683         SIN_INFO   
# 110  0.986592          763         SIN_INFO   
# 111  0.989586          573         SIN_INFO   
# 112  0.886659         4758         SIN_INFO   
# 113  0.995532          127         SIN_INFO   
# 114  0.980540         1098         SIN_INFO   
# 115  0.986500          766         SIN_INFO   
# 116  0.970865         1577         SIN_INFO   
# 117  0.974863         1397         SIN_INFO   
# 118  0.989835          557         SIN_INFO   
# 119  0.964552         1847         SIN_INFO   
# 
#                                     base  rank_piloto  \
# 120    df_6_razones_sospechosas_20260416            1   
# 121    df_6_razones_sospechosas_20260416            2   
# 122    df_6_razones_sospechosas_20260416            3   
# 123    df_6_razones_sospechosas_20260416            4   
# 124    df_6_razones_sospechosas_20260416            5   
# 125    df_6_razones_sospechosas_20260416            6   
# 126    df_6_razones_sospechosas_20260416            7   
# 127    df_6_razones_sospechosas_20260416            8   
# 128    df_6_razones_sospechosas_20260416            9   
# 129    df_6_razones_sospechosas_20260416           10   
# 130    df_6_razones_sospechosas_20260416           11   
# 131    df_6_razones_sospechosas_20260416           12   
# 132    df_6_razones_sospechosas_20260416           13   
# 133    df_6_razones_sospechosas_20260416           14   
# 134    df_6_razones_sospechosas_20260416           15   
# 135    df_6_razones_sospechosas_20260416           16   
# 136    df_6_razones_sospechosas_20260416           17   
# 137    df_6_razones_sospechosas_20260416           18   
# 138    df_6_razones_sospechosas_20260416           19   
# 139    df_6_razones_sospechosas_20260416           20   
# 140    df_6_razones_sospechosas_20260416           21   
# 141    df_6_razones_sospechosas_20260416           22   
# 142    df_6_razones_sospechosas_20260416           23   
# 143    df_6_razones_sospechosas_20260416           24   
# 144    df_6_razones_sospechosas_20260416           25   
# 145    df_6_razones_sospechosas_20260416           26   
# 146    df_6_razones_sospechosas_20260416           27   
# 147    df_6_razones_sospechosas_20260416           28   
# 148    df_6_razones_sospechosas_20260416           29   
# 149    df_6_razones_sospechosas_20260416           30   
# 150    df_6_razones_sospechosas_20260416           31   
# 151    df_6_razones_sospechosas_20260416           32   
# 152    df_6_razones_sospechosas_20260416           33   
# 153    df_6_razones_sospechosas_20260416           34   
# 154    df_6_razones_sospechosas_20260416           35   
# 155    df_6_razones_sospechosas_20260416           36   
# 156    df_6_razones_sospechosas_20260416           37   
# 157    df_6_razones_sospechosas_20260416           38   
# 158    df_6_razones_sospechosas_20260416           39   
# 159    df_6_razones_sospechosas_20260416           40   
# 160    df_6_razones_sospechosas_20260416           41   
# 161    df_6_razones_sospechosas_20260416           42   
# 162    df_6_razones_sospechosas_20260416           43   
# 163    df_6_razones_sospechosas_20260416           44   
# 164    df_6_razones_sospechosas_20260416           45   
# 165    df_6_razones_sospechosas_20260416           46   
# 166    df_6_razones_sospechosas_20260416           47   
# 167    df_6_razones_sospechosas_20260416           48   
# 168    df_6_razones_sospechosas_20260416           49   
# 169    df_6_razones_sospechosas_20260416           50   
# 170    df_6_razones_sospechosas_20260416           51   
# 171    df_6_razones_sospechosas_20260416           52   
# 172    df_6_razones_sospechosas_20260416           53   
# 173    df_6_razones_sospechosas_20260416           54   
# 174    df_6_razones_sospechosas_20260416           55   
# 175    df_6_razones_sospechosas_20260416           56   
# 176    df_6_razones_sospechosas_20260416           57   
# 177    df_6_razones_sospechosas_20260416           58   
# 178    df_6_razones_sospechosas_20260416           59   
# 179    df_6_razones_sospechosas_20260416           60   
# 180    df_6_razones_sospechosas_20260416           61   
# 181    df_6_razones_sospechosas_20260416           62   
# 182    df_6_razones_sospechosas_20260416           63   
# 183    df_6_razones_sospechosas_20260416           64   
# 0    df_6_razones_sospechosas_20260409 1           65   
# 1    df_6_razones_sospechosas_20260409 1           66   
# 2    df_6_razones_sospechosas_20260409 1           67   
# 3    df_6_razones_sospechosas_20260409 1           68   
# 4    df_6_razones_sospechosas_20260409 1           69   
# 5    df_6_razones_sospechosas_20260409 1           70   
# 6    df_6_razones_sospechosas_20260409 1           71   
# 7    df_6_razones_sospechosas_20260409 1           72   
# 8    df_6_razones_sospechosas_20260409 1           73   
# 9    df_6_razones_sospechosas_20260409 1           74   
# 10   df_6_razones_sospechosas_20260409 1           75   
# 11   df_6_razones_sospechosas_20260409 1           76   
# 12   df_6_razones_sospechosas_20260409 1           77   
# 13   df_6_razones_sospechosas_20260409 1           78   
# 14   df_6_razones_sospechosas_20260409 1           79   
# 15   df_6_razones_sospechosas_20260409 1           80   
# 16   df_6_razones_sospechosas_20260409 1           81   
# 17   df_6_razones_sospechosas_20260409 1           82   
# 18   df_6_razones_sospechosas_20260409 1           83   
# 19   df_6_razones_sospechosas_20260409 1           84   
# 20   df_6_razones_sospechosas_20260409 1           85   
# 21   df_6_razones_sospechosas_20260409 1           86   
# 22   df_6_razones_sospechosas_20260409 1           87   
# 23   df_6_razones_sospechosas_20260409 1           88   
# 24   df_6_razones_sospechosas_20260409 1           89   
# 25   df_6_razones_sospechosas_20260409 1           90   
# 26   df_6_razones_sospechosas_20260409 1           91   
# 27   df_6_razones_sospechosas_20260409 1           92   
# 28   df_6_razones_sospechosas_20260409 1           93   
# 29   df_6_razones_sospechosas_20260409 1           94   
# 30   df_6_razones_sospechosas_20260409 1           95   
# 31   df_6_razones_sospechosas_20260409 1           96   
# 32   df_6_razones_sospechosas_20260409 1           97   
# 33   df_6_razones_sospechosas_20260409 1           98   
# 34   df_6_razones_sospechosas_20260409 1           99   
# 35   df_6_razones_sospechosas_20260409 1          100   
# 36   df_6_razones_sospechosas_20260409 1          101   
# 37   df_6_razones_sospechosas_20260409 1          102   
# 38   df_6_razones_sospechosas_20260409 1          103   
# 39   df_6_razones_sospechosas_20260409 1          104   
# 40   df_6_razones_sospechosas_20260409 1          105   
# 41   df_6_razones_sospechosas_20260409 1          106   
# 42   df_6_razones_sospechosas_20260409 1          107   
# 43   df_6_razones_sospechosas_20260409 1          108   
# 44   df_6_razones_sospechosas_20260409 1          109   
# 45   df_6_razones_sospechosas_20260409 1          110   
# 46   df_6_razones_sospechosas_20260409 1          111   
# 47   df_6_razones_sospechosas_20260409 1          112   
# 48   df_6_razones_sospechosas_20260409 1          113   
# 49   df_6_razones_sospechosas_20260409 1          114   
# 50   df_6_razones_sospechosas_20260409 1          115   
# 51   df_6_razones_sospechosas_20260409 1          116   
# 52   df_6_razones_sospechosas_20260409 1          117   
# 53   df_6_razones_sospechosas_20260409 1          118   
# 54   df_6_razones_sospechosas_20260409 1          119   
# 55   df_6_razones_sospechosas_20260409 1          120   
# 56   df_6_razones_sospechosas_20260409 1          121   
# 57   df_6_razones_sospechosas_20260409 1          122   
# 58   df_6_razones_sospechosas_20260409 1          123   
# 59   df_6_razones_sospechosas_20260409 1          124   
# 60   df_6_razones_sospechosas_20260409 1          125   
# 61   df_6_razones_sospechosas_20260409 1          126   
# 62   df_6_razones_sospechosas_20260409 1          127   
# 63   df_6_razones_sospechosas_20260409 1          128   
# 64   df_6_razones_sospechosas_20260409 1          129   
# 65   df_6_razones_sospechosas_20260409 1          130   
# 66   df_6_razones_sospechosas_20260409 1          131   
# 67   df_6_razones_sospechosas_20260409 1          132   
# 68   df_6_razones_sospechosas_20260409 1          133   
# 69   df_6_razones_sospechosas_20260409 1          134   
# 70   df_6_razones_sospechosas_20260409 1          135   
# 71   df_6_razones_sospechosas_20260409 1          136   
# 72   df_6_razones_sospechosas_20260409 1          137   
# 73   df_6_razones_sospechosas_20260409 1          138   
# 74   df_6_razones_sospechosas_20260409 1          139   
# 75   df_6_razones_sospechosas_20260409 1          140   
# 76   df_6_razones_sospechosas_20260409 1          141   
# 77   df_6_razones_sospechosas_20260409 1          142   
# 78   df_6_razones_sospechosas_20260409 1          143   
# 79   df_6_razones_sospechosas_20260409 1          144   
# 80   df_6_razones_sospechosas_20260409 1          145   
# 81   df_6_razones_sospechosas_20260409 1          146   
# 82   df_6_razones_sospechosas_20260409 1          147   
# 83   df_6_razones_sospechosas_20260409 1          148   
# 84   df_6_razones_sospechosas_20260409 1          149   
# 85   df_6_razones_sospechosas_20260409 1          150   
# 86   df_6_razones_sospechosas_20260409 1          151   
# 87   df_6_razones_sospechosas_20260409 1          152   
# 88   df_6_razones_sospechosas_20260409 1          153   
# 89   df_6_razones_sospechosas_20260409 1          154   
# 90   df_6_razones_sospechosas_20260409 1          155   
# 91   df_6_razones_sospechosas_20260409 1          156   
# 92   df_6_razones_sospechosas_20260409 1          157   
# 93   df_6_razones_sospechosas_20260409 1          158   
# 94   df_6_razones_sospechosas_20260409 1          159   
# 95   df_6_razones_sospechosas_20260409 1          160   
# 96   df_6_razones_sospechosas_20260409 1          161   
# 97   df_6_razones_sospechosas_20260409 1          162   
# 98   df_6_razones_sospechosas_20260409 1          163   
# 99   df_6_razones_sospechosas_20260409 1          164   
# 100  df_6_razones_sospechosas_20260409 1          165   
# 101  df_6_razones_sospechosas_20260409 1          166   
# 102  df_6_razones_sospechosas_20260409 1          167   
# 103  df_6_razones_sospechosas_20260409 1          168   
# 104  df_6_razones_sospechosas_20260409 1          169   
# 105  df_6_razones_sospechosas_20260409 1          170   
# 106  df_6_razones_sospechosas_20260409 1          171   
# 107  df_6_razones_sospechosas_20260409 1          172   
# 108  df_6_razones_sospechosas_20260409 1          173   
# 109  df_6_razones_sospechosas_20260409 1          174   
# 110  df_6_razones_sospechosas_20260409 1          175   
# 111  df_6_razones_sospechosas_20260409 1          176   
# 112  df_6_razones_sospechosas_20260409 1          177   
# 113  df_6_razones_sospechosas_20260409 1          178   
# 114  df_6_razones_sospechosas_20260409 1          179   
# 115  df_6_razones_sospechosas_20260409 1          180   
# 116  df_6_razones_sospechosas_20260409 1          181   
# 117  df_6_razones_sospechosas_20260409 1          182   
# 118  df_6_razones_sospechosas_20260409 1          183   
# 119  df_6_razones_sospechosas_20260409 1          184   
# 
#                      estado_cruce  dif_prob  dif_orden  
# 120  Incluido en ranking completo -0.001162         94  
# 121  Incluido en ranking completo -0.001526        133  
# 122  Incluido en ranking completo  0.000354         31  
# 123  Incluido en ranking completo  0.000440         29  
# 124  Incluido en ranking completo -0.001757        174  
# 125  Incluido en ranking completo  0.000277         42  
# 126  Incluido en ranking completo  0.000652         24  
# 127  Incluido en ranking completo -0.001942        201  
# 128  Incluido en ranking completo  0.000260         54  
# 129  Incluido en ranking completo -0.000386         95  
# 130  Incluido en ranking completo -0.000691        120  
# 131  Incluido en ranking completo -0.008460        687  
# 132  Incluido en ranking completo  0.000638         51  
# 133  Incluido en ranking completo -0.002623        281  
# 134  Incluido en ranking completo -0.001398        193  
# 135  Incluido en ranking completo -0.001060        178  
# 136  Incluido en ranking completo  0.002730        -14  
# 137  Incluido en ranking completo -0.002609        291  
# 138  Incluido en ranking completo  0.001211         27  
# 139  Incluido en ranking completo  0.001494         12  
# 140  Incluido en ranking completo -0.000147        108  
# 141  Incluido en ranking completo -0.000355        134  
# 142  Incluido en ranking completo -0.002250        271  
# 143  Incluido en ranking completo -0.003291        350  
# 144  Incluido en ranking completo  0.001790         11  
# 145  Incluido en ranking completo  0.002966        -16  
# 146  Incluido en ranking completo -0.002841        337  
# 147  Incluido en ranking completo -0.002099        289  
# 148  Incluido en ranking completo  0.003735        -27  
# 149  Incluido en ranking completo -0.000511        172  
# 150  Incluido en ranking completo -0.411420      13775  
# 151  Incluido en ranking completo -0.000884        200  
# 152  Incluido en ranking completo -0.000509        177  
# 153  Incluido en ranking completo  0.000668         87  
# 154  Incluido en ranking completo  0.003134        -20  
# 155  Incluido en ranking completo  0.000404        126  
# 156  Incluido en ranking completo -0.742242      41022  
# 157  Incluido en ranking completo -0.000495        196  
# 158  Incluido en ranking completo  0.001274         64  
# 159  Incluido en ranking completo  0.001681         44  
# 160  Incluido en ranking completo  0.002103         21  
# 161  Incluido en ranking completo  0.000879         97  
# 162  Incluido en ranking completo -0.014728       1102  
# 163  Incluido en ranking completo -0.000920        230  
# 164  Incluido en ranking completo -0.002221        327  
# 165  Incluido en ranking completo -0.000657        208  
# 166  Incluido en ranking completo  0.000923         99  
# 167  Incluido en ranking completo  0.003674        -35  
# 168  Incluido en ranking completo  0.000907        104  
# 169  Incluido en ranking completo  0.001008         97  
# 170  Incluido en ranking completo  0.004030        -42  
# 171  Incluido en ranking completo -0.002919        386  
# 172  Incluido en ranking completo  0.001845         60  
# 173  Incluido en ranking completo -0.001055        281  
# 174  Incluido en ranking completo -0.000364        236  
# 175  Incluido en ranking completo  0.003176         -6  
# 176  Incluido en ranking completo  0.004527        -46  
# 177  Incluido en ranking completo -0.000018        222  
# 178  Incluido en ranking completo -0.008589        800  
# 179  Incluido en ranking completo  0.004418        -42  
# 180  Incluido en ranking completo  0.002237         58  
# 181  Incluido en ranking completo  0.001199        142  
# 182  Incluido en ranking completo -0.000686        286  
# 183  Incluido en ranking completo -0.002114        385  
# 0    Incluido en ranking completo  0.001225        164  
# 1    Incluido en ranking completo -0.001237        341  
# 2    Incluido en ranking completo -0.001095        334  
# 3    Incluido en ranking completo -0.002434        440  
# 4    Incluido en ranking completo -0.000501        297  
# 5    Incluido en ranking completo  0.002986         42  
# 6    Incluido en ranking completo  0.002067        122  
# 7    Incluido en ranking completo -0.001788        409  
# 8    Incluido en ranking completo -0.001559        391  
# 9    Incluido en ranking completo  0.001713        154  
# 10   Incluido en ranking completo -0.580591      22006  
# 11   Incluido en ranking completo -0.108614       4785  
# 12   Incluido en ranking completo  0.000942        234  
# 13   Incluido en ranking completo -0.008967        896  
# 14   Incluido en ranking completo  0.001526        193  
# 15   Incluido en ranking completo -0.000647        367  
# 16   Incluido en ranking completo  0.003293         85  
# 17   Incluido en ranking completo -0.003975        629  
# 18   Incluido en ranking completo -0.015734       1276  
# 19   Incluido en ranking completo -0.005007        696  
# 20   Incluido en ranking completo -0.002156        521  
# 21   Incluido en ranking completo  0.003795        102  
# 22   Incluido en ranking completo  0.007271        -80  
# 23   Incluido en ranking completo -0.001982        522  
# 24   Incluido en ranking completo -0.021800       1563  
# 25   Incluido en ranking completo  0.003100        151  
# 26   Incluido en ranking completo  0.001566        280  
# 27   Incluido en ranking completo  0.001760        269  
# 28   Incluido en ranking completo -0.022565       1622  
# 29   Incluido en ranking completo -0.022073       1594  
# 30   Incluido en ranking completo -0.000712        485  
# 31   Incluido en ranking completo -0.009648       1001  
# 32   Incluido en ranking completo  0.004116        125  
# 33   Incluido en ranking completo -0.001985        575  
# 34   Incluido en ranking completo  0.003693        162  
# 35   Incluido en ranking completo -0.001217        528  
# 36   Incluido en ranking completo -0.018900       1468  
# 37   Incluido en ranking completo -0.003961        705  
# 38   Incluido en ranking completo  0.006011         12  
# 39   Incluido en ranking completo  0.005995         29  
# 40   Incluido en ranking completo -0.625275      26447  
# 41   Incluido en ranking completo  0.000324        466  
# 42   Incluido en ranking completo -0.001834        615  
# 43   Incluido en ranking completo  0.003844        213  
# 44   Incluido en ranking completo -0.003708        723  
# 45   Incluido en ranking completo -0.000588        542  
# 46   Incluido en ranking completo -0.107542       4820  
# 47   Incluido en ranking completo -0.002400        648  
# 48   Incluido en ranking completo -0.009858       1068  
# 49   Incluido en ranking completo -0.003865        737  
# 50   Incluido en ranking completo  0.001361        401  
# 51   Incluido en ranking completo  0.001178        415  
# 52   Incluido en ranking completo  0.006849          0  
# 53   Incluido en ranking completo  0.002193        339  
# 54   Incluido en ranking completo  0.003454        257  
# 55   Incluido en ranking completo  0.005399        115  
# 56   Incluido en ranking completo -0.000041        518  
# 57   Incluido en ranking completo  0.004816        166  
# 58   Incluido en ranking completo -0.006025        894  
# 59   Incluido en ranking completo  0.006296         75  
# 60   Incluido en ranking completo -0.037096       2262  
# 61   Incluido en ranking completo -0.047557       2687  
# 62   Incluido en ranking completo  0.006379         79  
# 63   Incluido en ranking completo -0.002405        690  
# 64   Incluido en ranking completo  0.006311         86  
# 65   Incluido en ranking completo  0.005271        177  
# 66   Incluido en ranking completo  0.000219        547  
# 67   Incluido en ranking completo -0.631621      27577  
# 68   Incluido en ranking completo  0.006063        119  
# 69   Incluido en ranking completo  0.008586        -52  
# 70   Incluido en ranking completo -0.010011       1125  
# 71   Incluido en ranking completo  0.008131        -16  
# 72   Incluido en ranking completo  0.006744         89  
# 73   Incluido en ranking completo  0.005530        193  
# 74   Incluido en ranking completo -0.015832       1413  
# 75   Incluido en ranking completo -0.003799        816  
# 76   Incluido en ranking completo -0.065028       3369  
# 77   Incluido en ranking completo  0.004845        248  
# 78   Incluido en ranking completo -0.002219        717  
# 79   Incluido en ranking completo  0.008561        -22  
# 80   Incluido en ranking completo  0.006612        120  
# 81   Incluido en ranking completo -0.035806       2255  
# 82   Incluido en ranking completo  0.001761        504  
# 83   Incluido en ranking completo  0.003459        389  
# 84   Incluido en ranking completo -0.093048       4357  
# 85   Incluido en ranking completo -0.095544       4454  
# 86   Incluido en ranking completo  0.002762        451  
# 87   Incluido en ranking completo -0.747069      43454  
# 88   Incluido en ranking completo  0.005206        280  
# 89   Incluido en ranking completo  0.005163        290  
# 90   Incluido en ranking completo -0.016701       1488  
# 91   Incluido en ranking completo -0.006288        995  
# 92   Incluido en ranking completo  0.000886        600  
# 93   Incluido en ranking completo -0.019158       1614  
# 94   Incluido en ranking completo -0.006281       1004  
# 95   Incluido en ranking completo -0.005260        950  
# 96   Incluido en ranking completo  0.008699         76  
# 97   Incluido en ranking completo  0.003723        445  
# 98   Incluido en ranking completo -0.000669        723  
# 99   Incluido en ranking completo  0.000025        679  
# 100  Incluido en ranking completo -0.029772       2058  
# 101  Incluido en ranking completo  0.010187         -8  
# 102  Incluido en ranking completo  0.005705        329  
# 103  Incluido en ranking completo -0.061203       3285  
# 104  Incluido en ranking completo -0.026675       1940  
# 105  Incluido en ranking completo  0.008897         98  
# 106  Incluido en ranking completo -0.594243      23596  
# 107  Incluido en ranking completo  0.006567        280  
# 108  Incluido en ranking completo  0.006355        295  
# 109  Incluido en ranking completo  0.003490        509  
# 110  Incluido en ranking completo  0.002177        588  
# 111  Incluido en ranking completo  0.005281        397  
# 112  Incluido en ranking completo -0.097617       4581  
# 113  Incluido en ranking completo  0.011260        -51  
# 114  Incluido en ranking completo -0.003710        919  
# 115  Incluido en ranking completo  0.002269        586  
# 116  Incluido en ranking completo -0.013221       1396  
# 117  Incluido en ranking completo -0.009185       1215  
# 118  Incluido en ranking completo  0.005829        374  
# 119  Incluido en ranking completo -0.019416       1663  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 85 ---
# execution_count: 58

# ============================================================
# Validacion de similitud: piloto original vs nuevo modelo
# ============================================================

# Se validan solo clientes con cruce exitoso y ambas probabilidades disponibles.
df_validacion_similitud = df_comparacion_orden.dropna(
    subset=['prob_piloto', 'prob', 'rank_piloto', 'rank_modelo']
).copy()

n_validacion = len(df_validacion_similitud)
delta_prob = (
    df_validacion_similitud['prob']
    - df_validacion_similitud['prob_piloto']
)
delta_rank = (
    df_validacion_similitud['rank_modelo']
    - df_validacion_similitud['rank_piloto']
)

metricas_similitud = pd.DataFrame({
    'metrica': [
        'Clientes evaluados',
        'Correlacion Pearson de probabilidades',
        'Correlacion Spearman de probabilidades',
        'MAE absoluto de probabilidad',
        'RMSE de probabilidad',
        'Clientes con diferencia de probabilidad <= 0.005',
        'Clientes con diferencia de probabilidad <= 0.010',
        'Mediana de diferencia absoluta de ranking',
        'Clientes con diferencia absoluta de ranking <= 10',
        'Clientes con diferencia absoluta de ranking <= 25',
        'Clientes con diferencia absoluta de ranking <= 50',
    ],
    'valor': [
        n_validacion,
        df_validacion_similitud['prob_piloto'].corr(
            df_validacion_similitud['prob'], method='pearson'
        ),
        df_validacion_similitud['prob_piloto'].corr(
            df_validacion_similitud['prob'], method='spearman'
        ),
        delta_prob.abs().mean(),
        np.sqrt((delta_prob ** 2).mean()),
        (delta_prob.abs() <= 0.005).sum(),
        (delta_prob.abs() <= 0.010).sum(),
        delta_rank.abs().median(),
        (delta_rank.abs() <= 10).sum(),
        (delta_rank.abs() <= 25).sum(),
        (delta_rank.abs() <= 50).sum(),
    ]
})

# Coincidencia de los principales clientes del piloto en el ranking actual.
filas_top_k = []
for k in [10, 20, 50, 100]:
    top_piloto = set(
        df_validacion_similitud.loc[
            df_validacion_similitud['rank_piloto'] <= k,
            'cod_cli_piloto'
        ]
    )
    top_modelo = set(
        df_validacion_similitud.loc[
            df_validacion_similitud['rank_modelo'] <= k,
            'cod_cli_piloto'
        ]
    )
    interseccion = len(top_piloto & top_modelo)
    filas_top_k.append({
        'K': k,
        'clientes_top_k_piloto': len(top_piloto),
        'clientes_top_k_modelo': len(top_modelo),
        'coincidencias': interseccion,
        'recall_top_k_piloto': interseccion / len(top_piloto)
        if top_piloto else 0.0,
    })

df_top_k_similitud = pd.DataFrame(filas_top_k)

print('METRICAS DE SIMILITUD')
display(metricas_similitud)
print('COINCIDENCIA DE CLIENTES EN TOP-K')
display(df_top_k_similitud)

# Clientes con mayor cambio de posicion para revisar excepciones.
df_mayores_cambios = (
    df_validacion_similitud.assign(
        diferencia_abs_rank=delta_rank.abs(),
        diferencia_abs_prob=delta_prob.abs()
    )
    .sort_values(
        ['diferencia_abs_rank', 'diferencia_abs_prob'],
        ascending=False
    )
    [[
        'cod_cli_piloto', 'rank_piloto', 'prob_piloto',
        'rank_modelo', 'prob', 'dif_orden', 'dif_prob',
        'tipo_alerta_n2'
    ]]
)

df_mayores_cambios.head(20)


# --- OUTPUT ---

# Output 1:
# METRICAS DE SIMILITUD

# Output 2:
#                                               metrica       valor
# 0                                  Clientes evaluados  184.000000
# 1               Correlacion Pearson de probabilidades    0.103033
# 2              Correlacion Spearman de probabilidades    0.575129
# 3                        MAE absoluto de probabilidad    0.031717
# 4                                RMSE de probabilidad    0.124019
# 5    Clientes con diferencia de probabilidad <= 0.005  115.000000
# 6    Clientes con diferencia de probabilidad <= 0.010  151.000000
# 7           Mediana de diferencia absoluta de ranking  289.500000
# 8   Clientes con diferencia absoluta de ranking <= 10    3.000000
# 9   Clientes con diferencia absoluta de ranking <= 25   13.000000
# 10  Clientes con diferencia absoluta de ranking <= 50   25.000000

# Output 3:
# COINCIDENCIA DE CLIENTES EN TOP-K

# Output 4:
#      K  clientes_top_k_piloto  clientes_top_k_modelo  coincidencias  \
# 0   10                     10                      5              0   
# 1   20                     20                      9              1   
# 2   50                     50                     17             12   
# 3  100                    100                     23             22   
# 
#    recall_top_k_piloto  
# 0                 0.00  
# 1                 0.05  
# 2                 0.24  
# 3                 0.22  

# Output 5:
#     cod_cli_piloto  rank_piloto  prob_piloto  rank_modelo      prob  \
# 87        22100457          152     0.986146        43606  0.239077   
# 156       22040445           37     0.994661        41059  0.252419   
# 67        22019634          132     0.987842        27709  0.356221   
# 40        22044922          105     0.989304        26552  0.364029   
# 106       22042318          171     0.984665        23767  0.390422   
# 10        22090236           75     0.992238        22081  0.411647   
# 150       21292833           31     0.995093        13806  0.583673   
# 46        19782535          111     0.989067         4931  0.881525   
# 11        22063180           76     0.992206         4861  0.883592   
# 112       22111510          177     0.984276         4758  0.886659   
# 85        22058820          150     0.986461         4604  0.890917   
# 84        11871738          149     0.986505         4506  0.893457   
# 76        17356462          141     0.987177         3510  0.922149   
# 103       21998466          168     0.984872         3453  0.923669   
# 61        21977847          126     0.988263         2813  0.940706   
# 60        17269518          125     0.988275         2387  0.951179   
# 81        22038761          146     0.986786         2401  0.950980   
# 100       21884121          165     0.985112         2223  0.955340   
# 104       21970800          169     0.984769         2109  0.958095   
# 119       19886797          184     0.983969         1847  0.964552   
# 
#      dif_orden  dif_prob tipo_alerta_n2  
# 87       43454 -0.747069       SIN_INFO  
# 156      41022 -0.742242       SIN_INFO  
# 67       27577 -0.631621       SIN_INFO  
# 40       26447 -0.625275       SIN_INFO  
# 106      23596 -0.594243       SIN_INFO  
# 10       22006 -0.580591       SIN_INFO  
# 150      13775 -0.411420       SIN_INFO  
# 46        4820 -0.107542       SIN_INFO  
# 11        4785 -0.108614       SIN_INFO  
# 112       4581 -0.097617       SIN_INFO  
# 85        4454 -0.095544       SIN_INFO  
# 84        4357 -0.093048       SIN_INFO  
# 76        3369 -0.065028       SIN_INFO  
# 103       3285 -0.061203       SIN_INFO  
# 61        2687 -0.047557       SIN_INFO  
# 60        2262 -0.037096       SIN_INFO  
# 81        2255 -0.035806       SIN_INFO  
# 100       2058 -0.029772       SIN_INFO  
# 104       1940 -0.026675       SIN_INFO  
# 119       1663 -0.019416       SIN_INFO  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 86 ---
# execution_count: 59

# ============================================================
# Similitud del orden relativo dentro de los 184 clientes piloto
# ============================================================

# Este ranking no mide la posicion frente a todo el universo.
# Mide si el nuevo modelo conserva el orden entre los mismos 184 clientes.
df_validacion_similitud['rank_modelo_dentro_piloto'] = (
    df_validacion_similitud['prob']
    .rank(ascending=False, method='first')
    .astype(int)
)

delta_rank_relativo = (
    df_validacion_similitud['rank_modelo_dentro_piloto']
    - df_validacion_similitud['rank_piloto']
)

metricas_orden_relativo = pd.DataFrame({
    'metrica': [
        'Correlacion Spearman del orden relativo',
        'Mediana de diferencia absoluta de orden relativo',
        'Clientes con diferencia relativa <= 10 posiciones',
        'Clientes con diferencia relativa <= 25 posiciones',
        'Clientes con diferencia relativa <= 50 posiciones',
    ],
    'valor': [
        df_validacion_similitud['rank_piloto'].corr(
            df_validacion_similitud['rank_modelo_dentro_piloto'],
            method='spearman'
        ),
        delta_rank_relativo.abs().median(),
        (delta_rank_relativo.abs() <= 10).sum(),
        (delta_rank_relativo.abs() <= 25).sum(),
        (delta_rank_relativo.abs() <= 50).sum(),
    ]
})

filas_top_k_relativo = []
for k in [10, 20, 50, 100]:
    top_piloto = set(
        df_validacion_similitud.loc[
            df_validacion_similitud['rank_piloto'] <= k,
            'cod_cli_piloto'
        ]
    )
    top_modelo_relativo = set(
        df_validacion_similitud.loc[
            df_validacion_similitud['rank_modelo_dentro_piloto'] <= k,
            'cod_cli_piloto'
        ]
    )
    interseccion = len(top_piloto & top_modelo_relativo)
    filas_top_k_relativo.append({
        'K': k,
        'coincidencias': interseccion,
        'recall_top_k_relativo': interseccion / len(top_piloto)
        if top_piloto else 0.0,
    })

df_top_k_relativo = pd.DataFrame(filas_top_k_relativo)

print('METRICAS DEL ORDEN RELATIVO ENTRE LOS 184 CLIENTES')
display(metricas_orden_relativo)
print('COINCIDENCIA TOP-K DENTRO DE LOS 184 CLIENTES')
display(df_top_k_relativo)

df_validacion_similitud[
    [
        'cod_cli_piloto', 'rank_piloto', 'prob_piloto',
        'rank_modelo_dentro_piloto', 'prob', 'dif_prob'
    ]
].sort_values('rank_piloto')


# --- OUTPUT ---

# Output 1:
# METRICAS DEL ORDEN RELATIVO ENTRE LOS 184 CLIENTES

# Output 2:
#                                              metrica       valor
# 0            Correlacion Spearman del orden relativo    0.575129
# 1   Mediana de diferencia absoluta de orden relativo   31.000000
# 2  Clientes con diferencia relativa <= 10 posiciones   37.000000
# 3  Clientes con diferencia relativa <= 25 posiciones   79.000000
# 4  Clientes con diferencia relativa <= 50 posiciones  133.000000

# Output 3:
# COINCIDENCIA TOP-K DENTRO DE LOS 184 CLIENTES

# Output 4:
#      K  coincidencias  recall_top_k_relativo
# 0   10              1                   0.10
# 1   20              9                   0.45
# 2   50             31                   0.62
# 3  100             75                   0.75

# Output 5:
#     cod_cli_piloto  rank_piloto  prob_piloto  rank_modelo_dentro_piloto  \
# 120       21948529            1     0.997276                         23   
# 121       22190173            2     0.997007                         38   
# 122       22118647            3     0.996746                         13   
# 123       22109646            4     0.996661                         12   
# 124       21985478            5     0.996643                         47   
# 125       22066220            6     0.996615                         16   
# 126       22104261            7     0.996533                         10   
# 127       21931341            8     0.996446                         56   
# 128       22113091            9     0.996402                         19   
# 129       21454964           10     0.996226                         25   
# 130       21885882           11     0.996189                         36   
# 131       22041620           12     0.996142                        128   
# 132       22063468           13     0.996018                         20   
# 133       22015147           14     0.995937                         79   
# 134       22004920           15     0.995907                         55   
# 135       22039884           16     0.995789                         50   
# 136       22089643           17     0.995762                          2   
# 137       22013932           18     0.995756                         81   
# 138       21973119           19     0.995691                         15   
# 139       22164362           20     0.995681                         11   
# 140       22162461           21     0.995664                         35   
# 141       22000021           22     0.995618                         43   
# 142       22021405           23     0.995566                         78   
# 143       22109913           24     0.995507                         93   
# 144       22069441           25     0.995299                         14   
# 145       22070723           26     0.995208                          5   
# 146       21998214           27     0.995198                         89   
# 147       21975560           28     0.995165                         83   
# 148       22100843           29     0.995144                          1   
# 149       22018823           30     0.995109                         52   
# 150       21292833           31     0.995093                        178   
# 151       21985472           32     0.995013                         63   
# 152       22061098           33     0.995003                         57   
# 153       21969602           34     0.994969                         32   
# 154       22066040           35     0.994923                          8   
# 155       21788462           36     0.994765                         45   
# 156       22040445           37     0.994661                        183   
# 157       21980314           38     0.994614                         64   
# 158       22059912           39     0.994592                         24   
# 159       21940749           40     0.994572                         22   
# 160       21980449           41     0.994568                         18   
# 161       21996385           42     0.994563                         39   
# 162       22109298           43     0.994515                        150   
# 163       22014274           44     0.994490                         74   
# 164       22054536           45     0.994452                         92   
# 165       21982407           46     0.994451                         69   
# 166       21945684           47     0.994447                         40   
# 167       22067710           48     0.994408                          7   
# 168       21809989           49     0.994379                         42   
# 169       21542789           50     0.994345                         41   
# 170       22098441           51     0.994191                          4   
# 171       21723312           52     0.994151                         99   
# 172       22036611           53     0.993914                         27   
# 173       22169827           54     0.993879                         86   
# 174       21882591           55     0.993730                         77   
# 175       21973099           56     0.993686                         17   
# 176       22065925           57     0.993633                          6   
# 177       21954811           58     0.993521                         75   
# 178       22001484           59     0.993508                        141   
# 179       22071869           60     0.993479                          9   
# 180       22063317           61     0.993419                         30   
# 181       22091878           62     0.993390                         53   
# 182       22088286           63     0.993271                         87   
# 183       20053187           64     0.993225                        102   
# 0         21927707           65     0.992935                         62   
# 1         21881108           66     0.992926                         97   
# 2         21932484           67     0.992924                         96   
# 3         21936243           68     0.992869                        109   
# 4         21971477           69     0.992842                         90   
# 5         21947688           70     0.992784                         26   
# 6         22024447           71     0.992667                         49   
# 7         22011612           72     0.992573                        107   
# 8         22054719           73     0.992469                        105   
# 9         21875153           74     0.992458                         61   
# 10        22090236           75     0.992238                        179   
# 11        22063180           76     0.992206                        176   
# 12        22118157           77     0.992175                         82   
# 13        22051568           78     0.992116                        145   
# 14        22013457           79     0.992051                         73   
# 15        22087071           80     0.991783                        101   
# 16        21396713           81     0.991764                         46   
# 17        22083646           82     0.991478                        129   
# 18        22068291           83     0.991414                        155   
# 19        21945557           84     0.991323                        135   
# 20        22039891           85     0.991206                        118   
# 21        21977712           86     0.990966                         48   
# 22        21983768           87     0.990953                          3   
# 23        21972361           88     0.990942                        120   
# 24        21703889           89     0.990899                        161   
# 25        21943372           90     0.990866                         67   
# 26        22015059           91     0.990699                         91   
# 27        22106528           92     0.990649                         88   
# 28        22052223           93     0.990456                        163   
# 29        22075591           94     0.990449                        162   
# 30        22049402           95     0.990201                        116   
# 31        21905298           96     0.990190                        147   
# 32        21905327           97     0.990126                         59   
# 33        21999217           98     0.990123                        125   
# 34        21949472           99     0.989997                         70   
# 35        22072563          100     0.989995                        121   
# 36        22114799          101     0.989969                        158   
# 37        21932428          102     0.989893                        136   
# 38        21878966          103     0.989732                         28   
# 39        21906060          104     0.989491                         37   
# 40        22044922          105     0.989304                        181   
# 41        22001025          106     0.989274                        114   
# 42        19378420          107     0.989195                        130   
# 43        21906046          108     0.989183                         84   
# 44        22014979          109     0.989156                        138   
# 45        14878020          110     0.989097                        124   
# 46        19782535          111     0.989067                        177   
# 47        21938517          112     0.989022                        132   
# 48        22001399          113     0.988948                        153   
# 49        22040402          114     0.988931                        140   
# 50        21942502          115     0.988913                        110   
# 51        21540756          116     0.988911                        111   
# 52        21908418          117     0.988832                         29   
# 53        21724301          118     0.988817                        104   
# 54        21791332          119     0.988743                         94   
# 55        21692378          120     0.988714                         65   
# 56        21964445          121     0.988666                        122   
# 57        21948379          122     0.988627                         76   
# 58        20392042          123     0.988457                        146   
# 59        21866473          124     0.988367                         51   
# 60        17269518          125     0.988275                        168   
# 61        21977847          126     0.988263                        170   
# 62        21898069          127     0.988150                         54   
# 63        16754084          128     0.988096                        137   
# 64        21918315          129     0.988073                         58   
# 65        21692406          130     0.987900                         80   
# 66        21060605          131     0.987854                        126   
# 67        22019634          132     0.987842                        182   
# 68        21918062          133     0.987752                         68   
# 69        21983786          134     0.987713                         21   
# 70        21940721          135     0.987672                        154   
# 71        21480293          136     0.987508                         31   
# 72        21809596          137     0.987454                         60   
# 73        21918930          138     0.987388                         85   
# 74        22085208          139     0.987339                        157   
# 75        21976682          140     0.987227                        144   
# 76        17356462          141     0.987177                        172   
# 77        22054188          142     0.987146                         95   
# 78        22014546          143     0.987132                        142   
# 79        21816207          144     0.987061                         33   
# 80        21908270          145     0.987059                         71   
# 81        22038761          146     0.986786                        169   
# 82        21864573          147     0.986751                        123   
# 83        22022981          148     0.986611                        112   
# 84        11871738          149     0.986505                        173   
# 85        22058820          150     0.986461                        174   
# 86        21834137          151     0.986337                        117   
# 87        22100457          152     0.986146                        184   
# 88        21917811          153     0.986140                         98   
# 89        21736268          154     0.986006                        100   
# 90        22075302          155     0.985966                        160   
# 91        22097386          156     0.985958                        151   
# 92        20580041          157     0.985790                        131   
# 93        17243383          158     0.985705                        164   
# 94        22133044          159     0.985675                        152   
# 95        22020085          160     0.985621                        149   
# 96        21968274          161     0.985370                         66   
# 97        20249161          162     0.985325                        119   
# 98        19688327          163     0.985260                        143   
# 99        22088439          164     0.985206                        139   
# 100       21884121          165     0.985112                        167   
# 101       21994351          166     0.985034                         44   
# 102       21933273          167     0.984897                        108   
# 103       21998466          168     0.984872                        171   
# 104       21970800          169     0.984769                        166   
# 105       21727657          170     0.984759                         72   
# 106       22042318          171     0.984665                        180   
# 107       21724767          172     0.984515                        103   
# 108       21650523          173     0.984513                        106   
# 109       21538263          174     0.984496                        127   
# 110       17900869          175     0.984415                        133   
# 111       21778202          176     0.984304                        115   
# 112       22111510          177     0.984276                        175   
# 113       21739662          178     0.984272                         34   
# 114       21841312          179     0.984249                        148   
# 115       19503433          180     0.984230                        134   
# 116       21649033          181     0.984086                        159   
# 117       17768246          182     0.984048                        156   
# 118       21896636          183     0.984005                        113   
# 119       19886797          184     0.983969                        165   
# 
#          prob  dif_prob  
# 120  0.996114 -0.001162  
# 121  0.995481 -0.001526  
# 122  0.997100  0.000354  
# 123  0.997101  0.000440  
# 124  0.994885 -0.001757  
# 125  0.996892  0.000277  
# 126  0.997185  0.000652  
# 127  0.994504 -0.001942  
# 128  0.996662  0.000260  
# 129  0.995840 -0.000386  
# 130  0.995498 -0.000691  
# 131  0.987681 -0.008460  
# 132  0.996656  0.000638  
# 133  0.993315 -0.002623  
# 134  0.994510 -0.001398  
# 135  0.994729 -0.001060  
# 136  0.998492  0.002730  
# 137  0.993147 -0.002609  
# 138  0.996902  0.001211  
# 139  0.997175  0.001494  
# 140  0.995517 -0.000147  
# 141  0.995263 -0.000355  
# 142  0.993316 -0.002250  
# 143  0.992217 -0.003291  
# 144  0.997089  0.001790  
# 145  0.998174  0.002966  
# 146  0.992356 -0.002841  
# 147  0.993066 -0.002099  
# 148  0.998879  0.003735  
# 149  0.994598 -0.000511  
# 150  0.583673 -0.411420  
# 151  0.994129 -0.000884  
# 152  0.994494 -0.000509  
# 153  0.995637  0.000668  
# 154  0.998056  0.003134  
# 155  0.995169  0.000404  
# 156  0.252419 -0.742242  
# 157  0.994119 -0.000495  
# 158  0.995866  0.001274  
# 159  0.996253  0.001681  
# 160  0.996671  0.002103  
# 161  0.995441  0.000879  
# 162  0.979788 -0.014728  
# 163  0.993569 -0.000920  
# 164  0.992231 -0.002221  
# 165  0.993794 -0.000657  
# 166  0.995370  0.000923  
# 167  0.998083  0.003674  
# 168  0.995286  0.000907  
# 169  0.995353  0.001008  
# 170  0.998221  0.004030  
# 171  0.991232 -0.002919  
# 172  0.995759  0.001845  
# 173  0.992824 -0.001055  
# 174  0.993366 -0.000364  
# 175  0.996862  0.003176  
# 176  0.998160  0.004527  
# 177  0.993502 -0.000018  
# 178  0.984919 -0.008589  
# 179  0.997897  0.004418  
# 180  0.995656  0.002237  
# 181  0.994589  0.001199  
# 182  0.992584 -0.000686  
# 183  0.991110 -0.002114  
# 0    0.994161  0.001225  
# 1    0.991689 -0.001237  
# 2    0.991829 -0.001095  
# 3    0.990435 -0.002434  
# 4    0.992341 -0.000501  
# 5    0.995770  0.002986  
# 6    0.994734  0.002067  
# 7    0.990785 -0.001788  
# 8    0.990910 -0.001559  
# 9    0.994171  0.001713  
# 10   0.411647 -0.580591  
# 11   0.883592 -0.108614  
# 12   0.993117  0.000942  
# 13   0.983149 -0.008967  
# 14   0.993577  0.001526  
# 15   0.991136 -0.000647  
# 16   0.995057  0.003293  
# 17   0.987503 -0.003975  
# 18   0.975681 -0.015734  
# 19   0.986317 -0.005007  
# 20   0.989050 -0.002156  
# 21   0.994761  0.003795  
# 22   0.998223  0.007271  
# 23   0.988960 -0.001982  
# 24   0.969099 -0.021800  
# 25   0.993966  0.003100  
# 26   0.992265  0.001566  
# 27   0.992409  0.001760  
# 28   0.967892 -0.022565  
# 29   0.968376 -0.022073  
# 30   0.989489 -0.000712  
# 31   0.980542 -0.009648  
# 32   0.994242  0.004116  
# 33   0.988138 -0.001985  
# 34   0.993690  0.003693  
# 35   0.988778 -0.001217  
# 36   0.971068 -0.018900  
# 37   0.985931 -0.003961  
# 38   0.995742  0.006011  
# 39   0.995486  0.005995  
# 40   0.364029 -0.625275  
# 41   0.989597  0.000324  
# 42   0.987362 -0.001834  
# 43   0.993027  0.003844  
# 44   0.985448 -0.003708  
# 45   0.988509 -0.000588  
# 46   0.881525 -0.107542  
# 47   0.986623 -0.002400  
# 48   0.979090 -0.009858  
# 49   0.985066 -0.003865  
# 50   0.990274  0.001361  
# 51   0.990090  0.001178  
# 52   0.995681  0.006849  
# 53   0.991010  0.002193  
# 54   0.992197  0.003454  
# 55   0.994113  0.005399  
# 56   0.988626 -0.000041  
# 57   0.993443  0.004816  
# 58   0.982432 -0.006025  
# 59   0.994662  0.006296  
# 60   0.951179 -0.037096  
# 61   0.940706 -0.047557  
# 62   0.994529  0.006379  
# 63   0.985691 -0.002405  
# 64   0.994384  0.006311  
# 65   0.993170  0.005271  
# 66   0.988073  0.000219  
# 67   0.356221 -0.631621  
# 68   0.993815  0.006063  
# 69   0.996299  0.008586  
# 70   0.977661 -0.010011  
# 71   0.995639  0.008131  
# 72   0.994198  0.006744  
# 73   0.992918  0.005530  
# 74   0.971507 -0.015832  
# 75   0.983429 -0.003799  
# 76   0.922149 -0.065028  
# 77   0.991991  0.004845  
# 78   0.984913 -0.002219  
# 79   0.995623  0.008561  
# 80   0.993670  0.006612  
# 81   0.950980 -0.035806  
# 82   0.988512  0.001761  
# 83   0.990070  0.003459  
# 84   0.893457 -0.093048  
# 85   0.890917 -0.095544  
# 86   0.989098  0.002762  
# 87   0.239077 -0.747069  
# 88   0.991346  0.005206  
# 89   0.991169  0.005163  
# 90   0.969265 -0.016701  
# 91   0.979670 -0.006288  
# 92   0.986676  0.000886  
# 93   0.966546 -0.019158  
# 94   0.979394 -0.006281  
# 95   0.980361 -0.005260  
# 96   0.994070  0.008699  
# 97   0.989048  0.003723  
# 98   0.984591 -0.000669  
# 99   0.985231  0.000025  
# 100  0.955340 -0.029772  
# 101  0.995222  0.010187  
# 102  0.990602  0.005705  
# 103  0.923669 -0.061203  
# 104  0.958095 -0.026675  
# 105  0.993656  0.008897  
# 106  0.390422 -0.594243  
# 107  0.991081  0.006567  
# 108  0.990868  0.006355  
# 109  0.987986  0.003490  
# 110  0.986592  0.002177  
# 111  0.989586  0.005281  
# 112  0.886659 -0.097617  
# 113  0.995532  0.011260  
# 114  0.980540 -0.003710  
# 115  0.986500  0.002269  
# 116  0.970865 -0.013221  
# 117  0.974863 -0.009185  
# 118  0.989835  0.005829  
# 119  0.964552 -0.019416  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 87 ---
# execution_count: 60

# ============================================================
# Casos fuera con punto de corte
# ============================================================

PUNTO_CORTE_ACTUAL = 0.989226

# Universo del piloto cruzado contra el nuevo modelo.
fuera_piloto = df_comparacion_orden[
    df_comparacion_orden['prob'] < PUNTO_CORTE_ACTUAL
].copy()

# Universo completo de df_inf_202604.
fuera_universo = df_inf_202604[
    df_inf_202604['prob'] < PUNTO_CORTE_ACTUAL
].copy()

print(f"Punto de corte: {PUNTO_CORTE_ACTUAL:.6f}")
print(
    f"Fuera dentro del piloto: {len(fuera_piloto)} de "
    f"{len(df_comparacion_orden)} "
    f"({len(fuera_piloto) / len(df_comparacion_orden):.1%})"
)
print(
    f"Fuera en df_inf_202604 completo: {len(fuera_universo)} de "
    f"{len(df_inf_202604)} "
    f"({len(fuera_universo) / len(df_inf_202604):.1%})"
)

fuera_piloto[
    [
        'cod_cli_piloto', 'rank_piloto', 'prob_piloto',
        'prob', 'rank_modelo', 'tipo_alerta_n2'
    ]
].sort_values('prob')


# --- OUTPUT ---

# Output 1:
# Punto de corte: 0.989226
# Fuera dentro del piloto: 68 de 184 (37.0%)
# Fuera en df_inf_202604 completo: 171910 de 172505 (99.7%)

# Output 2:
#     cod_cli_piloto  rank_piloto  prob_piloto      prob  rank_modelo  \
# 87        22100457          152     0.986146  0.239077        43606   
# 156       22040445           37     0.994661  0.252419        41059   
# 67        22019634          132     0.987842  0.356221        27709   
# 40        22044922          105     0.989304  0.364029        26552   
# 106       22042318          171     0.984665  0.390422        23767   
# 10        22090236           75     0.992238  0.411647        22081   
# 150       21292833           31     0.995093  0.583673        13806   
# 46        19782535          111     0.989067  0.881525         4931   
# 11        22063180           76     0.992206  0.883592         4861   
# 112       22111510          177     0.984276  0.886659         4758   
# 85        22058820          150     0.986461  0.890917         4604   
# 84        11871738          149     0.986505  0.893457         4506   
# 76        17356462          141     0.987177  0.922149         3510   
# 103       21998466          168     0.984872  0.923669         3453   
# 61        21977847          126     0.988263  0.940706         2813   
# 81        22038761          146     0.986786  0.950980         2401   
# 60        17269518          125     0.988275  0.951179         2387   
# 100       21884121          165     0.985112  0.955340         2223   
# 104       21970800          169     0.984769  0.958095         2109   
# 119       19886797          184     0.983969  0.964552         1847   
# 93        17243383          158     0.985705  0.966546         1772   
# 28        22052223           93     0.990456  0.967892         1715   
# 29        22075591           94     0.990449  0.968376         1688   
# 24        21703889           89     0.990899  0.969099         1652   
# 90        22075302          155     0.985966  0.969265         1643   
# 116       21649033          181     0.984086  0.970865         1577   
# 36        22114799          101     0.989969  0.971068         1569   
# 74        22085208          139     0.987339  0.971507         1552   
# 117       17768246          182     0.984048  0.974863         1397   
# 18        22068291           83     0.991414  0.975681         1359   
# 70        21940721          135     0.987672  0.977661         1260   
# 48        22001399          113     0.988948  0.979090         1181   
# 94        22133044          159     0.985675  0.979394         1163   
# 91        22097386          156     0.985958  0.979670         1151   
# 162       22109298           43     0.994515  0.979788         1145   
# 95        22020085          160     0.985621  0.980361         1110   
# 114       21841312          179     0.984249  0.980540         1098   
# 31        21905298           96     0.990190  0.980542         1097   
# 58        20392042          123     0.988457  0.982432         1017   
# 13        22051568           78     0.992116  0.983149          974   
# 75        21976682          140     0.987227  0.983429          956   
# 98        19688327          163     0.985260  0.984591          886   
# 78        22014546          143     0.987132  0.984913          860   
# 178       22001484           59     0.993508  0.984919          859   
# 49        22040402          114     0.988931  0.985066          851   
# 99        22088439          164     0.985206  0.985231          843   
# 44        22014979          109     0.989156  0.985448          832   
# 63        16754084          128     0.988096  0.985691          818   
# 37        21932428          102     0.989893  0.985931          807   
# 19        21945557           84     0.991323  0.986317          780   
# 115       19503433          180     0.984230  0.986500          766   
# 110       17900869          175     0.984415  0.986592          763   
# 47        21938517          112     0.989022  0.986623          760   
# 92        20580041          157     0.985790  0.986676          757   
# 42        19378420          107     0.989195  0.987362          722   
# 17        22083646           82     0.991478  0.987503          711   
# 131       22041620           12     0.996142  0.987681          699   
# 109       21538263          174     0.984496  0.987986          683   
# 66        21060605          131     0.987854  0.988073          678   
# 33        21999217           98     0.990123  0.988138          673   
# 45        14878020          110     0.989097  0.988509          652   
# 82        21864573          147     0.986751  0.988512          651   
# 56        21964445          121     0.988666  0.988626          639   
# 35        22072563          100     0.989995  0.988778          628   
# 23        21972361           88     0.990942  0.988960          610   
# 97        20249161          162     0.985325  0.989048          607   
# 20        22039891           85     0.991206  0.989050          606   
# 86        21834137          151     0.986337  0.989098          602   
# 
#     tipo_alerta_n2  
# 87        SIN_INFO  
# 156       SIN_INFO  
# 67        SIN_INFO  
# 40        SIN_INFO  
# 106       SIN_INFO  
# 10        SIN_INFO  
# 150       SIN_INFO  
# 46        SIN_INFO  
# 11        SIN_INFO  
# 112       SIN_INFO  
# 85        SIN_INFO  
# 84        SIN_INFO  
# 76        SIN_INFO  
# 103       SIN_INFO  
# 61        SIN_INFO  
# 81        SIN_INFO  
# 60        SIN_INFO  
# 100       SIN_INFO  
# 104       SIN_INFO  
# 119       SIN_INFO  
# 93          MANUAL  
# 28        SIN_INFO  
# 29        SIN_INFO  
# 24        SIN_INFO  
# 90        SIN_INFO  
# 116       SIN_INFO  
# 36        SIN_INFO  
# 74        SIN_INFO  
# 117       SIN_INFO  
# 18        SIN_INFO  
# 70        SIN_INFO  
# 48        SIN_INFO  
# 94        SIN_INFO  
# 91        SIN_INFO  
# 162       SIN_INFO  
# 95        SIN_INFO  
# 114       SIN_INFO  
# 31        SIN_INFO  
# 58        SIN_INFO  
# 13        SIN_INFO  
# 75        SIN_INFO  
# 98        SIN_INFO  
# 78        SIN_INFO  
# 178       SIN_INFO  
# 49        SIN_INFO  
# 99        SIN_INFO  
# 44        SIN_INFO  
# 63        SIN_INFO  
# 37        SIN_INFO  
# 19        SIN_INFO  
# 115       SIN_INFO  
# 110       SIN_INFO  
# 47        SIN_INFO  
# 92        SIN_INFO  
# 42        SIN_INFO  
# 17        SIN_INFO  
# 131       SIN_INFO  
# 109       SIN_INFO  
# 66        SIN_INFO  
# 33        SIN_INFO  
# 45        SIN_INFO  
# 82        SIN_INFO  
# 56        SIN_INFO  
# 35        SIN_INFO  
# 23        SIN_INFO  
# 97        SIN_INFO  
# 20        SIN_INFO  
# 86        SIN_INFO  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 88 ---
# execution_count: 45

print(df_inf_202604['tipo_alerta_n2'].value_counts(dropna=False))


# --- OUTPUT ---

# Output 1:
# tipo_alerta_n2
# SIN_INFO           171837
# AUTOMATICA            502
# MANUAL                 94
# SEMI AUTOMATICA        72
# Name: count, dtype: Int64

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 89 ---
# execution_count: 46

# ============================================================
# Repetir la comparación de orden, pero rankeando SOLO dentro
# del subconjunto de "alertas nuevas" (mismo criterio usado en
# el resto del notebook: tipo_alerta_n2 != 'SIN_INFO'),
# que es el candidate pool real del que salió el piloto.
# ============================================================

df_candidatos = df_inf_202604[df_inf_202604['tipo_alerta_n2'] != 'SIN_INFO'].copy()
df_candidatos['rank_modelo_candidatos'] = df_candidatos['prob'].rank(ascending=False, method='min').astype(int)
n_candidatos = len(df_candidatos)
print(f"Candidatos (tipo_alerta_n2 != 'SIN_INFO'): {n_candidatos}")

def comparar_orden_candidatos(df_ext, nombre_base):
    df_ext_ = df_ext.copy()
    df_ext_['codunico'] = normalizar_id(df_ext_['codunico'])

    comp = df_candidatos.merge(
        df_ext_[['codunico', 'orden', 'score']],
        left_on='cod_cli_norm',
        right_on='codunico',
        how='inner'
    )
    return comp[['cod_cli', 'orden', 'rank_modelo_candidatos', 'prob', 'score']].rename(
        columns={'orden': 'orden_piloto', 'score': 'prob_piloto'}
    ).assign(base=nombre_base)

comp_c1 = comparar_orden_candidatos(df_ext_1, 'df_6_razones_sospechosas_20260409 1')
comp_c2 = comparar_orden_candidatos(df_ext_2, 'df_6_razones_sospechosas_20260409')
df_comparacion_candidatos = pd.concat([comp_c1, comp_c2], ignore_index=True)

n_piloto_base1, n_piloto_base2 = len(df_ext_1), len(df_ext_2)

for nombre, grupo, n_piloto_base in [
    ('df_6_razones_sospechosas_20260409 1', comp_c1, n_piloto_base1),
    ('df_6_razones_sospechosas_20260409', comp_c2, n_piloto_base2),
]:
    corr = grupo[['orden_piloto', 'rank_modelo_candidatos']].corr(method='spearman').iloc[0, 1]
    en_top = (grupo['rank_modelo_candidatos'] <= n_piloto_base).sum()
    print(f"\n{nombre}: {len(grupo)} de {n_piloto_base} coinciden con candidatos")
    print(f"  Correlación de Spearman (orden piloto vs rank modelo en candidatos) = {corr:.3f}")
    print(f"  En el propio top-{n_piloto_base} del modelo (dentro de candidatos): {en_top} ({en_top/len(grupo):.1%})")

df_comparacion_candidatos.sort_values('orden_piloto')


# --- OUTPUT ---

# Output 1:
# Candidatos (tipo_alerta_n2 != 'SIN_INFO'): 668
# 
# df_6_razones_sospechosas_20260409 1: 10 de 120 coinciden con candidatos
#   Correlación de Spearman (orden piloto vs rank modelo en candidatos) = 0.091
#   En el propio top-120 del modelo (dentro de candidatos): 9 (90.0%)
# 
# df_6_razones_sospechosas_20260409: 7 de 64 coinciden con candidatos
#   Correlación de Spearman (orden piloto vs rank modelo en candidatos) = 0.821
#   En el propio top-64 del modelo (dentro de candidatos): 6 (85.7%)

# Output 2:
#        cod_cli  orden_piloto  rank_modelo_candidatos      prob  prob_piloto  \
# 15  0021454964           450                      36  0.995840     0.996226   
# 10  0021885882           454                      41  0.995498     0.996189   
# 16  0021973119           480                      19  0.996902     0.995691   
# 13  0021788462           513                      45  0.995169     0.994765   
# 12  0021542789           536                      43  0.995353     0.994345   
# 11  0021882591           551                      75  0.993366     0.993730   
# 14  0022091878           568                      51  0.994589     0.993390   
# 5   0021881108           694                      95  0.991689     0.992926   
# 9   0021932484           695                      94  0.991829     0.992924   
# 0   0022024447           703                      50  0.994734     0.992667   
# 2   0022013457           724                      71  0.993577     0.992051   
# 3   0021905327           776                      57  0.994242     0.990126   
# 4   0021878966           786                      39  0.995742     0.989732   
# 8   0021540756           810                     119  0.990090     0.988911   
# 1   0021918930           847                      83  0.992918     0.987388   
# 6   0017243383           882                     277  0.966546     0.985705   
# 7   0021727657           901                      70  0.993656     0.984759   
# 
#                                    base  
# 15    df_6_razones_sospechosas_20260409  
# 10    df_6_razones_sospechosas_20260409  
# 16    df_6_razones_sospechosas_20260409  
# 13    df_6_razones_sospechosas_20260409  
# 12    df_6_razones_sospechosas_20260409  
# 11    df_6_razones_sospechosas_20260409  
# 14    df_6_razones_sospechosas_20260409  
# 5   df_6_razones_sospechosas_20260409 1  
# 9   df_6_razones_sospechosas_20260409 1  
# 0   df_6_razones_sospechosas_20260409 1  
# 2   df_6_razones_sospechosas_20260409 1  
# 3   df_6_razones_sospechosas_20260409 1  
# 4   df_6_razones_sospechosas_20260409 1  
# 8   df_6_razones_sospechosas_20260409 1  
# 1   df_6_razones_sospechosas_20260409 1  
# 6   df_6_razones_sospechosas_20260409 1  
# 7   df_6_razones_sospechosas_20260409 1  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 90 ---
# execution_count: 47

# ============================================================
# Cruce simple: prob (modelo actual) vs prob_piloto, cliente por cliente
# ============================================================

pd.set_option('display.max_rows', None)

df_prob_vs_prob = df_conciliado_inf[['base', 'cod_cli', 'prob', 'prob_piloto', 'diff_prob']].sort_values(
    ['base', 'prob_piloto'], ascending=[True, False]
).reset_index(drop=True)

df_prob_vs_prob


# --- OUTPUT ---

# Output 1:
#                                     base     cod_cli      prob  prob_piloto  \
# 0      df_6_razones_sospechosas_20260409  0021948529  0.996114     0.997276   
# 1      df_6_razones_sospechosas_20260409  0022190173  0.995481     0.997007   
# 2      df_6_razones_sospechosas_20260409  0022118647  0.997100     0.996746   
# 3      df_6_razones_sospechosas_20260409  0022109646  0.997101     0.996661   
# 4      df_6_razones_sospechosas_20260409  0021985478  0.994885     0.996643   
# 5      df_6_razones_sospechosas_20260409  0022066220  0.996892     0.996615   
# 6      df_6_razones_sospechosas_20260409  0022104261  0.997185     0.996533   
# 7      df_6_razones_sospechosas_20260409  0021931341  0.994504     0.996446   
# 8      df_6_razones_sospechosas_20260409  0022113091  0.996662     0.996402   
# 9      df_6_razones_sospechosas_20260409  0021454964  0.995840     0.996226   
# 10     df_6_razones_sospechosas_20260409  0021885882  0.995498     0.996189   
# 11     df_6_razones_sospechosas_20260409  0022041620  0.987681     0.996142   
# 12     df_6_razones_sospechosas_20260409  0022063468  0.996656     0.996018   
# 13     df_6_razones_sospechosas_20260409  0022015147  0.993315     0.995937   
# 14     df_6_razones_sospechosas_20260409  0022004920  0.994510     0.995907   
# 15     df_6_razones_sospechosas_20260409  0022039884  0.994729     0.995789   
# 16     df_6_razones_sospechosas_20260409  0022089643  0.998492     0.995762   
# 17     df_6_razones_sospechosas_20260409  0022013932  0.993147     0.995756   
# 18     df_6_razones_sospechosas_20260409  0021973119  0.996902     0.995691   
# 19     df_6_razones_sospechosas_20260409  0022164362  0.997175     0.995681   
# 20     df_6_razones_sospechosas_20260409  0022162461  0.995517     0.995664   
# 21     df_6_razones_sospechosas_20260409  0022000021  0.995263     0.995618   
# 22     df_6_razones_sospechosas_20260409  0022021405  0.993316     0.995566   
# 23     df_6_razones_sospechosas_20260409  0022109913  0.992217     0.995507   
# 24     df_6_razones_sospechosas_20260409  0022069441  0.997089     0.995299   
# 25     df_6_razones_sospechosas_20260409  0022070723  0.998174     0.995208   
# 26     df_6_razones_sospechosas_20260409  0021998214  0.992356     0.995198   
# 27     df_6_razones_sospechosas_20260409  0021975560  0.993066     0.995165   
# 28     df_6_razones_sospechosas_20260409  0022100843  0.998879     0.995144   
# 29     df_6_razones_sospechosas_20260409  0022018823  0.994598     0.995109   
# 30     df_6_razones_sospechosas_20260409  0021292833  0.583673     0.995093   
# 31     df_6_razones_sospechosas_20260409  0021985472  0.994129     0.995013   
# 32     df_6_razones_sospechosas_20260409  0022061098  0.994494     0.995003   
# 33     df_6_razones_sospechosas_20260409  0021969602  0.995637     0.994969   
# 34     df_6_razones_sospechosas_20260409  0022066040  0.998056     0.994923   
# 35     df_6_razones_sospechosas_20260409  0021788462  0.995169     0.994765   
# 36     df_6_razones_sospechosas_20260409  0022040445  0.252419     0.994661   
# 37     df_6_razones_sospechosas_20260409  0021980314  0.994119     0.994614   
# 38     df_6_razones_sospechosas_20260409  0022059912  0.995866     0.994592   
# 39     df_6_razones_sospechosas_20260409  0021940749  0.996253     0.994572   
# 40     df_6_razones_sospechosas_20260409  0021980449  0.996671     0.994568   
# 41     df_6_razones_sospechosas_20260409  0021996385  0.995441     0.994563   
# 42     df_6_razones_sospechosas_20260409  0022109298  0.979788     0.994515   
# 43     df_6_razones_sospechosas_20260409  0022014274  0.993569     0.994490   
# 44     df_6_razones_sospechosas_20260409  0022054536  0.992231     0.994452   
# 45     df_6_razones_sospechosas_20260409  0021982407  0.993794     0.994451   
# 46     df_6_razones_sospechosas_20260409  0021945684  0.995370     0.994447   
# 47     df_6_razones_sospechosas_20260409  0022067710  0.998083     0.994408   
# 48     df_6_razones_sospechosas_20260409  0021809989  0.995286     0.994379   
# 49     df_6_razones_sospechosas_20260409  0021542789  0.995353     0.994345   
# 50     df_6_razones_sospechosas_20260409  0022098441  0.998221     0.994191   
# 51     df_6_razones_sospechosas_20260409  0021723312  0.991232     0.994151   
# 52     df_6_razones_sospechosas_20260409  0022036611  0.995759     0.993914   
# 53     df_6_razones_sospechosas_20260409  0022169827  0.992824     0.993879   
# 54     df_6_razones_sospechosas_20260409  0021882591  0.993366     0.993730   
# 55     df_6_razones_sospechosas_20260409  0021973099  0.996862     0.993686   
# 56     df_6_razones_sospechosas_20260409  0022065925  0.998160     0.993633   
# 57     df_6_razones_sospechosas_20260409  0021954811  0.993502     0.993521   
# 58     df_6_razones_sospechosas_20260409  0022001484  0.984919     0.993508   
# 59     df_6_razones_sospechosas_20260409  0022071869  0.997897     0.993479   
# 60     df_6_razones_sospechosas_20260409  0022063317  0.995656     0.993419   
# 61     df_6_razones_sospechosas_20260409  0022091878  0.994589     0.993390   
# 62     df_6_razones_sospechosas_20260409  0022088286  0.992584     0.993271   
# 63     df_6_razones_sospechosas_20260409  0020053187  0.991110     0.993225   
# 64   df_6_razones_sospechosas_20260409 1  0021927707  0.994161     0.992935   
# 65   df_6_razones_sospechosas_20260409 1  0021881108  0.991689     0.992926   
# 66   df_6_razones_sospechosas_20260409 1  0021932484  0.991829     0.992924   
# 67   df_6_razones_sospechosas_20260409 1  0021936243  0.990435     0.992869   
# 68   df_6_razones_sospechosas_20260409 1  0021971477  0.992341     0.992842   
# 69   df_6_razones_sospechosas_20260409 1  0021947688  0.995770     0.992784   
# 70   df_6_razones_sospechosas_20260409 1  0022024447  0.994734     0.992667   
# 71   df_6_razones_sospechosas_20260409 1  0022011612  0.990785     0.992573   
# 72   df_6_razones_sospechosas_20260409 1  0022054719  0.990910     0.992469   
# 73   df_6_razones_sospechosas_20260409 1  0021875153  0.994171     0.992458   
# 74   df_6_razones_sospechosas_20260409 1  0022090236  0.411647     0.992238   
# 75   df_6_razones_sospechosas_20260409 1  0022063180  0.883592     0.992206   
# 76   df_6_razones_sospechosas_20260409 1  0022118157  0.993117     0.992175   
# 77   df_6_razones_sospechosas_20260409 1  0022051568  0.983149     0.992116   
# 78   df_6_razones_sospechosas_20260409 1  0022013457  0.993577     0.992051   
# 79   df_6_razones_sospechosas_20260409 1  0022087071  0.991136     0.991783   
# 80   df_6_razones_sospechosas_20260409 1  0021396713  0.995057     0.991764   
# 81   df_6_razones_sospechosas_20260409 1  0022083646  0.987503     0.991478   
# 82   df_6_razones_sospechosas_20260409 1  0022068291  0.975681     0.991414   
# 83   df_6_razones_sospechosas_20260409 1  0021945557  0.986317     0.991323   
# 84   df_6_razones_sospechosas_20260409 1  0022039891  0.989050     0.991206   
# 85   df_6_razones_sospechosas_20260409 1  0021977712  0.994761     0.990966   
# 86   df_6_razones_sospechosas_20260409 1  0021983768  0.998223     0.990953   
# 87   df_6_razones_sospechosas_20260409 1  0021972361  0.988960     0.990942   
# 88   df_6_razones_sospechosas_20260409 1  0021703889  0.969099     0.990899   
# 89   df_6_razones_sospechosas_20260409 1  0021943372  0.993966     0.990866   
# 90   df_6_razones_sospechosas_20260409 1  0022015059  0.992265     0.990699   
# 91   df_6_razones_sospechosas_20260409 1  0022106528  0.992409     0.990649   
# 92   df_6_razones_sospechosas_20260409 1  0022052223  0.967892     0.990456   
# 93   df_6_razones_sospechosas_20260409 1  0022075591  0.968376     0.990449   
# 94   df_6_razones_sospechosas_20260409 1  0022049402  0.989489     0.990201   
# 95   df_6_razones_sospechosas_20260409 1  0021905298  0.980542     0.990190   
# 96   df_6_razones_sospechosas_20260409 1  0021905327  0.994242     0.990126   
# 97   df_6_razones_sospechosas_20260409 1  0021999217  0.988138     0.990123   
# 98   df_6_razones_sospechosas_20260409 1  0021949472  0.993690     0.989997   
# 99   df_6_razones_sospechosas_20260409 1  0022072563  0.988778     0.989995   
# 100  df_6_razones_sospechosas_20260409 1  0022114799  0.971068     0.989969   
# 101  df_6_razones_sospechosas_20260409 1  0021932428  0.985931     0.989893   
# 102  df_6_razones_sospechosas_20260409 1  0021878966  0.995742     0.989732   
# 103  df_6_razones_sospechosas_20260409 1  0021906060  0.995486     0.989491   
# 104  df_6_razones_sospechosas_20260409 1  0022044922  0.364029     0.989304   
# 105  df_6_razones_sospechosas_20260409 1  0022001025  0.989597     0.989274   
# 106  df_6_razones_sospechosas_20260409 1  0019378420  0.987362     0.989195   
# 107  df_6_razones_sospechosas_20260409 1  0021906046  0.993027     0.989183   
# 108  df_6_razones_sospechosas_20260409 1  0022014979  0.985448     0.989156   
# 109  df_6_razones_sospechosas_20260409 1  0014878020  0.988509     0.989097   
# 110  df_6_razones_sospechosas_20260409 1  0019782535  0.881525     0.989067   
# 111  df_6_razones_sospechosas_20260409 1  0021938517  0.986623     0.989022   
# 112  df_6_razones_sospechosas_20260409 1  0022001399  0.979090     0.988948   
# 113  df_6_razones_sospechosas_20260409 1  0022040402  0.985066     0.988931   
# 114  df_6_razones_sospechosas_20260409 1  0021942502  0.990274     0.988913   
# 115  df_6_razones_sospechosas_20260409 1  0021540756  0.990090     0.988911   
# 116  df_6_razones_sospechosas_20260409 1  0021908418  0.995681     0.988832   
# 117  df_6_razones_sospechosas_20260409 1  0021724301  0.991010     0.988817   
# 118  df_6_razones_sospechosas_20260409 1  0021791332  0.992197     0.988743   
# 119  df_6_razones_sospechosas_20260409 1  0021692378  0.994113     0.988714   
# 120  df_6_razones_sospechosas_20260409 1  0021964445  0.988626     0.988666   
# 121  df_6_razones_sospechosas_20260409 1  0021948379  0.993443     0.988627   
# 122  df_6_razones_sospechosas_20260409 1  0020392042  0.982432     0.988457   
# 123  df_6_razones_sospechosas_20260409 1  0021866473  0.994662     0.988367   
# 124  df_6_razones_sospechosas_20260409 1  0017269518  0.951179     0.988275   
# 125  df_6_razones_sospechosas_20260409 1  0021977847  0.940706     0.988263   
# 126  df_6_razones_sospechosas_20260409 1  0021898069  0.994529     0.988150   
# 127  df_6_razones_sospechosas_20260409 1  0016754084  0.985691     0.988096   
# 128  df_6_razones_sospechosas_20260409 1  0021918315  0.994384     0.988073   
# 129  df_6_razones_sospechosas_20260409 1  0021692406  0.993170     0.987900   
# 130  df_6_razones_sospechosas_20260409 1  0021060605  0.988073     0.987854   
# 131  df_6_razones_sospechosas_20260409 1  0022019634  0.356221     0.987842   
# 132  df_6_razones_sospechosas_20260409 1  0021918062  0.993815     0.987752   
# 133  df_6_razones_sospechosas_20260409 1  0021983786  0.996299     0.987713   
# 134  df_6_razones_sospechosas_20260409 1  0021940721  0.977661     0.987672   
# 135  df_6_razones_sospechosas_20260409 1  0021480293  0.995639     0.987508   
# 136  df_6_razones_sospechosas_20260409 1  0021809596  0.994198     0.987454   
# 137  df_6_razones_sospechosas_20260409 1  0021918930  0.992918     0.987388   
# 138  df_6_razones_sospechosas_20260409 1  0022085208  0.971507     0.987339   
# 139  df_6_razones_sospechosas_20260409 1  0021976682  0.983429     0.987227   
# 140  df_6_razones_sospechosas_20260409 1  0017356462  0.922149     0.987177   
# 141  df_6_razones_sospechosas_20260409 1  0022054188  0.991991     0.987146   
# 142  df_6_razones_sospechosas_20260409 1  0022014546  0.984913     0.987132   
# 143  df_6_razones_sospechosas_20260409 1  0021816207  0.995623     0.987061   
# 144  df_6_razones_sospechosas_20260409 1  0021908270  0.993670     0.987059   
# 145  df_6_razones_sospechosas_20260409 1  0022038761  0.950980     0.986786   
# 146  df_6_razones_sospechosas_20260409 1  0021864573  0.988512     0.986751   
# 147  df_6_razones_sospechosas_20260409 1  0022022981  0.990070     0.986611   
# 148  df_6_razones_sospechosas_20260409 1  0011871738  0.893457     0.986505   
# 149  df_6_razones_sospechosas_20260409 1  0022058820  0.890917     0.986461   
# 150  df_6_razones_sospechosas_20260409 1  0021834137  0.989098     0.986337   
# 151  df_6_razones_sospechosas_20260409 1  0022100457  0.239077     0.986146   
# 152  df_6_razones_sospechosas_20260409 1  0021917811  0.991346     0.986140   
# 153  df_6_razones_sospechosas_20260409 1  0021736268  0.991169     0.986006   
# 154  df_6_razones_sospechosas_20260409 1  0022075302  0.969265     0.985966   
# 155  df_6_razones_sospechosas_20260409 1  0022097386  0.979670     0.985958   
# 156  df_6_razones_sospechosas_20260409 1  0020580041  0.986676     0.985790   
# 157  df_6_razones_sospechosas_20260409 1  0017243383  0.966546     0.985705   
# 158  df_6_razones_sospechosas_20260409 1  0022133044  0.979394     0.985675   
# 159  df_6_razones_sospechosas_20260409 1  0022020085  0.980361     0.985621   
# 160  df_6_razones_sospechosas_20260409 1  0021968274  0.994070     0.985370   
# 161  df_6_razones_sospechosas_20260409 1  0020249161  0.989048     0.985325   
# 162  df_6_razones_sospechosas_20260409 1  0019688327  0.984591     0.985260   
# 163  df_6_razones_sospechosas_20260409 1  0022088439  0.985231     0.985206   
# 164  df_6_razones_sospechosas_20260409 1  0021884121  0.955340     0.985112   
# 165  df_6_razones_sospechosas_20260409 1  0021994351  0.995222     0.985034   
# 166  df_6_razones_sospechosas_20260409 1  0021933273  0.990602     0.984897   
# 167  df_6_razones_sospechosas_20260409 1  0021998466  0.923669     0.984872   
# 168  df_6_razones_sospechosas_20260409 1  0021970800  0.958095     0.984769   
# 169  df_6_razones_sospechosas_20260409 1  0021727657  0.993656     0.984759   
# 170  df_6_razones_sospechosas_20260409 1  0022042318  0.390422     0.984665   
# 171  df_6_razones_sospechosas_20260409 1  0021724767  0.991081     0.984515   
# 172  df_6_razones_sospechosas_20260409 1  0021650523  0.990868     0.984513   
# 173  df_6_razones_sospechosas_20260409 1  0021538263  0.987986     0.984496   
# 174  df_6_razones_sospechosas_20260409 1  0017900869  0.986592     0.984415   
# 175  df_6_razones_sospechosas_20260409 1  0021778202  0.989586     0.984304   
# 176  df_6_razones_sospechosas_20260409 1  0022111510  0.886659     0.984276   
# 177  df_6_razones_sospechosas_20260409 1  0021739662  0.995532     0.984272   
# 178  df_6_razones_sospechosas_20260409 1  0021841312  0.980540     0.984249   
# 179  df_6_razones_sospechosas_20260409 1  0019503433  0.986500     0.984230   
# 180  df_6_razones_sospechosas_20260409 1  0021649033  0.970865     0.984086   
# 181  df_6_razones_sospechosas_20260409 1  0017768246  0.974863     0.984048   
# 182  df_6_razones_sospechosas_20260409 1  0021896636  0.989835     0.984005   
# 183  df_6_razones_sospechosas_20260409 1  0019886797  0.964552     0.983969   
# 
#      diff_prob  
# 0    -0.001162  
# 1    -0.001526  
# 2     0.000354  
# 3     0.000440  
# 4    -0.001757  
# 5     0.000277  
# 6     0.000652  
# 7    -0.001942  
# 8     0.000260  
# 9    -0.000386  
# 10   -0.000691  
# 11   -0.008460  
# 12    0.000638  
# 13   -0.002623  
# 14   -0.001398  
# 15   -0.001060  
# 16    0.002730  
# 17   -0.002609  
# 18    0.001211  
# 19    0.001494  
# 20   -0.000147  
# 21   -0.000355  
# 22   -0.002250  
# 23   -0.003291  
# 24    0.001790  
# 25    0.002966  
# 26   -0.002841  
# 27   -0.002099  
# 28    0.003735  
# 29   -0.000511  
# 30   -0.411420  
# 31   -0.000884  
# 32   -0.000509  
# 33    0.000668  
# 34    0.003134  
# 35    0.000404  
# 36   -0.742242  
# 37   -0.000495  
# 38    0.001274  
# 39    0.001681  
# 40    0.002103  
# 41    0.000879  
# 42   -0.014728  
# 43   -0.000920  
# 44   -0.002221  
# 45   -0.000657  
# 46    0.000923  
# 47    0.003674  
# 48    0.000907  
# 49    0.001008  
# 50    0.004030  
# 51   -0.002919  
# 52    0.001845  
# 53   -0.001055  
# 54   -0.000364  
# 55    0.003176  
# 56    0.004527  
# 57   -0.000018  
# 58   -0.008589  
# 59    0.004418  
# 60    0.002237  
# 61    0.001199  
# 62   -0.000686  
# 63   -0.002114  
# 64    0.001225  
# 65   -0.001237  
# 66   -0.001095  
# 67   -0.002434  
# 68   -0.000501  
# 69    0.002986  
# 70    0.002067  
# 71   -0.001788  
# 72   -0.001559  
# 73    0.001713  
# 74   -0.580591  
# 75   -0.108614  
# 76    0.000942  
# 77   -0.008967  
# 78    0.001526  
# 79   -0.000647  
# 80    0.003293  
# 81   -0.003975  
# 82   -0.015734  
# 83   -0.005007  
# 84   -0.002156  
# 85    0.003795  
# 86    0.007271  
# 87   -0.001982  
# 88   -0.021800  
# 89    0.003100  
# 90    0.001566  
# 91    0.001760  
# 92   -0.022565  
# 93   -0.022073  
# 94   -0.000712  
# 95   -0.009648  
# 96    0.004116  
# 97   -0.001985  
# 98    0.003693  
# 99   -0.001217  
# 100  -0.018900  
# 101  -0.003961  
# 102   0.006011  
# 103   0.005995  
# 104  -0.625275  
# 105   0.000324  
# 106  -0.001834  
# 107   0.003844  
# 108  -0.003708  
# 109  -0.000588  
# 110  -0.107542  
# 111  -0.002400  
# 112  -0.009858  
# 113  -0.003865  
# 114   0.001361  
# 115   0.001178  
# 116   0.006849  
# 117   0.002193  
# 118   0.003454  
# 119   0.005399  
# 120  -0.000041  
# 121   0.004816  
# 122  -0.006025  
# 123   0.006296  
# 124  -0.037096  
# 125  -0.047557  
# 126   0.006379  
# 127  -0.002405  
# 128   0.006311  
# 129   0.005271  
# 130   0.000219  
# 131  -0.631621  
# 132   0.006063  
# 133   0.008586  
# 134  -0.010011  
# 135   0.008131  
# 136   0.006744  
# 137   0.005530  
# 138  -0.015832  
# 139  -0.003799  
# 140  -0.065028  
# 141   0.004845  
# 142  -0.002219  
# 143   0.008561  
# 144   0.006612  
# 145  -0.035806  
# 146   0.001761  
# 147   0.003459  
# 148  -0.093048  
# 149  -0.095544  
# 150   0.002762  
# 151  -0.747069  
# 152   0.005206  
# 153   0.005163  
# 154  -0.016701  
# 155  -0.006288  
# 156   0.000886  
# 157  -0.019158  
# 158  -0.006281  
# 159  -0.005260  
# 160   0.008699  
# 161   0.003723  
# 162  -0.000669  
# 163   0.000025  
# 164  -0.029772  
# 165   0.010187  
# 166   0.005705  
# 167  -0.061203  
# 168  -0.026675  
# 169   0.008897  
# 170  -0.594243  
# 171   0.006567  
# 172   0.006355  
# 173   0.003490  
# 174   0.002177  
# 175   0.005281  
# 176  -0.097617  
# 177   0.011260  
# 178  -0.003710  
# 179   0.002269  
# 180  -0.013221  
# 181  -0.009185  
# 182   0.005829  
# 183  -0.019416  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 91 ---
# execution_count: 48

n_menor_96 = (df_prob_vs_prob['prob'] < 0.96).sum()
print(f"Clientes con prob (modelo actual) < 0.96: {n_menor_96} de {len(df_prob_vs_prob)}")

df_prob_vs_prob[df_prob_vs_prob['prob'] < 0.96]


# --- OUTPUT ---

# Output 1:
# Clientes con prob (modelo actual) < 0.96: 19 de 184

# Output 2:
#                                     base     cod_cli      prob  prob_piloto  \
# 30     df_6_razones_sospechosas_20260409  0021292833  0.583673     0.995093   
# 36     df_6_razones_sospechosas_20260409  0022040445  0.252419     0.994661   
# 74   df_6_razones_sospechosas_20260409 1  0022090236  0.411647     0.992238   
# 75   df_6_razones_sospechosas_20260409 1  0022063180  0.883592     0.992206   
# 104  df_6_razones_sospechosas_20260409 1  0022044922  0.364029     0.989304   
# 110  df_6_razones_sospechosas_20260409 1  0019782535  0.881525     0.989067   
# 124  df_6_razones_sospechosas_20260409 1  0017269518  0.951179     0.988275   
# 125  df_6_razones_sospechosas_20260409 1  0021977847  0.940706     0.988263   
# 131  df_6_razones_sospechosas_20260409 1  0022019634  0.356221     0.987842   
# 140  df_6_razones_sospechosas_20260409 1  0017356462  0.922149     0.987177   
# 145  df_6_razones_sospechosas_20260409 1  0022038761  0.950980     0.986786   
# 148  df_6_razones_sospechosas_20260409 1  0011871738  0.893457     0.986505   
# 149  df_6_razones_sospechosas_20260409 1  0022058820  0.890917     0.986461   
# 151  df_6_razones_sospechosas_20260409 1  0022100457  0.239077     0.986146   
# 164  df_6_razones_sospechosas_20260409 1  0021884121  0.955340     0.985112   
# 167  df_6_razones_sospechosas_20260409 1  0021998466  0.923669     0.984872   
# 168  df_6_razones_sospechosas_20260409 1  0021970800  0.958095     0.984769   
# 170  df_6_razones_sospechosas_20260409 1  0022042318  0.390422     0.984665   
# 176  df_6_razones_sospechosas_20260409 1  0022111510  0.886659     0.984276   
# 
#      diff_prob  
# 30   -0.411420  
# 36   -0.742242  
# 74   -0.580591  
# 75   -0.108614  
# 104  -0.625275  
# 110  -0.107542  
# 124  -0.037096  
# 125  -0.047557  
# 131  -0.631621  
# 140  -0.065028  
# 145  -0.035806  
# 148  -0.093048  
# 149  -0.095544  
# 151  -0.747069  
# 164  -0.029772  
# 167  -0.061203  
# 168  -0.026675  
# 170  -0.594243  
# 176  -0.097617  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 92 ---
# execution_count: 56

# ============================================================
# Tabla final: piloto original vs nuevo orden del modelo
# ============================================================

df_orden_lado_a_lado = df_comparacion_orden[
    [
        'base',
        'cod_cli_piloto',
        'cod_cli_modelo',
        'rank_piloto',
        'orden_piloto_original',
        'prob_piloto',
        'rank_modelo',
        'prob',
        'dif_prob',
        'dif_orden',
        'tipo_alerta_n2',
        'estado_cruce',
    ]
].sort_values(
    ['rank_piloto']
).reset_index(drop=True)

df_orden_lado_a_lado


# --- OUTPUT ---

# Output 1:
#                                     base cod_cli_piloto cod_cli_modelo  \
# 0      df_6_razones_sospechosas_20260416       21948529     0021948529   
# 1      df_6_razones_sospechosas_20260416       22190173     0022190173   
# 2      df_6_razones_sospechosas_20260416       22118647     0022118647   
# 3      df_6_razones_sospechosas_20260416       22109646     0022109646   
# 4      df_6_razones_sospechosas_20260416       21985478     0021985478   
# 5      df_6_razones_sospechosas_20260416       22066220     0022066220   
# 6      df_6_razones_sospechosas_20260416       22104261     0022104261   
# 7      df_6_razones_sospechosas_20260416       21931341     0021931341   
# 8      df_6_razones_sospechosas_20260416       22113091     0022113091   
# 9      df_6_razones_sospechosas_20260416       21454964           <NA>   
# 10     df_6_razones_sospechosas_20260416       21885882           <NA>   
# 11     df_6_razones_sospechosas_20260416       22041620     0022041620   
# 12     df_6_razones_sospechosas_20260416       22063468     0022063468   
# 13     df_6_razones_sospechosas_20260416       22015147     0022015147   
# 14     df_6_razones_sospechosas_20260416       22004920     0022004920   
# 15     df_6_razones_sospechosas_20260416       22039884     0022039884   
# 16     df_6_razones_sospechosas_20260416       22089643     0022089643   
# 17     df_6_razones_sospechosas_20260416       22013932     0022013932   
# 18     df_6_razones_sospechosas_20260416       21973119           <NA>   
# 19     df_6_razones_sospechosas_20260416       22164362     0022164362   
# 20     df_6_razones_sospechosas_20260416       22162461     0022162461   
# 21     df_6_razones_sospechosas_20260416       22000021     0022000021   
# 22     df_6_razones_sospechosas_20260416       22021405     0022021405   
# 23     df_6_razones_sospechosas_20260416       22109913     0022109913   
# 24     df_6_razones_sospechosas_20260416       22069441     0022069441   
# 25     df_6_razones_sospechosas_20260416       22070723     0022070723   
# 26     df_6_razones_sospechosas_20260416       21998214     0021998214   
# 27     df_6_razones_sospechosas_20260416       21975560     0021975560   
# 28     df_6_razones_sospechosas_20260416       22100843     0022100843   
# 29     df_6_razones_sospechosas_20260416       22018823     0022018823   
# 30     df_6_razones_sospechosas_20260416       21292833     0021292833   
# 31     df_6_razones_sospechosas_20260416       21985472     0021985472   
# 32     df_6_razones_sospechosas_20260416       22061098     0022061098   
# 33     df_6_razones_sospechosas_20260416       21969602     0021969602   
# 34     df_6_razones_sospechosas_20260416       22066040     0022066040   
# 35     df_6_razones_sospechosas_20260416       21788462           <NA>   
# 36     df_6_razones_sospechosas_20260416       22040445     0022040445   
# 37     df_6_razones_sospechosas_20260416       21980314     0021980314   
# 38     df_6_razones_sospechosas_20260416       22059912     0022059912   
# 39     df_6_razones_sospechosas_20260416       21940749     0021940749   
# 40     df_6_razones_sospechosas_20260416       21980449     0021980449   
# 41     df_6_razones_sospechosas_20260416       21996385     0021996385   
# 42     df_6_razones_sospechosas_20260416       22109298     0022109298   
# 43     df_6_razones_sospechosas_20260416       22014274     0022014274   
# 44     df_6_razones_sospechosas_20260416       22054536     0022054536   
# 45     df_6_razones_sospechosas_20260416       21982407     0021982407   
# 46     df_6_razones_sospechosas_20260416       21945684     0021945684   
# 47     df_6_razones_sospechosas_20260416       22067710     0022067710   
# 48     df_6_razones_sospechosas_20260416       21809989     0021809989   
# 49     df_6_razones_sospechosas_20260416       21542789           <NA>   
# 50     df_6_razones_sospechosas_20260416       22098441     0022098441   
# 51     df_6_razones_sospechosas_20260416       21723312     0021723312   
# 52     df_6_razones_sospechosas_20260416       22036611     0022036611   
# 53     df_6_razones_sospechosas_20260416       22169827     0022169827   
# 54     df_6_razones_sospechosas_20260416       21882591           <NA>   
# 55     df_6_razones_sospechosas_20260416       21973099     0021973099   
# 56     df_6_razones_sospechosas_20260416       22065925     0022065925   
# 57     df_6_razones_sospechosas_20260416       21954811     0021954811   
# 58     df_6_razones_sospechosas_20260416       22001484     0022001484   
# 59     df_6_razones_sospechosas_20260416       22071869     0022071869   
# 60     df_6_razones_sospechosas_20260416       22063317     0022063317   
# 61     df_6_razones_sospechosas_20260416       22091878           <NA>   
# 62     df_6_razones_sospechosas_20260416       22088286     0022088286   
# 63     df_6_razones_sospechosas_20260416       20053187     0020053187   
# 64   df_6_razones_sospechosas_20260409 1       21927707     0021927707   
# 65   df_6_razones_sospechosas_20260409 1       21881108           <NA>   
# 66   df_6_razones_sospechosas_20260409 1       21932484           <NA>   
# 67   df_6_razones_sospechosas_20260409 1       21936243     0021936243   
# 68   df_6_razones_sospechosas_20260409 1       21971477     0021971477   
# 69   df_6_razones_sospechosas_20260409 1       21947688     0021947688   
# 70   df_6_razones_sospechosas_20260409 1       22024447           <NA>   
# 71   df_6_razones_sospechosas_20260409 1       22011612     0022011612   
# 72   df_6_razones_sospechosas_20260409 1       22054719     0022054719   
# 73   df_6_razones_sospechosas_20260409 1       21875153     0021875153   
# 74   df_6_razones_sospechosas_20260409 1       22090236     0022090236   
# 75   df_6_razones_sospechosas_20260409 1       22063180     0022063180   
# 76   df_6_razones_sospechosas_20260409 1       22118157     0022118157   
# 77   df_6_razones_sospechosas_20260409 1       22051568     0022051568   
# 78   df_6_razones_sospechosas_20260409 1       22013457           <NA>   
# 79   df_6_razones_sospechosas_20260409 1       22087071     0022087071   
# 80   df_6_razones_sospechosas_20260409 1       21396713     0021396713   
# 81   df_6_razones_sospechosas_20260409 1       22083646     0022083646   
# 82   df_6_razones_sospechosas_20260409 1       22068291     0022068291   
# 83   df_6_razones_sospechosas_20260409 1       21945557     0021945557   
# 84   df_6_razones_sospechosas_20260409 1       22039891     0022039891   
# 85   df_6_razones_sospechosas_20260409 1       21977712     0021977712   
# 86   df_6_razones_sospechosas_20260409 1       21983768     0021983768   
# 87   df_6_razones_sospechosas_20260409 1       21972361     0021972361   
# 88   df_6_razones_sospechosas_20260409 1       21703889     0021703889   
# 89   df_6_razones_sospechosas_20260409 1       21943372     0021943372   
# 90   df_6_razones_sospechosas_20260409 1       22015059     0022015059   
# 91   df_6_razones_sospechosas_20260409 1       22106528     0022106528   
# 92   df_6_razones_sospechosas_20260409 1       22052223     0022052223   
# 93   df_6_razones_sospechosas_20260409 1       22075591     0022075591   
# 94   df_6_razones_sospechosas_20260409 1       22049402     0022049402   
# 95   df_6_razones_sospechosas_20260409 1       21905298     0021905298   
# 96   df_6_razones_sospechosas_20260409 1       21905327           <NA>   
# 97   df_6_razones_sospechosas_20260409 1       21999217     0021999217   
# 98   df_6_razones_sospechosas_20260409 1       21949472     0021949472   
# 99   df_6_razones_sospechosas_20260409 1       22072563     0022072563   
# 100  df_6_razones_sospechosas_20260409 1       22114799     0022114799   
# 101  df_6_razones_sospechosas_20260409 1       21932428     0021932428   
# 102  df_6_razones_sospechosas_20260409 1       21878966           <NA>   
# 103  df_6_razones_sospechosas_20260409 1       21906060     0021906060   
# 104  df_6_razones_sospechosas_20260409 1       22044922     0022044922   
# 105  df_6_razones_sospechosas_20260409 1       22001025     0022001025   
# 106  df_6_razones_sospechosas_20260409 1       19378420     0019378420   
# 107  df_6_razones_sospechosas_20260409 1       21906046     0021906046   
# 108  df_6_razones_sospechosas_20260409 1       22014979     0022014979   
# 109  df_6_razones_sospechosas_20260409 1       14878020     0014878020   
# 110  df_6_razones_sospechosas_20260409 1       19782535     0019782535   
# 111  df_6_razones_sospechosas_20260409 1       21938517     0021938517   
# 112  df_6_razones_sospechosas_20260409 1       22001399     0022001399   
# 113  df_6_razones_sospechosas_20260409 1       22040402     0022040402   
# 114  df_6_razones_sospechosas_20260409 1       21942502     0021942502   
# 115  df_6_razones_sospechosas_20260409 1       21540756           <NA>   
# 116  df_6_razones_sospechosas_20260409 1       21908418     0021908418   
# 117  df_6_razones_sospechosas_20260409 1       21724301     0021724301   
# 118  df_6_razones_sospechosas_20260409 1       21791332     0021791332   
# 119  df_6_razones_sospechosas_20260409 1       21692378     0021692378   
# 120  df_6_razones_sospechosas_20260409 1       21964445     0021964445   
# 121  df_6_razones_sospechosas_20260409 1       21948379     0021948379   
# 122  df_6_razones_sospechosas_20260409 1       20392042     0020392042   
# 123  df_6_razones_sospechosas_20260409 1       21866473     0021866473   
# 124  df_6_razones_sospechosas_20260409 1       17269518     0017269518   
# 125  df_6_razones_sospechosas_20260409 1       21977847     0021977847   
# 126  df_6_razones_sospechosas_20260409 1       21898069     0021898069   
# 127  df_6_razones_sospechosas_20260409 1       16754084     0016754084   
# 128  df_6_razones_sospechosas_20260409 1       21918315     0021918315   
# 129  df_6_razones_sospechosas_20260409 1       21692406     0021692406   
# 130  df_6_razones_sospechosas_20260409 1       21060605     0021060605   
# 131  df_6_razones_sospechosas_20260409 1       22019634     0022019634   
# 132  df_6_razones_sospechosas_20260409 1       21918062     0021918062   
# 133  df_6_razones_sospechosas_20260409 1       21983786     0021983786   
# 134  df_6_razones_sospechosas_20260409 1       21940721     0021940721   
# 135  df_6_razones_sospechosas_20260409 1       21480293     0021480293   
# 136  df_6_razones_sospechosas_20260409 1       21809596     0021809596   
# 137  df_6_razones_sospechosas_20260409 1       21918930           <NA>   
# 138  df_6_razones_sospechosas_20260409 1       22085208     0022085208   
# 139  df_6_razones_sospechosas_20260409 1       21976682     0021976682   
# 140  df_6_razones_sospechosas_20260409 1       17356462     0017356462   
# 141  df_6_razones_sospechosas_20260409 1       22054188     0022054188   
# 142  df_6_razones_sospechosas_20260409 1       22014546     0022014546   
# 143  df_6_razones_sospechosas_20260409 1       21816207     0021816207   
# 144  df_6_razones_sospechosas_20260409 1       21908270     0021908270   
# 145  df_6_razones_sospechosas_20260409 1       22038761     0022038761   
# 146  df_6_razones_sospechosas_20260409 1       21864573     0021864573   
# 147  df_6_razones_sospechosas_20260409 1       22022981     0022022981   
# 148  df_6_razones_sospechosas_20260409 1       11871738     0011871738   
# 149  df_6_razones_sospechosas_20260409 1       22058820     0022058820   
# 150  df_6_razones_sospechosas_20260409 1       21834137     0021834137   
# 151  df_6_razones_sospechosas_20260409 1       22100457     0022100457   
# 152  df_6_razones_sospechosas_20260409 1       21917811     0021917811   
# 153  df_6_razones_sospechosas_20260409 1       21736268     0021736268   
# 154  df_6_razones_sospechosas_20260409 1       22075302     0022075302   
# 155  df_6_razones_sospechosas_20260409 1       22097386     0022097386   
# 156  df_6_razones_sospechosas_20260409 1       20580041     0020580041   
# 157  df_6_razones_sospechosas_20260409 1       17243383           <NA>   
# 158  df_6_razones_sospechosas_20260409 1       22133044     0022133044   
# 159  df_6_razones_sospechosas_20260409 1       22020085     0022020085   
# 160  df_6_razones_sospechosas_20260409 1       21968274     0021968274   
# 161  df_6_razones_sospechosas_20260409 1       20249161     0020249161   
# 162  df_6_razones_sospechosas_20260409 1       19688327     0019688327   
# 163  df_6_razones_sospechosas_20260409 1       22088439     0022088439   
# 164  df_6_razones_sospechosas_20260409 1       21884121     0021884121   
# 165  df_6_razones_sospechosas_20260409 1       21994351     0021994351   
# 166  df_6_razones_sospechosas_20260409 1       21933273     0021933273   
# 167  df_6_razones_sospechosas_20260409 1       21998466     0021998466   
# 168  df_6_razones_sospechosas_20260409 1       21970800     0021970800   
# 169  df_6_razones_sospechosas_20260409 1       21727657           <NA>   
# 170  df_6_razones_sospechosas_20260409 1       22042318     0022042318   
# 171  df_6_razones_sospechosas_20260409 1       21724767     0021724767   
# 172  df_6_razones_sospechosas_20260409 1       21650523     0021650523   
# 173  df_6_razones_sospechosas_20260409 1       21538263     0021538263   
# 174  df_6_razones_sospechosas_20260409 1       17900869     0017900869   
# 175  df_6_razones_sospechosas_20260409 1       21778202     0021778202   
# 176  df_6_razones_sospechosas_20260409 1       22111510     0022111510   
# 177  df_6_razones_sospechosas_20260409 1       21739662     0021739662   
# 178  df_6_razones_sospechosas_20260409 1       21841312     0021841312   
# 179  df_6_razones_sospechosas_20260409 1       19503433     0019503433   
# 180  df_6_razones_sospechosas_20260409 1       21649033     0021649033   
# 181  df_6_razones_sospechosas_20260409 1       17768246     0017768246   
# 182  df_6_razones_sospechosas_20260409 1       21896636     0021896636   
# 183  df_6_razones_sospechosas_20260409 1       19886797     0019886797   
# 
#      rank_piloto  orden_piloto_original  prob_piloto  rank_modelo      prob  \
# 0              1                    398     0.997276         62.0  0.996114   
# 1              2                    418     0.997007         94.0  0.995481   
# 2              3                    429     0.996746         22.0  0.997100   
# 3              4                    434     0.996661         21.0  0.997101   
# 4              5                    436     0.996643        132.0  0.994885   
# 5              6                    437     0.996615         29.0  0.996892   
# 6              7                    439     0.996533         19.0  0.997185   
# 7              8                    441     0.996446        157.0  0.994504   
# 8              9                    445     0.996402         40.0  0.996662   
# 9             10                    450     0.996226          NaN       NaN   
# 10            11                    454     0.996189          NaN       NaN   
# 11            12                    457     0.996142        559.0  0.987681   
# 12            13                    461     0.996018         41.0  0.996656   
# 13            14                    463     0.995937        220.0  0.993315   
# 14            15                    465     0.995907        156.0  0.994510   
# 15            16                    473     0.995789        144.0  0.994729   
# 16            17                    476     0.995762          2.0  0.998492   
# 17            18                    478     0.995756        231.0  0.993147   
# 18            19                    480     0.995691          NaN       NaN   
# 19            20                    481     0.995681         20.0  0.997175   
# 20            21                    483     0.995664         89.0  0.995517   
# 21            22                    486     0.995618        113.0  0.995263   
# 22            23                    488     0.995566        219.0  0.993316   
# 23            24                    490     0.995507        284.0  0.992217   
# 24            25                    495     0.995299         24.0  0.997089   
# 25            26                    497     0.995208          7.0  0.998174   
# 26            27                    499     0.995198        274.0  0.992356   
# 27            28                    500     0.995165        238.0  0.993066   
# 28            29                    501     0.995144          1.0  0.998879   
# 29            30                    502     0.995109        152.0  0.994598   
# 30            31                    503     0.995093      13233.0  0.583673   
# 31            32                    505     0.995013        174.0  0.994129   
# 32            33                    506     0.995003        158.0  0.994494   
# 33            34                    508     0.994969         81.0  0.995637   
# 34            35                    510     0.994923         11.0  0.998056   
# 35            36                    513     0.994765          NaN       NaN   
# 36            37                    517     0.994661      40458.0  0.252419   
# 37            38                    519     0.994614        175.0  0.994119   
# 38            39                    520     0.994592         68.0  0.995866   
# 39            40                    523     0.994572         56.0  0.996253   
# 40            41                    524     0.994568         39.0  0.996671   
# 41            42                    525     0.994563         97.0  0.995441   
# 42            43                    526     0.994515        934.0  0.979788   
# 43            44                    528     0.994490        202.0  0.993569   
# 44            45                    529     0.994452        282.0  0.992231   
# 45            46                    530     0.994451        190.0  0.993794   
# 46            47                    531     0.994447        104.0  0.995370   
# 47            48                    532     0.994408         10.0  0.998083   
# 48            49                    534     0.994379        110.0  0.995286   
# 49            50                    536     0.994345          NaN       NaN   
# 50            51                    538     0.994191          6.0  0.998221   
# 51            52                    541     0.994151        339.0  0.991232   
# 52            53                    544     0.993914         75.0  0.995759   
# 53            54                    546     0.993879        251.0  0.992824   
# 54            55                    551     0.993730          NaN       NaN   
# 55            56                    556     0.993686         31.0  0.996862   
# 56            57                    558     0.993633          8.0  0.998160   
# 57            58                    563     0.993521        207.0  0.993502   
# 58            59                    564     0.993508        690.0  0.984919   
# 59            60                    565     0.993479         13.0  0.997897   
# 60            61                    566     0.993419         79.0  0.995656   
# 61            62                    568     0.993390          NaN       NaN   
# 62            63                    572     0.993271        262.0  0.992584   
# 63            64                    576     0.993225        348.0  0.991110   
# 64            65                    693     0.992935        171.0  0.994161   
# 65            66                    694     0.992926          NaN       NaN   
# 66            67                    695     0.992924          NaN       NaN   
# 67            68                    696     0.992869        396.0  0.990435   
# 68            69                    697     0.992842        276.0  0.992341   
# 69            70                    699     0.992784         74.0  0.995770   
# 70            71                    703     0.992667          NaN       NaN   
# 71            72                    706     0.992573        375.0  0.990785   
# 72            73                    708     0.992469        360.0  0.990910   
# 73            74                    709     0.992458        170.0  0.994171   
# 74            75                    714     0.992238      21490.0  0.411647   
# 75            76                    715     0.992206       4409.0  0.883592   
# 76            77                    717     0.992175        233.0  0.993117   
# 77            78                    721     0.992116        789.0  0.983149   
# 78            79                    724     0.992051          NaN       NaN   
# 79            80                    733     0.991783        346.0  0.991136   
# 80            81                    734     0.991764        121.0  0.995057   
# 81            82                    741     0.991478        569.0  0.987503   
# 82            83                    742     0.991414       1115.0  0.975681   
# 83            84                    744     0.991323        627.0  0.986317   
# 84            85                    748     0.991206        476.0  0.989050   
# 85            86                    752     0.990966        140.0  0.994761   
# 86            87                    754     0.990953          4.0  0.998223   
# 87            88                    755     0.990942        480.0  0.988960   
# 88            89                    758     0.990899       1381.0  0.969099   
# 89            90                    762     0.990866        181.0  0.993966   
# 90            91                    765     0.990699        281.0  0.992265   
# 91            92                    767     0.990649        271.0  0.992409   
# 92            93                    770     0.990456       1441.0  0.967892   
# 93            94                    771     0.990449       1416.0  0.968376   
# 94            95                    774     0.990201        456.0  0.989489   
# 95            96                    775     0.990190        894.0  0.980542   
# 96            97                    776     0.990126          NaN       NaN   
# 97            98                    778     0.990123        535.0  0.988138   
# 98            99                    779     0.989997        194.0  0.993690   
# 99           100                    780     0.989995        493.0  0.988778   
# 100          101                    782     0.989969       1308.0  0.971068   
# 101          102                    784     0.989893        648.0  0.985931   
# 102          103                    786     0.989732          NaN       NaN   
# 103          104                    790     0.989491         92.0  0.995486   
# 104          105                    795     0.989304      25959.0  0.364029   
# 105          106                    796     0.989274        448.0  0.989597   
# 106          107                    798     0.989195        579.0  0.987362   
# 107          108                    799     0.989183        241.0  0.993027   
# 108          109                    800     0.989156        669.0  0.985448   
# 109          110                    802     0.989097        515.0  0.988509   
# 110          111                    803     0.989067       4475.0  0.881525   
# 111          112                    805     0.989022        614.0  0.986623   
# 112          113                    807     0.988948        965.0  0.979090   
# 113          114                    808     0.988931        683.0  0.985066   
# 114          115                    809     0.988913        402.0  0.990274   
# 115          116                    810     0.988911          NaN       NaN   
# 116          117                    811     0.988832         77.0  0.995681   
# 117          118                    812     0.988817        356.0  0.991010   
# 118          119                    813     0.988743        286.0  0.992197   
# 119          120                    816     0.988714        176.0  0.994113   
# 120          121                    818     0.988666        503.0  0.988626   
# 121          122                    819     0.988627        215.0  0.993443   
# 122          123                    823     0.988457        823.0  0.982432   
# 123          124                    826     0.988367        149.0  0.994662   
# 124          125                    827     0.988275       2065.0  0.951179   
# 125          126                    828     0.988263       2457.0  0.940706   
# 126          127                    830     0.988150        155.0  0.994529   
# 127          128                    831     0.988096        659.0  0.985691   
# 128          129                    832     0.988073        160.0  0.994384   
# 129          130                    833     0.987900        229.0  0.993170   
# 130          131                    835     0.987854        539.0  0.988073   
# 131          132                    836     0.987842      27116.0  0.356221   
# 132          133                    838     0.987752        188.0  0.993815   
# 133          134                    840     0.987713         54.0  0.996299   
# 134          135                    842     0.987672       1032.0  0.977661   
# 135          136                    844     0.987508         80.0  0.995639   
# 136          137                    845     0.987454        168.0  0.994198   
# 137          138                    847     0.987388          NaN       NaN   
# 138          139                    848     0.987339       1291.0  0.971507   
# 139          140                    849     0.987227        774.0  0.983429   
# 140          141                    851     0.987177       3112.0  0.922149   
# 141          142                    852     0.987146        298.0  0.991991   
# 142          143                    853     0.987132        691.0  0.984913   
# 143          144                    854     0.987061         82.0  0.995623   
# 144          145                    855     0.987059        198.0  0.993670   
# 145          146                    858     0.986786       2078.0  0.950980   
# 146          147                    859     0.986751        514.0  0.988512   
# 147          148                    863     0.986611        417.0  0.990070   
# 148          149                    867     0.986505       4065.0  0.893457   
# 149          150                    868     0.986461       4160.0  0.890917   
# 150          151                    870     0.986337        473.0  0.989098   
# 151          152                    873     0.986146      43004.0  0.239077   
# 152          153                    874     0.986140        334.0  0.991346   
# 153          154                    878     0.986006        343.0  0.991169   
# 154          155                    879     0.985966       1374.0  0.969265   
# 155          156                    880     0.985958        939.0  0.979670   
# 156          157                    881     0.985790        611.0  0.986676   
# 157          158                    882     0.985705          NaN       NaN   
# 158          159                    884     0.985675        950.0  0.979394   
# 159          160                    885     0.985621        906.0  0.980361   
# 160          161                    889     0.985370        178.0  0.994070   
# 161          162                    890     0.985325        477.0  0.989048   
# 162          163                    891     0.985260        717.0  0.984591   
# 163          164                    892     0.985206        676.0  0.985231   
# 164          165                    893     0.985112       1910.0  0.955340   
# 165          166                    894     0.985034        114.0  0.995222   
# 166          167                    897     0.984897        387.0  0.990602   
# 167          168                    899     0.984872       3057.0  0.923669   
# 168          169                    900     0.984769       1802.0  0.958095   
# 169          170                    901     0.984759          NaN       NaN   
# 170          171                    902     0.984665      23176.0  0.390422   
# 171          172                    904     0.984515        351.0  0.991081   
# 172          173                    905     0.984513        364.0  0.990868   
# 173          174                    906     0.984496        544.0  0.987986   
# 174          175                    907     0.984415        617.0  0.986592   
# 175          176                    908     0.984304        449.0  0.989586   
# 176          177                    909     0.984276       4307.0  0.886659   
# 177          178                    910     0.984272         87.0  0.995532   
# 178          179                    911     0.984249        895.0  0.980540   
# 179          180                    912     0.984230        619.0  0.986500   
# 180          181                    913     0.984086       1315.0  0.970865   
# 181          182                    914     0.984048       1150.0  0.974863   
# 182          183                    915     0.984005        435.0  0.989835   
# 183          184                    916     0.983969       1560.0  0.964552   
# 
#      dif_prob  dif_orden   tipo_alerta_n2                  estado_cruce  
# 0   -0.001162       61.0         SIN_INFO     Incluido en ranking nuevo  
# 1   -0.001526       92.0         SIN_INFO     Incluido en ranking nuevo  
# 2    0.000354       19.0         SIN_INFO     Incluido en ranking nuevo  
# 3    0.000440       17.0         SIN_INFO     Incluido en ranking nuevo  
# 4   -0.001757      127.0         SIN_INFO     Incluido en ranking nuevo  
# 5    0.000277       23.0         SIN_INFO     Incluido en ranking nuevo  
# 6    0.000652       12.0         SIN_INFO     Incluido en ranking nuevo  
# 7   -0.001942      149.0         SIN_INFO     Incluido en ranking nuevo  
# 8    0.000260       31.0         SIN_INFO     Incluido en ranking nuevo  
# 9         NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 10        NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 11  -0.008460      547.0         SIN_INFO     Incluido en ranking nuevo  
# 12   0.000638       28.0         SIN_INFO     Incluido en ranking nuevo  
# 13  -0.002623      206.0         SIN_INFO     Incluido en ranking nuevo  
# 14  -0.001398      141.0         SIN_INFO     Incluido en ranking nuevo  
# 15  -0.001060      128.0         SIN_INFO     Incluido en ranking nuevo  
# 16   0.002730      -15.0         SIN_INFO     Incluido en ranking nuevo  
# 17  -0.002609      213.0         SIN_INFO     Incluido en ranking nuevo  
# 18        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 19   0.001494        0.0         SIN_INFO     Incluido en ranking nuevo  
# 20  -0.000147       68.0         SIN_INFO     Incluido en ranking nuevo  
# 21  -0.000355       91.0         SIN_INFO     Incluido en ranking nuevo  
# 22  -0.002250      196.0         SIN_INFO     Incluido en ranking nuevo  
# 23  -0.003291      260.0         SIN_INFO     Incluido en ranking nuevo  
# 24   0.001790       -1.0         SIN_INFO     Incluido en ranking nuevo  
# 25   0.002966      -19.0         SIN_INFO     Incluido en ranking nuevo  
# 26  -0.002841      247.0         SIN_INFO     Incluido en ranking nuevo  
# 27  -0.002099      210.0         SIN_INFO     Incluido en ranking nuevo  
# 28   0.003735      -28.0         SIN_INFO     Incluido en ranking nuevo  
# 29  -0.000511      122.0         SIN_INFO     Incluido en ranking nuevo  
# 30  -0.411420    13202.0         SIN_INFO     Incluido en ranking nuevo  
# 31  -0.000884      142.0         SIN_INFO     Incluido en ranking nuevo  
# 32  -0.000509      125.0         SIN_INFO     Incluido en ranking nuevo  
# 33   0.000668       47.0         SIN_INFO     Incluido en ranking nuevo  
# 34   0.003134      -24.0         SIN_INFO     Incluido en ranking nuevo  
# 35        NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 36  -0.742242    40421.0         SIN_INFO     Incluido en ranking nuevo  
# 37  -0.000495      137.0         SIN_INFO     Incluido en ranking nuevo  
# 38   0.001274       29.0         SIN_INFO     Incluido en ranking nuevo  
# 39   0.001681       16.0         SIN_INFO     Incluido en ranking nuevo  
# 40   0.002103       -2.0         SIN_INFO     Incluido en ranking nuevo  
# 41   0.000879       55.0         SIN_INFO     Incluido en ranking nuevo  
# 42  -0.014728      891.0         SIN_INFO     Incluido en ranking nuevo  
# 43  -0.000920      158.0         SIN_INFO     Incluido en ranking nuevo  
# 44  -0.002221      237.0         SIN_INFO     Incluido en ranking nuevo  
# 45  -0.000657      144.0         SIN_INFO     Incluido en ranking nuevo  
# 46   0.000923       57.0         SIN_INFO     Incluido en ranking nuevo  
# 47   0.003674      -38.0         SIN_INFO     Incluido en ranking nuevo  
# 48   0.000907       61.0         SIN_INFO     Incluido en ranking nuevo  
# 49        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 50   0.004030      -45.0         SIN_INFO     Incluido en ranking nuevo  
# 51  -0.002919      287.0         SIN_INFO     Incluido en ranking nuevo  
# 52   0.001845       22.0         SIN_INFO     Incluido en ranking nuevo  
# 53  -0.001055      197.0         SIN_INFO     Incluido en ranking nuevo  
# 54        NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 55   0.003176      -25.0         SIN_INFO     Incluido en ranking nuevo  
# 56   0.004527      -49.0         SIN_INFO     Incluido en ranking nuevo  
# 57  -0.000018      149.0         SIN_INFO     Incluido en ranking nuevo  
# 58  -0.008589      631.0         SIN_INFO     Incluido en ranking nuevo  
# 59   0.004418      -47.0         SIN_INFO     Incluido en ranking nuevo  
# 60   0.002237       18.0         SIN_INFO     Incluido en ranking nuevo  
# 61        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 62  -0.000686      199.0         SIN_INFO     Incluido en ranking nuevo  
# 63  -0.002114      284.0         SIN_INFO     Incluido en ranking nuevo  
# 64   0.001225      106.0         SIN_INFO     Incluido en ranking nuevo  
# 65        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 66        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 67  -0.002434      328.0         SIN_INFO     Incluido en ranking nuevo  
# 68  -0.000501      207.0         SIN_INFO     Incluido en ranking nuevo  
# 69   0.002986        4.0         SIN_INFO     Incluido en ranking nuevo  
# 70        NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 71  -0.001788      303.0         SIN_INFO     Incluido en ranking nuevo  
# 72  -0.001559      287.0         SIN_INFO     Incluido en ranking nuevo  
# 73   0.001713       96.0         SIN_INFO     Incluido en ranking nuevo  
# 74  -0.580591    21415.0         SIN_INFO     Incluido en ranking nuevo  
# 75  -0.108614     4333.0         SIN_INFO     Incluido en ranking nuevo  
# 76   0.000942      156.0         SIN_INFO     Incluido en ranking nuevo  
# 77  -0.008967      711.0         SIN_INFO     Incluido en ranking nuevo  
# 78        NaN        NaN           MANUAL  Excluido por alerta anterior  
# 79  -0.000647      266.0         SIN_INFO     Incluido en ranking nuevo  
# 80   0.003293       40.0         SIN_INFO     Incluido en ranking nuevo  
# 81  -0.003975      487.0         SIN_INFO     Incluido en ranking nuevo  
# 82  -0.015734     1032.0         SIN_INFO     Incluido en ranking nuevo  
# 83  -0.005007      543.0         SIN_INFO     Incluido en ranking nuevo  
# 84  -0.002156      391.0         SIN_INFO     Incluido en ranking nuevo  
# 85   0.003795       54.0         SIN_INFO     Incluido en ranking nuevo  
# 86   0.007271      -83.0         SIN_INFO     Incluido en ranking nuevo  
# 87  -0.001982      392.0         SIN_INFO     Incluido en ranking nuevo  
# 88  -0.021800     1292.0         SIN_INFO     Incluido en ranking nuevo  
# 89   0.003100       91.0         SIN_INFO     Incluido en ranking nuevo  
# 90   0.001566      190.0         SIN_INFO     Incluido en ranking nuevo  
# 91   0.001760      179.0         SIN_INFO     Incluido en ranking nuevo  
# 92  -0.022565     1348.0         SIN_INFO     Incluido en ranking nuevo  
# 93  -0.022073     1322.0         SIN_INFO     Incluido en ranking nuevo  
# 94  -0.000712      361.0         SIN_INFO     Incluido en ranking nuevo  
# 95  -0.009648      798.0         SIN_INFO     Incluido en ranking nuevo  
# 96        NaN        NaN       AUTOMATICA  Excluido por alerta anterior  
# 97  -0.001985      437.0         SIN_INFO     Incluido en ranking nuevo  
# 98   0.003693       95.0         SIN_INFO     Incluido en ranking nuevo  
# 99  -0.001217      393.0         SIN_INFO     Incluido en ranking nuevo  
# 100 -0.018900     1207.0         SIN_INFO     Incluido en ranking nuevo  
# 101 -0.003961      546.0         SIN_INFO     Incluido en ranking nuevo  
# 102       NaN        NaN  SEMI AUTOMATICA  Excluido por alerta anterior  
# 103  0.005995      -12.0         SIN_INFO     Incluido en ranking nuevo  
# 104 -0.625275    25854.0         SIN_INFO     Incluido en ranking nuevo  
# 105  0.000324      342.0         SIN_INFO     Incluido en ranking nuevo  
# 106 -0.001834      472.0         SIN_INFO     Incluido en ranking nuevo  
# 107  0.003844      133.0         SIN_INFO     Incluido en ranking nuevo  
# 108 -0.003708      560.0         SIN_INFO     Incluido en ranking nuevo  
# 109 -0.000588      405.0         SIN_INFO     Incluido en ranking nuevo  
# 110 -0.107542     4364.0         SIN_INFO     Incluido en ranking nuevo  
# 111 -0.002400      502.0         SIN_INFO     Incluido en ranking nuevo  
# 112 -0.009858      852.0         SIN_INFO     Incluido en ranking nuevo  
# 113 -0.003865      569.0         SIN_INFO     Incluido en ranking nuevo  
# 114  0.001361      287.0         SIN_INFO     Incluido en ranking nuevo  
# 115       NaN        NaN           MANUAL  Excluido por alerta anterior  
# 116  0.006849      -40.0         SIN_INFO     Incluido en ranking nuevo  
# 117  0.002193      238.0         SIN_INFO     Incluido en ranking nuevo  
# 118  0.003454      167.0         SIN_INFO     Incluido en ranking nuevo  
# 119  0.005399       56.0         SIN_INFO     Incluido en ranking nuevo  
# 120 -0.000041      382.0         SIN_INFO     Incluido en ranking nuevo  
# 121  0.004816       93.0         SIN_INFO     Incluido en ranking nuevo  
# 122 -0.006025      700.0         SIN_INFO     Incluido en ranking nuevo  
# 123  0.006296       25.0         SIN_INFO     Incluido en ranking nuevo  
# 124 -0.037096     1940.0         SIN_INFO     Incluido en ranking nuevo  
# 125 -0.047557     2331.0         SIN_INFO     Incluido en ranking nuevo  
# 126  0.006379       28.0         SIN_INFO     Incluido en ranking nuevo  
# 127 -0.002405      531.0         SIN_INFO     Incluido en ranking nuevo  
# 128  0.006311       31.0         SIN_INFO     Incluido en ranking nuevo  
# 129  0.005271       99.0         SIN_INFO     Incluido en ranking nuevo  
# 130  0.000219      408.0         SIN_INFO     Incluido en ranking nuevo  
# 131 -0.631621    26984.0         SIN_INFO     Incluido en ranking nuevo  
# 132  0.006063       55.0         SIN_INFO     Incluido en ranking nuevo  
# 133  0.008586      -80.0         SIN_INFO     Incluido en ranking nuevo  
# 134 -0.010011      897.0         SIN_INFO     Incluido en ranking nuevo  
# 135  0.008131      -56.0         SIN_INFO     Incluido en ranking nuevo  
# 136  0.006744       31.0         SIN_INFO     Incluido en ranking nuevo  
# 137       NaN        NaN           MANUAL  Excluido por alerta anterior  
# 138 -0.015832     1152.0         SIN_INFO     Incluido en ranking nuevo  
# 139 -0.003799      634.0         SIN_INFO     Incluido en ranking nuevo  
# 140 -0.065028     2971.0         SIN_INFO     Incluido en ranking nuevo  
# 141  0.004845      156.0         SIN_INFO     Incluido en ranking nuevo  
# 142 -0.002219      548.0         SIN_INFO     Incluido en ranking nuevo  
# 143  0.008561      -62.0         SIN_INFO     Incluido en ranking nuevo  
# 144  0.006612       53.0         SIN_INFO     Incluido en ranking nuevo  
# 145 -0.035806     1932.0         SIN_INFO     Incluido en ranking nuevo  
# 146  0.001761      367.0         SIN_INFO     Incluido en ranking nuevo  
# 147  0.003459      269.0         SIN_INFO     Incluido en ranking nuevo  
# 148 -0.093048     3916.0         SIN_INFO     Incluido en ranking nuevo  
# 149 -0.095544     4010.0         SIN_INFO     Incluido en ranking nuevo  
# 150  0.002762      322.0         SIN_INFO     Incluido en ranking nuevo  
# 151 -0.747069    42852.0         SIN_INFO     Incluido en ranking nuevo  
# 152  0.005206      181.0         SIN_INFO     Incluido en ranking nuevo  
# 153  0.005163      189.0         SIN_INFO     Incluido en ranking nuevo  
# 154 -0.016701     1219.0         SIN_INFO     Incluido en ranking nuevo  
# 155 -0.006288      783.0         SIN_INFO     Incluido en ranking nuevo  
# 156  0.000886      454.0         SIN_INFO     Incluido en ranking nuevo  
# 157       NaN        NaN           MANUAL  Excluido por alerta anterior  
# 158 -0.006281      791.0         SIN_INFO     Incluido en ranking nuevo  
# 159 -0.005260      746.0         SIN_INFO     Incluido en ranking nuevo  
# 160  0.008699       17.0         SIN_INFO     Incluido en ranking nuevo  
# 161  0.003723      315.0         SIN_INFO     Incluido en ranking nuevo  
# 162 -0.000669      554.0         SIN_INFO     Incluido en ranking nuevo  
# 163  0.000025      512.0         SIN_INFO     Incluido en ranking nuevo  
# 164 -0.029772     1745.0         SIN_INFO     Incluido en ranking nuevo  
# 165  0.010187      -52.0         SIN_INFO     Incluido en ranking nuevo  
# 166  0.005705      220.0         SIN_INFO     Incluido en ranking nuevo  
# 167 -0.061203     2889.0         SIN_INFO     Incluido en ranking nuevo  
# 168 -0.026675     1633.0         SIN_INFO     Incluido en ranking nuevo  
# 169       NaN        NaN           MANUAL  Excluido por alerta anterior  
# 170 -0.594243    23005.0         SIN_INFO     Incluido en ranking nuevo  
# 171  0.006567      179.0         SIN_INFO     Incluido en ranking nuevo  
# 172  0.006355      191.0         SIN_INFO     Incluido en ranking nuevo  
# 173  0.003490      370.0         SIN_INFO     Incluido en ranking nuevo  
# 174  0.002177      442.0         SIN_INFO     Incluido en ranking nuevo  
# 175  0.005281      273.0         SIN_INFO     Incluido en ranking nuevo  
# 176 -0.097617     4130.0         SIN_INFO     Incluido en ranking nuevo  
# 177  0.011260      -91.0         SIN_INFO     Incluido en ranking nuevo  
# 178 -0.003710      716.0         SIN_INFO     Incluido en ranking nuevo  
# 179  0.002269      439.0         SIN_INFO     Incluido en ranking nuevo  
# 180 -0.013221     1134.0         SIN_INFO     Incluido en ranking nuevo  
# 181 -0.009185      968.0         SIN_INFO     Incluido en ranking nuevo  
# 182  0.005829      252.0         SIN_INFO     Incluido en ranking nuevo  
# 183 -0.019416     1376.0         SIN_INFO     Incluido en ranking nuevo  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 93 ---
# execution_count: 50

df_ext_1.head()


# --- OUTPUT ---

# Output 1:
#    codmes  num_documento  codunico              modelo  fec_replica  \
# 0  202604            NaN  21927707  plaft_pj_minorista     20260409   
# 1  202604            NaN  21881108  plaft_pj_minorista     20260409   
# 2  202604            NaN  21932484  plaft_pj_minorista     20260409   
# 3  202604            NaN  21936243  plaft_pj_minorista     20260409   
# 4  202604            NaN  21971477  plaft_pj_minorista     20260409   
# 
#   grupo_alerta  grupo_corte_nueva_alerta     score  orden variable1  \
# 0           P1                         0  0.992935    693  SIN_INFO   
# 1           P1                         0  0.992926    694  SIN_INFO   
# 2           P1                         0  0.992924    695  SIN_INFO   
# 3           P1                         0  0.992869    696  SIN_INFO   
# 4           P1                         0  0.992842    697  SIN_INFO   
# 
#    variable2  variable3                                   razon_sospechosa  
# 0        NaN        NaN  Cargos en efectivo muy elevados (S/1,059,300) ...  
# 1        NaN        NaN  Cargos en efectivo muy elevados (S/2,121,674) ...  
# 2        NaN        NaN  Cargos en efectivo muy elevados (S/765,475) co...  
# 3        NaN        NaN  Casi el 100% de abonos son en efectivo (ratio ...  
# 4        NaN        NaN  Cargos en efectivo muy elevados (S/1,244,722) ...  

# --- FIN OUTPUT ---


# %%
# --- CELDA DE CÓDIGO 94 ---
# execution_count: None


