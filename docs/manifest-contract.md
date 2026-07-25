# Manifest Contract

## Purpose

The manifest is a compact handoff record for ownership, artifacts, recorded checks, claim status, recovery, privacy review, and residual risk.
The CLI checks JSON input safety, structure, allowed values, cross-references, and status consistency.

> **Attestation boundary:** verification commands, recorded outcomes, evidence descriptions, recovery notes, and privacy-review records are statements supplied by the manifest author.
> The validator does not execute those commands, reproduce those outcomes, inspect evidence content, or independently perform the privacy review.

Run the validator with this command.

```bash
python3 -m vadf validate examples/verified_handoff.json
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The manifest is `CONTRACT VALID` for schema version `1.0`. |
| `1` | The JSON input is readable, but one or more contract rules fail. |
| `2` | The file is unreadable, non-UTF-8, malformed JSON, or contains a duplicate object key at any nesting level. |

Duplicate object keys are rejected before contract validation because standard JSON object decoding would otherwise discard an earlier value silently.

## Top-level fields

| Field | Contract |
| --- | --- |
| `schema_version` | Must equal `1.0`. |
| `handoff_id` | Must be a lowercase identifier with 2 to 64 allowed characters. |
| `implementation_owner` | Must identify one worker handle and one repository-relative worktree with exclusive ownership. |
| `artifacts` | Must contain at least one uniquely identified repository-relative artifact record. |
| `verification` | Must contain at least one check attested as passed and an overall recorded `passed` status. |
| `claims` | Must contain at least one claim with a status and evidence-reference list. |
| `residual_risks` | Must be an array, which may be empty when no residual risk is recorded. |
| `recovery` | Must record same-session and same-worktree recovery or state that recovery was not needed. |
| `privacy_review` | Must contain a `passed` attestation and at least one recorded review check. |

Unknown fields are rejected at every object level.
This rule makes accidental schema drift visible to the implementation owner and reviewer.

## Ownership rules

The owner record contains `role`, `worker_handle`, `worktree`, and `exclusive`.
The worker handle is an opaque public-safe identifier rather than a private process or filesystem detail.
The worktree uses a sanitized repository-relative path.
The `exclusive` value must be `true`.

## Artifact rules

Each artifact contains `id`, `path`, `kind`, `status`, and `description`.
Artifact identifiers and paths must both be unique.
Paths must be repository-relative, use forward slashes, and exclude empty, current, or parent path segments.
Allowed kinds are `configuration`, `documentation`, `example`, `report`, `source`, and `test`.
Allowed statuses are `created`, `changed`, and `inspected`.

## Verification-record rules

Each verification record contains an identifier, exact command string, recorded outcome, and human-readable evidence attestation.
Every recorded outcome must be `passed`, and the overall recorded status must also be `passed`.
The validator treats these values as attestations and does not execute the command string.
A failed or unrun check belongs in an in-progress record rather than a contract-valid handoff.

## Evidence-reference and status-consistency rules

Each claim contains an identifier, text, status, evidence-reference list, and `included_in_output` flag.
A `supported` claim requires at least one evidence reference.
A `limited` claim requires an explicit `limitation` string.
A `blocked` claim must have `included_in_output` set to `false`.

Every evidence entry must use one of these forms.

- `artifact:<id>` must reference an artifact identifier declared in the same manifest.
- `check:<id>` must reference a verification-check identifier declared in the same manifest.
- `path:<repository-relative-path>` must contain a safe repository-relative path.

These rules form an evidence-reference and status-consistency gate.
They prevent dangling identifiers, unsafe path references, empty supported-claim records, missing limitations, and blocked claims marked for output.
They do not determine whether a referenced artifact, check, or path semantically proves the claim.
Human review must inspect the actual evidence and wording.

## Privacy-review records

The privacy-review object contains a recorded status and one or more check descriptions.
The status must be `passed` for a contract-valid handoff.
The validator checks the record's shape and status only.
It does not perform the described privacy checks or prove that they occurred.

## Residual risk rules

Each risk contains an identifier, description, disposition, and mitigation.
Allowed dispositions are `accepted`, `mitigated`, and `open`.
Open risks are permitted because a handoff should expose uncertainty rather than erase it.

## Examples

- [`verified_handoff.json`](../examples/verified_handoff.json) satisfies the structural contract.
- [`invalid_handoff.json`](../examples/invalid_handoff.json) intentionally violates multiple contract rules.
- [`examples/README.md`](../examples/README.md) provides a short learning path.
