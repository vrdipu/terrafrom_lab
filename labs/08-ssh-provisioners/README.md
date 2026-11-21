# File and remote-exec provisioners

Time: 60 minutes. Prerequisites: AWS S3 labs completed; EC2/VPC/SSM parameter read permissions; SSH outbound allowed. Cost: EC2, EBS and public IPv4 billed; no free-tier assumption.

Copy a file from Windows to EC2 and execute a remote command.

## How the blocks work

- `terraform` sets the Terraform version range. `required_providers` tells `init` to install `hashicorp/aws` in the 6.x series.
- `provider "aws"` uses the configured AWS credentials and `var.aws_region` to make API calls. `allowed_account_ids` checks the actual account against the supplied ID. `default_tags` supplies `Project`, `Owner` and `Environment` tags on supported resources.
- The shared `variable` blocks define the AWS region (default `ap-south-1`), sandbox account ID, owner and environment (default `lab`). The `account_id` validation checks for exactly 12 digits. The provider performs the separate account identity check.

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

## Steps

Start from repository root in Git Bash:

```bash
cd labs/08-ssh-provisioners
cat main.tf
terraform init
terraform fmt
terraform validate
```

`init` prepares this directory. `fmt` formats the source and `validate` checks the configuration. A successful `validate` prints `Success! The configuration is valid.`

Create ~/.ssh with mkdir -p "$HOME/.ssh". Generate a dedicated SSH key OUTSIDE the repository: ssh-keygen -t ed25519 -f "$HOME/.ssh/terraform-training". For this short classroom demo use a dedicated unencrypted key (empty passphrase); delete it after cleanup, never reuse a personal key. After AWS destroy succeeds, remove only the dedicated key files with rm -f "$HOME/.ssh/terraform-training" "$HOME/.ssh/terraform-training.pub" and unset TF_VAR_private_key_path. Put public_key_path = "~/.ssh/terraform-training.pub" and admin_cidr = "YOUR-PUBLIC-IP/32" in terraform.tfvars with account_id and owner. Run export TF_VAR_private_key_path="$(cygpath -m "$HOME/.ssh/terraform-training")" before plan AND apply. This ephemeral input is not saved in the plan. Run terraform plan/apply with the environment still set. File runs before remote-exec. This SSH example omits host-key pinning for first-contact teaching only; verified host_key or SSM is required for hardened operations. Prefer cloud-init, immutable images and SSM in real deployments.

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

`plan` saves the proposed actions to `review.tfplan`. `show` lets you read that exact plan before `apply` executes it. `output` reads saved root outputs, and the final `plan` checks whether any changes remain. In plan output, `+` means create, `~` means update in place, and `-` means destroy.

Expected: The file contains the two expected lines on EC2 and the root output shows its public IP.

Practice: Change welcome.txt; inspect terraform_data replacement. Contrast remote-exec with EC2 user_data.

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
