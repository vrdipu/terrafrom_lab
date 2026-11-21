# First AWS resource: private S3 bucket

Time: 45 minutes. Prerequisites: AWS identity configured; sandbox permissions for S3. Cost: S3 requests/storage may incur charges.

Configure a provider, identity guard and private storage.

## How the blocks work

- `terraform` sets the Terraform version range. `required_providers` tells `init` to install `hashicorp/aws` in the 6.x series.
- `provider "aws"` uses the configured AWS credentials and `var.aws_region` to make API calls. `allowed_account_ids` checks the actual account against the supplied ID. `default_tags` supplies `Project`, `Owner` and `Environment` tags on supported resources.
- The shared `variable` blocks define the AWS region (default `ap-south-1`), sandbox account ID, owner and environment (default `lab`). The `account_id` validation checks for exactly 12 digits. The provider performs the separate account identity check.


- `aws_s3_bucket.practice` creates one bucket. Terraform uses `bucket_prefix` and generates a suffix for the name. `force_destroy = false` requires the bucket to be empty before Terraform can delete it.
- `aws_s3_bucket_public_access_block.practice` references the bucket ID. Its four flags block new public ACLs and policies, ignore public ACLs, and restrict access when a public policy exists.
- `aws_s3_bucket_server_side_encryption_configuration.practice` references the same ID. The nested `rule` and `apply_server_side_encryption_by_default` set SSE-S3 (`AES256`) as the default.
- `output "bucket_name"` returns the bucket ID, which for this resource is the bucket name. The two settings resources depend on the bucket through their ID references.

### How many instances are created?

The three resource blocks each produce a single instance. They manage three parts of one bucket, so the two settings blocks do not create additional buckets.


## Expected terminal output

The first plan lists the bucket and both settings resources. It ends with `Plan: 3 to add, 0 to change, 0 to destroy.` The generated bucket name is known after apply. With a successful apply, `terraform output` shows a name like this:

```text
bucket_name = "tf-training-20261121090000000000000001"
```

Use `terraform output -raw bucket_name` to get your exact name without quotes. `terraform state list` shows `aws_s3_bucket.practice`, `aws_s3_bucket_public_access_block.practice` and `aws_s3_bucket_server_side_encryption_configuration.practice`. In the S3 console, check that Block Public Access is on and default encryption is SSE-S3. An unchanged second plan reports no changes. A wrong-account error stops the run before creating resources.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/04-aws-storage
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Run cp terraform.tfvars.example terraform.tfvars and replace the account ID and owner. Authenticate outside Terraform. Run aws sts get-caller-identity and compare the Account before plan. Do not upload objects in this first lab.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

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
