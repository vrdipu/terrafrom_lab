# Validation record

Checked 7 November 2026 with Terraform 1.10.5 on Windows AMD64 and AWS provider 6.72.0.

- All 12 roots initialized with backend disabled and passed `terraform validate`: eight labs, backend bootstrap, and dev/stage/prod.
- Labs 01–03 passed actual local apply, a no-change plan with detailed exit code 0, and destroy. Local-exec printed its expected message.
- After switching the course to Git Bash on Windows, the Bash local-exec implementation passed apply, a no-change plan and destroy again from Git Bash. Both shell scripts passed `bash -n` syntax checks.
- `terraform fmt -check -recursive` passed.
- HTML structural checks passed: eight lab sections, five inline SVG diagrams, unique IDs and valid internal navigation targets.
- Basic repository secret/artifact guard passed. This does not replace full-history secret scanning or human diff review.
- Nine AWS root provider lock files contain matching provider hashes and the signed-registry package checksums, supporting normal installation on other platforms.

AWS credentials were not used and AWS resources were not deployed. Account signup, IAM policy behavior, service quotas, live SSH, remote locking and cloud cleanup require the trainer's sandbox rehearsal before class. HTML checks are structural; no browser screenshot review is claimed. No Git remote was configured and no push was attempted.

Repeat source checks in Git Bash on Windows with `bash scripts/validate.sh` after installing Terraform/Python/Git. Run `python scripts/check_html.py` for guide checks. CI repeats source validation on Linux; it does not run local-exec or cloud applies.
