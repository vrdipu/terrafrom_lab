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
variable "admin_cidr" {
  type = string
  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/32$", var.admin_cidr)) && can(cidrhost(var.admin_cidr, 0))
    error_message = "Use your current public IPv4 address with /32."
  }
}
variable "public_key_path" {
  type = string
}
variable "private_key_path" {
  type      = string
  sensitive = true
  ephemeral = true
}
data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
resource "aws_vpc" "demo" {
  cidr_block = "10.77.0.0/16"
}
resource "aws_subnet" "demo" {
  vpc_id                  = aws_vpc.demo.id
  cidr_block              = "10.77.1.0/24"
  map_public_ip_on_launch = true
}
resource "aws_internet_gateway" "demo" {
  vpc_id = aws_vpc.demo.id
}
resource "aws_route_table" "demo" {
  vpc_id = aws_vpc.demo.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.demo.id
  }
}
resource "aws_route_table_association" "demo" {
  subnet_id      = aws_subnet.demo.id
  route_table_id = aws_route_table.demo.id
}
resource "aws_security_group" "ssh" {
  name_prefix = "training-ssh-"
  vpc_id      = aws_vpc.demo.id
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_key_pair" "demo" {
  key_name_prefix = "training-"
  public_key      = file(pathexpand(var.public_key_path))
}
resource "aws_instance" "demo" {
  ami                         = data.aws_ssm_parameter.ami.value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.demo.id
  vpc_security_group_ids      = [aws_security_group.ssh.id]
  key_name                    = aws_key_pair.demo.key_name
  associate_public_ip_address = true
  metadata_options {
    http_tokens = "required"
  }
  root_block_device {
    encrypted   = true
    volume_size = 8
  }
  depends_on = [aws_route_table_association.demo]
}
resource "terraform_data" "configure" {
  triggers_replace = [aws_instance.demo.id, filesha256("${path.module}/welcome.txt")]
  connection {
    type        = "ssh"
    user        = "ec2-user"
    host        = aws_instance.demo.public_ip
    private_key = file(pathexpand(var.private_key_path))
    timeout     = "5m"
  }
  provisioner "file" {
    source      = "${path.module}/welcome.txt"
    destination = "/tmp/welcome.txt"
  }
  provisioner "remote-exec" {
    inline = ["mkdir -p /home/ec2-user/training", "cp /tmp/welcome.txt /home/ec2-user/training/welcome.txt", "cat /home/ec2-user/training/welcome.txt"]
  }
}
output "public_ip" {
  value = aws_instance.demo.public_ip
}
