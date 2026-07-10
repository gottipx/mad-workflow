from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - Hermes normally has PyYAML
    yaml = None

OWNER_TO_PROFILE = {
    "workstream-agent": "mad-workstream",
    "architect-agent": "mad-architect",
    "coding-agent": "mad-coding",
    "qa-agent": "mad-qa",
    "release-agent": "mad-release",
}

PROFILE_DESCRIPTIONS = {
    "mad-workstream": "MAD workstream orchestrator: owns Kanban flow, task contracts, dependencies, blockers, and revalidation. Routes work; does not implement product code by default.",
    "mad-architect": "MAD architect: converts intent into concise specifications, ticket candidates, shared contracts, acceptance criteria, and architecture/design constraints.",
    "mad-coding": "MAD coding worker: implements one bounded task in one isolated workspace/branch from an explicit task contract.",
    "mad-qa": "MAD QA worker: reviews diffs, runs checks, validates contracts/security/accessibility/performance, and returns gate decisions.",
    "mad-release": "MAD release integrator: merges QA-approved branches into integration branches, runs final gates, and prepares PR/MR summaries for human approval.",
}

ROLE_SKILLS = {
    "workstream-agent": [
        "workstream-management", "spec-and-ticket-decomposition", "task-contracts",
        "repository-workspaces", "change-impact-analysis", "completion-and-handoff",
    ],
    "architect-agent": [
        "spec-and-ticket-decomposition", "contracts-and-interfaces",
        "frontend-design-system", "task-contracts", "completion-and-handoff",
    ],
    "coding-agent": [
        "task-contracts", "repository-workspaces", "contracts-and-interfaces",
        "coding-standards", "completion-and-handoff",
    ],
    "qa-agent": [
        "testing-and-quality-gates", "change-impact-analysis", "contracts-and-interfaces",
        "frontend-design-system", "completion-and-handoff",
    ],
    "release-agent": [
        "repository-workspaces", "change-impact-analysis", "testing-and-quality-gates",
        "completion-and-handoff",
    ],
}

REQUIRED_FIELDS = [
    "task_id", "source_item", "owner_agent", "goal", "context", "mode",
    "allowed_scope", "forbidden_scope", "dependencies", "contracts_consumed",
    "contracts_produced_or_modified", "definition_of_done", "required_checks",
    "report_format",
]

VALID_MODES = {"architecture", "coding", "backend", "frontend", "mobile", "data", "infra", "qa", "release", "revalidation", "planning"}


def setup_cli(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(func=mad_command)
    sub = parser.add_subparsers(dest="mad_action")

    p_init = sub.add_parser("init", help="Initialize a Hermes board/profiles for MAD")
    p_init.add_argument("--board", default="mad-workflow", help="Kanban board slug to create/use")
    p_init.add_argument("--workdir", default=None, help="Default workdir for the board")
    p_init.add_argument("--create-profiles", action="store_true", help="Create the five MAD Hermes profiles if missing")
    p_init.add_argument("--install-skills-from", default=None, metavar="PATH", help="Copy MAD skills from a mad-workflow checkout")
    p_init.add_argument("--switch", action="store_true", help="Switch active Kanban board to the MAD board")
    p_init.add_argument("--json", action="store_true")

    p_val = sub.add_parser("validate-contract", aliases=["validate"], help="Validate a MAD task contract YAML file")
    p_val.add_argument("contract")
    p_val.add_argument("--json", action="store_true")

    p_report = sub.add_parser("validate-report", help="Validate a MAD completion, QA, or impact report")
    p_report.add_argument("kind", choices=["completion", "qa", "impact"])
    p_report.add_argument("report")
    p_report.add_argument("--contract", default=None, help="Optional task contract to cross-check task_id and required checks")
    p_report.add_argument("--json", action="store_true")

    p_gate = sub.add_parser("gate", help="Evaluate whether a Kanban task may move to review, integration, or done")
    p_gate.add_argument("task_id")
    p_gate.add_argument("--stage", choices=["review", "integration", "done"], required=True)
    p_gate.add_argument("--board", default=None)
    p_gate.add_argument("--contract", default=None, help="Optional contract path; otherwise parsed from task body")
    p_gate.add_argument("--reports-dir", default=".agents/reports", help="Directory containing MAD reports")
    p_gate.add_argument("--completion", default=None, help="Completion report path override")
    p_gate.add_argument("--qa", default=None, help="QA gate report path override")
    p_gate.add_argument("--impact", default=None, help="Impact report path override")
    p_gate.add_argument("--block-on-fail", action="store_true", help="Block the Kanban task when the gate fails")
    p_gate.add_argument("--json", action="store_true")

    p_graph = sub.add_parser("graph", help="Validate and query a MAD contract dependency registry")
    graph_sub = p_graph.add_subparsers(dest="graph_action")
    p_graph_validate = graph_sub.add_parser("validate", help="Validate contracts registry structure")
    p_graph_validate.add_argument("graph")
    p_graph_validate.add_argument("--repo", default=".", help="Repo root used to check contract paths")
    p_graph_validate.add_argument("--json", action="store_true")
    p_graph_consumers = graph_sub.add_parser("consumers", help="List consumers for a contract path or id")
    p_graph_consumers.add_argument("graph")
    p_graph_consumers.add_argument("contract")
    p_graph_consumers.add_argument("--json", action="store_true")

    p_impact = sub.add_parser("impact", help="Generate an impact report from git diff and a contract registry")
    p_impact.add_argument("task_id")
    p_impact.add_argument("--graph", default=".agents/contracts.yaml", help="Contract registry path")
    p_impact.add_argument("--repo", default=".")
    p_impact.add_argument("--base", default=None, help="Base ref for committed diff, e.g. origin/main")
    p_impact.add_argument("--out", default=None, help="Write impact report YAML to this path")
    p_impact.add_argument("--json", action="store_true")

    p_gh = sub.add_parser("github", help="Generate or create GitHub issues/PR bodies from MAD artifacts")
    gh_sub = p_gh.add_subparsers(dest="github_action")
    p_issue_body = gh_sub.add_parser("issue-body", help="Render a GitHub issue body from a task contract")
    p_issue_body.add_argument("contract")
    p_issue_body.add_argument("--out", default=None)
    p_issue_body.add_argument("--json", action="store_true")
    p_pr_body = gh_sub.add_parser("pr-body", help="Render a PR body from MAD reports")
    p_pr_body.add_argument("contract")
    p_pr_body.add_argument("--completion", default=None)
    p_pr_body.add_argument("--qa", default=None)
    p_pr_body.add_argument("--impact", default=None)
    p_pr_body.add_argument("--out", default=None)
    p_pr_body.add_argument("--json", action="store_true")
    p_create_issue = gh_sub.add_parser("create-issue", help="Create a GitHub issue from a task contract using gh")
    p_create_issue.add_argument("contract")
    p_create_issue.add_argument("--repo", default=None, help="owner/repo; defaults to gh current repo")
    p_create_issue.add_argument("--label", action="append", default=[])
    p_create_issue.add_argument("--dry-run", action="store_true")
    p_create_issue.add_argument("--json", action="store_true")
    p_link_pr = gh_sub.add_parser("link-pr", help="Record a PR URL on a Kanban task as a comment")
    p_link_pr.add_argument("task_id")
    p_link_pr.add_argument("pr_url")
    p_link_pr.add_argument("--board", default=None)
    p_link_pr.add_argument("--json", action="store_true")

    p_create = sub.add_parser("create-task", help="Create a Hermes Kanban task from a MAD task contract")
    p_create.add_argument("contract")
    p_create.add_argument("--board", default=None)
    p_create.add_argument("--assignee", default=None, help="Override assignee profile")
    p_create.add_argument("--workspace", default=None, help="scratch | worktree | worktree:<path> | dir:<path>")
    p_create.add_argument("--branch", default=None)
    p_create.add_argument("--priority", type=int, default=0)
    p_create.add_argument("--parent", action="append", default=[])
    p_create.add_argument("--link-dependencies", action="store_true", help="Treat contract dependencies that look like task IDs as Kanban parents")
    p_create.add_argument("--idempotency-key", default=None)
    p_create.add_argument("--json", action="store_true")

    p_scope = sub.add_parser("check-scope", help="Check git diff against contract allowed/forbidden scope")
    p_scope.add_argument("contract")
    p_scope.add_argument("--repo", default=".")
    p_scope.add_argument("--base", default=None, help="Base ref for committed diff, e.g. origin/main")
    p_scope.add_argument("--json", action="store_true")

    p_prompt = sub.add_parser("prompt", help="Render a role-specific worker prompt from a task contract")
    p_prompt.add_argument("contract")
    p_prompt.add_argument("--role", default=None, help="Override owner_agent role")

    p_decompose = sub.add_parser("decompose", help="Generate draft MAD task contracts from a feature plan")
    p_decompose.add_argument("feature_plan")
    p_decompose.add_argument("--out", default=".agents/task-contracts", help="Output directory for generated contracts")
    p_decompose.add_argument("--start", type=int, default=1, help="First TASK number to use")
    p_decompose.add_argument("--json", action="store_true")

    p_run = sub.add_parser("run", help="Kick off the full MAD workflow from a feature plan: decompose, create Kanban tasks, link deps, promote, and optionally dispatch")
    p_run.add_argument("feature_plan", help="Path to feature plan YAML")
    p_run.add_argument("--board", default=None, help="Kanban board slug (default: mad-workflow)")
    p_run.add_argument("--out", default=".agents/task-contracts", help="Directory for generated task contracts")
    p_run.add_argument("--dispatch", action="store_true", help="Run hermes kanban dispatch after creating tasks")
    p_run.add_argument("--dry-run", action="store_true", help="Show what would be created but do not create Kanban tasks")
    p_run.add_argument("--json", action="store_true")


def mad_command(args: argparse.Namespace) -> None:
    """Top-level CLI handler.

    Hermes currently invokes plugin CLI handlers without using their return
    value, so this handler must raise SystemExit explicitly for CI-friendly
    non-zero status propagation.
    """
    raise SystemExit(_mad_command(args))


def _mad_command(args: argparse.Namespace) -> int:
    action = getattr(args, "mad_action", None)
    if action is None:
        print("Use `hermes mad --help` for commands.")
        return 2
    if action == "init":
        return cmd_init(args)
    if action in {"validate-contract", "validate"}:
        return cmd_validate(args)
    if action == "validate-report":
        return cmd_validate_report(args)
    if action == "gate":
        return cmd_gate(args)
    if action == "graph":
        return cmd_graph(args)
    if action == "impact":
        return cmd_impact(args)
    if action == "github":
        return cmd_github(args)
    if action == "decompose":
        return cmd_decompose(args)
    if action == "create-task":
        return cmd_create_task(args)
    if action == "check-scope":
        return cmd_check_scope(args)
    if action == "prompt":
        return cmd_prompt(args)
    if action == "run":
        return cmd_run(args)
    print(f"Unknown mad action: {action}", file=sys.stderr)
    return 2


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _emit(data: dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    status = data.get("status")
    if status:
        print(status)
    for item in data.get("messages", []):
        print(f"- {item}")
    if data.get("errors"):
        print("Errors:", file=sys.stderr)
        for e in data["errors"]:
            print(f"- {e}", file=sys.stderr)
    if data.get("warnings"):
        print("Warnings:", file=sys.stderr)
        for w in data["warnings"]:
            print(f"- {w}", file=sys.stderr)


def load_contract(path: str | Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read MAD contracts")
    p = Path(path).expanduser()
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError("contract must be a YAML mapping/object")
    return data


PLACEHOLDER_RE = re.compile(r"^(?:todo|tbd|unset|<[^>]+>|\.\.\.)$", re.IGNORECASE)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return not text or bool(PLACEHOLDER_RE.match(text))
    if isinstance(value, list):
        return not value
    if isinstance(value, dict):
        return not value
    return False


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.match(value.strip())) or "TODO" in value or "TBD" in value
    if isinstance(value, list):
        return any(_contains_placeholder(v) for v in value)
    if isinstance(value, dict):
        return any(_contains_placeholder(v) for v in value.values())
    return False


def validate_contract(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
        elif field in {"task_id", "source_item", "owner_agent", "goal", "context", "mode"} and _is_blank(data.get(field)):
            errors.append(f"{field} must not be empty or a placeholder")
    if _contains_placeholder(data):
        errors.append("contract contains unresolved TODO/TBD/placeholder values")
    owner = str(data.get("owner_agent", "")).strip()
    if owner and owner not in OWNER_TO_PROFILE:
        errors.append(f"owner_agent must be one of {sorted(OWNER_TO_PROFILE)}, got {owner!r}")
    mode = str(data.get("mode", "")).strip()
    if mode and mode not in VALID_MODES:
        errors.append(f"mode must be one of {sorted(VALID_MODES)}, got {mode!r}")
    list_fields = ["allowed_scope", "forbidden_scope", "dependencies", "contracts_consumed", "contracts_produced_or_modified", "definition_of_done", "required_checks"]
    for field in list_fields:
        if field in data and not isinstance(data[field], list):
            errors.append(f"{field} must be a list")
    allowed = set(map(str, data.get("allowed_scope") or []))
    forbidden = set(map(str, data.get("forbidden_scope") or []))
    overlap = sorted(allowed & forbidden)
    if overlap:
        errors.append(f"allowed_scope overlaps forbidden_scope: {', '.join(overlap)}")
    if not data.get("allowed_scope"):
        errors.append("allowed_scope must not be empty")
    if not data.get("definition_of_done"):
        errors.append("definition_of_done must not be empty")
    if mode in {"coding", "qa", "release", "revalidation"} and not data.get("required_checks"):
        errors.append(f"{mode} task must declare required_checks")
    report_format = data.get("report_format")
    if not isinstance(report_format, dict) or not report_format:
        errors.append("report_format must be a non-empty mapping")
    if data.get("task_id") and not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$", str(data["task_id"])):
        warnings.append("task_id contains unusual characters; prefer TASK-001 style IDs")
    return errors, warnings


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        data = load_contract(args.contract)
        errors, warnings = validate_contract(data)
    except Exception as exc:
        errors, warnings = [str(exc)], []
        data = {}
    ok = not errors
    _emit({
        "status": "PASS: contract is valid" if ok else "FAIL: contract is invalid",
        "contract": data.get("task_id"),
        "errors": errors,
        "warnings": warnings,
    }, args.json)
    return 0 if ok else 1


REPORT_REQUIRED_FIELDS = {
    "completion": [
        "schema_version", "report_id", "task_id", "owner_agent", "status", "branch", "workspace",
        "base_revision", "revision", "changed_files", "contracts_changed", "tests_run", "test_result",
        "blockers", "downstream_impact", "recommended_next_actions",
    ],
    "qa": [
        "schema_version", "report_id", "task_id", "target_branch", "base_revision", "target_revision",
        "decision", "evidence", "checks_run", "failed_checks", "contract_findings",
        "required_fixes", "follow_up_recommendations",
    ],
    "impact": [
        "schema_version", "report_id", "source_task", "base_revision", "changed_revision",
        "changed_files", "changed_artifacts", "change_type", "impacted_tasks",
        "impacted_contracts", "required_revalidation", "risk_level", "notes",
    ],
}

VALID_COMPLETION_STATUSES = {"completed", "blocked", "failed", "partial"}
VALID_QA_DECISIONS = {"pass", "pass_with_notes", "fail", "blocked"}
VALID_CHANGE_TYPES = {"internal", "additive", "behavioral", "breaking", "unclear"}
VALID_RISK_LEVELS = {"low", "medium", "high"}


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read MAD YAML files")
    p = Path(path).expanduser()
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{p} must be a YAML mapping/object")
    return data


def validate_report_data(kind: str, data: dict[str, Any], contract: dict[str, Any] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in REPORT_REQUIRED_FIELDS[kind]:
        if field not in data:
            errors.append(f"missing required field: {field}")

    list_fields = {
        "completion": [
            "changed_files", "contracts_changed", "acceptance_evidence", "tests_run",
            "evidence", "assumptions", "blockers", "residual_risks",
            "downstream_impact", "recommended_next_actions",
        ],
        "qa": [
            "evidence", "acceptance_coverage", "checks_run", "failed_checks",
            "contract_findings", "security_findings", "accessibility_findings",
            "performance_findings", "operational_findings", "required_fixes",
            "residual_risks", "follow_up_recommendations", "revalidation_scope",
        ],
        "impact": [
            "changed_files", "changed_artifacts", "classification_evidence",
            "impacted_tasks", "impacted_contracts", "stale_reports_or_tasks",
            "required_revalidation", "registry_updates", "notes",
        ],
    }[kind]
    for field in list_fields:
        if field in data and not isinstance(data[field], list):
            errors.append(f"{field} must be a list")

    if kind == "completion":
        status = str(data.get("status", "")).strip()
        if not status or status not in VALID_COMPLETION_STATUSES:
            errors.append(f"status must be one of {sorted(VALID_COMPLETION_STATUSES)}, got {status!r}")
        if status == "completed" and not data.get("tests_run"):
            errors.append("completed report must list tests_run")
        if status == "completed" and str(data.get("test_result") or "").strip() != "passed":
            errors.append("completed report requires test_result: passed")
        if not data.get("revision"):
            errors.append("completion report must pin the candidate revision")
    elif kind == "qa":
        decision = str(data.get("decision", "")).strip()
        if not decision or decision not in VALID_QA_DECISIONS:
            errors.append(f"decision must be one of {sorted(VALID_QA_DECISIONS)}, got {decision!r}")
        if decision in {"fail", "blocked"} and not data.get("required_fixes"):
            errors.append("failing/blocked QA report must list required_fixes or restart conditions")
        if decision in {"pass", "pass_with_notes"} and data.get("failed_checks"):
            errors.append("passing QA report must not contain failed_checks")
        if decision in {"pass", "pass_with_notes"} and not data.get("evidence"):
            errors.append("passing QA report must contain evidence")
        if not data.get("target_revision"):
            errors.append("QA report must pin the reviewed candidate revision")
    elif kind == "impact":
        change_type = str(data.get("change_type", "")).strip()
        risk = str(data.get("risk_level", "")).strip()
        if not change_type or change_type not in VALID_CHANGE_TYPES:
            errors.append(f"change_type must be one of {sorted(VALID_CHANGE_TYPES)}, got {change_type!r}")
        if not risk or risk not in VALID_RISK_LEVELS:
            errors.append(f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}, got {risk!r}")
        if change_type in {"behavioral", "breaking", "unclear"} and not data.get("required_revalidation"):
            errors.append("behavioral/breaking/unclear impact must list required_revalidation")
        if not data.get("changed_revision"):
            errors.append("impact report must pin the changed revision")

    if contract:
        expected_task_id = str(contract.get("task_id") or "")
        actual_task_id = str(data.get("task_id") or data.get("source_task") or "")
        if expected_task_id and actual_task_id and expected_task_id != actual_task_id:
            errors.append(f"report task id {actual_task_id!r} does not match contract task_id {expected_task_id!r}")
        if kind in {"completion", "qa"}:
            required_checks = set(map(str, contract.get("required_checks") or []))
            run_field = "tests_run" if kind == "completion" else "checks_run"
            run_checks = set(map(str, data.get(run_field) or []))
            missing = sorted(required_checks - run_checks)
            if missing:
                errors.append(f"report does not mention required checks: {', '.join(missing)}")
    return errors, warnings


def cmd_validate_report(args: argparse.Namespace) -> int:
    try:
        report = load_yaml_file(args.report)
        contract = load_contract(args.contract) if args.contract else None
        errors, warnings = validate_report_data(args.kind, report, contract)
    except Exception as exc:
        report = {}
        errors, warnings = [str(exc)], []
    ok = not errors
    _emit({
        "status": f"PASS: {args.kind} report is valid" if ok else f"FAIL: {args.kind} report is invalid",
        "report": args.report,
        "errors": errors,
        "warnings": warnings,
    }, args.json)
    return 0 if ok else 1


def _contract_from_task_body(body: str | None) -> dict[str, Any] | None:
    if not body or yaml is None:
        return None
    match = re.search(r"```yaml\s*(.*?)\s*```", body, flags=re.DOTALL)
    if not match:
        return None
    data = yaml.safe_load(match.group(1)) or {}
    return data if isinstance(data, dict) else None


def _report_path(reports_dir: str | Path, task_key: str, suffix: str, override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    return Path(reports_dir).expanduser() / f"{task_key}-{suffix}.yaml"


def _load_optional_report(path: Path, kind: str, contract: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    if not path.exists():
        return None, [f"missing {kind} report: {path}"], []
    data = load_yaml_file(path)
    errors, warnings = validate_report_data(kind, data, contract)
    return data, errors, warnings


def _completion_qa_consistency_errors(completion: dict[str, Any] | None, qa: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not completion or not qa:
        return errors
    completion_revision = str(completion.get("revision") or "").strip()
    qa_revision = str(qa.get("target_revision") or "").strip()
    if not completion_revision:
        errors.append("completion report must pin revision before QA can approve integration")
    if not qa_revision:
        errors.append("QA report must pin target_revision before integration")
    if completion_revision and qa_revision and completion_revision != qa_revision:
        errors.append(
            f"QA target_revision {qa_revision!r} does not match completion revision {completion_revision!r}"
        )
    completion_branch = str(completion.get("branch") or "").strip()
    qa_branch = str(qa.get("target_branch") or "").strip()
    if completion_branch and qa_branch and completion_branch != qa_branch:
        errors.append(
            f"QA target_branch {qa_branch!r} does not match completion branch {completion_branch!r}"
        )
    return errors


def cmd_gate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    messages: list[str] = []
    try:
        from hermes_cli import kanban_db as kb
        with kb.connect(board=args.board) as conn:
            task = kb.get_task(conn, args.task_id)
            if task is None:
                raise ValueError(f"unknown Kanban task: {args.task_id}")
            contract = load_contract(args.contract) if args.contract else _contract_from_task_body(task.body)
            if not contract:
                errors.append("could not resolve task contract; pass --contract")
            else:
                c_errors, c_warnings = validate_contract(contract)
                errors.extend(c_errors)
                warnings.extend(c_warnings)

            task_key = str((contract or {}).get("task_id") or args.task_id)
            completion_path = _report_path(args.reports_dir, task_key, "completion", args.completion)
            qa_path = _report_path(args.reports_dir, task_key, "quality-gate", args.qa)
            impact_path = _report_path(args.reports_dir, task_key, "impact", args.impact)

            completion = qa = impact = None
            if args.stage in {"review", "integration", "done"}:
                completion, e, w = _load_optional_report(completion_path, "completion", contract)
                errors.extend(e); warnings.extend(w)
                if completion and completion.get("status") != "completed":
                    errors.append(f"completion status must be 'completed' for {args.stage}, got {completion.get('status')!r}")
            if args.stage in {"integration", "done"}:
                qa, e, w = _load_optional_report(qa_path, "qa", contract)
                errors.extend(e); warnings.extend(w)
                if qa and qa.get("decision") not in {"pass", "pass_with_notes"}:
                    errors.append(f"QA decision must be pass/pass_with_notes for {args.stage}, got {qa.get('decision')!r}")
                errors.extend(_completion_qa_consistency_errors(completion, qa))
            contracts_changed = list((completion or {}).get("contracts_changed") or [])
            if args.stage == "done" and contracts_changed:
                impact, e, w = _load_optional_report(impact_path, "impact", contract)
                errors.extend(e); warnings.extend(w)
                if impact and impact.get("change_type") in {"breaking", "unclear"}:
                    errors.append("done gate rejects breaking/unclear impact without explicit human exception")

            ok = not errors
            messages.append(f"stage: {args.stage}")
            messages.append(f"task: {args.task_id}")
            if contract:
                messages.append(f"contract: {contract.get('task_id')}")
            if completion:
                messages.append(f"completion report: {completion_path}")
            if qa:
                messages.append(f"QA report: {qa_path}")
            if impact:
                messages.append(f"impact report: {impact_path}")

            if args.block_on_fail and not ok:
                reason = "MAD gate failed for " + args.stage + ": " + "; ".join(errors[:5])
                kb.block_task(conn, args.task_id, reason=reason, kind="needs_input")
                messages.append("blocked Kanban task because --block-on-fail was set")
            elif ok:
                kb.add_comment(conn, args.task_id, "mad-workflow", f"MAD {args.stage} gate passed.")

        _emit({
            "status": f"PASS: MAD {args.stage} gate passed" if ok else f"FAIL: MAD {args.stage} gate failed",
            "messages": messages,
            "errors": errors,
            "warnings": warnings,
        }, args.json)
        return 0 if ok else 1
    except Exception as exc:
        _emit({"status": "FAIL: could not evaluate MAD gate", "errors": [str(exc)]}, args.json)
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    messages: list[str] = []
    errors: list[str] = []
    board_cmd = ["hermes", "kanban", "boards", "create", args.board, "--name", "MAD Workflow", "--description", "Multi-Agent Delivery Workflow board"]
    if args.workdir:
        board_cmd += ["--default-workdir", str(Path(args.workdir).expanduser())]
    if args.switch:
        board_cmd.append("--switch")
    proc = _run(board_cmd)
    if proc.returncode == 0:
        messages.append(f"created board {args.board!r}")
    elif "already" in (proc.stderr + proc.stdout).lower() or "exists" in (proc.stderr + proc.stdout).lower():
        messages.append(f"board {args.board!r} already exists")
        if args.switch:
            sw = _run(["hermes", "kanban", "boards", "switch", args.board])
            if sw.returncode == 0:
                messages.append(f"switched active board to {args.board!r}")
            else:
                errors.append(sw.stderr.strip() or sw.stdout.strip())
    else:
        errors.append(proc.stderr.strip() or proc.stdout.strip() or "failed to create board")

    if args.install_skills_from:
        src = Path(args.install_skills_from).expanduser() / "skills"
        dest_root = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes") / "skills" / "mad-workflow"
        if not src.exists():
            errors.append(f"skills source not found: {src}")
        else:
            dest_root.mkdir(parents=True, exist_ok=True)
            copied = 0
            for skill_dir in src.iterdir():
                if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                    continue
                dest = dest_root / skill_dir.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(skill_dir, dest)
                copied += 1
            messages.append(f"installed {copied} MAD skills into {dest_root}")

    if args.create_profiles:
        existing = _run(["hermes", "profile", "list"]).stdout
        for profile, desc in PROFILE_DESCRIPTIONS.items():
            if profile in existing:
                messages.append(f"profile {profile!r} already exists")
                continue
            proc = _run(["hermes", "profile", "create", profile, "--clone", "--no-alias", "--description", desc])
            if proc.returncode == 0:
                messages.append(f"created profile {profile!r}")
            else:
                errors.append(f"profile {profile}: {proc.stderr.strip() or proc.stdout.strip()}")

    _emit({"status": "MAD init complete" if not errors else "MAD init completed with errors", "messages": messages, "errors": errors}, args.json)
    return 0 if not errors else 1


def load_contract_graph(path: str | Path) -> dict[str, Any]:
    data = load_yaml_file(path)
    contracts = data.get("contracts")
    if not isinstance(contracts, dict):
        raise ValueError("contract graph must contain a 'contracts' mapping")
    return data


def _contract_entries(graph: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    for contract_id, entry in (graph.get("contracts") or {}).items():
        if isinstance(entry, dict):
            out.append((str(contract_id), entry))
    return out


def validate_contract_graph(data: dict[str, Any], repo: str | Path = ".") -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    contracts = data.get("contracts")
    if not isinstance(contracts, dict):
        return ["contracts must be a mapping"], warnings
    repo_root = Path(repo).expanduser().resolve()
    seen_paths: dict[str, str] = {}
    for contract_id, entry in contracts.items():
        if not isinstance(entry, dict):
            errors.append(f"contracts.{contract_id} must be a mapping")
            continue
        path = str(entry.get("path") or "").strip()
        if not path:
            errors.append(f"contracts.{contract_id}.path is required")
        elif path in seen_paths:
            errors.append(f"contract path {path!r} is used by both {seen_paths[path]!r} and {contract_id!r}")
        else:
            seen_paths[path] = str(contract_id)
            if not (repo_root / path).exists():
                warnings.append(f"contract path does not exist yet: {path}")
        for field in ["producers", "consumers"]:
            if field in entry and not isinstance(entry[field], list):
                errors.append(f"contracts.{contract_id}.{field} must be a list")
        if not entry.get("consumers"):
            warnings.append(f"contracts.{contract_id} has no consumers")
    return errors, warnings


def _match_contract(graph: dict[str, Any], query: str) -> tuple[str, dict[str, Any]] | None:
    q = query.strip().lstrip("/")
    for contract_id, entry in _contract_entries(graph):
        if q == contract_id or q == str(entry.get("path") or "").lstrip("/"):
            return contract_id, entry
    return None


def _changed_contracts(graph: dict[str, Any], changed_files: list[str]) -> list[tuple[str, dict[str, Any]]]:
    changed = set(f.lstrip("/") for f in changed_files)
    hits: list[tuple[str, dict[str, Any]]] = []
    for contract_id, entry in _contract_entries(graph):
        path = str(entry.get("path") or "").lstrip("/")
        if path and path in changed:
            hits.append((contract_id, entry))
    return hits


def _git_head(repo: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _impact_report(task_id: str, changed_files: list[str], graph: dict[str, Any]) -> dict[str, Any]:
    hits = _changed_contracts(graph, changed_files)
    impacted_tasks: list[str] = []
    impacted_contracts: list[str] = []
    required_revalidation: list[str] = []
    for contract_id, entry in hits:
        impacted_contracts.append(contract_id)
        for consumer in entry.get("consumers") or []:
            consumer_s = str(consumer)
            if consumer_s != task_id and consumer_s not in impacted_tasks:
                impacted_tasks.append(consumer_s)
                required_revalidation.append(consumer_s)
    change_type = "internal" if not hits else "behavioral"
    risk_level = "low" if not hits else "medium"
    return {
        "schema_version": "mad.impact-report/v1",
        "report_id": f"{task_id}-impact-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "source_task": task_id,
        "base_revision": "",
        "changed_revision": _git_head(Path.cwd()),
        "changed_files": changed_files,
        "changed_artifacts": [entry.get("path") for _, entry in hits],
        "change_type": change_type,
        "classification_evidence": ["Generated from git diff and contract registry"],
        "impacted_tasks": impacted_tasks,
        "impacted_contracts": impacted_contracts,
        "stale_reports_or_tasks": [],
        "required_revalidation": required_revalidation,
        "registry_updates": [],
        "risk_level": risk_level,
        "rollback_or_migration": "",
        "notes": ["Generated by hermes mad impact"],
    }


def cmd_graph(args: argparse.Namespace) -> int:
    action = getattr(args, "graph_action", None)
    if action is None:
        print("Use `hermes mad graph --help` for commands.")
        return 2
    try:
        graph = load_contract_graph(args.graph)
        if action == "validate":
            errors, warnings = validate_contract_graph(graph, args.repo)
            ok = not errors
            _emit({
                "status": "PASS: contract graph is valid" if ok else "FAIL: contract graph is invalid",
                "graph": args.graph,
                "contracts": len(graph.get("contracts") or {}),
                "errors": errors,
                "warnings": warnings,
            }, args.json)
            return 0 if ok else 1
        if action == "consumers":
            match = _match_contract(graph, args.contract)
            if not match:
                _emit({"status": "FAIL: contract not found", "errors": [args.contract]}, args.json)
                return 1
            contract_id, entry = match
            consumers = list(map(str, entry.get("consumers") or []))
            _emit({
                "status": "contract consumers",
                "contract_id": contract_id,
                "path": entry.get("path"),
                "consumers": consumers,
                "messages": [f"{contract_id}: {', '.join(consumers) if consumers else '(none)'}"],
            }, args.json)
            return 0
        print(f"Unknown graph action: {action}", file=sys.stderr)
        return 2
    except Exception as exc:
        _emit({"status": "FAIL: could not read contract graph", "errors": [str(exc)]}, getattr(args, "json", False))
        return 1


def _md_list(items: list[Any]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def github_issue_body(contract: dict[str, Any]) -> str:
    return f"""## MAD Task Contract

**Task:** `{contract.get('task_id', '')}`  
**Source item:** `{contract.get('source_item', '')}`  
**Owner agent:** `{contract.get('owner_agent', '')}`  
**Mode:** `{contract.get('mode', '')}`

## Goal

{contract.get('goal', '')}

## Context

{contract.get('context', '') or '_No extra context provided._'}

## Allowed scope

{_md_list(contract.get('allowed_scope') or [])}

## Forbidden scope

{_md_list(contract.get('forbidden_scope') or [])}

## Dependencies

{_md_list(contract.get('dependencies') or [])}

## Contracts consumed

{_md_list(contract.get('contracts_consumed') or [])}

## Contracts produced or modified

{_md_list(contract.get('contracts_produced_or_modified') or [])}

## Definition of done

{_md_list(contract.get('definition_of_done') or [])}

## Required checks

{_md_list(contract.get('required_checks') or [])}
"""


def github_pr_body(contract: dict[str, Any], completion: dict[str, Any] | None, qa: dict[str, Any] | None, impact: dict[str, Any] | None) -> str:
    task_id = contract.get("task_id", "")
    checks = (completion or {}).get("tests_run") or (qa or {}).get("checks_run") or []
    changed_files = (completion or {}).get("changed_files") or (impact or {}).get("changed_files") or []
    qa_decision = (qa or {}).get("decision", "not provided")
    impact_type = (impact or {}).get("change_type", "not provided")
    risk = (impact or {}).get("risk_level", "not provided")
    return f"""## MAD Release Candidate

**Task:** `{task_id}`  
**Source item:** `{contract.get('source_item', '')}`  
**Owner agent:** `{contract.get('owner_agent', '')}`

## Goal

{contract.get('goal', '')}

## Changed files

{_md_list(changed_files)}

## Checks run

{_md_list(checks)}

## QA gate

Decision: `{qa_decision}`

Required fixes:

{_md_list((qa or {}).get('required_fixes') or [])}

## Contract impact

Change type: `{impact_type}`  
Risk level: `{risk}`

Impacted contracts:

{_md_list((impact or {}).get('impacted_contracts') or [])}

Required revalidation:

{_md_list((impact or {}).get('required_revalidation') or [])}

## Human approval

Human review remains required before merge.
"""


def _write_or_print_markdown(markdown: str, out: str | None, as_json: bool, label: str) -> None:
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    if as_json:
        print(json.dumps({"status": f"generated {label}", "out": out, "markdown": markdown}, indent=2))
    else:
        if out:
            print(f"generated {label}: {out}")
        else:
            print(markdown)


def cmd_github(args: argparse.Namespace) -> int:
    action = getattr(args, "github_action", None)
    if action is None:
        print("Use `hermes mad github --help` for commands.")
        return 2
    try:
        if action == "issue-body":
            contract = load_contract(args.contract)
            errors, warnings = validate_contract(contract)
            if errors:
                _emit({"status": "FAIL: contract is invalid", "errors": errors, "warnings": warnings}, args.json)
                return 1
            _write_or_print_markdown(github_issue_body(contract), args.out, args.json, "issue body")
            return 0
        if action == "pr-body":
            contract = load_contract(args.contract)
            errors, warnings = validate_contract(contract)
            if errors:
                _emit({"status": "FAIL: contract is invalid", "errors": errors, "warnings": warnings}, args.json)
                return 1
            completion = load_yaml_file(args.completion) if args.completion else None
            qa = load_yaml_file(args.qa) if args.qa else None
            impact = load_yaml_file(args.impact) if args.impact else None
            _write_or_print_markdown(github_pr_body(contract, completion, qa, impact), args.out, args.json, "PR body")
            return 0
        if action == "create-issue":
            contract = load_contract(args.contract)
            errors, warnings = validate_contract(contract)
            if errors:
                _emit({"status": "FAIL: contract is invalid", "errors": errors, "warnings": warnings}, args.json)
                return 1
            body = github_issue_body(contract)
            title = f"{contract.get('task_id')}: {contract.get('goal')}"
            if args.dry_run:
                _emit({"status": "dry-run: GitHub issue not created", "title": title, "body": body, "warnings": warnings}, args.json)
                return 0
            gh = shutil.which("gh")
            if not gh:
                raise RuntimeError("gh CLI is required for create-issue")
            body_file = Path(os.environ.get("TMPDIR", "/tmp")) / f"mad-issue-{_slug(str(contract.get('task_id')))}.md"
            body_file.write_text(body, encoding="utf-8")
            cmd = [gh, "issue", "create", "--title", title, "--body-file", str(body_file)]
            if args.repo:
                cmd += ["--repo", args.repo]
            for label in args.label or []:
                cmd += ["--label", label]
            proc = _run(cmd)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gh issue create failed")
            url = proc.stdout.strip()
            _emit({"status": "created GitHub issue", "url": url, "messages": [url], "warnings": warnings}, args.json)
            return 0
        if action == "link-pr":
            from hermes_cli import kanban_db as kb
            with kb.connect(board=args.board) as conn:
                if kb.get_task(conn, args.task_id) is None:
                    raise ValueError(f"unknown Kanban task: {args.task_id}")
                kb.add_comment(conn, args.task_id, "mad-workflow", f"GitHub PR: {args.pr_url}")
            _emit({"status": "linked PR to Kanban task", "messages": [f"{args.task_id}: {args.pr_url}"]}, args.json)
            return 0
        print(f"Unknown github action: {action}", file=sys.stderr)
        return 2
    except Exception as exc:
        _emit({"status": "FAIL: GitHub mapping command failed", "errors": [str(exc)]}, getattr(args, "json", False))
        return 1


def cmd_impact(args: argparse.Namespace) -> int:
    try:
        graph = load_contract_graph(args.graph)
        graph_errors, graph_warnings = validate_contract_graph(graph, args.repo)
        if graph_errors:
            _emit({"status": "FAIL: contract graph is invalid", "errors": graph_errors, "warnings": graph_warnings}, args.json)
            return 1
        repo = Path(args.repo).expanduser().resolve()
        if not (repo / ".git").exists():
            proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
            if proc.returncode != 0:
                raise ValueError(f"not a git repository: {repo}")
            repo = Path(proc.stdout.strip())
        changed, git_errors = _git_changed_files(repo, args.base)
        report = _impact_report(args.task_id, changed, graph)
        report["base_revision"] = args.base or ""
        report["changed_revision"] = _git_head(repo)
        errors, warnings = validate_report_data("impact", report)
        errors.extend(git_errors)
        warnings.extend(graph_warnings)
        if args.out:
            out = Path(args.out).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
        ok = not errors
        payload = {
            "status": "PASS: impact report generated" if ok else "FAIL: generated impact report is invalid",
            "report": report,
            "out": args.out,
            "errors": errors,
            "warnings": warnings,
            "messages": [
                f"changed files: {len(changed)}",
                f"impacted contracts: {len(report['impacted_contracts'])}",
                f"required revalidation: {len(report['required_revalidation'])}",
            ],
        }
        _emit(payload, args.json)
        return 0 if ok else 1
    except Exception as exc:
        _emit({"status": "FAIL: could not generate impact report", "errors": [str(exc)]}, args.json)
        return 1


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower()).strip("-")
    return s[:48] or "task"


def _default_branch(contract: dict[str, Any]) -> str:
    source = _slug(str(contract.get("source_item") or "work"))
    task = _slug(str(contract.get("task_id") or contract.get("goal") or "task"))
    return f"agent/{source}/{task}"


def _workspace_parts(value: str | None, mode: str) -> tuple[str, str | None]:
    if not value:
        return ("worktree", None) if mode in {"coding", "release"} else ("scratch", None)
    if value in {"scratch", "worktree"}:
        return value, None
    if value.startswith("worktree:"):
        return "worktree", value.split(":", 1)[1]
    if value.startswith("dir:"):
        return "dir", value.split(":", 1)[1]
    raise ValueError("--workspace must be scratch, worktree, worktree:<path>, or dir:<path>")


def contract_body(contract: dict[str, Any]) -> str:
    dumped = yaml.safe_dump(contract, sort_keys=False).strip() if yaml else json.dumps(contract, indent=2)
    dod = "\n".join(f"- {x}" for x in contract.get("definition_of_done") or [])
    checks = "\n".join(f"- `{x}`" for x in contract.get("required_checks") or [])
    return f"""MAD task contract

## Goal
{contract.get('goal', '')}

## Definition of Done
{dod or '- (none declared)'}

## Required Checks
{checks or '- (none declared)'}

## Contract YAML
```yaml
{dumped}
```
"""


def cmd_create_task(args: argparse.Namespace) -> int:
    try:
        from hermes_cli import kanban_db as kb
        contract = load_contract(args.contract)
        errors, warnings = validate_contract(contract)
        if errors:
            _emit({"status": "FAIL: contract is invalid", "errors": errors, "warnings": warnings}, args.json)
            return 1
        owner = contract["owner_agent"]
        mode = str(contract.get("mode") or "coding")
        assignee = args.assignee or OWNER_TO_PROFILE[owner]
        workspace_kind, workspace_path = _workspace_parts(args.workspace or contract.get("workspace"), mode)
        branch = args.branch or contract.get("branch") or (None if workspace_kind != "worktree" else _default_branch(contract))
        parents = list(args.parent or [])
        if args.link_dependencies:
            parents.extend(str(d) for d in contract.get("dependencies") or [] if str(d).startswith("t_") or str(d).startswith("TASK"))
        title = f"{contract.get('task_id')}: {contract.get('goal')}"
        skills = ROLE_SKILLS.get(owner, [])
        with kb.connect(board=args.board) as conn:
            task_id = kb.create_task(
                conn,
                title=title,
                body=contract_body(contract),
                assignee=assignee,
                workspace_kind=workspace_kind,
                workspace_path=workspace_path,
                branch_name=branch,
                priority=args.priority,
                parents=parents,
                created_by="mad-workflow",
                idempotency_key=args.idempotency_key or f"mad:{contract.get('source_item')}:{contract.get('task_id')}",
                skills=skills,
                board=args.board,
            )
            kb.add_comment(conn, task_id, "mad-workflow", f"Created from MAD contract `{Path(args.contract).name}`. Owner role: `{owner}`. Required checks: {len(contract.get('required_checks') or [])}.")
        _emit({
            "status": "created Kanban task",
            "task_id": task_id,
            "messages": [f"task: {task_id}", f"assignee: {assignee}", f"workspace: {workspace_kind}{':' + workspace_path if workspace_path else ''}", f"branch: {branch or '(none)'}"],
            "warnings": warnings,
        }, args.json)
        return 0
    except Exception as exc:
        _emit({"status": "FAIL: could not create task", "errors": [str(exc)]}, args.json)
        return 1


def _norm_patterns(patterns: list[Any]) -> list[str]:
    out: list[str] = []
    for p in patterns or []:
        s = str(p).strip().lstrip("/")
        if not s:
            continue
        if s.endswith("/"):
            s += "**"
        out.append(s)
    return out


def _matches(path: str, patterns: list[str]) -> bool:
    p = path.lstrip("/")
    for pat in patterns:
        if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch("/" + p, pat):
            return True
        if pat.endswith("/**") and (p == pat[:-3].rstrip("/") or p.startswith(pat[:-3])):
            return True
    return False


def _git_changed_files(repo: Path, base: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    files: set[str] = set()

    def collect(cmd: list[str], *, fatal: bool = True) -> None:
        proc = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
        if proc.returncode != 0:
            msg = proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(cmd)}"
            if fatal:
                errors.append(msg)
            return
        for line in proc.stdout.splitlines():
            if line.strip():
                files.add(line.strip())

    if base:
        collect(["git", "diff", "--name-only", f"{base}...HEAD"], fatal=True)
    else:
        proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo, text=True, capture_output=True)
        if proc.returncode == 0 and proc.stdout.strip():
            collect(["git", "diff", "--name-only", f"{proc.stdout.strip()}...HEAD"], fatal=True)
        else:
            collect(["git", "diff", "--name-only", "HEAD~1...HEAD"], fatal=True)
    collect(["git", "diff", "--name-only"], fatal=True)
    collect(["git", "diff", "--cached", "--name-only"], fatal=True)
    collect(["git", "ls-files", "--others", "--exclude-standard"], fatal=True)
    return sorted(files), errors


def cmd_check_scope(args: argparse.Namespace) -> int:
    try:
        contract = load_contract(args.contract)
        errors, warnings = validate_contract(contract)
        if errors:
            _emit({"status": "FAIL: contract is invalid", "errors": errors, "warnings": warnings}, args.json)
            return 1
        repo = Path(args.repo).expanduser().resolve()
        if not (repo / ".git").exists():
            proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
            if proc.returncode != 0:
                raise ValueError(f"not a git repository: {repo}")
            repo = Path(proc.stdout.strip())
        changed, git_errors = _git_changed_files(repo, args.base)
        errors.extend(git_errors)
        allowed = _norm_patterns(contract.get("allowed_scope") or [])
        forbidden = _norm_patterns(contract.get("forbidden_scope") or [])
        outside = [f for f in changed if not _matches(f, allowed)]
        forbidden_hits = [f for f in changed if _matches(f, forbidden)]
        ok = not errors and not outside and not forbidden_hits
        _emit({
            "status": "PASS: diff stays within MAD scope" if ok else "FAIL: diff violates MAD scope",
            "changed_files": changed,
            "outside_allowed_scope": outside,
            "forbidden_scope_hits": forbidden_hits,
            "errors": errors,
            "warnings": warnings,
            "messages": [f"changed files: {len(changed)}", f"outside allowed_scope: {len(outside)}", f"forbidden hits: {len(forbidden_hits)}"],
        }, args.json)
        return 0 if ok else 1
    except Exception as exc:
        _emit({"status": "FAIL: could not check scope", "errors": [str(exc)]}, args.json)
        return 1


def _task_text(task: Any) -> str:
    if isinstance(task, str):
        return task
    if isinstance(task, dict):
        return str(task.get("title") or task.get("goal") or task.get("name") or "Untitled task")
    return str(task)


def _task_scope(task: Any, key: str) -> list[str]:
    if isinstance(task, dict):
        value = task.get(key)
        if isinstance(value, list):
            return list(map(str, value))
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


def _wave_role_and_mode(purpose: str, task: Any) -> tuple[str, str]:
    if isinstance(task, dict):
        owner = str(task.get("owner_agent") or "").strip()
        mode = str(task.get("mode") or "").strip()
        if owner and mode:
            return owner, mode
    task_text = _task_text(task).lower()
    purpose_text = purpose.lower()
    if "release" in task_text or "integrat" in task_text:
        return "release-agent", "release"
    if "qa" in task_text or "test" in task_text or "review" in task_text or "validat" in task_text:
        return "qa-agent", "qa"
    if "architect" in task_text or "contract" in task_text or "spec" in task_text or "design" in task_text:
        return "architect-agent", "architecture"
    if "release" in purpose_text or "integrat" in purpose_text:
        return "release-agent", "release"
    if "qa" in purpose_text or "test" in purpose_text or "review" in purpose_text or "validat" in purpose_text:
        return "qa-agent", "qa"
    if "architect" in purpose_text or "contract" in purpose_text or "spec" in purpose_text or "design" in purpose_text:
        return "architect-agent", "architecture"
    return "coding-agent", "coding"


def _default_checks(mode: str) -> list[str]:
    if mode == "architecture":
        return ["hermes mad graph validate .agents/contracts.yaml --repo ."]
    if mode == "qa":
        return ["hermes mad validate-report completion <report-path>", "hermes mad validate-report qa <report-path>"]
    if mode == "release":
        return ["hermes mad gate <task-id> --stage done"]
    return ["pytest"]


def _default_definition_of_done(mode: str) -> list[str]:
    defaults = {
        "architecture": [
            "Specification and acceptance criteria are testable and complete.",
            "Controlled contracts are proposed, classified, and registered.",
            "Architecture decisions are recorded where trade-offs exist.",
            "Open decisions are documented with owners.",
        ],
        "coding": [
            "Implementation satisfies the acceptance criteria within allowed scope.",
            "Required checks pass on the reported revision.",
            "Completion report lists changed files, checks, and downstream impact.",
        ],
        "qa": [
            "Every acceptance criterion has independent evidence.",
            "Scope, contract compatibility, and risk-relevant checks are verified.",
            "Quality-gate report is complete with a pass/fail/blocked decision.",
        ],
        "release": [
            "All dependencies are QA-approved at the same revision.",
            "Integrated checks pass on the integration branch.",
            "Release candidate summary, rollback statement, and PR body are ready.",
        ],
    }
    return defaults.get(mode, defaults["coding"])


def _contract_from_plan_task(source_item: str, summary: str, task: Any, index: int, owner: str, mode: str) -> dict[str, Any]:
    goal = _task_text(task)
    dependencies = _task_scope(task, "dependencies") or _task_scope(task, "depends_on")
    allowed_scope = _task_scope(task, "allowed_scope") or [".agents/**", "docs/**"] if mode in {"architecture", "qa", "release"} else _task_scope(task, "allowed_scope") or ["src/**", "tests/**"]
    forbidden_scope = _task_scope(task, "forbidden_scope")
    dod = _task_scope(task, "definition_of_done")
    if not dod:
        dod = _default_definition_of_done(mode)
    checks = _task_scope(task, "required_checks") or _default_checks(mode)
    return {
        "schema_version": "mad.task-contract/v1",
        "task_id": f"TASK-{index:03d}",
        "source_item": source_item,
        "owner_agent": owner,
        "goal": goal,
        "context": summary,
        "mode": mode,
        "allowed_scope": allowed_scope,
        "forbidden_scope": forbidden_scope,
        "dependencies": dependencies,
        "contracts_consumed": _task_scope(task, "contracts_consumed"),
        "contracts_produced_or_modified": _task_scope(task, "contracts_produced_or_modified"),
        "definition_of_done": dod,
        "required_checks": checks,
        "report_format": {
            "schema": "templates/completion-report.yaml",
            "required_fields": ["status", "changed_files", "tests_run", "blockers", "downstream_impact"],
        },
    }


def cmd_decompose(args: argparse.Namespace) -> int:
    try:
        plan = load_yaml_file(args.feature_plan)
        source_item = str(plan.get("source_item") or Path(args.feature_plan).stem)
        summary = str(plan.get("summary") or "")
        waves = plan.get("execution_waves") or []
        if not isinstance(waves, list) or not waves:
            raise ValueError("feature plan must contain execution_waves with tasks")
        out_dir = Path(args.out).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        generated: list[str] = []
        index = args.start
        for wave in waves:
            if not isinstance(wave, dict):
                continue
            purpose = str(wave.get("purpose") or "")
            tasks = wave.get("tasks") or []
            if not isinstance(tasks, list):
                raise ValueError(f"wave {wave.get('wave')} tasks must be a list")
            for task in tasks:
                owner, mode = _wave_role_and_mode(purpose, task)
                contract = _contract_from_plan_task(source_item, summary, task, index, owner, mode)
                filename = f"{contract['task_id']}-{_slug(contract['goal'])}.yaml"
                path = out_dir / filename
                path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
                generated.append(str(path))
                index += 1
        if not generated:
            raise ValueError("feature plan did not contain any tasks to decompose")
        _emit({
            "status": "generated draft MAD task contracts",
            "generated": generated,
            "messages": generated,
            "warnings": ["Review generated contracts before dispatch; TODO scope/check fields may need tightening."],
        }, args.json)
        return 0
    except Exception as exc:
        _emit({"status": "FAIL: could not decompose feature plan", "errors": [str(exc)]}, args.json)
        return 1

def _parse_dep_ids(deps: list[Any]) -> list[str]:
    """Extract task IDs from dependency entries (plain strings or dicts)."""
    ids: list[str] = []
    for d in deps or []:
        if isinstance(d, str):
            ids.append(d.strip())
        elif isinstance(d, dict):
            ids.append(str(d.get("task_id") or d.get("id") or "").strip())
    return [i for i in ids if i]


def _build_wave_contracts(feature_plan: str, out_dir: Path, start: int) -> tuple[list[dict[str, Any]], dict[int, list[int]]]:
    """Decompose a feature plan and return contracts + wave→contract indices mapping."""
    plan = load_yaml_file(feature_plan)
    source_item = str(plan.get("source_item") or Path(feature_plan).stem)
    summary = str(plan.get("summary") or "")
    waves = plan.get("execution_waves") or plan.get("waves") or []
    if not isinstance(waves, list) or not waves:
        raise ValueError("feature plan must contain execution_waves or waves with tasks")

    contracts: list[dict[str, Any]] = []
    wave_map: dict[int, list[int]] = {}
    index = start
    for wave_idx, wave in enumerate(waves):
        if not isinstance(wave, dict):
            continue
        purpose = str(wave.get("purpose") or "")
        tasks = wave.get("tasks") or []
        if not isinstance(tasks, list):
            raise ValueError(f"wave {wave.get('wave')} tasks must be a list")
        wave_indices: list[int] = []
        for task in tasks:
            owner, mode = _wave_role_and_mode(purpose, task)
            contract = _contract_from_plan_task(source_item, summary, task, index, owner, mode)
            contracts.append(contract)
            wave_indices.append(len(contracts) - 1)
            index += 1
        if wave_indices:
            wave_map[wave_idx] = wave_indices
    return contracts, wave_map


def cmd_run(args: argparse.Namespace) -> int:
    """hermes mad run — kick off the full MAD workflow from a feature plan."""
    try:
        from hermes_cli import kanban_db as kb
        board = args.board or "mad-workflow"
        out_dir = Path(args.out).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Decompose the feature plan into contracts
        contracts, wave_map = _build_wave_contracts(args.feature_plan, out_dir, 1)
        if not contracts:
            raise ValueError("feature plan did not produce any tasks")

        # Write contracts to disk
        written: list[str] = []
        for contract in contracts:
            filename = f"{contract['task_id']}-{_slug(contract['goal'])}.yaml"
            path = out_dir / filename
            path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            written.append(str(path))

        # 2. Validate each contract
        contract_errors: list[str] = []
        contract_warnings: list[str] = []
        for i, contract in enumerate(contracts):
            errs, warns = validate_contract(contract)
            if errs:
                contract_errors.extend(f"{contract['task_id']}: {e}" for e in errs)
            else:
                contract_warnings.extend(f"{contract['task_id']}: {w}" for w in warns)
        if contract_errors:
            _emit({
                "status": "FAIL: one or more generated contracts are invalid",
                "contracts": written,
                "errors": contract_errors,
                "messages": ["Draft contracts written to disk but contain validation errors. Review and fix before dispatch."],
            }, args.json)
            return 1

        if args.dry_run:
            _emit({
                "status": "dry-run: would create Kanban tasks",
                "contracts": written,
                "tasks": [{c["task_id"]: {"owner": c["owner_agent"], "goal": c["goal"], "mode": c["mode"]}} for c in contracts],
                "wave_map": {str(k): [contracts[i]["task_id"] for i in v] for k, v in wave_map.items()},
                "messages": [f"contracts written: {len(written)}"] + written,
            }, args.json)
            return 0

        # 3. Create Kanban tasks
        task_map: dict[str, str] = {}  # TASK-XXX -> kanban_task_id
        created_ids: list[str] = []
        with kb.connect(board=board) as conn:
            for contract in contracts:
                owner = contract["owner_agent"]
                mode = str(contract.get("mode") or "coding")
                assignee = OWNER_TO_PROFILE[owner]
                ws_kind, ws_path = _workspace_parts(None, mode)
                branch = _default_branch(contract) if ws_kind == "worktree" else None
                parents: list[str] = []
                skills = ROLE_SKILLS.get(owner, [])

                task_id = kb.create_task(
                    conn,
                    title=f"{contract['task_id']}: {contract['goal']}",
                    body=contract_body(contract),
                    assignee=assignee,
                    workspace_kind=ws_kind,
                    workspace_path=ws_path,
                    branch_name=branch,
                    priority=0,
                    parents=parents,
                    created_by="mad-workflow",
                    idempotency_key=f"mad:{contract.get('source_item')}:{contract.get('task_id')}",
                    skills=skills,
                    board=board,
                )
                task_map[contract["task_id"]] = task_id
                created_ids.append(task_id)

        # 4. Link parent→child dependencies
        links_created = 0
        with kb.connect(board=board) as conn:
            for contract in contracts:
                child_tid = task_map.get(contract["task_id"])
                if not child_tid:
                    continue
                for dep_id in _parse_dep_ids(contract.get("dependencies") or []):
                    parent_tid = task_map.get(dep_id)
                    if parent_tid and parent_tid != child_tid:
                        kb.link_tasks(conn, parent_tid, child_tid)
                        links_created += 1

        # 5. Promote first-wave tasks to Ready
        promoted = 0
        if wave_map and 0 in wave_map:
            with kb.connect(board=board) as conn:
                for idx in wave_map[0]:
                    tid = task_map.get(contracts[idx]["task_id"])
                    if tid:
                        kb.promote_task(conn, tid, actor="mad-workflow")
                        promoted += 1

        # 6. Dispatch if requested
        dispatch_result = None
        if args.dispatch:
            proc = subprocess.run(
                ["hermes", "kanban", "dispatch", "--board", board, "--max", str(len(created_ids) + 2), "--json"],
                text=True, capture_output=True
            )
            try:
                dispatch_result = json.loads(proc.stdout) if proc.stdout.strip() else {}
            except json.JSONDecodeError:
                dispatch_result = {"output": proc.stdout[:500]}

        _emit({
            "status": "MAD run complete",
            "contracts": written,
            "tasks_created": len(created_ids),
            "task_ids": created_ids,
            "links_created": links_created,
            "promoted": promoted,
            "dispatch": dispatch_result,
            "messages": [
                f"board: {board}",
                f"contracts: {len(written)}",
                f"tasks created: {len(created_ids)}",
                f"dependency links: {links_created}",
                f"first-wave tasks promoted: {promoted}",
            ],
        }, args.json)
        return 0
    except Exception as exc:
        _emit({"status": "FAIL: could not complete MAD run", "errors": [str(exc)]}, args.json)
        return 1


def cmd_prompt(args: argparse.Namespace) -> int:
    contract = load_contract(args.contract)
    role = args.role or contract.get("owner_agent")
    profile = OWNER_TO_PROFILE.get(str(role), str(role))
    print(f"You are {role} running under Hermes profile `{profile}`.")
    print()
    print(f"Task: {contract.get('task_id')}")
    print(f"Goal: {contract.get('goal')}")
    print(f"Mode: {contract.get('mode')}")
    print()
    print("Allowed scope:")
    for x in contract.get("allowed_scope") or []:
        print(f"- {x}")
    print("\nForbidden scope:")
    for x in contract.get("forbidden_scope") or []:
        print(f"- {x}")
    print("\nRequired checks:")
    for x in contract.get("required_checks") or []:
        print(f"- {x}")
    print("\nStop and block the Kanban task if required work touches forbidden scope, shared contracts need unapproved changes, or required checks cannot run.")
    return 0

