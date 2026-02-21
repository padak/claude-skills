#!/usr/bin/env python3
"""
swarm.py — CLI tool for managing swarm skill execution.

Subcommands:
  prereq       Check prerequisites (CLAUDE.md, Makefile, git worktree support)
  parse        Validate plan file, output execution graph, create/read status file
  update       Update phase status in the status file
  status       Display current state of all phases
  next         Show phases ready to start (dependencies DONE)
  check-group  Show parallel groups where all phases are PR_APPROVED
  add-phase    Add a synthetic phase (for integration fixes)
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

# Phase statuses in lifecycle order
VALID_STATUSES = {
    "PENDING",
    "DISPATCHED",
    "DEVELOPING",
    "FOR_REVIEW",
    "REJECTED",
    "FIXING",
    "MERGED",
    "PR_APPROVED",
    "DONE",
    "ESCALATED",
}

REQUIRED_SECTIONS = {
    "Branch",
    "Scope",
    "Files to Create/Modify",
    "Acceptance Criteria",
    "Tests Required",
}

REQUIRED_MAKEFILE_TARGETS = {"setup", "build", "test", "worktree", "worktree-remove"}

# Sections expected in CLAUDE.md for swarm to work effectively.
# Each entry: (heading pattern regex, human-readable label)
REQUIRED_CLAUDE_MD_SECTIONS = [
    (
        r"(?i)##?\s*(tech\s*)?stack|##?\s*tools|##?\s*frameworks",
        "Stack (tools, frameworks, versions)",
    ),
    (r"(?i)##?\s*test", "Testing conventions"),
    (r"(?i)##?\s*(code\s*quality|lint|format)", "Code quality standards"),
    (r"(?i)##?\s*project\s*structure", "Project structure"),
    (r"(?i)##?\s*config|##?\s*env", "Config management"),
]


def error(msg: str) -> None:
    """Print error to stderr and exit."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def validate_branch_name(branch: str, context: str = "") -> None:
    """Validate branch name for git compatibility and flat worktree layout.

    Two-stage validation:
    1. git check-ref-format --branch — catches all Git-specific problems
    2. Extra check on / and \\ — Git allows them but they break flat worktree layout
    """
    if not branch:
        error(f"Empty branch name{f' (from {context})' if context else ''}")
    result = subprocess.run(
        ["git", "check-ref-format", "--branch", branch],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        error(
            f"Invalid branch name '{branch}'{f' (from {context})' if context else ''}: {result.stderr.strip()}"
        )
    if "/" in branch or "\\" in branch:
        error(
            f"Branch name '{branch}'{f' (from {context})' if context else ''} contains slashes. Use hyphens instead."
        )


def status_file_path(plan_file: Path) -> Path:
    """Return the status file path for a given plan file."""
    return plan_file.parent / f"{plan_file.name}.swarm_status.json"


def resolve_plan_file(path_str: str) -> Path:
    """Resolve and validate plan file path exists."""
    plan_file = Path(path_str).resolve()
    if not plan_file.exists():
        error(f"Plan file not found: {plan_file}")
    return plan_file


def parse_phases(content: str) -> list[dict]:
    """Parse phases from plan file content. Returns list of phase dicts."""
    phases = []
    # Match opening tags: <!-- PHASE:N --> or <!-- PHASE:N DEPENDS:1,2 -->
    open_pattern = re.compile(r"<!--\s*PHASE:(\d+)(?:\s+DEPENDS:([\d,]+))?\s*-->")
    close_pattern = re.compile(r"<!--\s*/PHASE:(\d+)\s*-->")

    open_tags = list(open_pattern.finditer(content))
    close_tags = list(close_pattern.finditer(content))

    # Build close tag map
    close_map = {}
    for m in close_tags:
        phase_id = int(m.group(1))
        if phase_id in close_map:
            error(f"Duplicate closing tag for Phase {phase_id}")
        close_map[phase_id] = m

    for m in open_tags:
        phase_id = int(m.group(1))
        depends_str = m.group(2)
        depends = [int(d) for d in depends_str.split(",")] if depends_str else []

        # Check for duplicate
        if any(p["id"] == phase_id for p in phases):
            error(f"Duplicate opening tag for Phase {phase_id}")

        # Find matching close tag
        if phase_id not in close_map:
            error(f"No closing tag for Phase {phase_id}")

        close_match = close_map[phase_id]
        if close_match.start() < m.end():
            error(f"Closing tag for Phase {phase_id} appears before opening tag")

        phase_content = content[m.end() : close_match.start()]

        # Extract branch name
        branch_match = re.search(r"###\s*Branch\s*\n\s*`([^`]+)`", phase_content)
        branch = branch_match.group(1) if branch_match else f"phase-{phase_id}"
        validate_branch_name(branch, context=f"Phase {phase_id}")

        # Extract name from heading
        name_match = re.search(r"##\s*Phase\s*\d+:\s*(.+)", phase_content)
        name = name_match.group(1).strip() if name_match else f"Phase {phase_id}"

        # Extract files to create/modify
        files = []
        files_match = re.search(
            r"###\s*Files to Create/Modify\s*\n(.*?)(?=###|\Z)",
            phase_content,
            re.DOTALL,
        )
        if files_match:
            for line in files_match.group(1).strip().splitlines():
                # Extract file path: strip list markers, backticks, and trailing descriptions
                line = line.strip().lstrip("- ").strip()
                if line.startswith("`"):
                    line = line.split("`")[1]
                elif " " in line and "—" in line:
                    line = line.split("—")[0].strip().strip("`")
                else:
                    line = line.strip("`")
                if line:
                    files.append(line)

        # Check required sections
        missing = []
        for section in REQUIRED_SECTIONS:
            if not re.search(rf"###\s*{re.escape(section)}", phase_content):
                missing.append(section)

        if missing:
            error(f"Phase {phase_id} missing required sections: {', '.join(missing)}")

        phases.append(
            {
                "id": phase_id,
                "name": name,
                "branch": branch,
                "depends": depends,
                "files": files,
            }
        )

    return phases


def detect_implicit_dependencies(phases: list[dict]) -> list[dict]:
    """Add implicit dependencies from overlapping files.

    When multiple phases touch the same file, they must run sequentially.
    All later phases get a dependency on the earliest phase that owns the file.
    """
    file_owners = {}
    for phase in sorted(phases, key=lambda p: p["id"]):
        for f in phase["files"]:
            if f in file_owners:
                earlier = file_owners[f]
                if earlier not in phase["depends"]:
                    phase["depends"].append(earlier)
            else:
                file_owners[f] = phase["id"]
    return phases


def check_dependency_refs(phases: list[dict]) -> None:
    """Verify all dependency references point to existing phases."""
    phase_ids = {p["id"] for p in phases}
    for phase in phases:
        for dep in phase["depends"]:
            if dep not in phase_ids:
                error(
                    f"Phase {phase['id']} depends on Phase {dep} which does not exist"
                )


def detect_cycles(phases: list[dict]) -> None:
    """Detect cycles using Kahn's algorithm. Exit with error if cycle found."""
    phase_ids = {p["id"] for p in phases}
    in_degree = {pid: 0 for pid in phase_ids}
    adjacency = defaultdict(list)

    for phase in phases:
        for dep in phase["depends"]:
            adjacency[dep].append(phase["id"])
            in_degree[phase["id"]] += 1

    queue = deque(pid for pid, deg in in_degree.items() if deg == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(phase_ids):
        remaining = [pid for pid, deg in in_degree.items() if deg > 0]
        error(f"Dependency cycle detected involving phases: {remaining}")


def build_execution_groups(phases: list[dict]) -> list[list[int]]:
    """Build execution groups via topological sort. Returns list of groups."""
    phase_map = {p["id"]: p for p in phases}
    in_degree = {p["id"]: len(p["depends"]) for p in phases}
    adjacency = defaultdict(list)

    for phase in phases:
        for dep in phase["depends"]:
            adjacency[dep].append(phase["id"])

    groups = []
    remaining = set(phase_map.keys())

    while remaining:
        # Find all with in_degree 0 among remaining
        group = [pid for pid in remaining if in_degree[pid] == 0]
        if not group:
            break  # Cycle — already caught by detect_cycles
        group.sort()
        groups.append(group)
        for pid in group:
            remaining.remove(pid)
            for neighbor in adjacency[pid]:
                in_degree[neighbor] -= 1

    return groups


def assign_groups(
    phases: list[dict], execution_groups: list[list[int]]
) -> dict[int, str | None]:
    """Assign group labels to phases. Solo phases get None, parallel phases get A, B, C...

    Supports up to 26 parallel groups (A-Z). Raises error if exceeded.
    """
    group_labels = {}
    label_idx = 0
    for group in execution_groups:
        if len(group) > 1:
            if label_idx > 25:
                error("Too many parallel execution groups (max 26, A-Z)")
            label = chr(ord("A") + label_idx)
            label_idx += 1
            for pid in group:
                group_labels[pid] = label
        else:
            group_labels[group[0]] = None
    return group_labels


def check_makefile(plan_file: Path) -> list[str]:
    """Check that Makefile exists and has required targets. Returns list of issues."""
    issues = []
    # Look for Makefile in common locations relative to plan file
    candidates = [
        plan_file.parent / "Makefile",
        plan_file.parent.parent / "Makefile",
        plan_file.parent.parent / "main" / "Makefile",
    ]

    makefile = None
    for c in candidates:
        if c.exists():
            makefile = c
            break

    if not makefile:
        issues.append("Makefile not found. Run `/swarm init` first.")
        return issues

    content = makefile.read_text()
    missing_targets = []
    for target in REQUIRED_MAKEFILE_TARGETS:
        if not re.search(rf"^{re.escape(target)}\s*:", content, re.MULTILINE):
            missing_targets.append(target)

    if missing_targets:
        issues.append(
            f"Makefile missing required targets: {', '.join(missing_targets)}. "
            f"Run `/swarm init` to create them."
        )

    return issues


def check_claude_md(plan_file: Path) -> list[str]:
    """Check that CLAUDE.md exists and covers required sections. Returns list of issues."""
    issues = []
    # Look for CLAUDE.md in common locations
    candidates = [
        plan_file.parent / "CLAUDE.md",
        plan_file.parent.parent / "CLAUDE.md",
        plan_file.parent.parent / "main" / "CLAUDE.md",
    ]

    claude_md = None
    for c in candidates:
        if c.exists():
            claude_md = c
            break

    if not claude_md:
        issues.append(
            "CLAUDE.md not found. Create one with project standards before running swarm."
        )
        return issues

    content = claude_md.read_text()
    for pattern, label in REQUIRED_CLAUDE_MD_SECTIONS:
        if not re.search(pattern, content):
            issues.append(f"CLAUDE.md missing section: {label}")

    return issues


def check_git_worktree() -> list[str]:
    """Check that git worktree support is available. Returns list of issues."""
    issues = []
    if not shutil.which("git"):
        issues.append("git not found in PATH")
        return issues

    result = subprocess.run(
        ["git", "worktree", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        issues.append(f"git worktree not available: {result.stderr.strip()}")

    return issues


def check_gh_cli() -> list[str]:
    """Check that GitHub CLI (gh) is installed and authenticated. Returns list of issues."""
    issues = []
    if not shutil.which("gh"):
        issues.append(
            "gh (GitHub CLI) not found in PATH. Install: https://cli.github.com/"
        )
        return issues

    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        issues.append(
            f"gh not authenticated: {result.stderr.strip()}. Run `gh auth login`."
        )

    return issues


def check_make_cli() -> list[str]:
    """Check that make is available in PATH. Returns list of issues."""
    issues = []
    if not shutil.which("make"):
        issues.append("make not found in PATH")
    return issues


def check_directory_structure(plan_file: Path) -> list[str]:
    """Check that main/ and worktrees/ directories exist with correct layout.

    Walks up from the plan file to find the project root containing main/.
    """
    issues = []
    candidates = [
        plan_file.parent,
        plan_file.parent.parent,
        plan_file.parent.parent.parent,
    ]

    project_root = None
    for candidate in candidates:
        if (candidate / "main").is_dir():
            project_root = candidate
            break

    if project_root is None:
        issues.append(
            "Directory 'main/' not found. "
            "Swarm expects a worktree layout: project-root/main/ (primary checkout) "
            "and project-root/worktrees/. See worktree-guide.md for setup."
        )
        return issues

    main_dir = project_root / "main"
    if not (main_dir / ".git").exists():
        issues.append(
            f"'{main_dir}' exists but is not a git repository (no .git found)"
        )

    worktrees_dir = project_root / "worktrees"
    if not worktrees_dir.is_dir():
        issues.append(
            f"Directory 'worktrees/' not found at {project_root}. "
            f"Create it with: mkdir -p {worktrees_dir}"
        )

    return issues


def check_clean_worktree(plan_file: Path) -> list[str]:
    """Check that the main checkout has no uncommitted changes. Returns list of issues."""
    issues = []
    # Find main/ directory (same walk-up logic)
    candidates = [
        plan_file.parent,
        plan_file.parent.parent,
        plan_file.parent.parent.parent,
    ]

    main_dir = None
    for candidate in candidates:
        if (candidate / "main").is_dir():
            main_dir = candidate / "main"
            break

    if main_dir is None:
        return issues  # check_directory_structure will catch this

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=main_dir,
    )
    if result.returncode == 0 and result.stdout.strip():
        issues.append(
            f"Uncommitted changes in {main_dir}. Commit or stash before running swarm."
        )

    return issues


def check_remote_origin(plan_file: Path) -> list[str]:
    """Check that a remote origin is configured. Returns list of issues."""
    issues = []
    candidates = [
        plan_file.parent,
        plan_file.parent.parent,
        plan_file.parent.parent.parent,
    ]

    main_dir = None
    for candidate in candidates:
        if (candidate / "main").is_dir():
            main_dir = candidate / "main"
            break

    if main_dir is None:
        return issues  # check_directory_structure will catch this

    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=main_dir,
    )
    if result.returncode != 0:
        issues.append(
            "No remote 'origin' configured. Swarm needs a remote to push branches and create PRs."
        )

    return issues


def check_toolchain(plan_file: Path) -> list[str]:
    """Check that project toolchain works by running `make build`. Returns list of issues."""
    issues = []
    candidates = [
        plan_file.parent,
        plan_file.parent.parent,
        plan_file.parent.parent.parent,
    ]

    main_dir = None
    for candidate in candidates:
        if (candidate / "main").is_dir():
            main_dir = candidate / "main"
            break

    if main_dir is None:
        return issues  # check_directory_structure will catch this

    makefile = main_dir / "Makefile"
    if not makefile.exists():
        return issues  # check_makefile will catch this

    result = subprocess.run(
        ["make", "build"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=main_dir,
    )
    if result.returncode != 0:
        stderr_tail = (
            result.stderr.strip().splitlines()[-5:] if result.stderr.strip() else []
        )
        detail = "\n".join(stderr_tail)
        issues.append(f"`make build` failed in {main_dir}:\n{detail}")

    return issues


def load_status(plan_file: Path) -> dict:
    """Load status file. Returns empty dict if not found."""
    sf = status_file_path(plan_file)
    if not sf.exists():
        return {}
    try:
        return json.loads(sf.read_text())
    except json.JSONDecodeError as e:
        error(f"Corrupt status file {sf}: {e}")


def require_status(plan_file: Path) -> dict:
    """Load status file, exit with error if not found."""
    status_data = load_status(plan_file)
    if not status_data:
        error(f"No status file found for {plan_file}. Run `swarm.py parse` first.")
    return status_data


def save_status(plan_file: Path, status_data: dict) -> None:
    """Save status file."""
    sf = status_file_path(plan_file)
    sf.write_text(json.dumps(status_data, indent=2) + "\n")


def init_status(plan_file: Path, phases: list[dict], group_labels: dict) -> dict:
    """Initialize status data from parsed phases."""
    sf = status_file_path(plan_file)
    if sf.exists():
        try:
            return json.loads(sf.read_text())
        except json.JSONDecodeError as e:
            error(f"Corrupt status file {sf}: {e}")

    status_data = {
        "plan_file": str(plan_file),
        "base_branch": None,  # Set by Tech Lead at runtime
        "phases": {},
    }
    for phase in phases:
        status_data["phases"][str(phase["id"])] = {
            "status": "PENDING",
            "pr": None,
            "attempts": 0,
            "group": group_labels.get(phase["id"]),
        }
    save_status(plan_file, status_data)
    return status_data


# ---- Subcommands ----


def cmd_prereq(args: argparse.Namespace) -> None:
    """Check all prerequisites before running swarm."""
    plan_file = resolve_plan_file(args.plan_file)

    all_issues: list[tuple[str, list[str]]] = []

    # 1. CLI tools
    all_issues.append(("gh CLI", check_gh_cli()))
    all_issues.append(("make", check_make_cli()))
    all_issues.append(("Git worktree", check_git_worktree()))

    # 2. Directory structure & git state
    all_issues.append(("Directory layout", check_directory_structure(plan_file)))
    all_issues.append(("Remote origin", check_remote_origin(plan_file)))
    all_issues.append(("Clean worktree", check_clean_worktree(plan_file)))

    # 3. Project config
    all_issues.append(("CLAUDE.md", check_claude_md(plan_file)))
    all_issues.append(("Makefile", check_makefile(plan_file)))

    # 4. Plan file structure (parse without exiting on error)
    plan_issues = []
    try:
        content = plan_file.read_text()
        phases = parse_phases(content)
        if not phases:
            plan_issues.append("No phases found in plan file")
        else:
            check_dependency_refs(phases)
            phases = detect_implicit_dependencies(phases)
            detect_cycles(phases)
    except SystemExit:
        # parse_phases and friends call error() which calls sys.exit
        # Catch and report — the error was already printed to stderr
        plan_issues.append("Plan file has structural errors (see above)")
    all_issues.append(("Plan file", plan_issues))

    # 5. Toolchain (run last — slowest check, skip if earlier checks failed)
    has_blockers = any(issues for _, issues in all_issues)
    if has_blockers:
        all_issues.append(
            ("Toolchain (make build)", ["Skipped — fix above issues first"])
        )
    else:
        all_issues.append(("Toolchain (make build)", check_toolchain(plan_file)))

    # Report
    has_errors = False
    for category, issues in all_issues:
        if issues:
            has_errors = True
            print(f"FAIL  {category}:")
            for issue in issues:
                print(f"        {issue}")
        else:
            print(f"OK    {category}")

    if has_errors:
        print(
            "\nPrerequisite check FAILED. Fix the issues above before running /swarm."
        )
        sys.exit(1)
    else:
        print("\nAll prerequisites OK.")


def cmd_parse(args: argparse.Namespace) -> None:
    """Parse and validate plan file, output execution graph."""
    plan_file = resolve_plan_file(args.plan_file)
    content = plan_file.read_text()

    # Parse and validate
    phases = parse_phases(content)
    if not phases:
        error("No phases found in plan file")

    check_dependency_refs(phases)
    phases = detect_implicit_dependencies(phases)
    detect_cycles(phases)

    # Check Makefile
    makefile_issues = check_makefile(plan_file)
    if makefile_issues:
        for issue in makefile_issues:
            error(issue)

    # Build execution graph
    execution_groups = build_execution_groups(phases)
    group_labels = assign_groups(phases, execution_groups)

    # Record base branch (must run inside a git repo)
    main_dir = None
    for candidate in [
        plan_file.parent,
        plan_file.parent.parent,
        plan_file.parent.parent.parent,
    ]:
        if (candidate / "main").is_dir():
            main_dir = candidate / "main"
            break
    if main_dir is None:
        main_dir = Path.cwd()  # fallback: assume cwd is inside git repo

    base_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
        cwd=main_dir,
    ).stdout.strip()

    # Init or load status
    status_data = init_status(plan_file, phases, group_labels)
    if status_data.get("base_branch") is None:
        status_data["base_branch"] = base_branch
        save_status(plan_file, status_data)

    # Output
    result = {
        "plan_file": str(plan_file),
        "phases": [
            {
                "id": p["id"],
                "name": p["name"],
                "branch": p["branch"],
                "depends": p["depends"],
                "files": p["files"],
                "group": group_labels.get(p["id"]),
            }
            for p in phases
        ],
        "execution_groups": execution_groups,
        "status": status_data.get("phases", {}),
    }
    print(json.dumps(result, indent=2))


def cmd_update(args: argparse.Namespace) -> None:
    """Update phase status."""
    plan_file = resolve_plan_file(args.plan_file)
    status_data = require_status(plan_file)

    if args.status not in VALID_STATUSES:
        error(
            f"Invalid status '{args.status}'. Valid: {', '.join(sorted(VALID_STATUSES))}"
        )

    phases = args.phase
    prs = args.pr if args.pr else [None] * len(phases)

    # Pad PRs if fewer than phases
    while len(prs) < len(phases):
        prs.append(None)

    for i, phase_id in enumerate(phases):
        pid = str(phase_id)
        if pid not in status_data.get("phases", {}):
            error(f"Phase {phase_id} not found in status file")

        status_data["phases"][pid]["status"] = args.status
        if prs[i]:
            status_data["phases"][pid]["pr"] = prs[i]
        if args.attempts is not None:
            status_data["phases"][pid]["attempts"] = args.attempts
        else:
            # Auto-increment attempts on REJECTED
            if args.status == "REJECTED":
                status_data["phases"][pid]["attempts"] += 1

    save_status(plan_file, status_data)
    print(f"Updated phase(s) {phases} to {args.status}")


def cmd_status(args: argparse.Namespace) -> None:
    """Display current state of all phases."""
    plan_file = resolve_plan_file(args.plan_file)
    status_data = require_status(plan_file)

    print(f"Plan: {status_data.get('plan_file', '?')}")
    print(f"Base branch: {status_data.get('base_branch', '(not set)')}")
    print()
    print(f"{'Phase':<8} {'Status':<14} {'PR':<8} {'Attempts':<10} {'Group':<6}")
    print("-" * 50)
    for pid, info in sorted(status_data.get("phases", {}).items(), key=lambda x: x[0]):
        print(
            f"{pid:<8} {info['status']:<14} {info.get('pr') or '-':<8} "
            f"{info.get('attempts', 0):<10} {info.get('group') or '-':<6}"
        )


def cmd_next(args: argparse.Namespace) -> None:
    """Show phases ready to start (all dependencies DONE)."""
    plan_file = resolve_plan_file(args.plan_file)
    status_data = require_status(plan_file)

    # Re-parse plan to get dependency info
    content = plan_file.read_text()
    phases = parse_phases(content)
    phases = detect_implicit_dependencies(phases)

    phase_statuses = status_data.get("phases", {})
    done_phases = {
        int(pid) for pid, info in phase_statuses.items() if info["status"] == "DONE"
    }

    ready = []
    for phase in phases:
        pid = str(phase["id"])
        if phase_statuses.get(pid, {}).get("status") != "PENDING":
            continue
        if all(dep in done_phases for dep in phase["depends"]):
            ready.append(phase)

    result = [{"id": p["id"], "name": p["name"], "branch": p["branch"]} for p in ready]

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if ready:
            print("Phases ready to start:")
            for p in ready:
                print(f"  Phase {p['id']}: {p['name']} (branch: {p['branch']})")
        else:
            print("No phases ready to start.")


def cmd_check_group(args: argparse.Namespace) -> None:
    """Show parallel groups where all phases are PR_APPROVED (ready for integration)."""
    plan_file = resolve_plan_file(args.plan_file)
    status_data = require_status(plan_file)

    # Group phases by their group label
    groups = defaultdict(list)
    for pid, info in status_data.get("phases", {}).items():
        group = info.get("group")
        if group:
            groups[group].append(
                {"id": pid, "status": info["status"], "pr": info.get("pr")}
            )

    ready_groups = []
    for group_label, members in sorted(groups.items()):
        if all(m["status"] == "PR_APPROVED" for m in members):
            ready_groups.append(
                {
                    "group": group_label,
                    "phases": [{"id": m["id"], "pr": m["pr"]} for m in members],
                }
            )

    if args.json:
        print(json.dumps({"groups": ready_groups}, indent=2))
    else:
        if ready_groups:
            print("Parallel groups ready for integration review:")
            for g in ready_groups:
                phase_ids = [str(p["id"]) for p in g["phases"]]
                print(f"  Group {g['group']}: Phases {', '.join(phase_ids)}")
        else:
            print("No parallel groups ready for integration review.")


def cmd_add_phase(args: argparse.Namespace) -> None:
    """Add a synthetic phase to the status file (for integration fixes)."""
    plan_file = resolve_plan_file(args.plan_file)
    status_data = require_status(plan_file)

    phase_id = args.id
    if phase_id in status_data.get("phases", {}):
        error(f"Phase '{phase_id}' already exists in status file")

    # Validate branch name
    validate_branch_name(args.branch, context=f"synthetic phase '{args.id}'")

    # Validate that dependency phases exist
    for dep in args.depends:
        if str(dep) not in status_data.get("phases", {}):
            error(f"Dependency phase '{dep}' not found in status file")

    status_data["phases"][phase_id] = {
        "status": "PENDING",
        "pr": None,
        "attempts": 0,
        "group": None,
        "synthetic": True,
        "branch": args.branch,
        "depends": args.depends,
    }

    save_status(plan_file, status_data)
    print(f"Added synthetic phase '{phase_id}' depending on {args.depends}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Swarm skill CLI — manage phased plan execution",
        prog="swarm.py",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prereq
    p_prereq = subparsers.add_parser("prereq", help="Check all prerequisites")
    p_prereq.add_argument("plan_file", help="Path to plan file")

    # parse
    p_parse = subparsers.add_parser(
        "parse", help="Validate plan and output execution graph"
    )
    p_parse.add_argument("plan_file", help="Path to plan file")

    # update
    p_update = subparsers.add_parser("update", help="Update phase status")
    p_update.add_argument("plan_file", help="Path to plan file")
    p_update.add_argument(
        "--phase", type=str, nargs="+", required=True, help="Phase ID(s)"
    )
    p_update.add_argument("--status", required=True, help="New status")
    p_update.add_argument("--pr", nargs="+", help="PR number(s)")
    p_update.add_argument("--attempts", type=int, help="Attempt count")

    # status
    p_status = subparsers.add_parser(
        "status", help="Display current state of all phases"
    )
    p_status.add_argument("plan_file", help="Path to plan file")

    # next
    p_next = subparsers.add_parser("next", help="Show phases ready to start")
    p_next.add_argument("plan_file", help="Path to plan file")
    p_next.add_argument("--json", action="store_true", help="Output as JSON only")

    # check-group
    p_group = subparsers.add_parser(
        "check-group", help="Show parallel groups ready for integration"
    )
    p_group.add_argument("plan_file", help="Path to plan file")
    p_group.add_argument("--json", action="store_true", help="Output as JSON only")

    # add-phase
    p_add = subparsers.add_parser(
        "add-phase", help="Add synthetic phase for integration fixes"
    )
    p_add.add_argument("plan_file", help="Path to plan file")
    p_add.add_argument("--id", required=True, help="Phase ID (e.g. I-A)")
    p_add.add_argument(
        "--depends", nargs="+", required=True, help="Phase IDs this depends on"
    )
    p_add.add_argument("--branch", required=True, help="Branch name for this phase")
    p_add.add_argument(
        "--synthetic",
        action="store_true",
        default=True,
        help="Mark as synthetic (default)",
    )

    args = parser.parse_args()

    commands = {
        "prereq": cmd_prereq,
        "parse": cmd_parse,
        "update": cmd_update,
        "status": cmd_status,
        "next": cmd_next,
        "check-group": cmd_check_group,
        "add-phase": cmd_add_phase,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
