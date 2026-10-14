"""Progress auditor collector: every mechanically checkable fact, with its source.

Writes the facts to .claude/auditor/runs/<YYYY-MM-DD HHMM>.json and prints a short
summary. Stdlib only. The only state-changing commands it runs are `git fetch origin`
and `git worktree add/remove` on a path inside its own temporary directory.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
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
