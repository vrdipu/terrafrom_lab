# Local execution on Windows

Time: 30 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Understand where commands execute and why provisioners are a last resort.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/03-local-exec
cat main.tf
terraform init
terraform fmt
terraform validate
```

Apply twice: the provisioner runs on creation only. Change message and plan again; triggers_replace causes replacement. The command executes on the trainer/student PC, not AWS. Environment passing avoids interpolating input into executable shell text.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: Console prints the message once during creation.

Practice: Explain taint/replacement on creation-time provisioner failure and why on_failure = continue can hide errors.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
