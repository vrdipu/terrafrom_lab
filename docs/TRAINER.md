# Delivery plan and assessment

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
