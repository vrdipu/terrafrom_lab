# Terraform language, files and commands

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
