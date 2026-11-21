terraform {
  required_version = ">= 1.10, < 2.0"
}
variable "message" {
  type    = string
  default = "Training provisioner completed"
}
resource "terraform_data" "notice" {
  triggers_replace = [var.message]
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "bash notice.sh"
    environment = { TRAINING_MESSAGE = var.message }
  }
}
