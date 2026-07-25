# Examples Learning Path

Start with [`verified_handoff.json`](verified_handoff.json).
It shows exclusive worktree ownership, identified repository-relative artifacts, recorded passed checks, structured evidence references, claim statuses, recovery attestations, privacy-review attestations, and one accepted limitation.

Validate its structural contract with this command.

```bash
python3 -m vadf validate examples/verified_handoff.json
```

The command should print `CONTRACT VALID` and an attestation notice.
The result does not mean that the validator executed the recorded commands, reproduced the outcomes, inspected evidence content, or performed the privacy review.

Next, inspect [`invalid_handoff.json`](invalid_handoff.json).
It deliberately contains an invalid schema version, ambiguous identifiers, unsafe paths, failed recorded verification, a blocked claim marked for output, incomplete risk records, invalid recovery state, and a failed privacy-review record.

Run the invalid case and inspect the complete error list.

```bash
python3 -m vadf validate examples/invalid_handoff.json
```

The invalid command should return exit code `1`.
The example is valid JSON so the output demonstrates contract failures rather than parser failures.
Malformed JSON, duplicate object keys, and non-UTF-8 input return exit code `2` before contract validation.

Read the [manifest contract](../docs/manifest-contract.md) for field-level rules and attestation boundaries.
Read the [architecture](../docs/architecture.md) for the role and state boundaries behind the format.
