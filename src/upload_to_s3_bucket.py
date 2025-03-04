from src.connection import connect_to_db, close_db_connection
from pg8000.native import literal, identifier
from boto3 import client
from botocore.exceptions import ClientError
from utils.utils_for_ingestion import reformat_data_to_json, list_of_tables
from datetime import datetime 
import json 


def write_to_s3_bucket(s3_client, bucket_name, list_of_tables, reformat_data_to_json):
    count =0
    list_of_tables = list_of_tables()
    try:

        if s3_client.list_objects_v2(Bucket=bucket_name)['KeyCount'] ==0:
            db = connect_to_db()
            for table in list_of_tables: 
                count+=1
                
                operational_data = db.run(f" SELECT * FROM {identifier(table)};")
                columns = [col["name"] for col in db.columns]
                json_formatted_data_to_upload = reformat_data_to_json(operational_data,columns)
                data_to_upload = [json_formatted_data_to_upload[0]]
                for i in range(1,len(json_formatted_data_to_upload)):
                    if i==len(json_formatted_data_to_upload)-1:
                        data_to_upload.append(json_formatted_data_to_upload[i])
                        date_updated = datetime.strptime(json_formatted_data_to_upload[i]["last_updated"], '%Y-%m-%dT%H:%M:%S.%f')
                        year=date_updated.year
                        month=date_updated.month
                        day=date_updated.day
                        time=date_updated.time()
                        object_key = f"{table}/{year}/{month}/{day}/{time}.json"
                        s3_client.put_object(Bucket=bucket_name,Key=object_key,Body=json.dumps(data_to_upload))
                        s3_client.put_object(Bucket=bucket_name,Key=f'{table}/last_updated.txt',Body=object_key)
 
                    elif json_formatted_data_to_upload[i]["last_updated"]==json_formatted_data_to_upload[i-1]["last_updated"]:
                        data_to_upload.append(json_formatted_data_to_upload[i])
                    elif json_formatted_data_to_upload[i]["last_updated"]!=json_formatted_data_to_upload[i-1]["last_updated"]:
                        date_updated = datetime.strptime(json_formatted_data_to_upload[i-1]["last_updated"], '%Y-%m-%dT%H:%M:%S.%f')
                        year=date_updated.year
                        month=date_updated.month
                        day=date_updated.day
                        time=date_updated.time()
                        object_key = f"{table}/{year}/{month}/{day}/{time}.json"
                        s3_client.put_object(Bucket=bucket_name,Key=object_key,Body=json.dumps(data_to_upload))
                        data_to_upload = [json_formatted_data_to_upload[i]]
            close_db_connection(db)
                   
            return f"success - {count} database tables have been written to {bucket_name}!"
        
    except ClientError:
        return {'result': 'FAILURE' ,"message":"file could not be uploaded"}
    

