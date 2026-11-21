# IAM trainer design

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


## Console role creation walkthrough (trainer only)

1. In sandbox IAM > Policies > Create policy > JSON, create TrainingS3Lab using iam/s3-lab-policy.json after reviewing it. This example covers labs 04–05, not bootstrap/network/EC2.
2. IAM > Roles > Create role > Custom trust policy. Paste iam/trust-policy.json after replacing SOURCE_ACCOUNT_ID and SOURCE_USER. It deliberately trusts one IAM source user with MFA. Identity Center access uses its permission-set workflow instead.
3. Attach TrainingS3Lab, name the role TerraformTraining, review and create. Do not attach AdministratorAccess as a shortcut for missing lab actions.
4. On the source user, add the inline policy in iam/assume-role-policy.json after replacing SANDBOX_ACCOUNT_ID. Ensure the source user has an MFA device enrolled. Source key creation follows SETUP.md.
5. Configure the role profile from SETUP.md. Verify get-caller-identity returns assumed-role/TerraformTraining. Run Lab 04. Trainer extends narrowly reviewed service permissions for later labs based on the table above.

The example S3 create action must allow a future training bucket ARN; it does not grant access to arbitrary bucket names. Organization policies, session policies and permissions boundaries can still deny it. A dedicated sandbox and trainer review remain required.
