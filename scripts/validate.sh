#!/usr/bin/env bash
# Run from Git Bash on Windows or Bash on Linux/macOS. No AWS credentials needed.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
terraform_bin="${COURSE_TERRAFORM:-terraform}"
python scripts/check_repo.py
python scripts/check_html.py
"$terraform_bin" fmt -check -recursive
for course_root in labs/* bootstrap/state environments/*; do
  printf 'Validating %s\n' "$course_root"
  "$terraform_bin" "-chdir=$course_root" init -backend=false -input=false -no-color
  "$terraform_bin" "-chdir=$course_root" validate -no-color
done
