# Reusable modules and root composition

Time: 45 minutes. Prerequisites: Lab 06 completed and destroyed. Cost: No hourly network components.

Pass inputs to a child module and expose outputs.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/07-modules
cat main.tf
terraform init
terraform fmt
terraform validate
```

Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner. Read modules/network/main.tf before init. Notice that root output must explicitly expose child outputs. Change a module input and inspect the plan.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: Resource addresses start with module.network.

Practice: Create a second module call using a non-overlapping CIDR; inspect and destroy both.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
