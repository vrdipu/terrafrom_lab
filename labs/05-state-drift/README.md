# State, drift and import

Time: 45 minutes. Prerequisites: Lab 04 completed and destroyed. Cost: S3 requests/storage may incur charges.

Observe drift without deleting state.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/05-state-drift
cat main.tf
terraform init
terraform fmt
terraform validate
```

Create the empty bucket first. In AWS Console change its Owner tag. Run terraform plan -refresh-only, inspect it, then terraform plan and apply to restore the configured tag. Run terraform state list and terraform state show aws_s3_bucket.practice. For import practice: after normal destroy, create an EMPTY private bucket in the console, change bucket_prefix to bucket = "YOUR-EXACT-BUCKET", then terraform import aws_s3_bucket.practice YOUR-EXACT-BUCKET. Review the plan: import only adopts the bucket, companion controls still need apply. Destroy only your adopted training bucket.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: Drift appears in plan. Import establishes a binding between one resource address and one remote object.

Practice: Discuss why state rm forgets a resource without deleting it; never practice it on shared infrastructure.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
