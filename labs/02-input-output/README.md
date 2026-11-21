# Variables, types, validation, locals and outputs

Time: 45 minutes. Prerequisites: Windows setup completed. Cost: No AWS resources.

Practice precedence and expressions before spending on AWS.

## How the blocks work

- `terraform` sets the CLI version range and the lab uses Terraform's built-in `terraform_data` resource.
- `variable "owner"` requires a string at least three characters long. `variable "environment"` defaults to `dev` and validates the allowed values with `contains`. `variable "services"` defaults to a set containing `api` and `web`. A set drops duplicates and has no insertion order.
- `locals` names a reusable expression. With `owner = "student01"` and the default environment, `local.prefix` evaluates to `student01-dev`.
- `resource "terraform_data" "service"` uses `for_each` to create one instance per service. Each `input` combines the prefix with the service name.
- `output "services"` builds one keyed object from the instances' computed outputs.

### Expand the loop by hand

For a set of strings, `each.key` and `each.value` both equal the current string. Terraform can expand these keys at plan time because they come from inputs it already knows.

| Set member | `each.key` / `each.value` | Resource address | `input` |
| --- | --- | --- | --- |
| `api` | `api` | `terraform_data.service["api"]` | `student01-dev-api` |
| `web` | `web` | `terraform_data.service["web"]` | `student01-dev-web` |

Read `{ for k, v in terraform_data.service : k => v.output }` as “for each instance, put its output under the same key.” For example, `k` is `api`, `v` is the instance at `terraform_data.service["api"]`, and `v.output` becomes `student01-dev-api` after apply. The expression only builds a result to display. The `for_each` on the resource determines how many objects Terraform manages. A `count` example would identify instances by numeric indexes such as `[0]`.

## Expected terminal output

With only `owner = "student01"` set, the first plan lists both keyed addresses and ends with `Plan: 2 to add, 0 to change, 0 to destroy.` Both result values are known after apply. The `Outputs:` section and `terraform output` show:

```text
services = {
  "api" = "student01-dev-api"
  "web" = "student01-dev-web"
}
```

`terraform state list` shows the two addresses in the table. Add `services = ["api", "web", "worker"]` to the same `terraform.tfvars` and plan again. Expect only `+ terraform_data.service["worker"]`. After apply, the output gains `"worker" = "student01-dev-worker"`. Removing `web` would plan to destroy just its keyed instance, assuming no other edits. With `environment = "invalid"`, the plan stops with `Use dev, stage or prod.` Restore `dev` to continue.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/02-input-output
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Create terraform.tfvars with owner = "student01". Try environment = "invalid" and observe validation, then restore dev. Use terraform console to evaluate upper("terraform") and exit to leave. CLI -var overrides tfvars; TF_VAR_owner is another input source.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

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
