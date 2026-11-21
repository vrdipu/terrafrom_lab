from pathlib import Path
from html import escape
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def put(name, content):
    p=ROOT/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content.strip()+'\n',encoding='utf-8', newline='\n')

put('.gitignore', '''
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
*.plan
crash.log
crash.*.log
*.tfvars
*.tfvars.json
!*.tfvars.example
!*.tfvars.json.example
*.backend.hcl
!*.backend.hcl.example
.aws/
.env
.env.*
*.pem
*.key
*.pfx
*.ppk
override.tf
override.tf.json
*_override.tf
*_override.tf.json
generated/
__pycache__/
''')
version='''terraform {
  required_version = ">= 1.10, < 2.0"
}'''
aws='''terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  region = var.aws_region
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = { Project = "terraform-training", Owner = var.owner, Environment = var.environment }
  }
}
variable "aws_region" {
  type    = string
  default = "ap-south-1"
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply your 12 digit sandbox account ID."
  }
}
variable "owner" {
  type = string
}
variable "environment" {
  type    = string
  default = "lab"
}
'''
labdata=[]
def lab(slug,title,minutes,goal,main,steps,check,challenge,cost='No AWS resources',prereq='Windows setup completed'):
    folder='labs/'+slug
    put(folder+'/main.tf',main)
    labdata.append(dict(slug=slug,title=title,minutes=minutes,goal=goal,steps=steps,check=check,challenge=challenge,cost=cost,prereq=prereq))
    put(folder+'/README.md',f'''# {title}

Time: {minutes} minutes. Prerequisites: {prereq}. Cost: {cost}.

{goal}

## Steps

Start from repository root in Git Bash:

```bash
cd {folder}
cat main.tf
terraform init
terraform fmt
terraform validate
```

{steps}

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
terraform output
terraform plan
```

Expected: {check}

Practice: {challenge}

## Cleanup

```bash
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
terraform state list
cd ../..
```

Expected: no managed resources remain. Keep state until cleanup succeeds. Never run another lab inside this directory.
''')

lab('01-lifecycle','First init, plan, apply and destroy',30,'Learn desired state, resource addresses and idempotence.',version+'''
resource "terraform_data" "hello" {
  input = "Hello Terraform trainer"
}
output "message" {
  value = terraform_data.hello.output
}''','No input file is needed. Read every planned action before applying. Change the message after the first apply and repeat plan/apply.','One terraform_data resource; a second plan says no changes.','Explain why init downloads no external provider here.')
lab('02-input-output','Variables, types, validation, locals and outputs',45,'Practice precedence and expressions before spending on AWS.',version+'''
variable "owner" {
  type = string
  validation {
    condition     = length(var.owner) >= 3
    error_message = "Owner must contain at least three characters."
  }
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Use dev, stage or prod."
  }
}
variable "services" {
  type    = set(string)
  default = ["api", "web"]
}
locals {
  prefix = "${var.owner}-${var.environment}"
}
resource "terraform_data" "service" {
  for_each = var.services
  input    = "${local.prefix}-${each.key}"
}
output "services" {
  value = { for k, v in terraform_data.service : k => v.output }
}''','Create terraform.tfvars with owner = "student01". Try environment = "invalid" and observe validation, then restore dev. Use terraform console to evaluate upper("terraform") and exit to leave. CLI -var overrides tfvars; TF_VAR_owner is another input source.','Two resources keyed by api and web; output is a map.','Add worker to the set. Compare stable for_each keys to count indexes.')
lab('03-local-exec','Local execution on Windows',30,'Understand where commands execute and why provisioners are a last resort.',version+'''
variable "message" {
  type    = string
  default = "Training provisioner completed"
}
resource "terraform_data" "notice" {
  triggers_replace = [var.message]
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "bash notice.sh"
    environment = { TRAINING_MESSAGE = var.message }
  }
}''','Apply twice: the provisioner runs on creation only. Change message and plan again; triggers_replace causes replacement. The command executes on the trainer/student PC, not AWS. Environment passing avoids interpolating input into executable shell text.','Console prints the message once during creation.','Explain taint/replacement on creation-time provisioner failure and why on_failure = continue can hide errors.')
s3='''resource "aws_s3_bucket" "practice" {
  bucket_prefix = "tf-training-"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "practice" {
  bucket = aws_s3_bucket.practice.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "practice" {
  bucket = aws_s3_bucket.practice.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
output "bucket_name" {
  value = aws_s3_bucket.practice.id
}'''
lab('04-aws-storage','First AWS resource: private S3 bucket',45,'Configure a provider, identity guard and private storage.',aws+s3,'Run cp terraform.tfvars.example terraform.tfvars and replace the account ID and owner. Authenticate outside Terraform. Run aws sts get-caller-identity and compare the Account before plan. Do not upload objects in this first lab.','A private encrypted bucket; provider guard rejects the wrong account.','Explain provider plugin versus module and why credentials do not belong in provider blocks.','S3 requests/storage may incur charges','AWS identity configured; sandbox permissions for S3')
lab('05-state-drift','State, drift and import',45,'Observe drift without deleting state.',aws+s3,'Create the empty bucket first. In AWS Console change its Owner tag. Run terraform plan -refresh-only, inspect it, then terraform plan and apply to restore the configured tag. Run terraform state list and terraform state show aws_s3_bucket.practice. For import practice: after normal destroy, create an EMPTY private bucket in the console, change bucket_prefix to bucket = "YOUR-EXACT-BUCKET", then terraform import aws_s3_bucket.practice YOUR-EXACT-BUCKET. Review the plan: import only adopts the bucket, companion controls still need apply. Destroy only your adopted training bucket.','Drift appears in plan. Import establishes a binding between one resource address and one remote object.','Discuss why state rm forgets a resource without deleting it; never practice it on shared infrastructure.','S3 requests/storage may incur charges','Lab 04 completed and destroyed')
network='''variable "name" {
  type = string
}
variable "cidr" {
  type    = string
  default = "10.42.0.0/16"
}
resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_hostnames = true
  tags                = { Name = var.name }
}
resource "aws_subnet" "private" {
  for_each = { a = 0, b = 1 }
  vpc_id   = aws_vpc.this.id
  cidr_block = cidrsubnet(var.cidr, 8, each.value)
  availability_zone = data.aws_availability_zones.available.names[each.value]
  tags = { Name = "${var.name}-${each.key}" }
}
data "aws_availability_zones" "available" {
  state = "available"
}
output "vpc_id" {
  value = aws_vpc.this.id
}
output "subnet_ids" {
  value = { for k, v in aws_subnet.private : k => v.id }
}'''
put('modules/network/main.tf',network)
put('modules/network/versions.tf','''terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}''')
lab('06-network','VPC, subnets and dependencies',45,'Build a private network and understand implicit references.',aws+network.replace('variable "name" {\n  type = string\n}','variable "name" {\n  type = string\n  default = "training-network"\n}'),'Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner as in Lab 04. Inspect the references from subnets to VPC. No internet gateway, NAT, compute or public IP is created. Explain why availability-zone names differ between accounts.','One VPC and two private subnets in different available zones.','Change CIDR only after predicting which resources must be replaced.','VPC/subnets have no hourly fee; no compute created','Lab 04 identity setup')
lab('07-modules','Reusable modules and root composition',45,'Pass inputs to a child module and expose outputs.',aws+'''
module "network" {
  source = "../../modules/network"
  name   = "${var.owner}-module-lab"
}
output "vpc_id" {
  value = module.network.vpc_id
}
output "subnets" {
  value = module.network.subnet_ids
}''','Run cp terraform.tfvars.example terraform.tfvars, then edit account_id and owner. Read modules/network/main.tf before init. Notice that root output must explicitly expose child outputs. Change a module input and inspect the plan.','Resource addresses start with module.network.','Create a second module call using a non-overlapping CIDR; inspect and destroy both.','No hourly network components','Lab 06 completed and destroyed')
ssh='''variable "admin_cidr" {
  type = string
  validation {
    condition     = can(regex("^([0-9]{1,3}\\\\.){3}[0-9]{1,3}/32$", var.admin_cidr)) && can(cidrhost(var.admin_cidr, 0))
    error_message = "Use your current public IPv4 address with /32."
  }
}
variable "public_key_path" {
  type = string
}
variable "private_key_path" {
  type      = string
  sensitive = true
  ephemeral = true
}
data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
resource "aws_vpc" "demo" {
  cidr_block = "10.77.0.0/16"
}
resource "aws_subnet" "demo" {
  vpc_id                  = aws_vpc.demo.id
  cidr_block              = "10.77.1.0/24"
  map_public_ip_on_launch = true
}
resource "aws_internet_gateway" "demo" {
  vpc_id = aws_vpc.demo.id
}
resource "aws_route_table" "demo" {
  vpc_id = aws_vpc.demo.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.demo.id
  }
}
resource "aws_route_table_association" "demo" {
  subnet_id      = aws_subnet.demo.id
  route_table_id = aws_route_table.demo.id
}
resource "aws_security_group" "ssh" {
  name_prefix = "training-ssh-"
  vpc_id      = aws_vpc.demo.id
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_key_pair" "demo" {
  key_name_prefix = "training-"
  public_key      = file(pathexpand(var.public_key_path))
}
resource "aws_instance" "demo" {
  ami                         = data.aws_ssm_parameter.ami.value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.demo.id
  vpc_security_group_ids      = [aws_security_group.ssh.id]
  key_name                    = aws_key_pair.demo.key_name
  associate_public_ip_address = true
  metadata_options {
    http_tokens = "required"
  }
  root_block_device {
    encrypted = true
    volume_size = 8
  }
  depends_on = [aws_route_table_association.demo]
}
resource "terraform_data" "configure" {
  triggers_replace = [aws_instance.demo.id, filesha256("${path.module}/welcome.txt")]
  connection {
    type        = "ssh"
    user        = "ec2-user"
    host        = aws_instance.demo.public_ip
    private_key = file(pathexpand(var.private_key_path))
    timeout     = "5m"
  }
  provisioner "file" {
    source      = "${path.module}/welcome.txt"
    destination = "/tmp/welcome.txt"
  }
  provisioner "remote-exec" {
    inline = ["mkdir -p /home/ec2-user/training", "cp /tmp/welcome.txt /home/ec2-user/training/welcome.txt", "cat /home/ec2-user/training/welcome.txt"]
  }
}
output "public_ip" {
  value = aws_instance.demo.public_ip
}'''
lab('08-ssh-provisioners','File and remote-exec provisioners',60,'Copy a file from Windows to EC2 and execute a remote command.',aws+ssh,'''Create ~/.ssh with mkdir -p "$HOME/.ssh". Generate a dedicated SSH key OUTSIDE the repository: ssh-keygen -t ed25519 -f "$HOME/.ssh/terraform-training". For this short classroom demo use a dedicated unencrypted key (empty passphrase); delete it after cleanup, never reuse a personal key. After AWS destroy succeeds, remove only the dedicated key files with rm -f "$HOME/.ssh/terraform-training" "$HOME/.ssh/terraform-training.pub" and unset TF_VAR_private_key_path. Put public_key_path = "~/.ssh/terraform-training.pub" and admin_cidr = "YOUR-PUBLIC-IP/32" in terraform.tfvars with account_id and owner. Run export TF_VAR_private_key_path="$(cygpath -m "$HOME/.ssh/terraform-training")" before plan AND apply. This ephemeral input is not saved in the plan. Run terraform plan/apply with the environment still set. File runs before remote-exec. This SSH example omits host-key pinning for first-contact teaching only; verified host_key or SSM is required for hardened operations. Prefer cloud-init, immutable images and SSM in real deployments.''','Remote console prints welcome.txt; port 22 accepts only your /32.','Change welcome.txt; inspect terraform_data replacement. Contrast remote-exec with EC2 user_data.','EC2, EBS and public IPv4 billed; no free-tier assumption','AWS S3 labs completed; EC2/VPC/SSM parameter read permissions; SSH outbound allowed')
put('labs/03-local-exec/notice.sh', '''#!/usr/bin/env bash\nprintf '%s\\n' "$TRAINING_MESSAGE"''')
put('labs/08-ssh-provisioners/welcome.txt','Hello from a file copied by Terraform.\nThis is an isolated training machine.')
for d in ['04-aws-storage','05-state-drift','06-network','07-modules','08-ssh-provisioners']:
    put('labs/'+d+'/terraform.tfvars.example','account_id = "REPLACE_WITH_12_DIGITS"\nowner = "student01"\naws_region = "ap-south-1"')
put('labs/02-input-output/terraform.tfvars.example','owner = "student01"\nenvironment = "dev"')
put('bootstrap/state/main.tf',aws+s3.replace('force_destroy = false','force_destroy = false\n  lifecycle {\n    prevent_destroy = true\n  }')+'''
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.practice.id
  versioning_configuration {
    status = "Enabled"
  }
}
data "aws_iam_policy_document" "tls" {
  statement {
    effect = "Deny"
    actions = ["s3:*"]
    resources = [aws_s3_bucket.practice.arn, "${aws_s3_bucket.practice.arn}/*"]
    principals {
      type = "*"
      identifiers = ["*"]
    }
    condition {
      test = "Bool"
      variable = "aws:SecureTransport"
      values = ["false"]
    }
  }
}
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.practice.id
  policy = data.aws_iam_policy_document.tls.json
}''')
put('bootstrap/state/terraform.tfvars.example','account_id = "REPLACE_WITH_12_DIGITS"\nowner = "trainer"')
for env in ['dev','stage','prod']:
    put(f'environments/{env}/providers.tf',aws)
    put(f'environments/{env}/backend.tf','terraform {\n  backend "s3" {}\n}')
    put(f'environments/{env}/main.tf',f'''module "network" {{
  source = "../../modules/network"
  name   = "training-{env}"
  cidr   = "10.{ {'dev':42,'stage':43,'prod':44}[env] }.0.0/16"
}}
output "vpc_id" {{
  value = module.network.vpc_id
}}
output "subnet_ids" {{
  value = module.network.subnet_ids
}}''')
    put(f'environments/{env}/terraform.tfvars.example',f'account_id = "REPLACE_WITH_12_DIGITS"\nowner = "platform-team"\naws_region = "ap-south-1"\nenvironment = "{env}"')
    put(f'environments/{env}/state.backend.hcl.example',f'''bucket       = "REPLACE_WITH_BOOTSTRAP_BUCKET"
key          = "{env}/network/terraform.tfstate"
region       = "ap-south-1"
encrypt      = true
use_lockfile = true''')

put('docs/CAPSTONE.md','''# Capstone: production-style foundations

This is a production-style training skeleton, not a complete production platform. The capstone deploys private networking only. Use separate AWS accounts and roles for actual dev/stage/prod. Add reviewed service modules, private connectivity, logging, monitoring, backup, recovery and organization guardrails before a real workload.

1. Trainer authenticates to the sandbox, verifies identity and copies bootstrap/state/terraform.tfvars.example to terraform.tfvars. Set the real account ID and owner.
2. In bootstrap/state run init, validate, plan -out=review.tfplan, inspect, apply. Record terraform output -raw bucket_name. This root intentionally starts with local state; protect its state with encrypted restricted backup outside Git, or migrate to a separately governed organization backend. One trainer owns this root; students do not share local copies.
3. Copy environments/dev/state.backend.hcl.example to state.backend.hcl. Replace bucket and ensure region matches the bootstrap bucket. Run cp terraform.tfvars.example terraform.tfvars and edit account ID/owner.
4. In environments/dev run terraform init -backend-config=state.backend.hcl, validate, plan -out=review.tfplan, inspect and apply. This is a fresh root; there is no local state to migrate. If migrating an existing local-state root, back it up outside Git and use init -migrate-state, inspect the copy prompt and verify the resulting state before discarding backups. Never combine migration and reconfiguration casually.
5. Inspect the state object and .tflock behavior. During an active operation a second operation must wait/fail to acquire the same key lock. Never force-unlock an active run. Give each student a unique key prefix. Separate roots/keys isolate state; they do not provide account-level security isolation.
6. Repeat in stage with a distinct state key and preferably a distinct account. Promote reviewed module code and committed lock files, not state files. Prod requires a separately approved deployment role and protected CI environment.
7. Simulate review: one person opens a change, a second reviews plan replacements, identity, tags and blast radius. Apply the exact reviewed saved plan from the same trusted context. Saved plans contain sensitive data and must not be published as public artifacts.
8. Destroy dev/stage resources using their original backend settings and credentials. Keep the backend until every consumer is destroyed. The bootstrap bucket intentionally has prevent_destroy. Retaining it with protected state is the normal course outcome. Trainer-only final retirement: back up required state, confirm no consumers, review and remove prevent_destroy, explicitly delete every object version and delete marker in the dedicated bucket using the S3 console, then plan/apply destroy from bootstrap/state. Never purge a shared state bucket. Versioned buckets cannot be emptied by deleting current objects alone.

## Backend permissions

Backend role needs s3:ListBucket restricted to environment prefix, s3:GetObject and s3:PutObject on the state key, and s3:GetObject/PutObject/DeleteObject on key.tflock. KMS-encrypted backends also need relevant KMS permissions. Bootstrap provisioning needs separate bucket configuration permissions. AWS provider role permissions are independent of backend permissions. Do not put role credentials into backend files.

## Module contract

modules/network accepts name and cidr; returns vpc_id and subnet_ids. Root owns provider, backend and environment inputs. For a shared registry module add README, examples, tests, semantic tags and a pinned version. Local modules are versioned with this repository. Workspaces share configuration and are not a substitute for separate production accounts.
''')

put('docs/SETUP.md','''# Trainer and student setup — Git Bash on Windows

## AWS account and billing (trainer assisted, 45 minutes)

1. Use a dedicated sandbox account. Open https://aws.amazon.com/ and choose Create an AWS account. Supply a monitored email, account name and the verification requested by the current signup flow. Choose the account plan/support option appropriate for training; review its current terms. Complete contact, payment/identity checks where requested and wait for activation. Signup screens and free-tier offers change: never promise these labs are free.
2. Secure root with a unique password and MFA. Do not create root access keys. Store recovery details securely. Root is only for account administration tasks that require it; sign out before labs.
3. Set billing contacts and a small AWS Budget with email alerts before class. Budget alerts are delayed and do not cap spending. Confirm your region permits the resources and account quotas. Allocate one sandbox/account or isolated owner/state prefix per learner.
4. Trainer provisions workforce access using IAM Identity Center (requires organization/admin setup) and assigns a sandbox permission set. A permission set grants role permissions in the selected account. Students need the start URL, SSO region, account and assigned role. They cannot self-assign permissions.
5. For a standalone account without Identity Center, the account administrator provides an MFA-protected IAM identity that can assume a dedicated sandbox role. A role has a trust policy (who may assume it) AND a permission policy (what it can do). Both must allow the operation; role trust alone grants no service permissions. Avoid AdministratorAccess for a classroom. Trainer should review docs/IAM.md for service/action scope.

## Install (30 minutes)

Terraform: download the Windows AMD64/ARM64 ZIP matching your device from https://developer.hashicorp.com/terraform/install. Verify the published SHA256 checksum against sha256sum before extracting. Extract terraform.exe to a tools folder outside this repo, add that folder to your User PATH through Windows Environment Variables, and reopen Git Bash. Use Terraform >=1.10 and <2.0. Follow organization software policy.

AWS CLI v2: use the official Windows installer at https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html. Install Git for Windows from https://git-scm.com/downloads/win and open Git Bash from the Start menu. All course commands run in Git Bash. Install Python 3 for the repository helper scripts and enable its PATH option. VS Code with the HashiCorp Terraform extension is optional. Reopen terminal.

```bash
terraform version
aws --version
git --version
ssh -V
bash --version
python --version
command -v terraform aws git bash python
```

## Git Bash paths and environment

```bash
pwd
cd /c/Users/YOUR_WINDOWS_USER/terrafrom
ls -la
# Example: verify the downloaded Terraform ZIP in Downloads:
cd ~/Downloads
sha256sum terraform_VERSION_windows_amd64.zip
# Compare with the matching line in the official SHA256SUMS before extracting.
# Return to your repository (replace YOUR_WINDOWS_USER):
cd /c/Users/YOUR_WINDOWS_USER/terrafrom
```

Replace VERSION and the ZIP architecture with the release you downloaded. Use forward slashes and quote paths containing spaces. Git Bash /c/Users/... maps to C:/Users/...; Terraform is a native Windows executable. Use cygpath -m when passing an absolute Bash path through TF_VAR_* to Terraform, for example export TF_VAR_private_key_path="$(cygpath -m "$HOME/.ssh/terraform-training")". Terraform file paths inside .tf/.tfvars should use forward slashes; ~ paths are explicitly expanded with pathexpand in the SSH lab. Git Bash and native Windows AWS tools must use the same Windows user home for ~/.aws and ~/.ssh. Avoid overriding HOME. If AWS CLI rewrites a literal argument beginning with / (such as an SSM parameter path), use MSYS_NO_PATHCONV=1 for that one aws command only. The Terraform provider's API calls do not need this setting.

If a command is missing, inspect PATH and reopen Git Bash; do not download random binaries. CLI must show aws-cli/2. Terraform init installs provider plugins; installing Terraform does not install AWS CLI. Save manually created .sh files with LF line endings in your editor; .gitattributes enforces LF for checked-out shell scripts. Run them with bash script-name.sh, so an executable file bit is not required. Confirm command -v bash resolves Git for Windows Bash before Lab 03.

## Preferred: short-lived SSO credentials

```bash
aws configure sso --profile training
aws sso login --profile training
export AWS_PROFILE="training"
export AWS_REGION="ap-south-1"
aws sts get-caller-identity
```

Enter trainer-supplied SSO session name/start URL/SSO region, approve browser login, select assigned account/role, then default region and JSON output. SSO region can differ from resource region. Confirm the Account and assumed-role ARN with trainer before every AWS lab. Expired session: aws sso login --profile training. AccessDenied: trainer adjusts the role; do not switch to root.

## IAM access-key fallback: administrator controlled only

Programmatic access means authenticating an API/CLI/SDK; it does not require a permanent access key. If SSO is unavailable, trainer creates a dedicated IAM user without console access, assigns minimal permissions to assume the sandbox role, and creates a CLI access key in IAM > Users > selected user > Security credentials > Create access key. Secret appears once. Never paste it into chat, Terraform or Git. Configure interactively outside this repository:

```bash
aws configure --profile training-source
aws configure set role_arn arn:aws:iam::YOUR_ACCOUNT_ID:role/TerraformTraining --profile training
aws configure set source_profile training-source --profile training
aws configure set mfa_serial arn:aws:iam::YOUR_ACCOUNT_ID:mfa/YOUR_MFA_DEVICE --profile training
export AWS_PROFILE="training"
aws sts get-caller-identity
```

Replace placeholders. Source user needs sts:AssumeRole; role must trust it with MFA if configured. Do not add an MFA condition to an EC2 service role. AWS CLI stores profile configuration/keys under your user home .aws directory; protect it. Revoke the key after class and clear shared training PCs.

## Session credential export (Git Bash)

Preferred: keep AWS_PROFILE set and let Terraform use your authenticated role profile. If the exercise requires exported session credentials, export them from that role profile without typing secrets into command history. Do not run set -x or print the captured output.

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
if session_exports="$(aws configure export-credentials --profile training --format env)"; then
  eval "$session_exports"
  unset session_exports
  aws sts get-caller-identity
else
  unset session_exports
  printf '%s' 'Authentication failed. Sign in again before continuing.' >&2
fi
```

This sets AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN for temporary sessions. All three are required together. Exported credentials expire; repeat login/export when needed. Stop if authentication fails. Environment keys can override profile credentials. Clear them before changing profiles or troubleshooting identity:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
unset TF_VAR_private_key_path
aws sts get-caller-identity --profile training
aws sso logout
unset AWS_PROFILE AWS_REGION
```

Use export NAME="value" for the current Bash session and unset NAME to clear it. Never store secrets in .bashrc, .bash_profile, Git, command history or classroom recordings.

''')
put('docs/IAM.md','''# IAM trainer design

Use a dedicated training account, MFA workforce access and temporary sessions. Roles separate trust from service permission. Avoid granting students IAM user/key creation or iam:PassRole merely to complete these labs. Lab 08 deliberately has no EC2 instance role and needs no PassRole.

| Lab | Trainer reviews permissions |
| --- | --- |
| 01–03 | None: local Terraform only |
| 04–05 | S3 CreateBucket/DeleteBucket, ListBucket, bucket location, tags, encryption and public-access-block read/write; import needs reads of the existing bucket |
| 06–07/capstone | EC2 Describe APIs; VPC/subnet create/delete/tag and DNS attribute reads/modification |
| 08 | EC2 VPC/subnet/IGW/route-table/association/security-group/key-pair/instance lifecycle and tag/read APIs; ssm:GetParameter only for the public AMI parameter |
| Bootstrap | S3 bucket creation, tags, encryption, public access, versioning and TLS bucket policy lifecycle |

This is a permission design checklist, not an executable policy. Exact provider API calls can evolve. Trainer tests roles before class, uses CloudTrail/AccessDenied evidence to add narrowly scoped actions, scopes S3 resources to training bucket prefixes, and scopes EC2 writes with region and supported request/resource-tag conditions. Some EC2 Describe/list and create APIs need Resource "*"; evaluate service authorization support before adding resource restrictions. Separate bootstrap admin role, student deploy role and read-only reviewer. Set a permissions boundary/SCP in managed training accounts as appropriate.

Role-assumption exercise: trainer creates TerraformTraining role with a trust relationship allowing the approved source principal to call sts:AssumeRole, with MFA condition for an IAM user; attaches reviewed lab permissions. Trainer grants source principal sts:AssumeRole only on this role. Student configures the role profile in SETUP.md, confirms an assumed-role ARN, then demonstrates a deliberately denied out-of-scope action using a read-only check chosen by trainer. Students never grant themselves administrator access.
''')
iam_extra='''

## Console role creation walkthrough (trainer only)

1. In sandbox IAM > Policies > Create policy > JSON, create TrainingS3Lab using iam/s3-lab-policy.json after reviewing it. This example covers labs 04–05, not bootstrap/network/EC2.
2. IAM > Roles > Create role > Custom trust policy. Paste iam/trust-policy.json after replacing SOURCE_ACCOUNT_ID and SOURCE_USER. It deliberately trusts one IAM source user with MFA. Identity Center access uses its permission-set workflow instead.
3. Attach TrainingS3Lab, name the role TerraformTraining, review and create. Do not attach AdministratorAccess as a shortcut for missing lab actions.
4. On the source user, add the inline policy in iam/assume-role-policy.json after replacing SANDBOX_ACCOUNT_ID. Ensure the source user has an MFA device enrolled. Source key creation follows SETUP.md.
5. Configure the role profile from SETUP.md. Verify get-caller-identity returns assumed-role/TerraformTraining. Run Lab 04. Trainer extends narrowly reviewed service permissions for later labs based on the table above.

The example S3 create action must allow a future training bucket ARN; it does not grant access to arbitrary bucket names. Organization policies, session policies and permissions boundaries can still deny it. A dedicated sandbox and trainer review remain required.
'''
with (ROOT/'docs/IAM.md').open('a',encoding='utf-8') as stream:
    stream.write(iam_extra)
put('iam/trust-policy.json',json.dumps({"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::SOURCE_ACCOUNT_ID:user/SOURCE_USER"},"Action":"sts:AssumeRole","Condition":{"Bool":{"aws:MultiFactorAuthPresent":"true"}}}]},indent=2))
put('iam/assume-role-policy.json',json.dumps({"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"sts:AssumeRole","Resource":"arn:aws:iam::SANDBOX_ACCOUNT_ID:role/TerraformTraining"}]},indent=2))
put('iam/s3-lab-policy.json',json.dumps({"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:CreateBucket","s3:DeleteBucket","s3:GetBucketLocation","s3:ListBucket","s3:GetBucketTagging","s3:PutBucketTagging","s3:GetEncryptionConfiguration","s3:PutEncryptionConfiguration","s3:GetBucketPublicAccessBlock","s3:PutBucketPublicAccessBlock"],"Resource":"arn:aws:s3:::tf-training-*"}]},indent=2))

# The S3 provider reads multiple bucket settings while refreshing its resource.
s3_policy_path = ROOT/'iam/s3-lab-policy.json'
s3_policy = json.loads(s3_policy_path.read_text(encoding='utf-8'))
s3_policy['Statement'][0]['Action'] += ['s3:GetBucket*', 's3:GetLifecycleConfiguration', 's3:GetReplicationConfiguration', 's3:GetAccelerateConfiguration']
put('iam/s3-lab-policy.json', json.dumps(s3_policy, indent=2))

put('docs/REFERENCE.md','''# Terraform language, files and commands

Terraform is declarative infrastructure as code. HCL describes desired objects; providers translate requests to APIs. A provider is a versioned plugin (hashicorp/aws); a module is reusable Terraform configuration (local folder, Git source or registry). The registry is a catalog, not a runtime library import system. terraform_data is built in and needs no external provider. Functions such as cidrsubnet, file, jsonencode and lookup are built into the language.

| File | Purpose / Git rule |
| --- | --- |
| main.tf | Resources/module calls; ordinary naming convention |
| providers.tf, versions.tf | Provider setup and version constraints; ordinary names |
| variables.tf, outputs.tf, locals.tf | Input/output/local declarations; ordinary names |
| backend.tf | Backend declaration; root owns it |
| *.tf | All top-level files in ONE directory load together, not in filename order; subdirectories do not automatically load |
| *.tf.json | JSON representation of Terraform configuration |
| terraform.tfvars, *.auto.tfvars / JSON forms | Automatically loaded input values; ignored here to avoid accidental secret publication |
| *.tfvars.example | Safe sample; copy and edit privately |
| *.backend.hcl | Values passed to init -backend-config; not input variables; ignored |
| .terraform.lock.hcl | Provider versions/checksums: commit after init; not a state lock |
| .terraform/ | Downloaded providers/modules and backend metadata: ignore |
| terraform.tfstate and backups | Resource bindings and possibly secrets: ignore/protect |
| *.tfplan | Saved plan may contain secrets: ignore/protect |
| *.tftest.hcl | Terraform test definitions; real apply tests can cost money |
| .terraformrc / terraform.rc | CLI configuration in user home; never commit credentials |
| override.tf / *_override.tf | Special overrides; avoid in team workflows |

Input precedence, low to high: variable default; TF_VAR_* environment; terraform.tfvars; terraform.tfvars.json; *.auto.tfvars / *.auto.tfvars.json in lexical order; command-line -var and -var-file in supplied order. Sensitive=true hides routine display; values may still be in state/plan. ephemeral=true omits eligible transient inputs from saved artifacts and requires supplying them again for apply.

| Command | Purpose |
| --- | --- |
| init | Initialize backend; install modules/providers; rerun after source/backend changes |
| fmt -recursive | Canonical formatting |
| validate | Check configuration consistency after init, not AWS permissions/quota |
| plan -out=review.tfplan | Refresh, compare state/config and save intended actions |
| show review.tfplan | Inspect additions, changes and replacements |
| apply review.tfplan | Apply saved decisions; no extra confirmation prompt |
| output | Read root outputs; avoid printing sensitive values |
| console | Evaluate expressions interactively |
| state list / state show ADDRESS | Inspect resource bindings |
| plan -refresh-only | Review observed drift; does not repair infrastructure |
| import ADDRESS ID | Bind an existing remote object to configuration |
| plan -destroy -out=cleanup.tfplan | Review destruction before applying saved cleanup plan |

References create implicit dependencies. Use depends_on only for hidden ordering. count uses numeric addresses; for_each uses stable keys. lifecycle.prevent_destroy blocks planned destroy while present in configuration but is not an AWS deletion policy. create_before_destroy can require spare quota and unique naming. A moved block preserves bindings when refactoring addresses; do not rename resources blindly. Do not use -target as a normal deployment pattern.
''')
put('docs/TRAINER.md','''# Delivery plan and assessment

Audience: first-time DevOps learners comfortable opening a terminal. Three days, about 16 guided hours plus breaks and practice. Read SETUP.md and run all cloud labs in your own sandbox before teaching. AWS signup activation can take time: arrange accounts and quotas before day one. Students each need an owner identifier and separate state directory/key.

| Day | Sequence | Trainer checkpoints |
| --- | --- | --- |
| 1 | Account/MFA/budget 45m; tools/auth 60m; language/files 30m; labs 01–03 105m; Q&A/practice 60m | Correct identity; explain init vs plan; second plan is clean |
| 2 | IAM role exercise 45m; labs 04–07 180m; state/diagram review 30m; cleanup 30m | Private S3; no credential literals; explain drift/import and module addresses |
| 3 | Lab 08 60m; backend bootstrap 45m; dev/stage capstone 90m; peer review 45m; final assessment and cleanup 60m | Distinct state keys; locking; reviewed plan; all disposable resources removed |

For each lab: explain diagram (5m), show file creation (5m), students read/copy code (5m), predict plan (5m), execute and verify, then change one input and explain impact. Use the HTML expanders to display complete source files. Students can recreate files manually in their own empty lab directory or use supplied folders; never apply a second root to resources managed by another student.

Ask before apply: Which account/region? Which root/backend/key? How many additions/replacements/deletions? Which costs continue after class? Ask after apply: What changed in state? Why is second plan empty? Ask before destroy: Who owns these resources and does any other root depend on them?

Assessment (100 points): identity/MFA/no keys in Git 20; lifecycle and drift explanation 20; typed variables and outputs 15; reusable module and dependency explanation 15; backend locking/isolation 15; provisioner location/risks and complete cleanup 15. Pass >=80 AND no credential exposure AND confirmed cleanup. Learner submits code, sanitized command outcomes and architecture explanation, never state or saved plans.

Final exercise: add a second private network through the reusable module using a unique CIDR and state key. Peer predicts plan; learner applies, proves no changes, introduces a tag change, restores it, then destroys only their networks. Production discussion: identify missing telemetry, recovery, controls and workload requirements rather than claiming this skeleton is deploy-ready.

Troubleshooting: InvalidClientTokenId/ExpiredToken -> remove stale env keys and reauthenticate; AccessDenied -> compare actual role/account and trainer-reviewed permissions; init network failure -> verify proxy/registry access; wrong account -> account guard stops provider; bucket nonempty -> delete only lab objects/versions or retain bucket; SSH timeout -> verify /32, public route/IP, outbound 22 and instance readiness; key error -> check path and EC2 username; state lock -> locate active run and wait, never force-unlock casually; unexpected replacement -> stop and inspect immutable attributes and address changes. Failed apply may leave billable resources: inspect state and AWS console, correct failure, then destroy from the same root.
''')
put('docs/GIT-SAFETY.md','''# Publish code without credentials in the repository

Private AWS credentials remain in user-home profiles or temporary environment variables. Git pushes still require Git-host authentication; use Git Credential Manager/browser login or an SSH agent. A repository can contain zero credentials, but a private/authorized push cannot be unauthenticated. Never put tokens in remote URLs or Terraform.

```bash
git status --short
python scripts/check_repo.py
git add .
git diff --cached --stat
git diff --cached
git status --ignored --short
git commit -m "Add trainer-ready Terraform AWS course"
git branch -M main
# Create an empty repository in your Git host, then substitute its clean HTTPS URL:
git remote add origin https://github.com/YOUR_ORG/YOUR_REPO.git
git push -u origin main
```

If origin already exists, inspect git remote -v before updating it. Commit .terraform.lock.hcl generated after init in each root. Do not commit tfvars, private keys, state, backend settings or saved plans. The included scanner is a useful basic guard, not proof that arbitrary secrets are absent; use your Git host secret scanning and a maintained full-history scanner before publication. Review all staged diffs. No push is attempted by this course generator.

If credentials were committed, revoke/rotate first, then remove the secret from tracked files and coordinate history rewriting with your team. Adding .gitignore does not untrack files or erase history. Avoid printing secrets while investigating. Use git ls-files to review tracked paths. Terraform state and saved plans are sensitive even when outputs are marked sensitive.
''')
put('scripts/check_repo.py','''"""Basic source guard. Scans tracked plus non-ignored files; never prints matched secrets."""
from pathlib import Path
import re, subprocess, sys
root = Path(__file__).resolve().parents[1]
result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root, capture_output=True, check=True)
paths = set(result.stdout.decode().split("\\0")) - {""}
bad = []
key_pattern = re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
for name in sorted(paths):
    p = root / name
    if not p.is_file():
        continue
    if re.search(r"(?:^|/)(?:\\.terraform|\\.aws)/|\\.tfstate(?:\\.|$)|\\.(?:tfplan|pem|ppk|pfx)$", name) or (name.endswith((".tfvars", ".tfvars.json", ".backend.hcl"))):
        bad.append((name, "sensitive artifact path"))
        continue
    content = p.read_text(encoding="utf-8", errors="replace")
    if key_pattern.search(content):
        bad.append((name, "possible AWS key or private key"))
if bad:
    for name, reason in bad:
        print(f"BLOCKED: {name}: {reason}")
    sys.exit(1)
print(f"Basic credential/artifact checks passed for {len(paths)} files. Review staged diffs and history separately.")
''')
put('.github/workflows/validate.yml','''name: Terraform source validation
on: [push, pull_request]
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: '1.10.5'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python scripts/check_repo.py
      - run: python scripts/check_html.py
      - run: terraform fmt -check -recursive
      - name: Validate every root without AWS credentials
        shell: bash
        run: |
          for root in labs/* bootstrap/state environments/*; do
            terraform -chdir="$root" init -backend=false -input=false
            terraform -chdir="$root" validate
          done
''')
put('README.md','''# Terraform AWS — zero to production-style foundations

Start with **[the offline HTML lab guide](docs/index.html)** (open in a browser). All source files are included. No AWS deployment is performed by repository generation.

Three days of trainer-led Git Bash on Windows practice: account/MFA/billing, IAM roles and programmatic access, AWS CLI/session export, Terraform setup and language, lifecycle, inputs/outputs, local-exec, private S3, state/drift/import, networking, modules, file/remote-exec and S3 locked remote state.

- [Setup and credentials](docs/SETUP.md)
- [Trainer timing, checkpoints and assessment](docs/TRAINER.md)
- [Language and file reference](docs/REFERENCE.md)
- [IAM design](docs/IAM.md)
- [Capstone and backend retirement](docs/CAPSTONE.md)
- [Safe Git publishing](docs/GIT-SAFETY.md)

`labs/` contains independent roots; `modules/` reusable children; `environments/dev|stage|prod/` separate root/state compositions; `bootstrap/state/` owns the backend. Each lab README gives execution, expected results, practice and cleanup. Start with labs/01-lifecycle, which needs no AWS account.

Run `bash scripts/validate.sh` in Git Bash for formatting, HTML, basic credential checks and Terraform validation without AWS credentials. CI repeats source checks. Commit provider lock files after initialization. `python scripts/build_course.py` regenerates teaching files/HTML; it overwrites generated source files, so update this generator when changing course content.

Terraform >=1.10, <2; AWS provider ~>6.0. AWS labs incur possible charges, especially Lab 08 compute, EBS and public IPv4. This is a training skeleton; actual production requires organization-specific security, recovery, observability and workload design.
''')

# Format before embedding complete sources, when the official CLI is available.
terraform_exe = os.environ.get('COURSE_TERRAFORM') or shutil.which('terraform')
if terraform_exe:
    subprocess.run([terraform_exe, 'fmt', '-recursive'], cwd=ROOT, check=True, capture_output=True)

# Offline HTML: readable without CDN, Mermaid or a web server.
def diagram(title, nodes, caption):
    width=920; n=len(nodes); box=(width-40-(n-1)*28)/n
    marker_id = 'arrow-' + title[:2]
    rects=[]
    for i,(a,b) in enumerate(nodes):
        x=20+i*(box+28)
        rects.append(f'<rect x="{x}" y="24" width="{box}" height="86" rx="12"/><text x="{x+box/2}" y="58" text-anchor="middle">{escape(a)}</text><text class="sub" x="{x+box/2}" y="84" text-anchor="middle">{escape(b)}</text>')
        if i<n-1:rects.append(f'<path d="M{x+box+3} 67 h20" marker-end="url(#{marker_id})"/>')
    return f'<figure><h3>{title}</h3><svg role="img" aria-label="{escape(title)}" viewBox="0 0 920 136"><defs><marker id="{marker_id}" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6"/></marker></defs>{"".join(rects)}</svg><figcaption>{caption}</figcaption></figure>'
diagrams=[
diagram('01 · Identity and trust',[('Student + MFA','workforce identity'),('SSO / source user','temporary session'),('Sandbox role','trust + permissions'),('AWS APIs','account guard')],'Authentication proves who you are. Role trust allows assumption; attached permissions control API actions. Terraform reads the existing credential chain; secrets never enter source code.'),
diagram('02 · Terraform lifecycle',[('Write HCL','desired configuration'),('init + validate','plugins and checks'),('plan + review','compare state / AWS'),('apply → state','record bindings')],'Plan refreshes observations and predicts actions. Apply executes reviewed decisions and updates state. A second plan should report no changes. Destroy is a separately reviewed plan.'),
diagram('03 · State and collaboration',[('Student / CI','one active writer'),('S3 backend','environment state key'),('Native .tflock','serialize operations'),('Version history','recovery evidence')],'Every environment/student gets a unique state key. Versioning helps recovery; locking prevents competing Terraform writers, but does not stop manual AWS edits. Never delete state to fix drift.'),
diagram('04 · Capstone composition',[('dev / stage / prod','separate roots/accounts'),('network module','name + CIDR input'),('VPC','private address space'),('Two private subnets','different zones')],'Root modules own backend and provider identity. The child module returns IDs. No NAT, internet gateway or compute is provisioned by the capstone; private workload connectivity is a future design decision.'),
diagram('05 · SSH provisioner lab',[('Windows PC','local-exec runs here'),('Internet + /32 SG','SSH port 22'),('EC2 ec2-user','file copies payload'),('remote-exec','runs on EC2')],'Lab 08 creates a public subnet, route table, internet gateway, public IPv4 and encrypted EBS. The file provisioner copies welcome.txt first; remote-exec then copies and prints it. This topology is intentionally limited to the isolated demo.')]
diagrams[3] = '''<figure><h3>04 · Capstone architecture and module boundaries</h3><svg role="img" aria-label="Environment roots call network module; VPC contains private subnets in two availability zones; state stored separately in S3" viewBox="0 0 920 330"><rect x="15" y="20" width="245" height="112" rx="12"/><text x="137" y="55" text-anchor="middle">Environment root</text><text class="sub" x="137" y="80" text-anchor="middle">dev / stage / prod</text><text class="sub" x="137" y="103" text-anchor="middle">provider + inputs + backend</text><path d="M260 76 H320"/><text class="sub" x="290" y="62" text-anchor="middle">calls</text><rect x="325" y="20" width="575" height="290" rx="12"/><text x="612" y="52" text-anchor="middle">network module → VPC</text><text class="sub" x="612" y="76" text-anchor="middle">No internet / NAT / compute in capstone</text><rect x="355" y="110" width="240" height="165" rx="12"/><text x="475" y="148" text-anchor="middle">Availability zone A</text><text class="sub" x="475" y="182" text-anchor="middle">Private subnet a</text><text class="sub" x="475" y="210" text-anchor="middle">10.42.0.0/24 (dev)</text><text class="sub" x="475" y="244" text-anchor="middle">Local VPC route only</text><rect x="625" y="110" width="240" height="165" rx="12"/><text x="745" y="148" text-anchor="middle">Availability zone B</text><text class="sub" x="745" y="182" text-anchor="middle">Private subnet b</text><text class="sub" x="745" y="210" text-anchor="middle">10.42.1.0/24 (dev)</text><text class="sub" x="745" y="244" text-anchor="middle">Local VPC route only</text><path d="M137 132 V190"/><rect x="15" y="195" width="245" height="115" rx="12"/><text x="137" y="229" text-anchor="middle">Separate S3 backend</text><text class="sub" x="137" y="254" text-anchor="middle">Environment-specific state key</text><text class="sub" x="137" y="279" text-anchor="middle">Versioning + native lockfile</text></svg><figcaption>Root modules own identity and state. The child module owns VPC and subnet resources and returns their IDs. AWS creates default network components with the VPC; Terraform manages only declared resources. Separate state does not replace separate production accounts.</figcaption></figure>'''
sections=[]
for name,title in [('SETUP','Account, tools and authentication'),('REFERENCE','Language, libraries and file types'),('IAM','IAM trainer design'),('TRAINER','Delivery and assessment'),('CAPSTONE','Remote state and final structure'),('GIT-SAFETY','Credential-safe publication')]:
    # Plain-text rendering preserves exact Git Bash syntax and complete instructions offline.
    sections.append(f'<section id="{name.lower()}"><span class="eyebrow">TRAINER HANDBOOK</span><h2>{title}</h2><pre class="prose">{escape((ROOT/f"docs/{name}.md").read_text(encoding="utf-8"))}</pre></section>')
labshtml=[]
for i,item in enumerate(labdata):
    slug=item['slug']; sources=[]
    for p in sorted((ROOT/'labs'/slug).iterdir()):
        if p.suffix in ['.tf','.txt','.sh'] or p.name.endswith('.example'):
            sources.append(f'<details><summary>Create {escape(p.name)} — complete source</summary><pre><code>{escape(p.read_text(encoding="utf-8"))}</code></pre></details>')
    labshtml.append(f'''<section id="lab-{i+1}"><span class="eyebrow">LAB {i+1:02} · {item['minutes']} MIN</span><h2>{escape(item['title'])}</h2><p>{escape(item['goal'])}</p><div class="note">Prerequisite: {escape(item['prereq'])}<br>Cost: {escape(item['cost'])}</div><h3>1. Create the working directory and files</h3><p>Use the supplied labs/{slug} directory, or recreate these files in a separate empty lab folder. All .tf files in that directory load together.</p>{''.join(sources)}<h3>2. Execute, observe and clean up</h3><pre class="prose">{escape((ROOT/'labs'/slug/'README.md').read_text(encoding='utf-8'))}</pre><label class="complete"><input type="checkbox" data-lab="{slug}"> Completed, verified and cleaned up</label></section>''')
tree='\n'.join(['terraform-training/','├── docs/                   HTML + trainer handbooks','├── labs/01…08/             independent student roots','├── modules/network/        reusable child module','├── bootstrap/state/        protected backend bucket','├── environments/','│   ├── dev/                separate backend key','│   ├── stage/              separate backend key','│   └── prod/               separate account in real use','├── scripts/                generator and basic secret guard','└── .github/workflows/      credential-free validation'])
nav=''.join(f'<a href="#lab-{i+1}">{i+1:02} {escape(x["title"])}</a>' for i,x in enumerate(labdata))
html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Terraform AWS | Trainer Lab Academy</title><style>
:root{--ink:#183043;--brand:#075e69;--paper:#f3f6f8;--line:#d6e1e5}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,sans-serif}aside{position:fixed;inset:0 auto 0 0;width:275px;background:#102c3b;color:white;padding:26px 20px;overflow:auto}aside strong{font-size:22px}aside a{display:block;color:#dcebef;text-decoration:none;padding:7px 0;font-size:14px}main{margin-left:275px;max-width:1250px;padding:36px 44px}header{padding:42px;border-radius:20px;background:linear-gradient(130deg,#075e69,#173a57);color:white}h1{font-size:44px;line-height:1.12;margin:14px 0}h2{font-size:29px;line-height:1.25}h3{font-size:19px}.eyebrow{font-size:12px;font-weight:800;letter-spacing:2px;color:#087887}header .eyebrow{color:#b6f0da}section{background:white;padding:32px;margin:26px 0;border-radius:16px;border:1px solid var(--line);scroll-margin-top:18px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#102c3b;color:#e6f2f5;padding:22px;border-radius:10px;font:13px/1.65 Consolas,monospace}pre.prose{background:#f6f8fa;color:#183043;font:14px/1.75 Consolas,monospace}details{border:1px solid var(--line);border-radius:9px;margin:12px 0;padding:12px}summary{cursor:pointer;font-weight:650}.note{background:#eaf5f0;border-left:4px solid #148566;padding:16px}figure{margin:24px 0;padding:22px;background:#f7fafb;border:1px solid var(--line);border-radius:12px}svg{width:100%;height:auto}svg rect{fill:#e0f1ee;stroke:#0d6b70;stroke-width:1.5}svg text{font:15px system-ui;fill:#183043;font-weight:700}svg text.sub{font-size:12px;font-weight:400}svg path{stroke:#087887;stroke-width:2;fill:#087887}figcaption{font-size:14px}button{cursor:pointer;background:#e2f3eb;color:#173a43;border:0;border-radius:7px;padding:10px 16px;margin:8px}.complete{display:block;background:#eaf5f0;padding:14px}a{color:#087887}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.metric{padding:18px;border-radius:12px;background:#ffffff18}footer{padding:25px;font-size:13px}@media(max-width:850px){aside{position:static;width:auto;max-height:300px}main{margin:0;padding:18px}h1{font-size:34px}header,section{padding:23px}.grid{grid-template-columns:1fr}}@media print{aside,button,.complete{display:none}main{margin:0;max-width:none;padding:0}section,figure{break-inside:avoid;border-radius:0}details{display:block}header{background:white;color:#183043}pre{background:#f6f8fa;color:#183043}a{color:inherit}}
</style></head><body><aside><strong>Terraform Academy</strong><p>Trainer edition · AWS / Windows / Git Bash</p><a href="#overview">Course map & diagrams</a><a href="#setup">Account & credentials</a><a href="#reference">Language & file reference</a><a href="#iam">IAM design</a>'''+nav+'''<a href="#capstone">Capstone / remote state</a><a href="#trainer">Trainer assessment</a><a href="#git-safety">Publish safely</a><a href="#sources">Official references</a></aside><main><header><span class="eyebrow">ZERO TO PRODUCTION-STYLE FOUNDATIONS</span><h1>Learn it. Build it.<br>Explain every change.</h1><p>A complete trainer-led Terraform and AWS course, with runnable source, diagrams, expected results and cleanup.</p><div class="grid"><div class="metric">3 days<br><b>Guided training</b></div><div class="metric">8 labs + capstone<br><b>Local → AWS → team workflow</b></div><div class="metric">No embedded keys<br><b>Temporary identity first</b></div></div><button onclick="window.print()">Print / save as PDF</button></header><section id="overview"><span class="eyebrow">START HERE</span><h2>The learning journey</h2><p>Read account and Windows setup first. Labs 01–03 are local and need no AWS resources. Labs 04–08 are independent AWS exercises. Finish with a protected remote-state backend and environment roots. Every learner predicts a plan, applies it, proves convergence, explains the result and cleans up.</p><div class="note">AWS labs can incur charges. Confirm account, region, owner and state key before applying. Budget alerts do not stop spending. This repository does not deploy anything by being opened.</div>'''+''.join(diagrams)+f'<h3>Repository structure</h3><pre>{escape(tree)}</pre></section>'+''.join(sections[:3])+''.join(labshtml)+''.join(sections[3:])+'''<section id="sources"><h2>Official references</h2><p>Reviewed 7 November 2026. Use official documentation for changing signup flows, supported releases, provider arguments and pricing.</p><ul><li><a href="https://developer.hashicorp.com/terraform/install">Terraform installation</a></li><li><a href="https://developer.hashicorp.com/terraform/language">Terraform language</a></li><li><a href="https://registry.terraform.io/providers/hashicorp/aws/latest/docs">AWS provider reference</a></li><li><a href="https://developer.hashicorp.com/terraform/language/backend/s3">S3 backend and native locking</a></li><li><a href="https://developer.hashicorp.com/terraform/language/provisioners">Provisioners and alternatives</a></li><li><a href="https://docs.aws.amazon.com/accounts/latest/reference/manage-acct.html">AWS account management</a></li><li><a href="https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html">AWS CLI SSO configuration</a></li><li><a href="https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html">AWS CLI installation</a></li><li><a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html">IAM best practices</a></li></ul></section><footer>Trainer edition · Code is supplied for supervised sandbox practice. Completion checkboxes are saved in this browser when local storage is available.</footer></main><script>document.querySelectorAll('[data-lab]').forEach(box=>{try{box.checked=localStorage.getItem('tf-course-'+box.dataset.lab)==='true'}catch(e){}box.addEventListener('change',()=>{try{localStorage.setItem('tf-course-'+box.dataset.lab,box.checked)}catch(e){}})});</script></body></html>'''
put('docs/index.html',html)
print(f'Generated {len(labdata)} labs, handbook, diagrams, modules and environment roots.')
