# Security Policy

## Supported versions

This reference repository currently supports the latest revision on its default development line.
No production service or hosted endpoint is provided by this repository.

## Reporting a vulnerability

Use the repository host's private security-reporting feature when it is available.
If private reporting is unavailable, open only a minimal public issue that requests a private contact channel.
Do not include vulnerability details, reproduction steps, affected secrets, exploit information, credentials, private prompts, or personal data in that public issue.
Share the affected file, observed behavior, sanitized reproduction, and potential impact only through the established private channel.

## Security boundaries

The validator processes local JSON files and does not require network access.
It does not execute commands found inside a manifest.
Manifest commands, outcomes, evidence descriptions, recovery notes, and privacy-review records are author attestations.
The validator does not execute or independently prove those attestations.

The validator checks repository-relative paths, declared evidence references, and contract status fields.
The publication checker scans every Git-intended file returned by `git ls-files --cached --others --exclude-standard` and fails on non-UTF-8 content, selected credential shapes, personal path shapes, em dashes, and Markdown sentence-layout violations.
The publication patterns are bounded heuristics rather than a comprehensive secret scanner.
Neither tool is a malware scanner, a sandbox, or proof that external evidence is truthful.
Reviewers must still inspect content before publishing or executing it.

## Public-data policy

Do not commit secrets, credentials, tokens, personal filesystem paths, private messages, raw prompts, contacts, private memory, unpublished repository content, or personal resume data.
Use opaque example identifiers and repository-relative paths in public artifacts.
If sensitive data is discovered, stop distribution, remove the data from the working tree and relevant history, rotate affected credentials when applicable, and document the sanitized remediation.
