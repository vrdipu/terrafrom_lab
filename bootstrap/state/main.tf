terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = { Project = "terraform-training", Owner = var.owner, Environment = var.environment }
  }
}
variable "aws_region" {
  type    = string
  default = "ap-south-1"
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply your 12 digit sandbox account ID."
  }
}
variable "owner" {
  type = string
}
variable "environment" {
  type    = string
  default = "lab"
}
resource "aws_s3_bucket" "practice" {
  bucket_prefix = "tf-training-"
  force_destroy = false
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket_public_access_block" "practice" {
  bucket                  = aws_s3_bucket.practice.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "practice" {
  bucket = aws_s3_bucket.practice.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
output "bucket_name" {
  value = aws_s3_bucket.practice.id
}
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.practice.id
  versioning_configuration {
    status = "Enabled"
  }
}
data "aws_iam_policy_document" "tls" {
  statement {
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.practice.arn, "${aws_s3_bucket.practice.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.practice.id
  policy = data.aws_iam_policy_document.tls.json
}
