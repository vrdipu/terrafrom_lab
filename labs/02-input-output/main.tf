terraform {
  required_version = ">= 1.10, < 2.0"
}
variable "owner" {
  type = string
  validation {
    condition     = length(var.owner) >= 3
    error_message = "Owner must contain at least three characters."
  }
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Use dev, stage or prod."
  }
}
variable "services" {
  type    = set(string)
  default = ["api", "web"]
}
locals {
  prefix = "${var.owner}-${var.environment}"
}
resource "terraform_data" "service" {
  for_each = var.services
  input    = "${local.prefix}-${each.key}"
}
output "services" {
  value = { for k, v in terraform_data.service : k => v.output }
}
