# Phase 0 landing-zone skeleton. Private subnets, no public ingress except the ALB.
# NOT APPLIED: requires AWS credentials and review-board approval (see docs/RUNBOOK.md).
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 1)
  availability_zone = "${var.region}a"
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 2)
  availability_zone = "${var.region}b"
}

resource "aws_kms_key" "tenant" {
  description             = "Tenant data encryption (per-tenant keys created in Phase 1)"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}
