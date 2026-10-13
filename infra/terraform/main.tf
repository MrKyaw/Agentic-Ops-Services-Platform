terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = "services-ai-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# NOT APPLIED (IN-4/IN-5): cost budget alert + autoscaling posture, validated with plan only.
# resource "aws_budgets_budget" "platform" {
#   name         = "services-ai-platform-${var.environment}"
#   budget_type  = "COST"
#   limit_amount = "5000"
#   limit_unit   = "USD"
#   time_unit    = "MONTHLY"
# }
#
# EKS node-group autoscaling (NF-S1) lands with the cluster definition once the
# backend-host decision (EKS vs managed container service) is recorded.
