# Repository Instructions

Build and maintain a sanitized, people-facing case study of a verifiable multi-agent software-development framework.
Keep public documentation separate from implementation instructions and task artifacts.

## Required commands

Run these commands from the repository root before completion.

```bash
python3 -m unittest discover -s tests -v
python3 -m vadf validate examples/verified_handoff.json
python3 scripts/check_markdown_links.py
python3 scripts/check_publication_rules.py
```

Run the deliberately invalid example separately and confirm exit code `1`.

```bash
python3 -m vadf validate examples/invalid_handoff.json
```

## Constraints

- Use one implementation owner per isolated Git worktree.
- Use Python standard library where practical.
- Add tests for validator behavior changes.
- Keep examples deterministic and sanitized.
- Do not include secrets, credentials, personal filesystem paths, private messages, raw prompts, contacts, private memory, personal resume data, or private repository contents.
- Keep every public claim supported by inspectable repository evidence.
- Treat manifest verification and privacy records as author attestations rather than executed proof.
- Require claim evidence references to use declared artifact or check identifiers or safe repository-relative paths.
- Write each full Markdown sentence on its own physical line.
- Never use em dashes.
- Do not claim private application history, benchmark performance, measured speed, defect reduction, cost savings, accuracy gains, users, revenue, or production deployment.
- Do not commit generated caches, logs, local environments, or task artifacts.
