from boto3 import client
from src.connection import connect_to_db, close_db_connection
from pg8000.native import literal, identifier
from utils.utils_for_ingestion import reformat_data_to_json, list_of_tables,\
    get_file_contents_of_last_uploaded
from datetime import datetime
import decimal
import json

def update_data_to_s3_bucket(s3_client, bucket_name, list_of_tables, reformat_data_to_json, 
                             get_file_contents_of_last_uploaded):
    db = connect_to_db()
    list_of_table_data_uploaded = []
    for table in list_of_tables():
        last_data_uploaded = get_file_contents_of_last_uploaded(s3_client, bucket_name,table)
        last_updated_date =datetime.strptime('1900-11-03T14:20:52.186000', '%Y-%m-%dT%H:%M:%S.%f') 
        for row in last_data_uploaded:
            data_from_s3 = datetime.strptime(row["last_updated"], '%Y-%m-%dT%H:%M:%S.%f')
            if data_from_s3 > last_updated_date:
                last_updated_date = data_from_s3
        db_run_column = db.run(f""" SELECT * FROM {identifier(table)} 
                               WHERE last_updated > {literal(last_updated_date)};""")
        columns = [col["name"] for col in db.columns]
        additional_data_from_op_db = reformat_data_to_json(db_run_column,columns)

        if additional_data_from_op_db:
            data_to_upload = [additional_data_from_op_db[0]]
            if len(additional_data_from_op_db) == 1:
                date_updated = datetime.strptime(additional_data_from_op_db[0]
                                                 ["last_updated"], '%Y-%m-%dT%H:%M:%S.%f')
                year=date_updated.year
                month=date_updated.month
                day=date_updated.day
                time=date_updated.time()
                object_key = f"{table}/{year}/{month}/{day}/{time}.json"
                s3_client.put_object(Bucket=bucket_name,Key=object_key,
                                            Body=json.dumps(data_to_upload))
                s3_client.put_object(Bucket=bucket_name,Key=f'{table}/last_updated.txt',
                                            Body=object_key)
            for i in range(1,len(additional_data_from_op_db)):
                    if i==len(additional_data_from_op_db)-1:
                        data_to_upload.append(additional_data_from_op_db[i])
                        date_updated = datetime.strptime(additional_data_from_op_db[i]
                                                         ["last_updated"], '%Y-%m-%dT%H:%M:%S.%f')
                        year=date_updated.year
                        month=date_updated.month
                        day=date_updated.day
                        time=date_updated.time()
                        object_key = f"{table}/{year}/{month}/{day}/{time}.json"
                        s3_client.put_object(Bucket=bucket_name,Key=object_key,
                                             Body=json.dumps(data_to_upload))
                        s3_client.put_object(Bucket=bucket_name,Key=f'{table}/last_updated.txt',
                                             Body=object_key)
 
                    elif additional_data_from_op_db[i]["last_updated"]==(additional_data_from_op_db
                                                                         [i-1]["last_updated"]):
                        data_to_upload.append(additional_data_from_op_db[i])
                    elif additional_data_from_op_db[i]["last_updated"]!=(additional_data_from_op_db[i-1]
                                                                         ["last_updated"]):
                        date_updated = (datetime.strptime(additional_data_from_op_db[i-1]
                                                          ["last_updated"], '%Y-%m-%dT%H:%M:%S.%f'))
                        year=date_updated.year
                        month=date_updated.month
                        day=date_updated.day
                        time=date_updated.time()
                        object_key = f"{table}/{year}/{month}/{day}/{time}.json"
                        s3_client.put_object(Bucket=bucket_name,Key=object_key,Body=json.dumps(data_to_upload))
                        data_to_upload = [additional_data_from_op_db[i]]
            list_of_table_data_uploaded.append(table)
    close_db_connection(db)
    return f"data has been added to {bucket_name}, in files {list_of_table_data_uploaded}"

#update_data_to_s3_bucket(client("s3"), 'ingestion-bucket20250228065732358000000006' , list_of_tables,operational_entries_not_in_ingestion_bucket)