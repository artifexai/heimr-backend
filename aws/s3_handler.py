import json
import os
from functools import partial
from multiprocessing.pool import ThreadPool
from typing import Optional, Dict, List

import arrow
import boto3
from mypy_boto3_s3 import Client
from mypy_boto3_s3.service_resource import Bucket
from mypy_boto3_s3.service_resource import S3ServiceResource, ObjectSummary

from utils.types import DateType
from utils.types import ListDict


class S3:
    session: boto3.Session
    s3: S3ServiceResource
    client: Client
    bucket: Optional[Bucket]
    sub_directory: Optional[str]

    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=os.getenv('S3_ACCESS_ID'),
            aws_secret_access_key=os.getenv('S3_SECRET_KEY')
        )
        self.s3 = self.session.resource('s3')
        self.client = self.s3.meta.client

    def set_bucket(self, bucket_name: str, sub_directory: Optional[str] = None):
        self.bucket = self.s3.Bucket(bucket_name)
        self.sub_directory = sub_directory

    def objects_in_bucket(self):
        if not self.bucket:
            raise Exception('No S3 bucket has been set. Use set_bucket() to set one.')

        _objects: List[ObjectSummary] = []

        if self.sub_directory:
            _objects = list(self.bucket.objects.filter(Prefix=self.sub_directory))
        else:
            _objects = list(self.bucket.objects.all())

        _objects = [o for o in _objects if o.key.endswith('.json')]

        return _objects

    def list_files_in_bucket(self, extension: str = '.json') -> List[str]:
        paginator = self.client.get_paginator('list_objects_v2')
        bucket = self.bucket.name
        page_iterator = paginator.paginate(Bucket=bucket) if not self.sub_directory \
            else paginator.paginate(Bucket=bucket, Prefix=self.sub_directory)
        return list(page_iterator.search(
            f"Contents[? ends_with(Key, `{extension}`)].Key"
        ))

    def load_files_after_date(self,
                              date: Optional[DateType],
                              limit: Optional[int],
                              offset: Optional[int] = None,
                              log_frequency: Optional[int] = 100,
                              parallel: Optional[bool] = False
                              ):

        files: List[str] = self.list_files_in_bucket()

        # Sort files by date, they are partitioned by year/month/day so can be sorted directly
        paths: List[str] = sorted(files)

        if date:
            # If a date is set, filter files by iso timestamp
            iso = arrow.get(date).to('UTC').isoformat()
            paths = [f for f in paths if f.split('/')[-2] > iso]

        if offset:
            paths = paths[offset:]

        if limit:
            paths = paths[:limit]

        data = []
        start = arrow.now()
        print(f'\nLoading {len(paths)} files in parallel at {start}\n')

        if parallel and len(paths) > 2000:
            chunk_size = 1000
            chunks = [paths[i:i + chunk_size] for i in range(0, len(paths), chunk_size)]
            with ThreadPool(10) as pool:
                res = pool.map(
                    partial(load_off_thread, bucket=self.bucket.name),
                    chunks)
                for r in res:
                    data.extend(r)
            return data

        for path in paths:
            obj = self.client.get_object(Bucket=self.bucket.name, Key=path)
            data.append(json.loads(obj['Body'].read().decode('utf-8')))
            # print percent complete
            if len(data) % log_frequency == 0:
                duration = arrow.now() - start
                avg_duration = duration / len(data)
                estimated_duration = avg_duration * (len(paths) - len(data))
                print(
                    f'{round(len(data) / len(paths) * 100, 2)}% complete. Estimated time remaining: {estimated_duration}')

        return data

    @staticmethod
    def read_object_json(obj: ObjectSummary) -> Dict:
        print('Reading', obj.key)
        return json.loads(obj.get()['Body'].read().decode('utf-8'))

    @staticmethod
    def read_many_objects_json(objs: List[ObjectSummary]) -> ListDict:
        return [S3.read_object_json(o) for o in objs]


def load_off_thread(_paths: List[str], bucket: str):
    _s3 = S3()
    _s3.set_bucket(bucket)
    data = []
    print(f'Loading {len(_paths)}')
    for path in _paths:
        obj = _s3.client.get_object(Bucket=_s3.bucket.name, Key=path)
        data.append(json.loads(obj['Body'].read().decode('utf-8')))
    return data


if __name__ == '__main__':
    s3 = S3()
    s3.set_bucket('artifex-property-data-sandbox')
    objs = s3.objects_in_bucket()
    print(S3.read_many_objects_json(objs))
