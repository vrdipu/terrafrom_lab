"""Basic source guard. Scans tracked plus non-ignored files; never prints matched secrets."""
from pathlib import Path
import re, subprocess, sys
root = Path(__file__).resolve().parents[1]
result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root, capture_output=True, check=True)
paths = set(result.stdout.decode().split("\0")) - {""}
bad = []
key_pattern = re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
for name in sorted(paths):
    p = root / name
    if not p.is_file():
        continue
    if re.search(r"(?:^|/)(?:\.terraform|\.aws)/|\.tfstate(?:\.|$)|\.(?:tfplan|pem|ppk|pfx)$", name) or (name.endswith((".tfvars", ".tfvars.json", ".backend.hcl"))):
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
