# VPC, subnets and dependencies

Time: 45 minutes. Prerequisites: Lab 04 identity setup. Cost: VPC/subnets have no hourly fee; no compute created.

Build a private network and understand implicit references.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/06-network
cat main.tf
terraform init
terraform fmt
terraform validate
```

Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner as in Lab 04. Inspect the references from subnets to VPC. No internet gateway, NAT, compute or public IP is created. Explain why availability-zone names differ between accounts.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: One VPC and two private subnets in different available zones.

Practice: Change CIDR only after predicting which resources must be replaced.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
