# Case Study Policy: Resume Optimizer

## Scope

This document presents a sanitized architectural scenario for applying the framework to resume generation.
The public repository does not include a resume optimizer, resume data, PDF renderer, private prompts, employer contacts, or evidence of private execution history.
Claim review and PDF QA below are proposed policies, not implemented features.

## Risks

Resume generation creates two distinct risks.
A language model can introduce a persuasive claim without an approved evidence reference.
A technically readable PDF can still contain clipped text, missing content, or an unintended page count.

Claim review and document QA address separate risks; both are required.

## Proposed supervised flow

1. The human supplies the target role and approves the evidence sources that may be used.
2. The supervisory agent decomposes evidence selection, content generation, rendering, and QA into bounded tasks.
3. One implementation owner works inside one isolated worktree.
4. Generated statements receive a claim status and structured evidence references.
5. A candidate PDF is rendered to a temporary output location.
6. Automated and visual checks inspect the candidate before promotion.
7. The handoff records changed files, command and outcome attestations, evidence references, recovery state, privacy-review attestations, and remaining risks.

## Claim review

Each material claim is classified as `supported`, `limited`, or `blocked`.
A supported claim includes at least one structured evidence reference.
A limited claim includes an explicit statement of uncertainty or scope.
A blocked claim is excluded from generated output.

Evidence references can identify a declared artifact, identify a declared verification check, or provide a safe repository-relative path.
The public validator checks that reference syntax is safe and that artifact or check identifiers resolve within the manifest.
It also requires evidence references for supported claims, a limitation for limited claims, and `included_in_output: false` for blocked claims.
It does not inspect generated output or determine factual truth.
A human reviewer must inspect the referenced material and decide whether it supports the exact wording.

## Transactional PDF QA policy

The policy treats a newly rendered PDF as a candidate artifact rather than an immediate replacement.
The implementation owner writes the candidate to a temporary location, runs the required QA checks, and promotes it only after every required check passes.
If a check fails or execution is interrupted, the previously accepted PDF remains unchanged.

Proposed checks include:

- The PDF opens successfully and has the expected page count.
- Required text can be extracted from the rendered document.
- Rendered pages are inspected for clipping, overflow, blank regions, and unintended page breaks.
- The final artifact corresponds to the reviewed source revision.
- Promotion to the accepted path occurs only after the verification record is complete.

This repository does not implement or execute those PDF checks.
The policy does not claim that automated PDF checks can judge every typography or content decision.
Visual review and human approval remain part of the acceptance boundary.

## Recovery policy

If generation or QA is interrupted, the supervisor inspects the same worktree and session artifacts before relaunching work.
The implementation owner resumes from the last independently established point rather than starting an untracked duplicate effort.
The handoff records the recovery outcome and any residual uncertainty as author attestations.

Same-worktree recovery preserves the relationship among the candidate artifact, source revision, and available check records.
If ownership or repository state cannot be established, the safe policy is to stop and begin a new explicitly owned effort.

## Public evidence

The [validator and CLI tests](../tests/test_validator.py) cover input handling, evidence-reference rules, and status consistency.
The [example manifests](../examples/README.md) illustrate accepted and rejected records.
These checks do not establish that a resume was generated, reviewed, or used.

## Related documentation

- [Architecture](architecture.md)
- [Implementation glossary](implementation-glossary.md)
- [Manifest contract](manifest-contract.md)
- [Contract-valid example](../examples/verified_handoff.json)
