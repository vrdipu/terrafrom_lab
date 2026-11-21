# First init, plan, apply and destroy

Time: 30 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Learn desired state, resource addresses and idempotence.

## How the blocks work

- `terraform` declares the allowed CLI versions. `terraform_data` is built into Terraform, so this lab needs neither an AWS provider nor credentials.
- `resource "terraform_data" "hello"` creates one object at the address `terraform_data.hello`. Its `input` stores the greeting in state and its computed `output` echoes that value.
- `output "message"` reads `terraform_data.hello.output` and makes it available through `terraform output`. The reference tells Terraform where the value comes from.

There is no loop here. One resource block creates one instance, with no bracketed key after its address.

## Expected terminal output

On a fresh run, `plan` shows `+ terraform_data.hello`, its literal `input`, and a computed `output` marked `(known after apply)`. The plan ends with `Plan: 1 to add, 0 to change, 0 to destroy.` After apply:

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

message = "Hello Terraform trainer"
```

`terraform output` prints the `message` line again. `terraform state list` prints `terraform_data.hello`. A repeat plan reports `No changes.` If you edit the greeting, the next plan shows an in-place update to `terraform_data.hello` and a changed output. A destroy plan removes one resource and the saved root output.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/01-lifecycle
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

No input file is needed. Read every planned action before applying. Change the message after the first apply and repeat plan/apply.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

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
