variable "region" {
  description = "AWS region, pinned per environment for data-residency control"
  type        = string
  default     = "ca-central-1"
}

variable "environment" {
  description = "dev | staging | prod"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR for the landing zone"
  type        = string
  default     = "10.0.0.0/16"
}
