"""Student walkthroughs used by the lab README and offline course generator."""

AWS_BLOCKS = '''
- `terraform` sets the Terraform version range. `required_providers` tells `init` to install `hashicorp/aws` in the 6.x series.
- `provider "aws"` uses the configured AWS credentials and `var.aws_region` to make API calls. `allowed_account_ids` checks the actual account against the supplied ID. `default_tags` supplies `Project`, `Owner` and `Environment` tags on supported resources.
- The shared `variable` blocks define the AWS region (default `ap-south-1`), sandbox account ID, owner and environment (default `lab`). The `account_id` validation checks for exactly 12 digits. The provider performs the separate account identity check.
'''

STORAGE_BLOCKS = '''

- `aws_s3_bucket.practice` creates one bucket. Terraform uses `bucket_prefix` and generates a suffix for the name. `force_destroy = false` requires the bucket to be empty before Terraform can delete it.
- `aws_s3_bucket_public_access_block.practice` references the bucket ID. Its four flags block new public ACLs and policies, ignore public ACLs, and restrict access when a public policy exists.
- `aws_s3_bucket_server_side_encryption_configuration.practice` references the same ID. The nested `rule` and `apply_server_side_encryption_by_default` set SSE-S3 (`AES256`) as the default.
- `output "bucket_name"` returns the bucket ID, which for this resource is the bucket name. The two settings resources depend on the bucket through their ID references.

### How many instances are created?

The three resource blocks each produce a single instance. They manage three parts of one bucket, so the two settings blocks do not create additional buckets.
'''

NETWORK_LOOP = '''
`for_each = { a = 0, b = 1 }` gives Terraform two instances. The key is the instance identity and the number is an input to the subnet calculations. With the default `10.42.0.0/16`, `cidrsubnet(var.cidr, 8, each.value)` adds eight prefix bits to make a `/24` and selects its subnet number.

| `each.key` | `each.value` | Calculated CIDR | Availability zone | Tag `Name` |
| --- | --- | --- | --- | --- |
| `a` | `0` | `10.42.0.0/24` | `names[0]` (first) | `<name>-a` |
| `b` | `1` | `10.42.1.0/24` | `names[1]` (second) | `<name>-b` |

The subnets refer to `aws_vpc.this.id` and to the availability zone data source, so Terraform can determine their prerequisites from the references. The table shows how Terraform assigns values. It does not predict the order in which the two subnets finish creating. Adding a new key preserves the existing addresses. Renaming `a` changes its address and normally plans a destroy and create unless you declare a move.

The output expression `{ for k, v in aws_subnet.private : k => v.id }` reads every subnet instance. For key `a`, `v` is the whole subnet object and `v.id` is the ID printed next to `a`. It does the same for `b`, producing a keyed object. The resource `for_each` controls what exists, and the output `for` expression controls what gets displayed.
'''

WALKTHROUGHS = {
    '01-lifecycle': '''
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
''',
    '02-input-output': '''
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
''',
    '03-local-exec': '''
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
''',
    '04-aws-storage': '''
## How the blocks work
''' + STORAGE_BLOCKS + '''

## Expected terminal output

The first plan lists the bucket and both settings resources. It ends with `Plan: 3 to add, 0 to change, 0 to destroy.` The generated bucket name is known after apply. With a successful apply, `terraform output` shows a name like this:

```text
bucket_name = "tf-training-20261121090000000000000001"
```

Use `terraform output -raw bucket_name` to get your exact name without quotes. `terraform state list` shows `aws_s3_bucket.practice`, `aws_s3_bucket_public_access_block.practice` and `aws_s3_bucket_server_side_encryption_configuration.practice`. In the S3 console, check that Block Public Access is on and default encryption is SSE-S3. An unchanged second plan reports no changes. A wrong-account error stops the run before creating resources.
''',
    '05-state-drift': '''
## How the blocks work
''' + STORAGE_BLOCKS + '''

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
''',
    '06-network': '''
## How the blocks work

- `variable "name"` defaults to `training-network` and supplies the base `Name` tag. `variable "cidr"` defaults to `10.42.0.0/16` and supplies the VPC address range.
- `aws_vpc.this` creates the VPC with DNS hostnames enabled. `data "aws_availability_zones" "available"` reads the account's available zones in the selected region.
- `aws_subnet.private` defines the subnet instances. `vpc_id` attaches each to the VPC, while the loop calculates its CIDR, zone and tag.
- `output "vpc_id"` publishes the VPC ID. `output "subnet_ids"` publishes the subnet IDs keyed by `a` and `b`.

### Expand the subnet loop by hand

''' + NETWORK_LOOP + '''

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
''',
    '07-modules': '''
## How the blocks work

- The root `module "network"` loads `../../modules/network` once. It passes a `name` such as `student01-module-lab`. The child uses its own `cidr` default (`10.42.0.0/16`) because the root leaves that argument unset.
- In the child, `versions.tf` declares Terraform and AWS provider requirements. The child inherits the root's AWS provider configuration. Its two `variable` blocks accept `name` and `cidr`.
- In `modules/network/main.tf`, `aws_vpc.this` creates the VPC and enables DNS hostnames. The availability zone data source reads available zones. `aws_subnet.private` places each subnet inside the VPC using a calculated CIDR, zone index and tag.
- The child outputs `vpc_id` and `subnet_ids`. Root outputs read `module.network.vpc_id` and `module.network.subnet_ids`. The root names the second output `subnets`, which is the name `terraform output` displays.

### Follow the loop inside the module

''' + NETWORK_LOOP + '''

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
''',
    '08-ssh-provisioners': '''
## How the blocks work

- `variable "admin_cidr"` checks for a valid IPv4 `/32`, so the inbound SSH rule can use a single address. `public_key_path` points to the public key uploaded to AWS. `private_key_path` is sensitive and ephemeral, so Terraform redacts its value and omits it from plans and state.
- `data "aws_ssm_parameter" "ami"` reads the regional Amazon Linux 2023 x86-64 AMI ID. `aws_vpc.demo` creates the `10.77.0.0/16` network, and `aws_subnet.demo` gives it a `10.77.1.0/24` subnet configured to assign public IPs.
- `aws_internet_gateway.demo` attaches internet connectivity to the VPC. `aws_route_table.demo` sends `0.0.0.0/0` through that gateway. `aws_route_table_association.demo` assigns that route table to the lab subnet.
- `aws_security_group.ssh` allows inbound TCP 22 from `var.admin_cidr` and permits outbound traffic. `aws_key_pair.demo` registers the public key after `pathexpand` resolves `~` and `file` reads its contents.
- `aws_instance.demo` uses the AMI, subnet, security group and registered key to launch a `t3.micro`. It requests a public IP, requires IMDSv2 tokens and encrypts the 8 GiB root EBS volume. `depends_on` makes it wait for the route table association as well as its implicit dependencies.
- `terraform_data.configure` runs the SSH steps. Its `connection` reads the private key locally and connects as `ec2-user` to the instance's public IP. The `file` provisioner uploads `welcome.txt` to `/tmp/welcome.txt`. Then `remote-exec` creates the training directory, copies the file there and reads it. `triggers_replace` tracks the instance ID and file checksum. Either change reruns the steps by replacing the configuration resource.
- `output "public_ip"` exposes the EC2 instance's current public IPv4 address.

The resource blocks each create one instance. The list under `remote-exec.inline` contains three commands that run in sequence in a script on EC2. The three commands do not create three Terraform resource instances.

## Expected terminal output

An initial plan adds nine managed resources, including `terraform_data.configure`. The SSM parameter is a data lookup. The public IP is shown as `(known after apply)` during planning. A successful first apply ends with:

```text
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:

public_ip = "203.0.113.10"
```

The IP shown is an example. Read your IP through `terraform output -raw public_ip`. The `cat` command reads the following text on EC2. Provisioner logs can suppress lines when the connection uses sensitive or ephemeral values. Verify the file independently from Git Bash with the lab key:

```bash
ssh -i "$HOME/.ssh/terraform-training" "ec2-user@$(terraform output -raw public_ip)" 'cat /home/ec2-user/training/welcome.txt'
```

```text
Hello from a file copied by Terraform.
This is an isolated training machine.
```

If the AMI, inputs and file remain unchanged, another plan reports no changes. Editing just `welcome.txt` should plan a replacement of `terraform_data.configure`, while keeping the instance. The cleanup plan removes nine managed resources, including the EC2 instance. Keep the SSH key and `TF_VAR_private_key_path` available through cleanup.
''',
}
