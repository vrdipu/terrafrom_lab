# Reusable modules and root composition

Time: 45 minutes. Prerequisites: Lab 06 completed and destroyed. Cost: No hourly network components.

Pass inputs to a child module and expose outputs.

## How the blocks work

- `terraform` sets the Terraform version range. `required_providers` tells `init` to install `hashicorp/aws` in the 6.x series.
- `provider "aws"` uses the configured AWS credentials and `var.aws_region` to make API calls. `allowed_account_ids` checks the actual account against the supplied ID. `default_tags` supplies `Project`, `Owner` and `Environment` tags on supported resources.
- The shared `variable` blocks define the AWS region (default `ap-south-1`), sandbox account ID, owner and environment (default `lab`). The `account_id` validation checks for exactly 12 digits. The provider performs the separate account identity check.

- The root `module "network"` loads `../../modules/network` once. It passes a `name` such as `student01-module-lab`. The child uses its own `cidr` default (`10.42.0.0/16`) because the root leaves that argument unset.
- In the child, `versions.tf` declares Terraform and AWS provider requirements. The child inherits the root's AWS provider configuration. Its two `variable` blocks accept `name` and `cidr`.
- In `modules/network/main.tf`, `aws_vpc.this` creates the VPC and enables DNS hostnames. The availability zone data source reads available zones. `aws_subnet.private` places each subnet inside the VPC using a calculated CIDR, zone index and tag.
- The child outputs `vpc_id` and `subnet_ids`. Root outputs read `module.network.vpc_id` and `module.network.subnet_ids`. The root names the second output `subnets`, which is the name `terraform output` displays.

### Follow the loop inside the module


`for_each = { a = 0, b = 1 }` gives Terraform two instances. The key is the instance identity and the number is an input to the subnet calculations. With the default `10.42.0.0/16`, `cidrsubnet(var.cidr, 8, each.value)` adds eight prefix bits to make a `/24` and selects its subnet number.

| `each.key` | `each.value` | Calculated CIDR | Availability zone | Tag `Name` |
| --- | --- | --- | --- | --- |
| `a` | `0` | `10.42.0.0/24` | `names[0]` (first) | `<name>-a` |
| `b` | `1` | `10.42.1.0/24` | `names[1]` (second) | `<name>-b` |

The subnets refer to `aws_vpc.this.id` and to the availability zone data source, so Terraform can determine their prerequisites from the references. The table shows how Terraform assigns values. It does not predict the order in which the two subnets finish creating. Adding a new key preserves the existing addresses. Renaming `a` changes its address and normally plans a destroy and create unless you declare a move.

The output expression `{ for k, v in aws_subnet.private : k => v.id }` reads every subnet instance. For key `a`, `v` is the whole subnet object and `v.id` is the ID printed next to `a`. It does the same for `b`, producing a keyed object. The resource `for_each` controls what exists, and the output `for` expression controls what gets displayed.


Unlike the Lab 06 addresses, the child resources are prefixed with `module.network.`. Here, `a` and `b` are keys on the child subnet resource. The root calls the module once without its own `for_each`.

## Expected terminal output

The first plan adds `module.network.aws_vpc.this`, `module.network.aws_subnet.private["a"]` and `module.network.aws_subnet.private["b"]`. The first apply adds three resources. `terraform output` shows the root outputs below, using example AWS IDs:

```text
subnets = {
  "a" = "subnet-0123456789abcdef0"
  "b" = "subnet-0fedcba9876543210"
}
vpc_id = "vpc-0123456789abcdef0"
```

`terraform state list` also shows `module.network.data.aws_availability_zones.available` when recorded in state. For `owner = "student01"`, the VPC tag is `student01-module-lab` and the subnet tags append `-a` and `-b`. A second module call with a different label and CIDR would add three resources under that label. It gets its own `a` and `b`, and you can expose its results by adding separate root outputs.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/07-modules
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner. Read modules/network/main.tf before init. Notice that root output must explicitly expose child outputs. Change a module input and inspect the plan.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

Expected: Resource addresses start with module.network.

Practice: Create a second module call using a non-overlapping CIDR; inspect and destroy both.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
