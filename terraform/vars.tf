variable "ec2-instance" {
  type    = string
  default = "ec2_instance_for_cloudwatch"
}

variable "data_ingestion_bucket" {
  type    = string
  default = "ingestion-bucket"
}

variable "data_processed_bucket" {
  type    = string
  default = "processed-bucket"
}

variable "lambda_code_bucket" {
  type    = string
  default = "lambda-code-store-bucket"
}

variable "lambda_1_name" {
  type    = string
  default = "raw_data_to_ingestion_bucket"
}

variable "lambda_2_name" {
  type    = string
  default = "ingestion_to_processed_bucket"
}

variable "lambda_3_name" {
  type    = string
  default = "processed_bucket_to_warehouse"
}

variable "step_function_name" {
  type    = string
  default = "step_function"
}

variable "python_runtime" {
  type    = string
  default = "python3.12"
}