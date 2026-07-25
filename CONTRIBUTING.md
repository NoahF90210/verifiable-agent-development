# Contributing

## Scope

Contributions should improve the sanitized reference implementation, deterministic checks, examples, or public documentation.
Do not add private prompts, messages, memory, credentials, contact details, personal resume data, proprietary code, or personal filesystem paths.

## Development setup

Use Python 3.10 or newer.
The runtime implementation has no third-party dependencies.

Run the complete local check set from the repository root.

```bash
python3 -m unittest discover -s tests -v
python3 -m vadf validate examples/verified_handoff.json
python3 scripts/check_markdown_links.py
python3 scripts/check_publication_rules.py
```

The invalid example must fail with exit code `1`.

```bash
python3 -m vadf validate examples/invalid_handoff.json
```

## Change requirements

- Keep one implementation owner per active worktree.
- Add or update tests for validator behavior changes.
- Keep examples sanitized and deterministic.
- Write each full Markdown sentence on its own physical line.
- Do not use em dashes.
- Support every public claim with inspectable repository evidence or remove it from public documentation.
- Use `artifact:<id>`, `check:<id>`, or `path:<repository-relative-path>` for claim evidence references.
- Treat manifest commands, outcomes, evidence descriptions, recovery notes, and privacy-review records as author attestations until independently established.
- Do not add invented metrics, fake logs, private application-history claims, or placeholder verification output.

## Pull request evidence

A proposed change should identify changed files, exact commands actually run, observed outcomes, privacy-review results, claim-review results, and remaining caveats.
A passing command is evidence only when it was actually run and only for the behavior that command checks.
A manifest record of that command remains an attestation until independently repeated or otherwise established.
Human review remains required before acceptance.
