# State, drift and import

Time: 45 minutes. Prerequisites: Lab 04 completed and destroyed. Cost: S3 requests/storage may incur charges.

Observe drift without deleting state.

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

The initial plan adds three resources as in Lab 04. The first apply and `terraform output` show the generated bucket name, for example:

```text
bucket_name = "tf-training-20261121090100000000000001"
```

`terraform state list` shows the three addresses from the resource blocks above. `terraform state show aws_s3_bucket.practice` shows the recorded attributes, including the bucket ID and tags. If the configured owner is `student01` and you change it to `manual-edit` in the console, compare the two plans:

| Command | What to look for |
| --- | --- |
| `terraform plan -refresh-only` | The drift report shows the observed `Owner` change from `student01` to `manual-edit`, often under `tags_all`. Merely viewing this plan updates neither state nor AWS. |
| `terraform plan` | The planned action for `aws_s3_bucket.practice` updates the owner from `manual-edit` back to `student01` in place. |
| Apply the corrective plan | The bucket name stays the same. Expect one changed resource and no adds or destroys if the tag was the only difference. |

In the import exercise, `Import successful!` means the existing bucket is bound to `aws_s3_bucket.practice`. After import, `terraform state list` shows that address only. The follow-up plan adds the two companion settings and may update bucket attributes such as tags. After applying it, the `bucket_name` output contains the exact console-created bucket name you imported.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/05-state-drift
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Copy terraform.tfvars.example to terraform.tfvars and set account_id and owner as in Lab 04. Create the empty bucket first. In AWS Console change its Owner tag. Run terraform plan -refresh-only, inspect it, then terraform plan and apply to restore the configured tag. Run terraform state list and terraform state show aws_s3_bucket.practice. For import practice: after normal destroy, create an EMPTY private bucket in the console, change bucket_prefix to bucket = "YOUR-EXACT-BUCKET", then terraform import aws_s3_bucket.practice YOUR-EXACT-BUCKET. Review the plan: import only adopts the bucket, companion controls still need apply. Destroy only your adopted training bucket.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

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
