from src.update_data_to_s3_bucket import update_data_to_s3_bucket
import pytest
import os
import boto3
from moto import mock_aws
from unittest.mock import patch, Mock
from pprint import pprint
import json
import uuid
from datetime import datetime
@pytest.fixture(scope="module", autouse=True)
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
@pytest.fixture(scope="function")
def s3_client(aws_credentials):
    with mock_aws():
        yield boto3.client("s3", region_name="eu-west-2")
@pytest.fixture
def bucket(s3_client):
    bucket_name = f"test-bucket-{uuid.uuid4()}"
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
    )
    object_key1 = "address/seed.json"
    object_key2 = "address/2025-02-27 12:13:32.json"
    file1 = '[{"address_id": 1,"address_line_1": "6826 Herzog Via", "last_updated": "2025-02-27 9:13:32"}]'
    file2 = '[{"address_id": 2,"address_line_1": "6827 Herzog Via", "last_updated": "2025-02-27 10:13:32"}]'
    s3_client.put_object(Bucket=bucket_name,Key=object_key1,Body=file1)
    s3_client.put_object(Bucket=bucket_name,Key=object_key2,Body=file2)
    return bucket_name
test_list = [
        {'address_id': 1,'address_line_1': '6826 Herzog Via', 'last_updated': '2025-02-27 9:13:32' },
        {'address_id': 2,'address_line_1': '6827 Herzog Via', 'last_updated': '2025-02-27 10:13:32' },
        {'address_id': 3,'address_line_1': '6828 Herzog Via', 'last_updated': '2025-02-27 12:13:32' }
    ]
def test_func(test_list):
    return sorted(test_list, key=lambda d: d["address_id"])

class TestUploadsDataWithTimeStamp:
    @pytest.mark.it("unit test: retreieves list of files from S3 bucket")
    def test_retreives_list_of_files(self, s3_client, bucket):
        bucket_name = 'test_bucket'
        mock_reformat_data_to_json = Mock()
        mock_reformat_data_to_json.return_value = test_list
        update_data_to_s3_bucket(s3_client, bucket_name, test_list, mock_reformat_data_to_json)
        data_on_files_from_s3 = s3_client.list_objects_v2(Bucket= bucket)
        assert data_on_files_from_s3['KeyCount'] ==3
    # @pytest.mark.it("unit test: checks the data retreieved from s3 bucket")
    # def test_data_retreived_from_s3(s3, bucket, s3_client):
    #     data_on_files_from_s3 = s3_client.list_objects_v2(Bucket=bucket, Prefix="address")
    #     data_from_s3_bucket = []
    #     for i in range(len(data_on_files_from_s3['Contents'])):
    #         added_file = data_on_files_from_s3["Contents"][i]["Key"]
    #         file_data = s3_client.get_object(Bucket=bucket, Key=added_file)
    #         data = file_data['Body'].read().decode('utf-8')
    #         file_content = json.loads(data)
    #         for dict in file_content:
    #             data_from_s3_bucket.append(dict)
    #     assert sorted(data_from_s3_bucket, key=lambda d: d["address_id"]) == \
    #         sorted(test_func(test_list), key=lambda d: d["address_id"])
    # @pytest.mark.it("unti test: checks most recent datestamp")
    # def test_datestamp_on_latest_file():
    #     data_on_files_from_s3 = s3_client.list_objects_v2(Bucket=bucket, Prefix="address")
    #     objs = data_on_files_from_s3['Contents']
    #     get_last_modified = get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s'))
    #     added_file = [obj['Key'] for obj in sorted(objs, key=get_last_modified, reverse=True)][1]
    #     current_timestamp = datetime.now()
    #     formatted_timestamp = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    #     assert added_file == f"address/{formatted_timestamp}.json"