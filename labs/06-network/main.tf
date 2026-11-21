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
variable "name" {
  type    = string
  default = "training-network"
}
variable "cidr" {
  type    = string
  default = "10.42.0.0/16"
}
resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_hostnames = true
  tags                 = { Name = var.name }
}
resource "aws_subnet" "private" {
  for_each          = { a = 0, b = 1 }
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.cidr, 8, each.value)
  availability_zone = data.aws_availability_zones.available.names[each.value]
  tags              = { Name = "${var.name}-${each.key}" }
}
data "aws_availability_zones" "available" {
  state = "available"
}
output "vpc_id" {
  value = aws_vpc.this.id
}
output "subnet_ids" {
  value = { for k, v in aws_subnet.private : k => v.id }
}
