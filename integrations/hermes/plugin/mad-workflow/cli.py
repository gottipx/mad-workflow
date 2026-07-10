from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
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
    "task_id", "source_item", "owner_agent", "goal", "mode",
    "allowed_scope", "forbidden_scope", "dependencies", "contracts_consumed",
    "contracts_produced_or_modified", "definition_of_done", "required_checks",
]

VALID_MODES = {"architecture", "coding", "qa", "release", "revalidation", "planning"}


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
    if action == "create-task":
        return cmd_create_task(args)
    if action == "check-scope":
        return cmd_check_scope(args)
    if action == "prompt":
        return cmd_prompt(args)
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


def validate_contract(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
    owner = str(data.get("owner_agent", "")).strip()
    if owner and owner not in OWNER_TO_PROFILE:
        errors.append(f"owner_agent must be one of {sorted(OWNER_TO_PROFILE)}, got {owner!r}")
    mode = str(data.get("mode", "")).strip()
    if mode and mode not in VALID_MODES:
        errors.append(f"mode must be one of {sorted(VALID_MODES)}, got {mode!r}")
    for field in ["allowed_scope", "forbidden_scope", "dependencies", "contracts_consumed", "contracts_produced_or_modified", "definition_of_done", "required_checks"]:
        if field in data and not isinstance(data[field], list):
            errors.append(f"{field} must be a list")
    allowed = set(map(str, data.get("allowed_scope") or []))
    forbidden = set(map(str, data.get("forbidden_scope") or []))
    overlap = sorted(allowed & forbidden)
    if overlap:
        errors.append(f"allowed_scope overlaps forbidden_scope: {', '.join(overlap)}")
    if mode == "coding" and not data.get("required_checks"):
        warnings.append("coding task has no required_checks")
    if not data.get("allowed_scope"):
        errors.append("allowed_scope must not be empty")
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
    warnings: list[str] = []
    files: set[str] = set()
    def collect(cmd: list[str]) -> None:
        proc = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
        if proc.returncode != 0:
            warnings.append(proc.stderr.strip() or f"command failed: {' '.join(cmd)}")
            return
        for line in proc.stdout.splitlines():
            if line.strip():
                files.add(line.strip())
    if base:
        collect(["git", "diff", "--name-only", f"{base}...HEAD"])
    else:
        proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo, text=True, capture_output=True)
        if proc.returncode == 0 and proc.stdout.strip():
            collect(["git", "diff", "--name-only", f"{proc.stdout.strip()}...HEAD"])
        else:
            collect(["git", "diff", "--name-only", "HEAD~1...HEAD"])
    collect(["git", "diff", "--name-only"])
    collect(["git", "diff", "--cached", "--name-only"])
    return sorted(files), warnings


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
        changed, git_warnings = _git_changed_files(repo, args.base)
        warnings.extend(git_warnings)
        allowed = _norm_patterns(contract.get("allowed_scope") or [])
        forbidden = _norm_patterns(contract.get("forbidden_scope") or [])
        outside = [f for f in changed if not _matches(f, allowed)]
        forbidden_hits = [f for f in changed if _matches(f, forbidden)]
        ok = not outside and not forbidden_hits
        _emit({
            "status": "PASS: diff stays within MAD scope" if ok else "FAIL: diff violates MAD scope",
            "changed_files": changed,
            "outside_allowed_scope": outside,
            "forbidden_scope_hits": forbidden_hits,
            "warnings": warnings,
            "messages": [f"changed files: {len(changed)}", f"outside allowed_scope: {len(outside)}", f"forbidden hits: {len(forbidden_hits)}"],
        }, args.json)
        return 0 if ok else 1
    except Exception as exc:
        _emit({"status": "FAIL: could not check scope", "errors": [str(exc)]}, args.json)
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

