# VPC, subnets and dependencies

Time: 45 minutes. Prerequisites: Lab 04 identity setup. Cost: VPC/subnets have no hourly fee; no compute created.

Build a private network and understand implicit references.

## How the blocks work

- `terraform` sets the Terraform version range. `required_providers` tells `init` to install `hashicorp/aws` in the 6.x series.
- `provider "aws"` uses the configured AWS credentials and `var.aws_region` to make API calls. `allowed_account_ids` checks the actual account against the supplied ID. `default_tags` supplies `Project`, `Owner` and `Environment` tags on supported resources.
- The shared `variable` blocks define the AWS region (default `ap-south-1`), sandbox account ID, owner and environment (default `lab`). The `account_id` validation checks for exactly 12 digits. The provider performs the separate account identity check.

- `variable "name"` defaults to `training-network` and supplies the base `Name` tag. `variable "cidr"` defaults to `10.42.0.0/16` and supplies the VPC address range.
- `aws_vpc.this` creates the VPC with DNS hostnames enabled. `data "aws_availability_zones" "available"` reads the account's available zones in the selected region.
- `aws_subnet.private` defines the subnet instances. `vpc_id` attaches each to the VPC, while the loop calculates its CIDR, zone and tag.
- `output "vpc_id"` publishes the VPC ID. `output "subnet_ids"` publishes the subnet IDs keyed by `a` and `b`.

### Expand the subnet loop by hand


`for_each = { a = 0, b = 1 }` gives Terraform two instances. The key is the instance identity and the number is an input to the subnet calculations. With the default `10.42.0.0/16`, `cidrsubnet(var.cidr, 8, each.value)` adds eight prefix bits to make a `/24` and selects its subnet number.

| `each.key` | `each.value` | Calculated CIDR | Availability zone | Tag `Name` |
| --- | --- | --- | --- | --- |
| `a` | `0` | `10.42.0.0/24` | `names[0]` (first) | `<name>-a` |
| `b` | `1` | `10.42.1.0/24` | `names[1]` (second) | `<name>-b` |

The subnets refer to `aws_vpc.this.id` and to the availability zone data source, so Terraform can determine their prerequisites from the references. The table shows how Terraform assigns values. It does not predict the order in which the two subnets finish creating. Adding a new key preserves the existing addresses. Renaming `a` changes its address and normally plans a destroy and create unless you declare a move.

The output expression `{ for k, v in aws_subnet.private : k => v.id }` reads every subnet instance. For key `a`, `v` is the whole subnet object and `v.id` is the ID printed next to `a`. It does the same for `b`, producing a keyed object. The resource `for_each` controls what exists, and the output `for` expression controls what gets displayed.


## Expected terminal output

The first plan shows `aws_vpc.this`, `aws_subnet.private["a"]` and `aws_subnet.private["b"]` as additions. The zone lookup reads AWS and does not count as a resource addition. With the defaults, the tags are `training-network-a` and `training-network-b`. Expect `Plan: 3 to add, 0 to change, 0 to destroy.` After apply, `terraform output` looks like this with illustrative AWS IDs:

```text
subnet_ids = {
  "a" = "subnet-0123456789abcdef0"
  "b" = "subnet-0fedcba9876543210"
}
vpc_id = "vpc-0123456789abcdef0"
```

Run `terraform state show 'aws_subnet.private["a"]'` to check the first CIDR, zone, tag and VPC ID. Repeat with `b` to compare. `terraform state list` also shows the zone data source when recorded in state. A second plan with unchanged inputs reports no changes.

## Steps

Start from repository root in Git Bash:

```bash
cd labs/06-network
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner as in Lab 04. Inspect the references from subnets to VPC. No internet gateway, NAT, compute or public IP is created. Explain why availability-zone names differ between accounts.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

Expected: One VPC and two private subnets in different available zones.

Practice: Change CIDR only after predicting which resources must be replaced.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
