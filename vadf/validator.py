"""Deterministic contract validation for verification handoff manifests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0"
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


@dataclass(frozen=True)
class ValidationError:
    """One human-readable contract violation."""

    path: str
    message: str


def _error(errors: list[ValidationError], path: str, message: str) -> None:
    errors.append(ValidationError(path=path, message=message))


def _object(
    value: Any,
    path: str,
    errors: list[ValidationError],
) -> Mapping[str, Any] | None:
    if not isinstance(value, dict):
        _error(errors, path, "must be an object")
        return None
    return value


def _list(
    value: Any,
    path: str,
    errors: list[ValidationError],
    *,
    nonempty: bool = False,
) -> list[Any] | None:
    if not isinstance(value, list):
        _error(errors, path, "must be an array")
        return None
    if nonempty and not value:
        _error(errors, path, "must contain at least one item")
    return value


def _string(
    value: Any,
    path: str,
    errors: list[ValidationError],
    *,
    nonempty: bool = True,
) -> str | None:
    if not isinstance(value, str):
        _error(errors, path, "must be a string")
        return None
    if nonempty and not value.strip():
        _error(errors, path, "must not be empty")
    return value


def _boolean(value: Any, path: str, errors: list[ValidationError]) -> bool | None:
    if not isinstance(value, bool):
        _error(errors, path, "must be a boolean")
        return None
    return value


def _required(
    obj: Mapping[str, Any],
    required: Iterable[str],
    path: str,
    errors: list[ValidationError],
) -> None:
    for key in required:
        if key not in obj:
            _error(errors, f"{path}.{key}", "is required")


def _known_keys(
    obj: Mapping[str, Any],
    allowed: set[str],
    path: str,
    errors: list[ValidationError],
) -> None:
    for key in sorted(set(obj) - allowed):
        _error(errors, f"{path}.{key}", "is not allowed by schema version 1.0")


def _identifier(value: Any, path: str, errors: list[ValidationError]) -> str | None:
    text = _string(value, path, errors)
    if text is not None and not IDENTIFIER_PATTERN.fullmatch(text):
        _error(
            errors,
            path,
            "must be 2 to 64 lowercase letters, digits, dots, underscores, or hyphens",
        )
    return text


def _enum(
    value: Any,
    allowed: set[str],
    path: str,
    errors: list[ValidationError],
) -> str | None:
    text = _string(value, path, errors)
    if text is not None and text not in allowed:
        choices = ", ".join(sorted(allowed))
        _error(errors, path, f"must be one of: {choices}")
    return text


def _relative_path(value: Any, path: str, errors: list[ValidationError]) -> str | None:
    text = _string(value, path, errors)
    if text is None or not text:
        return text
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or text.startswith("~") or re.match(r"^[A-Za-z]:", text):
        _error(errors, path, "must be a repository-relative path")
    if "\\" in text:
        _error(errors, path, "must use forward slashes")
    if any(part in {"", ".", ".."} for part in text.split("/")):
        _error(errors, path, "must not contain empty, current, or parent path segments")
    return text


def _validate_owner(value: Any, errors: list[ValidationError]) -> None:
    path = "$.implementation_owner"
    obj = _object(value, path, errors)
    if obj is None:
        return
    fields = {"role", "worker_handle", "worktree", "exclusive"}
    _required(obj, fields, path, errors)
    _known_keys(obj, fields, path, errors)
    _string(obj.get("role"), f"{path}.role", errors)
    _identifier(obj.get("worker_handle"), f"{path}.worker_handle", errors)
    _relative_path(obj.get("worktree"), f"{path}.worktree", errors)
    exclusive = _boolean(obj.get("exclusive"), f"{path}.exclusive", errors)
    if exclusive is False:
        _error(errors, f"{path}.exclusive", "must be true for one-owner worktree isolation")


def _validate_artifacts(value: Any, errors: list[ValidationError]) -> set[str]:
    path = "$.artifacts"
    items = _list(value, path, errors, nonempty=True)
    if items is None:
        return set()
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    fields = {"id", "path", "kind", "status", "description"}
    for index, value in enumerate(items):
        item_path = f"{path}[{index}]"
        obj = _object(value, item_path, errors)
        if obj is None:
            continue
        _required(obj, fields, item_path, errors)
        _known_keys(obj, fields, item_path, errors)
        identifier = _identifier(obj.get("id"), f"{item_path}.id", errors)
        if identifier in seen_ids:
            _error(errors, f"{item_path}.id", "must be unique")
        elif identifier is not None:
            seen_ids.add(identifier)
        artifact_path = _relative_path(obj.get("path"), f"{item_path}.path", errors)
        if artifact_path in seen_paths:
            _error(errors, f"{item_path}.path", "must be unique")
        elif artifact_path is not None:
            seen_paths.add(artifact_path)
        _enum(
            obj.get("kind"),
            {"configuration", "documentation", "example", "report", "source", "test"},
            f"{item_path}.kind",
            errors,
        )
        _enum(
            obj.get("status"),
            {"created", "changed", "inspected"},
            f"{item_path}.status",
            errors,
        )
        _string(obj.get("description"), f"{item_path}.description", errors)
    return seen_ids


def _validate_verification(value: Any, errors: list[ValidationError]) -> set[str]:
    path = "$.verification"
    obj = _object(value, path, errors)
    if obj is None:
        return set()
    fields = {"overall_status", "checks"}
    _required(obj, fields, path, errors)
    _known_keys(obj, fields, path, errors)
    status = _enum(
        obj.get("overall_status"),
        {"passed", "failed"},
        f"{path}.overall_status",
        errors,
    )
    if status != "passed" and status is not None:
        _error(errors, f"{path}.overall_status", "must be passed for a verified handoff")

    checks = _list(obj.get("checks"), f"{path}.checks", errors, nonempty=True)
    if checks is None:
        return set()
    check_fields = {"id", "command", "outcome", "evidence"}
    seen: set[str] = set()
    for index, value in enumerate(checks):
        check_path = f"{path}.checks[{index}]"
        check = _object(value, check_path, errors)
        if check is None:
            continue
        _required(check, check_fields, check_path, errors)
        _known_keys(check, check_fields, check_path, errors)
        identifier = _identifier(check.get("id"), f"{check_path}.id", errors)
        if identifier in seen:
            _error(errors, f"{check_path}.id", "must be unique")
        elif identifier is not None:
            seen.add(identifier)
        _string(check.get("command"), f"{check_path}.command", errors)
        outcome = _enum(
            check.get("outcome"),
            {"passed", "failed", "not_run"},
            f"{check_path}.outcome",
            errors,
        )
        if outcome != "passed" and outcome is not None:
            _error(errors, f"{check_path}.outcome", "must be passed for a verified handoff")
        _string(check.get("evidence"), f"{check_path}.evidence", errors)
    return seen


def _validate_evidence_reference(
    value: Any,
    path: str,
    artifact_ids: set[str],
    check_ids: set[str],
    errors: list[ValidationError],
) -> None:
    reference = _string(value, path, errors)
    if reference is None:
        return
    reference_type, separator, target = reference.partition(":")
    if not separator or not target:
        _error(
            errors,
            path,
            "must use artifact:<id>, check:<id>, or path:<repository-relative-path>",
        )
        return
    if reference_type == "artifact":
        if not IDENTIFIER_PATTERN.fullmatch(target):
            _error(errors, path, "artifact reference must contain a valid identifier")
        elif target not in artifact_ids:
            _error(errors, path, "must reference a declared artifact id")
        return
    if reference_type == "check":
        if not IDENTIFIER_PATTERN.fullmatch(target):
            _error(errors, path, "check reference must contain a valid identifier")
        elif target not in check_ids:
            _error(errors, path, "must reference a declared verification check id")
        return
    if reference_type == "path":
        _relative_path(target, path, errors)
        return
    _error(
        errors,
        path,
        "must use artifact:<id>, check:<id>, or path:<repository-relative-path>",
    )


def _validate_claims(
    value: Any,
    artifact_ids: set[str],
    check_ids: set[str],
    errors: list[ValidationError],
) -> None:
    path = "$.claims"
    items = _list(value, path, errors, nonempty=True)
    if items is None:
        return
    fields = {"id", "text", "status", "evidence", "limitation", "included_in_output"}
    seen: set[str] = set()
    for index, value in enumerate(items):
        claim_path = f"{path}[{index}]"
        claim = _object(value, claim_path, errors)
        if claim is None:
            continue
        required = {"id", "text", "status", "evidence", "included_in_output"}
        _required(claim, required, claim_path, errors)
        _known_keys(claim, fields, claim_path, errors)
        identifier = _identifier(claim.get("id"), f"{claim_path}.id", errors)
        if identifier in seen:
            _error(errors, f"{claim_path}.id", "must be unique")
        elif identifier is not None:
            seen.add(identifier)
        _string(claim.get("text"), f"{claim_path}.text", errors)
        status = _enum(
            claim.get("status"),
            {"supported", "limited", "blocked"},
            f"{claim_path}.status",
            errors,
        )
        evidence = _list(claim.get("evidence"), f"{claim_path}.evidence", errors)
        if evidence is not None:
            for evidence_index, evidence_item in enumerate(evidence):
                _validate_evidence_reference(
                    evidence_item,
                    f"{claim_path}.evidence[{evidence_index}]",
                    artifact_ids,
                    check_ids,
                    errors,
                )
        included = _boolean(
            claim.get("included_in_output"),
            f"{claim_path}.included_in_output",
            errors,
        )
        if status == "supported" and not evidence:
            _error(errors, f"{claim_path}.evidence", "must not be empty for a supported claim")
        if status == "limited":
            _string(claim.get("limitation"), f"{claim_path}.limitation", errors)
        if status == "blocked" and included is True:
            _error(
                errors,
                f"{claim_path}.included_in_output",
                "must be false when claim status is blocked",
            )


def _validate_risks(value: Any, errors: list[ValidationError]) -> None:
    path = "$.residual_risks"
    items = _list(value, path, errors)
    if items is None:
        return
    fields = {"id", "description", "disposition", "mitigation"}
    seen: set[str] = set()
    for index, value in enumerate(items):
        risk_path = f"{path}[{index}]"
        risk = _object(value, risk_path, errors)
        if risk is None:
            continue
        _required(risk, fields, risk_path, errors)
        _known_keys(risk, fields, risk_path, errors)
        identifier = _identifier(risk.get("id"), f"{risk_path}.id", errors)
        if identifier in seen:
            _error(errors, f"{risk_path}.id", "must be unique")
        elif identifier is not None:
            seen.add(identifier)
        _string(risk.get("description"), f"{risk_path}.description", errors)
        _enum(
            risk.get("disposition"),
            {"accepted", "mitigated", "open"},
            f"{risk_path}.disposition",
            errors,
        )
        _string(risk.get("mitigation"), f"{risk_path}.mitigation", errors)


def _validate_recovery(value: Any, errors: list[ValidationError]) -> None:
    path = "$.recovery"
    obj = _object(value, path, errors)
    if obj is None:
        return
    fields = {"mode", "outcome", "notes"}
    _required(obj, fields, path, errors)
    _known_keys(obj, fields, path, errors)
    mode = _enum(
        obj.get("mode"),
        {"same_session_same_worktree", "not_needed"},
        f"{path}.mode",
        errors,
    )
    outcome = _enum(
        obj.get("outcome"),
        {"recovered", "not_needed"},
        f"{path}.outcome",
        errors,
    )
    if mode == "same_session_same_worktree" and outcome == "not_needed":
        _error(errors, f"{path}.outcome", "must be recovered when recovery mode was used")
    if mode == "not_needed" and outcome == "recovered":
        _error(errors, f"{path}.outcome", "must be not_needed when recovery mode was not needed")
    _string(obj.get("notes"), f"{path}.notes", errors)


def _validate_privacy(value: Any, errors: list[ValidationError]) -> None:
    path = "$.privacy_review"
    obj = _object(value, path, errors)
    if obj is None:
        return
    fields = {"status", "checks"}
    _required(obj, fields, path, errors)
    _known_keys(obj, fields, path, errors)
    status = _enum(obj.get("status"), {"passed", "failed"}, f"{path}.status", errors)
    if status == "failed":
        _error(errors, f"{path}.status", "must be passed for a public-safe handoff")
    checks = _list(obj.get("checks"), f"{path}.checks", errors, nonempty=True)
    if checks is not None:
        for index, check in enumerate(checks):
            _string(check, f"{path}.checks[{index}]", errors)


def validate_manifest(manifest: object) -> list[ValidationError]:
    """Return all deterministic contract violations in stable traversal order."""

    errors: list[ValidationError] = []
    root = _object(manifest, "$", errors)
    if root is None:
        return errors

    fields = {
        "schema_version",
        "handoff_id",
        "implementation_owner",
        "artifacts",
        "verification",
        "claims",
        "residual_risks",
        "recovery",
        "privacy_review",
    }
    _required(root, fields, "$", errors)
    _known_keys(root, fields, "$", errors)

    version = _string(root.get("schema_version"), "$.schema_version", errors)
    if version is not None and version != SCHEMA_VERSION:
        _error(errors, "$.schema_version", f"must equal {SCHEMA_VERSION}")
    _identifier(root.get("handoff_id"), "$.handoff_id", errors)
    _validate_owner(root.get("implementation_owner"), errors)
    artifact_ids = _validate_artifacts(root.get("artifacts"), errors)
    check_ids = _validate_verification(root.get("verification"), errors)
    _validate_claims(root.get("claims"), artifact_ids, check_ids, errors)
    _validate_risks(root.get("residual_risks"), errors)
    _validate_recovery(root.get("recovery"), errors)
    _validate_privacy(root.get("privacy_review"), errors)
    return errors
