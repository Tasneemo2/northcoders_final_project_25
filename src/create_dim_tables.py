from ingestion_to_processed_bucket.dim_date_function import extract_date_info_from_dim_date
from src.get_currency_name import get_currency_details
import pg8000.native
from s3_read_function.s3_read_function import read_files_from_s3

# This function will set up the dimensions tables
def set_up_dims_table(database_connection,table_names):
    # delete all existing dim tables
    for dim_table in dimensions_tables_creation:
        database_connection.run(f"DROP TABLE IF EXISTS {dim_table};")
    # create list of tables to be created from 
    dim_tables_to_be_created = []
    for dim_table in dimensions_tables_creation:
      if all(dependent in table_names for dependent in list(dimensions_tables_creation[dim_table][1:])):
        dim_tables_to_be_created.append(dim_table)
    for table in dim_tables_to_be_created:
        database_connection.run(f"CREATE TEMPORARY TABLE {dimensions_tables_creation[table][0]};")
    return dim_tables_to_be_created

def put_info_into_dims_schema(database_connection,dim_tables_created, date_str, currency_id):

    dimension_value_rows = {}
    # use select statement to choose information required for star schema
    for table in dim_tables_created:
        if table == "dim_date":
          date_info = extract_date_info_from_dim_date(date_str)
          print(f"Extracted Date Info for {table}: {date_info}")
        elif table == "dim_currency":
            get_currency = get_currency_details(currency_id)
            print(f"Currency details for {table}: {currency_id}")
        dimension_value_rows[table] =  database_connection.run(f'''
        INSERT INTO {table} {str(tuple(dim_tables_column_headers[table])).replace("'","")}
        {dimensions_insertion_queries[table]}
        RETURNING *;
        ''')
    print(f'''
        INSERT INTO {table} {str(tuple(dim_tables_column_headers[table])).replace("'","")}
        {dimensions_insertion_queries[table]}
        RETURNING *;
        ''')
        
    # return as variable
    return dimension_value_rows


# This is a dictionary of lists
# key = dimensions table names
# value[0] = headers
# value[1:] = dependencies
# for use in python, but written in SQL.
dimensions_tables_creation = {
  "dim_date":[
'''"dim_date" (
  "date_id" date PRIMARY KEY NOT NULL,
  "year" int NOT NULL,
  "month" int NOT NULL,
  "day" int NOT NULL,
  "day_of_week" int NOT NULL,
  "day_name" varchar NOT NULL,
  "month_name" varchar NOT NULL,
  "quarter" int NOT NULL
);''',"sales_order"],

"dim_staff":[
'''"dim_staff" (
  "staff_id" int PRIMARY KEY NOT NULL,
  "first_name" varchar NOT NULL,
  "last_name" varchar NOT NULL,
  "department_name" varchar NOT NULL,
  "location" varchar NOT NULL,
  "email_address" varchar NOT NULL
);''',"staff","department"],

"dim_location":[
'''"dim_location" (
  "location_id" int PRIMARY KEY NOT NULL,
  "address_line_1" varchar NOT NULL,
  "address_line_2" varchar,
  "district" varchar,
  "city" varchar NOT NULL,
  "postal_code" varchar NOT NULL,
  "country" varchar NOT NULL,
  "phone" varchar NOT NULL
);''',"address"],

"dim_currency":[
'''"dim_currency" (
  "currency_id" int PRIMARY KEY NOT NULL,
  "currency_code" varchar NOT NULL,
  "currency_name" varchar NOT NULL
);''',"currency"],

"dim_design":[
'''"dim_design" (
  "design_id" int PRIMARY KEY NOT NULL,
  "design_name" varchar NOT NULL,
  "file_location" varchar NOT NULL,
  "file_name" varchar NOT NULL
);''',"design"],

"dim_counterparty":[
'''"dim_counterparty" (
  "counterparty_id" int PRIMARY KEY NOT NULL,
  "counterparty_legal_name" varchar NOT NULL,
  "counterparty_legal_address_line_1" varchar NOT NULL,
  "counterparty_legal_address_line_2" varchar,
  "counterparty_legal_district" varchar,
  "counterparty_legal_city" varchar NOT NULL,
  "counterparty_legal_postal_code" varchar NOT NULL,
  "counterparty_legal_country" varchar NOT NULL,
  "counterparty_legal_phone_number" varchar NOT NULL
);''',"counterparty","address"]
}


dim_tables_column_headers = {"dim_date":
  ["date_id",
  "year",
  "month",
  "day",
  "day_of_week",
  "day_name",
  "month_name",
  "quarter"],

  "dim_staff":
  ["staff_id",
  "first_name",
  "last_name" ,
  "department_name",
  "location",
  "email_address"],

  "dim_location":
  ["location_id",
  "address_line_1",
  "address_line_2",
  "district",
  "city",
  "postal_code",
  "country",
  "phone"],

  "dim_currency":
  ["currency_id",
  "currency_code",
  "currency_name"],


  "dim_design":
  ["design_id",
  "design_name",
  "file_location",
  "file_name"],

  "dim_counterparty":
  ["counterparty_id",
  "counterparty_legal_name",
  "counterparty_legal_address_line_1",
  "counterparty_legal_address_line_2",
  "counterparty_legal_district",
  "counterparty_legal_city",
  "counterparty_legal_postal_code",
  "counterparty_legal_country",
  "counterparty_legal_phone_number"]
}

dimensions_insertion_queries = {
"dim_date":'''
SELECT created_at,last_updated,agreed_delivery_date,agreed_payment_date
FROM sales_order
''',
"dim_staff":'''
SELECT staff_id,first_name,last_name, department.department_name,department.location,email_address
FROM staff
JOIN department ON staff.department_id = department.department_id
''',
"dim_location":'''
SELECT address_id,address_line_1, address_line_2,district,city,postal_code,country,phone
FROM address
''',
# need to itegrate Erins currency function here
"dim_currency":'''
SELECT  currency_id, currency_code
FROM currency
''',
"dim_design":'''
SELECT design_id,design_name,file_location,file_name
FROM design
''',
"dim_counterparty":'''
SELECT 
counterparty_id,
counterparty_legal_name,
address.address_line_1,
address.address_line_2,
address.district,
address.city,
address.postal_code,
address.country,
address.phone
FROM counterparty
JOIN address
ON counterparty.legal_address_id = address.address_id
'''
}