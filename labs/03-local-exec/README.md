# Local execution on Windows

Time: 30 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Understand where commands execute and why provisioners are a last resort.

## How the blocks work

- `terraform` declares the required CLI range. `variable "message"` supplies the text and defaults to `Training provisioner completed`.
- `resource "terraform_data" "notice"` stores `triggers_replace = [var.message]`. If the message changes, Terraform replaces this resource so its creation-time provisioner can run again.
- The nested `provisioner "local-exec"` runs `bash notice.sh` in a local Bash process. `environment` passes `TRAINING_MESSAGE` to the command. `notice.sh` uses `printf` to print the variable as text.

There is one Terraform resource and one script invocation on creation. The brackets in `[var.message]` build a list containing one replacement trigger. The interpreter list supplies Bash and its `-c` flag.

## Expected terminal output

The first plan adds `terraform_data.notice`. During apply, the script logs this line among the Terraform progress messages:

```text
terraform_data.notice (local-exec): Training provisioner completed
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

There is no root `output` block. `terraform output` reports no outputs. `terraform state list` shows `terraform_data.notice`. Applying again without edits produces no changes and no script message. To see it run again, set `message = "Second run"` in `terraform.tfvars`. Expect a replacement (`-/+`, one add and one destroy), followed by `Second run` in the provisioner log on apply.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/03-local-exec
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Apply twice: the provisioner runs on creation only. Change message and plan again; triggers_replace causes replacement. The command executes on the trainer/student PC, not AWS. Environment passing avoids interpolating input into executable shell text.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

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
