module "network" {
  source = "../../modules/network"
  name   = "training-dev"
  cidr   = "10.42.0.0/16"
}
output "vpc_id" {
  value = module.network.vpc_id
}
output "subnet_ids" {
  value = module.network.subnet_ids
}
