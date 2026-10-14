"""Progress auditor collector: every mechanically checkable fact, with its source.

Writes the facts to .claude/auditor/runs/<YYYY-MM-DD HHMM>.json and prints a short
summary. Stdlib only. The only state-changing commands it runs are `git fetch origin`
and `git worktree add/remove` on a path inside its own temporary directory.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

BUILD_ORDER = "07 Build/Build order.md"
MILESTONE_LINE = re.compile(r"\*\*(M\d+)\*\*\s+D([12])\s+(\d{1,2}):(\d{2}):\s*(.+?)\.?\s*$")
OFFSET = re.compile(r"([+-])(\d{2}):(\d{2})")
GITHUB_REPO = re.compile(r"[\w.-]+/[\w.-]+")
GIT_TIMEOUT_S = 60
COMMIT_LIMIT = 150
BRANCH_PREFIX = re.compile(r"^(feature|fix|chore|docs|refactor|test)/")
LONG_LIVED_BRANCHES = {"HEAD", "main", "develop"}
ATTRIBUTION = re.compile(r"(?im)^\s*co-authored-by:|generated with \[?claude")
RECORD_SEPARATOR = "\x1e"
FIELD_SEPARATOR = "\x1f"
DOC_PATHS = ["README.md", "AGENTS.md", "ARCHITECTURE.md", "EVALS.md", "COST.md", "HANDOFF.md", "DEMO.md", "DECISIONS.md", "docs"]
GREP_PATTERNS = {
    "tbc": (r"\[TBC\]", []),
    "todo_in_docs": (r"TODO", DOC_PATHS),
    "non_eu_model_ids": (r"(global|us|apac)\.(anthropic|amazon|meta|mistral|cohere|deepseek)\.", []),
    "region_strings": (r"(us|eu|ap|ca|sa|me|af|il|mx)-(north|south|east|west|central|northeast|southeast|northwest|southwest)-[0-9]", []),
}
REGION = re.compile(GREP_PATTERNS["region_strings"][0])
ALLOWED_REGION = "eu-west-1"
SECRET_PATTERN = r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|npm_[A-Za-z0-9]{36}"
NO_MATCH_EXIT_CODE = 1
TIMEOUT_EXIT_CODE = 124
NOT_FOUND_EXIT_CODE = 127
GH_TIMEOUT_S = 60
TESTS_TIMEOUT_S = 300
PR_LIMIT = 200
PR_FIELDS = "number,title,state,isDraft,headRefName,baseRefName,author,createdAt,mergedAt,statusCheckRollup,files"
PASSED = re.compile(r"(\d+) passed")
FAILED = re.compile(r"(\d+) failed")
ERRORS = re.compile(r"(\d+) errors?\b")
COVERAGE_TOTAL = re.compile(r"(?m)^TOTAL\s.*?(\d+)%\s*$")
DROPPED_ENV_PREFIXES = ("AWS_", "VIRTUAL_ENV")
WINDOWS_UNSAFE = re.compile(r'[:*?"<>|\\]')
RELATED_FOOTER = re.compile(r"(?m)^Related:")
SKIPPED_VAULT_DIRS = {".git", ".obsidian", ".claude", ".trash", ".superpowers", "99 Templates"}
PROGRESS_DIR = "08 Progress"
REPORT_NAME = re.compile(r"\d{4}-\d{2}-\d{2} \d{4}\.md")
SHA = re.compile(r"[0-9a-f]{7,40}")
VAULT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(__file__).resolve().parent
EXIT_CONFIG = 2
EXIT_REPORT_EXISTS = 3
EXIT_BAD_SHA = 4


class ConfigError(Exception):
    """The auditor's config is missing or invalid; the message says how to fix it."""


@dataclass(frozen=True)
class Config:
    repo: Path
    github_repo: str
    use_gh: bool
    day1: datetime.date
    utc_offset: datetime.timedelta


def parse_offset(text: str) -> datetime.timedelta:
    match = OFFSET.fullmatch(text)
    if not match:
        raise ValueError(f"utc_offset must look like +00:00, got {text!r}")
    sign, hours, minutes = match.groups()
    offset = datetime.timedelta(hours=int(hours), minutes=int(minutes))
    return -offset if sign == "-" else offset


def load_config(config_dir: Path) -> Config:
    local_path = config_dir / "local.json"
    if not local_path.is_file():
        raise ConfigError(
            f"missing {local_path}: copy local.example.json to local.json and set \"repo\" to your clone of the repo"
        )
    try:
        local = json.loads(local_path.read_text(encoding="utf-8"))
        timeline = json.loads((config_dir / "timeline.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"unreadable auditor config: {error}") from error
    repo = Path(str(local.get("repo", ""))).expanduser()
    if not (repo / ".git").exists():
        raise ConfigError(f"\"repo\" in {local_path} is not a git clone: {repo}")
    github_repo = str(local.get("github_repo", ""))
    if not GITHUB_REPO.fullmatch(github_repo):
        raise ConfigError(f"\"github_repo\" in {local_path} must look like owner/name, got {github_repo!r}")
    try:
        day1 = datetime.date.fromisoformat(timeline["day1"])
        utc_offset = parse_offset(timeline["utc_offset"])
    except (KeyError, ValueError) as error:
        raise ConfigError(f"timeline.json needs day1 (YYYY-MM-DD) and utc_offset (+HH:MM): {error}") from error
    return Config(repo=repo, github_repo=github_repo, use_gh=bool(local.get("use_gh", True)), day1=day1, utc_offset=utc_offset)


def parse_milestones(build_order_text: str, day1: datetime.date, now: datetime.datetime) -> dict:
    milestones = []
    for line_number, line in enumerate(build_order_text.splitlines(), start=1):
        match = MILESTONE_LINE.search(line)
        if not match:
            continue
        milestone_id, day, hour, minute, label = match.groups()
        due = datetime.datetime.combine(
            day1 + datetime.timedelta(days=int(day) - 1),
            datetime.time(int(hour), int(minute)),
            tzinfo=now.tzinfo,
        )
        milestones.append({
            "id": milestone_id,
            "day": f"D{day}",
            "time": f"{int(hour):02d}:{minute}",
            "due": due.isoformat(),
            "label": label,
            "passed": now >= due,
            "source": f"{BUILD_ORDER}:{line_number}",
        })
    upcoming = [milestone["id"] for milestone in milestones if not milestone["passed"]]
    return {"items": milestones, "next": upcoming[0] if upcoming else None}


def report_stamp(now: datetime.datetime) -> str:
    return f"{now:%Y-%m-%d %H%M}"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(argv: list[str], cwd: Path, timeout: int, env: dict | None = None) -> CommandResult:
    """The one place the collector shells out. Tests replace it."""
    try:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired:
        return CommandResult(TIMEOUT_EXIT_CODE, "", f"timed out after {timeout}s")
    except FileNotFoundError as error:
        return CommandResult(NOT_FOUND_EXIT_CODE, "", str(error))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class Unavailable(Exception):
    """A fact source failed; the message is the one-line reason."""


def unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason}


def first_line(text: str) -> str:
    stripped = text.strip()
    return stripped.splitlines()[0] if stripped else ""


def checked(result: CommandResult, what: str) -> str:
    if result.returncode != 0:
        raise Unavailable(f"{what} failed: {first_line(result.stderr) or f'exit {result.returncode}'}")
    return result.stdout


def resolve_sha(repo: Path, ref: str, runner) -> str:
    output = checked(runner(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], repo, GIT_TIMEOUT_S), f"git rev-parse {ref}")
    return output.strip()


def collect_tree(repo: Path, sha: str, runner) -> dict:
    output = checked(runner(["git", "ls-tree", "-r", "--name-only", sha], repo, GIT_TIMEOUT_S), "git ls-tree")
    return {"paths": output.splitlines(), "source": f"git ls-tree -r --name-only {sha[:7]}"}


def collect_commits(repo: Path, revision: str, runner, limit: int = COMMIT_LIMIT) -> dict:
    log_format = f"{RECORD_SEPARATOR}%H{FIELD_SEPARATOR}%an{FIELD_SEPARATOR}%aI{FIELD_SEPARATOR}%s{FIELD_SEPARATOR}%B{FIELD_SEPARATOR}"
    argv = ["git", "log", "--no-merges", f"-n{limit}", f"--format={log_format}", "--name-only", revision]
    output = checked(runner(argv, repo, GIT_TIMEOUT_S), "git log")
    commits = []
    for record in output.split(RECORD_SEPARATOR):
        if not record.strip():
            continue
        commit_sha, author, date, subject, message, file_block = record.split(FIELD_SEPARATOR)
        body = [line for line in message.splitlines()[1:] if line.strip()]
        commits.append({
            "sha": commit_sha[:7],
            "author": author,
            "date": date,
            "subject": subject,
            "body_lines": len(body),
            "attribution": bool(ATTRIBUTION.search(message)),
            "files": [line for line in file_block.splitlines() if line.strip()],
        })
    return {"items": commits, "source": f"git log --no-merges -n{limit} {revision[:40]}"}


def collect_branches_from_refs(refs: list[str]) -> list[dict]:
    branches = []
    for ref in refs:
        name = ref.removeprefix("origin/")
        if name in LONG_LIVED_BRANCHES or name == ref:
            continue
        branches.append({"name": name, "prefix_ok": bool(BRANCH_PREFIX.match(name))})
    return branches


def collect_branches(repo: Path, runner) -> dict:
    output = checked(runner(["git", "branch", "-r", "--format=%(refname:short)"], repo, GIT_TIMEOUT_S), "git branch -r")
    return {"items": collect_branches_from_refs(output.split()), "source": "git branch -r"}


def grep_hits(repo: Path, sha: str, pattern: str, paths: list[str], runner) -> list[tuple[str, int, str]]:
    argv = ["git", "grep", "-n", "-I", "-E", "-e", pattern, sha]
    if paths:
        argv += ["--", *paths]
    result = runner(argv, repo, GIT_TIMEOUT_S)
    if result.returncode == NO_MATCH_EXIT_CODE:
        return []
    output = checked(result, "git grep")
    hits = []
    for line in output.splitlines():
        path, line_number, text = line.removeprefix(f"{sha}:").split(":", 2)
        hits.append((path, int(line_number), text))
    return hits


def collect_greps(repo: Path, sha: str, runner) -> dict:
    greps = {}
    for name, (pattern, paths) in GREP_PATTERNS.items():
        hits = grep_hits(repo, sha, pattern, paths, runner)
        if name == "region_strings":
            hits = [hit for hit in hits if any(found.group(0) != ALLOWED_REGION for found in REGION.finditer(hit[2]))]
        greps[name] = {
            "hits": [{"path": path, "line": line_number, "text": text.strip()} for path, line_number, text in hits],
            "source": f"git grep -E '{pattern}' {sha[:7]}",
        }
    secret_hits = grep_hits(repo, sha, SECRET_PATTERN, [], runner)
    greps["secrets"] = {
        "hits": [{"path": path, "line": line_number} for path, line_number, _text in secret_hits],
        "source": f"git grep -E <secret patterns> {sha[:7]} (matched text withheld)",
    }
    return greps


def collect_prs(github_repo: str, repo: Path, runner) -> dict:
    argv = ["gh", "pr", "list", "--repo", github_repo, "--state", "all", "--limit", str(PR_LIMIT), "--json", PR_FIELDS]
    try:
        raw_prs = json.loads(checked(runner(argv, repo, GH_TIMEOUT_S), "gh pr list"))
    except Unavailable as error:
        return unavailable(str(error))
    except json.JSONDecodeError as error:
        return unavailable(f"gh pr list returned invalid JSON: {error}")
    items = []
    for raw in raw_prs:
        items.append({
            "number": raw["number"],
            "title": raw["title"],
            "state": raw["state"],
            "draft": raw["isDraft"],
            "head": raw["headRefName"],
            "base": raw["baseRefName"],
            "author": (raw.get("author") or {}).get("login"),
            "created": raw["createdAt"],
            "merged": raw.get("mergedAt"),
            "checks": [
                {"name": check.get("name") or check.get("context"), "result": check.get("conclusion") or check.get("state") or check.get("status")}
                for check in raw.get("statusCheckRollup") or []
            ],
            "files": [changed["path"] for changed in raw.get("files") or []],
        })
    return {"items": items, "source": f"gh pr list --repo {github_repo} --state all"}


def parse_pytest(output: str, returncode: int, sha: str) -> dict:
    passed, failed, errors = (PASSED.search(output), FAILED.search(output), ERRORS.search(output))
    if not (passed or failed):
        return unavailable(f"pytest output not recognised (exit {returncode}): {first_line(output[-300:])}")
    coverage = COVERAGE_TOTAL.search(output)
    return {
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
        "errors": int(errors.group(1)) if errors else 0,
        "coverage_total": int(coverage.group(1)) if coverage else None,
        "exit_code": returncode,
        "source": f"uv run --locked pytest in a throwaway worktree of {sha[:7]}",
    }


def collect_tests(repo: Path, sha: str, runner) -> dict:
    temp_root = Path(tempfile.mkdtemp(prefix="auditor-"))
    worktree = temp_root / f"audit-{sha[:7]}"
    try:
        checked(runner(["git", "worktree", "add", "--detach", str(worktree), sha], repo, GIT_TIMEOUT_S), "git worktree add")
        env = {key: value for key, value in os.environ.items() if not key.startswith(DROPPED_ENV_PREFIXES)}
        # No explicit -q: the product's pyproject addopts already sets -q, and a second one
        # suppresses the "N passed" summary line that parse_pytest reads.
        result = runner(["uv", "run", "--locked", "pytest"], worktree, TESTS_TIMEOUT_S, env)
        if result.returncode == TIMEOUT_EXIT_CODE:
            return unavailable(f"pytest {result.stderr}")
        return parse_pytest(result.stdout + result.stderr, result.returncode, sha)
    except Unavailable as error:
        return unavailable(str(error))
    finally:
        runner(["git", "worktree", "remove", "--force", str(worktree)], repo, GIT_TIMEOUT_S)
        runner(["git", "worktree", "prune"], repo, GIT_TIMEOUT_S)
        shutil.rmtree(temp_root, ignore_errors=True)


def vault_notes(vault: Path):
    for directory, subdirectories, files in os.walk(vault):
        relative_dir = Path(directory).relative_to(vault)
        if relative_dir == Path("."):
            subdirectories[:] = [name for name in subdirectories if name not in SKIPPED_VAULT_DIRS]
        for file_name in files:
            yield relative_dir / file_name


def collect_vault(vault: Path, runner, names: list[str] | None = None) -> dict:
    notes = list(vault_notes(vault))
    all_names = names if names is not None else [note.name for note in notes]
    missing_footer = [
        note.as_posix() for note in notes
        if note.suffix == ".md" and not RELATED_FOOTER.search((vault / note).read_text(encoding="utf-8", errors="replace"))
    ]
    status = runner(["git", "--no-optional-locks", "status", "--porcelain"], vault, GIT_TIMEOUT_S)
    return {
        "unsafe_names": sorted(name for name in all_names if WINDOWS_UNSAFE.search(name)),
        "missing_related_footer": sorted(missing_footer),
        "git_status": status.stdout.rstrip("\n").splitlines() if status.returncode == 0 else unavailable(first_line(status.stderr)),
        "source": "os.walk of the vault (skipping .git, .obsidian, .claude, .trash, .superpowers, 99 Templates); git status --porcelain",
    }


def previous_report(vault: Path) -> str | None:
    progress = vault / PROGRESS_DIR
    if not progress.is_dir():
        return None
    reports = sorted(path.name for path in progress.iterdir() if REPORT_NAME.fullmatch(path.name))
    return f"{PROGRESS_DIR}/{reports[-1]}" if reports else None


def section(builder):
    """Run one fact source; a failure becomes an `unavailable` section instead of stopping the run."""
    try:
        return builder()
    except Unavailable as error:
        return unavailable(str(error))


def open_pr_commits(repo: Path, prs: dict, develop_sha: str, runner) -> dict:
    if "items" not in prs:
        return unavailable("no PR list")
    by_pr = {}
    for pr in prs["items"]:
        if pr["state"] != "OPEN":
            continue
        by_pr[str(pr["number"])] = section(lambda pr=pr: collect_commits(repo, f"{develop_sha}..origin/{pr['head']}", runner))
    return by_pr


def collect(config: Config, vault: Path, at: str | None, run_tests: bool, runner, now: datetime.datetime) -> dict:
    fetch = runner(["git", "fetch", "origin", "--prune", "--quiet"], config.repo, GIT_TIMEOUT_S)
    develop_sha = resolve_sha(config.repo, "origin/develop", runner)
    audited = resolve_sha(config.repo, at, runner) if at else develop_sha
    stamp = report_stamp(now)
    build_order_path = vault / BUILD_ORDER
    prs = collect_prs(config.github_repo, config.repo, runner) if config.use_gh else unavailable("gh disabled in local.json (use_gh: false)")
    return {
        "run": {
            "now": now.isoformat(),
            "day1": config.day1.isoformat(),
            "day2": (config.day1 + datetime.timedelta(days=1)).isoformat(),
            "vault": str(vault),
            "repo": str(config.repo),
            "github_repo": config.github_repo,
            "report_path": f"{PROGRESS_DIR}/{stamp}.md",
            "fetch": "ok" if fetch.returncode == 0 else f"failed: {first_line(fetch.stderr)} (refs may be stale)",
            "develop_sha": develop_sha,
            "at": audited,
        },
        "milestones": parse_milestones(build_order_path.read_text(encoding="utf-8"), config.day1, now) if build_order_path.is_file() else unavailable(f"{BUILD_ORDER} not found"),
        "tree": section(lambda: collect_tree(config.repo, audited, runner)),
        "commits": section(lambda: collect_commits(config.repo, audited, runner)),
        "open_pr_commits": open_pr_commits(config.repo, prs, develop_sha, runner),
        "prs": prs,
        "branches": section(lambda: collect_branches(config.repo, runner)),
        "greps": section(lambda: collect_greps(config.repo, audited, runner)),
        "tests": collect_tests(config.repo, audited, runner) if run_tests else unavailable("skipped (--no-tests)"),
        "vault": collect_vault(vault, runner),
        "previous_report": previous_report(vault),
    }


def summary_lines(facts: dict, facts_path: Path) -> str:
    run = facts["run"]
    milestones = facts["milestones"]
    next_id = milestones.get("next") if "items" in milestones else None
    unavailable_sections = [name for name, value in facts.items() if isinstance(value, dict) and value.get("status") == "unavailable"]
    lines = [
        f"facts: {facts_path}",
        f"report to write: {run['vault']}/{run['report_path']}",
        f"audited: {run['at'][:7]} (origin/develop {run['develop_sha'][:7]}; fetch {run['fetch']})",
        f"next milestone: {next_id or 'none'}",
        f"previous report: {facts['previous_report'] or 'none'}",
        f"unavailable: {', '.join(unavailable_sections) or 'none'}",
    ]
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Collect progress-auditor facts.")
    parser.add_argument("--at", help="audit this commit sha instead of origin/develop")
    parser.add_argument("--no-tests", action="store_true", help="skip the throwaway-worktree pytest run")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.at and not SHA.fullmatch(args.at):
        print(f"progress auditor: --at must be a hex sha, got {args.at!r}", file=sys.stderr)
        return EXIT_BAD_SHA
    try:
        config = load_config(CONFIG_DIR)
    except ConfigError as error:
        print(f"progress auditor: {error}", file=sys.stderr)
        return EXIT_CONFIG
    now = datetime.datetime.now(datetime.timezone(config.utc_offset)).replace(microsecond=0)
    stamp = report_stamp(now)
    if (VAULT / PROGRESS_DIR / f"{stamp}.md").exists():
        print(f"progress auditor: a report for {stamp} already exists; wait a minute and run again", file=sys.stderr)
        return EXIT_REPORT_EXISTS
    try:
        facts = collect(config, VAULT, args.at, not args.no_tests, run_command, now)
    except Unavailable as error:
        print(f"progress auditor: {error}", file=sys.stderr)
        return EXIT_BAD_SHA
    runs = CONFIG_DIR / "runs"
    runs.mkdir(exist_ok=True)
    facts_path = runs / f"{stamp}.json"
    facts_path.write_text(json.dumps(facts, indent=1), encoding="utf-8")
    print(summary_lines(facts, facts_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
