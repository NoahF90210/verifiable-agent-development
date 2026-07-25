# Implementation Glossary

This glossary explains generic roles first and then maps them to contextual tool names retained from the sanitized case-study architecture.
The public repository does not implement or prove the private source environment associated with those names.
The architecture does not depend on a reader knowing those tools.

## Generic terms

### Supervisory agent

A supervisory agent turns an approved objective into bounded implementation tasks, monitors launches, inspects artifacts, requests verification, and reports outcomes with evidence.
It coordinates work but does not replace the human approval boundary.

### Implementation harness

An implementation harness is the coding environment that reads repository instructions, edits files, runs commands, manages task artifacts, and exposes structured workflows.
It is responsible for carrying out a bounded task inside the assigned worktree.

### Isolated worktree

An isolated worktree is a Git working directory assigned to one implementation owner for one active change.
It separates file state and local verification from other concurrent efforts.

### Artifact handoff

An artifact handoff is a structured record of ownership, changed files, generated artifacts, command and outcome attestations, claim status, evidence references, privacy-review attestations, and remaining risks.
It gives a reviewer a consistent inspection index without proving that every recorded statement is true.

### Recovery

Recovery is the process of inspecting an interrupted or failed run and resuming from the last verified point.
The preferred path keeps the same logical owner, session context, and worktree when that state remains safe to use.

### Verification

Verification is the independent or deterministic examination of code, artifacts, claims, and command outcomes.
A manifest record becomes independent evidence only when a reviewer repeats or otherwise establishes the recorded check.
Verification evidence is scoped to what the performed check can actually establish.

## Implementation names

### Hermes

Hermes is the case-study label for the supervisory-assistant role.
The label represents decomposition, launch monitoring, artifact inspection, recovery coordination, and concise reporting within human approval boundaries.
This repository does not include Hermes implementation code or private execution records.

### Pi

Pi is the case-study label for the implementation-harness role.
The label represents repository-aware file operations, command execution, structured tools, and session context inside an assigned worktree.
This repository does not include the private harness implementation.

### rpiv

rpiv is the case-study label for a staged workflow layer associated with the implementation harness.
The label represents explicit research, design, planning, implementation, validation, review, and task-artifact controls.
This repository documents the conceptual mapping but does not reproduce the private workflow package.

## Relationship among the terms

Hermes fills the supervisory-agent role.
Pi fills the implementation-harness role.
rpiv provides reusable workflow stages and artifact conventions within that harness.
Git worktrees provide write isolation, and the handoff manifest provides a deterministic review boundary.
