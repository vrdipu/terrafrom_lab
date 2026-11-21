variable "name" {
  type = string
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
