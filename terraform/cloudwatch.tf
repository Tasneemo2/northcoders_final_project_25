resource "aws_cloudwatch_log_group" "lambda_log" {
  name = "Lambda_Ingestion"

  tags = {
    Environment = "production"
    Application = "serviceA"
  }
}

# resource "aws_cloudwatch_log_stream" "lambda_log_stream" {
#   name           = "Lambda_log_stream"
#   log_group_name = aws_cloudwatch_log_group.lambda_log.name
# }

# cloudwatch log group for step function
resource "aws_cloudwatch_log_group" "step_function_logs" {
  name = "/aws/states/my-step-function-logs"
  retention_in_days = 30
}

# resource to notify for email alerts

resource "aws_sns_topic" "cloudwatch_alerts" {
  name = "cloudwatch-error-alerts"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.cloudwatch_alerts.arn
  protocol  = "email"
  endpoint  = "benjstevenmorgan@gmail.com"  # Left as my email for now. Should this be user's email?
}


# logs metric for major errors in lambda log
resource "aws_cloudwatch_log_metric_filter" "error_metric_filter" {
  name           = "major-error-filter"
  log_group_name = aws_cloudwatch_log_group.lambda_log.name 

  pattern = "{ $.level = \"ERROR\" }"  # Detects logs where level is "ERROR"

  metric_transformation {
    name      = "MajorErrorCount"
    namespace = "LogMetrics"
    value     = "1"
  }
}


# alarm for lambda errors
resource "aws_cloudwatch_metric_alarm" "error_alarm" {
  alarm_name          = "MajorErrorAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.error_metric_filter.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.error_metric_filter.metric_transformation[0].namespace
  period              = 60  # Check every 1 minute
  statistic           = "Sum"
  threshold           = 1   # Alarm triggers if at least 1 error is detected
  alarm_description   = "Triggers when a major error is logged"

  alarm_actions = [aws_sns_topic.cloudwatch_alerts.arn]  # Send alert to SNS
}

# alarm for step function failures
resource "aws_cloudwatch_metric_alarm" "step_function_failure_alarm" {
  alarm_name          = "StepFunctionFailures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Triggers when Step Function fails"
  alarm_actions       = [aws_sns_topic.cloudwatch_alerts.arn]

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.lambda_1_2_3.arn
  }
}

resource "aws_cloudwatch_log_stream" "lambda_log_stream" {
  name           = "Lambda_log_stream"
  log_group_name = aws_cloudwatch_log_group.lambda_log.name
}

