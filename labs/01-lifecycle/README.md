# First init, plan, apply and destroy

Time: 30 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Learn desired state, resource addresses and idempotence.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/01-lifecycle
cat main.tf
terraform init
terraform fmt
terraform validate
```

No input file is needed. Read every planned action before applying. Change the message after the first apply and repeat plan/apply.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: One terraform_data resource; a second plan says no changes.

Practice: Explain why init downloads no external provider here.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
