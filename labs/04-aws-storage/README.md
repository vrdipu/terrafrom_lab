# First AWS resource: private S3 bucket

Time: 45 minutes. Prerequisites: AWS identity configured; sandbox permissions for S3. Cost: S3 requests/storage may incur charges.

Configure a provider, identity guard and private storage.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/04-aws-storage
cat main.tf
terraform init
terraform fmt
terraform validate
```

Run cp terraform.tfvars.example terraform.tfvars and replace the account ID and owner. Authenticate outside Terraform. Run aws sts get-caller-identity and compare the Account before plan. Do not upload objects in this first lab.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: A private encrypted bucket; provider guard rejects the wrong account.

Practice: Explain provider plugin versus module and why credentials do not belong in provider blocks.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
