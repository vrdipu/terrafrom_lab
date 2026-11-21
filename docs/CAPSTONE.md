# Capstone: production-style foundations

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
