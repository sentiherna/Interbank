"""
Local storage adapter for Lexia RAG pipeline.
Replaces S3 operations with local filesystem operations.

Usage:
    export STORAGE_MODE=local
"""

import os
import json
from pathlib import Path


BASE_PATH = '/media/santi/local_data/lexia'
BUCKET_MAPPING = {
    'ibk-discovery-comercial-us-east-1-654654352211-data': 'discovery'
}


class LocalS3Client:
    """Mock S3 client for local filesystem operations."""

    def __init__(self, base_path=BASE_PATH):
        self.base_path = base_path

    def _get_local_path(self, bucket, key):
        """Convert S3 bucket/key to local path."""
        # Key already contains full path like 'discovery/comercial/...'
        # So we just use it directly
        return os.path.join(self.base_path, key)

    def put_object(self, Bucket, Key, Body):
        """Upload object to local filesystem."""
        local_path = self._get_local_path(Bucket, Key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if isinstance(Body, bytes):
            with open(local_path, 'wb') as f:
                f.write(Body)
        else:
            with open(local_path, 'w') as f:
                f.write(Body)

        print(f"[INFO] Uploaded to local: {local_path}")
        return {'ETag': 'local'}

    def get_object(self, Bucket, Key):
        """Download object from local filesystem."""
        local_path = self._get_local_path(Bucket, Key)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        with open(local_path, 'rb') as f:
            body = f.read()

        return {'Body': type('obj', (object,), {'read': lambda self: body})()}

    def head_object(self, Bucket, Key):
        """Check if object exists."""
        local_path = self._get_local_path(Bucket, Key)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        return {'ContentLength': os.path.getsize(local_path)}

    def list_objects_v2(self, Bucket, Prefix, **kwargs):
        """List objects with prefix."""
        local_prefix = self._get_local_path(Bucket, Prefix)

        contents = []
        if os.path.exists(local_prefix):
            for root, dirs, files in os.walk(local_prefix):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, os.path.dirname(local_prefix))
                    contents.append({
                        'Key': os.path.join(Prefix, rel_path).replace('\\', '/'),
                        'Size': os.path.getsize(file_path)
                    })

        return {'Contents': contents}

    def get_paginator(self, operation):
        """Return paginator for list_objects_v2."""
        class LocalPaginator:
            def __init__(self, client):
                self.client = client

            def paginate(self, **kwargs):
                result = self.client.list_objects_v2(**kwargs)
                yield result

        return LocalPaginator(self)

    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn=3600):
        """Generate local file URL (doesn't actually pre-sign, just returns file path)."""
        bucket = Params.get('Bucket')
        key = Params.get('Key')
        local_path = self._get_local_path(bucket, key)
        return f"file://{local_path}"


def get_s3_client():
    """Get appropriate S3 client based on STORAGE_MODE."""
    if os.environ.get('STORAGE_MODE', '').lower() == 'local':
        print("[INFO] Using LOCAL storage mode")
        return LocalS3Client()
    else:
        print("[INFO] Using AWS S3 storage mode")
        import boto3
        return boto3.client('s3')


def is_local_mode():
    """Check if STORAGE_MODE environment variable is set to 'local'."""
    return os.environ.get('STORAGE_MODE', '').lower() == 'local'
