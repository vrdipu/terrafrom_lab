# Terraform AWS — zero to production-style foundations

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
