# Publish code without credentials in the repository

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
