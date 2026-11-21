# Variables, types, validation, locals and outputs

Time: 45 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Practice precedence and expressions before spending on AWS.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/02-input-output
cat main.tf
terraform init
terraform fmt
terraform validate
```

Create terraform.tfvars with owner = "student01". Try environment = "invalid" and observe validation, then restore dev. Use terraform console to evaluate upper("terraform") and exit to leave. CLI -var overrides tfvars; TF_VAR_owner is another input source.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: Two resources keyed by api and web; output is a map.

Practice: Add worker to the set. Compare stable for_each keys to count indexes.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
