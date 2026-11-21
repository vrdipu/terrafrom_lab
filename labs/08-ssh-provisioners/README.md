# File and remote-exec provisioners

Time: 60 minutes. Prerequisites: AWS S3 labs completed; EC2/VPC/SSM parameter read permissions; SSH outbound allowed. Cost: EC2, EBS and public IPv4 billed; no free-tier assumption.

Copy a file from Windows to EC2 and execute a remote command.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/08-ssh-provisioners
cat main.tf
terraform init
terraform fmt
terraform validate
```

Create ~/.ssh with mkdir -p "$HOME/.ssh". Generate a dedicated SSH key OUTSIDE the repository: ssh-keygen -t ed25519 -f "$HOME/.ssh/terraform-training". For this short classroom demo use a dedicated unencrypted key (empty passphrase); delete it after cleanup, never reuse a personal key. After AWS destroy succeeds, remove only the dedicated key files with rm -f "$HOME/.ssh/terraform-training" "$HOME/.ssh/terraform-training.pub" and unset TF_VAR_private_key_path. Put public_key_path = "~/.ssh/terraform-training.pub" and admin_cidr = "YOUR-PUBLIC-IP/32" in terraform.tfvars with account_id and owner. Run export TF_VAR_private_key_path="$(cygpath -m "$HOME/.ssh/terraform-training")" before plan AND apply. This ephemeral input is not saved in the plan. Run terraform plan/apply with the environment still set. File runs before remote-exec. This SSH example omits host-key pinning for first-contact teaching only; verified host_key or SSM is required for hardened operations. Prefer cloud-init, immutable images and SSM in real deployments.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: Remote console prints welcome.txt; port 22 accepts only your /32.

Practice: Change welcome.txt; inspect terraform_data replacement. Contrast remote-exec with EC2 user_data.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
