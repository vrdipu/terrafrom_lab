# Trainer and student setup — Git Bash on Windows

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
