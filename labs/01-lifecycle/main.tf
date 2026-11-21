terraform {
  required_version = ">= 1.10, < 2.0"
}
resource "terraform_data" "hello" {
  input = "Hello Terraform trainer"
}
output "message" {
  value = terraform_data.hello.output
}
