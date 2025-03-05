#lambda layer to import pg8000

data "archive_file" "lambda-layer" {
  type = "zip"
  source_dir = "${path.module}/../lambda-layer/python/"
  output_path = "${path.module}/../pg8000-layer.zip"
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename   = "${path.module}/../lambda-layer/pg8000-layer.zip"
  layer_name = "ingestion_bucket_dependencies"
}

resource "aws_lambda_layer_version_permission" "lambda_layer_permission" {
  layer_name     = aws_lambda_layer_version.lambda_layer.layer_name
  version_number = aws_lambda_layer_version.lambda_layer.version
  principal      = "*"
  action         = "lambda:GetLayerVersion"
  statement_id   = "test-pg8000-layer"
}



