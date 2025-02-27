resource "aws_scheduler_schedule" "lambda_ingestion_schedule" {
  name       = "nc-project-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"

  }

  schedule_expression = "rate(5 minutes)"

  target {
    arn      = aws_lambda_function.lambda_raw_data_to_ingestion_bucket.arn
    role_arn = aws_iam_role.eventbridge_scheduler_role.arn

  }
}


resource "aws_cloudwatch_event_rule" "invoke_step_function" {
  name        = "invoke-step-function"
  description = "Triggers Step Function based on event"

  schedule_expression = "rate(10 minutes)"  
}

resource "aws_iam_role" "eventbridge_to_sfn_role" {
  name = "EventBridgeInvokeStepFunctionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "eventbridge_to_sfn_policy" {
  name        = "EventBridgeInvokeStepFunctionPolicy"
  description = "Allows EventBridge to start Step Functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "states:StartExecution"
      Resource = aws_sfn_state_machine.lambda_1_2_3.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge_to_sfn_attachment" {
  role       = aws_iam_role.eventbridge_to_sfn_role.name
  policy_arn = aws_iam_policy.eventbridge_to_sfn_policy.arn
}

resource "aws_cloudwatch_event_target" "invoke_step_function_target" {
  rule      = aws_cloudwatch_event_rule.invoke_step_function.name
  arn       = aws_sfn_state_machine.lambda_1_2_3.arn
  role_arn  = aws_iam_role.eventbridge_to_sfn_role.arn
}