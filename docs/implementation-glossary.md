# Implementation Glossary

The workflow uses generic roles that do not depend on a particular agent or coding tool.
The implementation names below explain the case-study terminology; this repository does not include those tools or private execution records.

## Generic terms

### Supervisory agent

A supervisory agent turns an approved objective into bounded tasks, monitors work, inspects artifacts, requests verification, and reports outcomes with evidence.
The human retains approval authority.

### Implementation harness

An implementation harness is the coding environment that reads repository instructions, edits files, runs commands, and manages task artifacts inside the assigned worktree.

### Isolated worktree

An isolated worktree is a Git working directory assigned to one implementation owner for one active change.
It separates file state and local verification from other concurrent efforts.

### Artifact handoff

An artifact handoff records ownership, changed files, generated artifacts, check attestations, claim status, evidence references, privacy-review attestations, and remaining risks.
It gives reviewers an index of what to inspect, not proof that the recorded statements are true.

### Recovery

Recovery means inspecting an interrupted or failed run and resuming from the last verified point.
The preferred path keeps the same logical owner, session context, and worktree when that state remains safe to use.

### Verification

Verification examines code, artifacts, claims, and command outcomes through independent review or deterministic checks.
A recorded check needs independent confirmation, such as a reviewer repeating the command.
The evidence establishes only what that check can test.

## Implementation names

| Name | Case-study role | Responsibilities |
| --- | --- | --- |
| Hermes | Supervisory agent | Task decomposition, launch monitoring, artifact inspection, recovery coordination, and reporting |
| Pi | Implementation harness | Repository-aware file operations, command execution, structured tools, and session context |
| rpiv | Staged workflow layer within the implementation harness | Research, design, planning, implementation, validation, review, and task-artifact conventions |

Git worktrees provide separate working directories, while the handoff manifest records ownership and review references.
The validator checks that record; it does not enforce isolation or run the workflow.
