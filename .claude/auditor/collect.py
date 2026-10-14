"""Progress auditor collector: every mechanically checkable fact, with its source.

Writes the facts to .claude/auditor/runs/<YYYY-MM-DD HHMM>.json and prints a short
summary. Stdlib only. The only state-changing commands it runs are `git fetch origin`
and `git worktree add/remove` on a path inside its own temporary directory.
"""
from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from pathlib import Path

BUILD_ORDER = "07 Build/Build order.md"
MILESTONE_LINE = re.compile(r"\*\*(M\d+)\*\*\s+D([12])\s+(\d{1,2}):(\d{2}):\s*(.+?)\.?\s*$")
OFFSET = re.compile(r"([+-])(\d{2}):(\d{2})")
GITHUB_REPO = re.compile(r"[\w.-]+/[\w.-]+")


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
