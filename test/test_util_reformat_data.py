from utils.utils_for_ingestion import reformat_data_to_json, list_of_tables, get_file_contents_of_last_uploaded
from src.connection import connect_to_db, close_db_connection
import boto3
from pg8000.native import literal, identifier
from pg8000.exceptions import DatabaseError
import datetime
import pytest
from moto import mock_aws
import os
import json


@pytest.fixture()
def db():
    db = connect_to_db()
    yield db
    close_db_connection(db)

@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


class TestReformatData:
    def test_returns_list_of_dicts(self, db):
        test_data = db.run("SELECT * FROM address;")
        columns = [col["name"] for col in db.columns]
        result = reformat_data_to_json(test_data,columns)
        assert isinstance(result, list)
        for row_of_data in result:
            assert isinstance(row_of_data, dict)

    def test_returns_all_data_from_give_table(self, db):
        test_data = db.run("SELECT * FROM address;")
        columns = [col["name"] for col in db.columns]
        result = reformat_data_to_json(test_data,columns)
        assert len(result) == 30

    def test_all_dicts_contain_all_keys(self, db):
        for table in list_of_tables():
            test_data = db.run(f"SELECT * FROM {identifier(table)};")
            columns = [col["name"] for col in db.columns]
            result = reformat_data_to_json(test_data,columns)
            for dict in result:
                assert all([column in dict for column in columns])


    def test_data_sorted_by_date_last_updated(self, db):
        test_data = db.run(f"SELECT * FROM sales_order;")
        columns = [col["name"] for col in db.columns]
        result = reformat_data_to_json(test_data,columns)
        
        for i  in range(1,len(result)):
            assert result[i]["last_updated"] >= result[i-1]["last_updated"]

    def test_format_of_table(self, db):
        test_data = db.run(f"SELECT * FROM design;")
        columns = [col["name"] for col in db.columns]
        format_data = reformat_data_to_json(test_data,columns)
        for design in format_data:
            assert isinstance(design['design_id'], int)
            assert isinstance(design['created_at'], str)
            assert isinstance(design['design_name'], str)
            assert isinstance(design['file_location'], str)
            assert isinstance(design['file_name'], str)
            assert isinstance(design['last_updated'], str)

class TestTables:
    def test_all_tables_are_listed(self, db):
        tables_from_db = db.run("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        expected= [table for tables in tables_from_db for table in tables]
        result = list_of_tables()
        assert result.sort() == expected.sort()

class TestGetFileLastUploaded:
    def test_retrives_last_updated_file_name(self):
        with mock_aws():
            bucket_name = 'test_bucket'
            object_key = "address/last_updated.txt"
            json_object_key = "address/2024/11/03/14:20:52.187000"
            json_file = '[{"address_id": 2,"address_line_1": "6827 Herzog Via", "last_updated": "2024-11-03T14:20:52.187000"}]'
            file = "address/2024/11/03/14:20:52.187000"

            s3_client =boto3.client('s3')
            s3_client.create_bucket(
            Bucket="test_bucket",
            CreateBucketConfiguration={'LocationConstraint':'eu-west-2'}
            )
            s3_client.put_object(Bucket=bucket_name,Key=object_key,Body=file)
            s3_client.put_object(Bucket=bucket_name,Key=json_object_key,Body=json_file)
            result = get_file_contents_of_last_uploaded(s3_client, bucket_name, "address")
            assert result == json.loads(json_file)
        
