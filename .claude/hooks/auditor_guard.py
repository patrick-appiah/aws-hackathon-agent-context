"""Progress-auditor guard: a PreToolUse hook that keeps the auditor read-only.

Reads one hook payload on stdin. Allows by exiting 0 silently; denies by printing a
permissionDecision of "deny". Fails closed: anything it can't parse is denied.
The auditor's only writes are a new 08 Progress/<YYYY-MM-DD> <HHMM>.md report and
08 Progress/Progress.md. Reads are limited to the vault and the repo, never the eval
answer key, a .git directory or ~/.claude.
"""
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass

PREFIX = "progress-auditor guard: "
READ_PROGRAMS = {
    "ls", "cat", "head", "tail", "wc", "grep", "find", "sed", "sort", "uniq", "diff", "stat",
    "date", "basename", "dirname", "realpath", "pwd", "test", "nl", "cut", "tr", "comm",
}
GIT_SUBCOMMANDS = {"log", "show", "ls-tree", "diff", "rev-parse", "branch", "grep", "merge-base", "cat-file", "fetch"}
GIT_REFUSED_OPTIONS = ("--output", "--ext-diff", "--open-files-in-pager", "-O", "--no-index", "--exec", "-f")
GIT_BRANCH_OPTIONS = {"-r", "--remotes", "-a", "--all", "--list", "-v", "-vv", "--merged", "--no-merged"}
GIT_FETCH_OPTIONS = {"--prune", "--quiet", "-q"}
GH_PR_READS = {"list", "view", "checks", "diff"}
GH_WRITE_FIELDS = re.compile(r"^(-[fF]|--field|--raw-field|--input)")
FIND_REFUSED = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls"}
SEGMENT_OPERATORS = {"|", "||", "&&", ";"}
PUNCTUATION = set("();<>|&")
STDERR_TO_NULL = re.compile(r"(?<=\s)2>/dev/null(?=\s|$)")
DOTDOT = re.compile(r"(^|[/:=])\.\.(/|$)")
SED_RANGE = re.compile(r"\d+(,\d+)?p")
SHA = re.compile(r"[0-9a-f]{7,40}")
REPORT_NAME = re.compile(r"\d{4}-\d{2}-\d{2} \d{4}\.md")
GLOB_CHARACTERS = set("*?[")
INDEX_NAME = "Progress.md"


class Denied(Exception):
    pass


def deny(reason):
    raise Denied(reason)


@dataclass(frozen=True)
class Roots:
    vault: str
    repo: str | None
    use_gh: bool

    @property
    def evals(self):
        return os.path.join(self.vault, "07 Build", "Progress auditor", "evals")

    @property
    def progress(self):
        return os.path.join(self.vault, "08 Progress")

    @property
    def collector(self):
        return os.path.join(self.vault, ".claude", "auditor", "collect.py")

    def readable(self):
        return [root for root in (self.vault, self.repo) if root]

    def denied_dirs(self):
        dirs = [self.evals, os.path.join(self.vault, ".git"), os.path.realpath(os.path.expanduser("~/.claude"))]
        if self.repo:
            dirs.append(os.path.join(self.repo, ".git"))
        return dirs


def load_roots():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        deny("CLAUDE_PROJECT_DIR is not set; run the auditor from the vault root")
    vault = os.path.realpath(project_dir)
    repo, use_gh = None, True
    try:
        with open(os.path.join(vault, ".claude", "auditor", "local.json"), encoding="utf-8") as handle:
            local = json.load(handle)
        candidate = os.path.realpath(os.path.expanduser(str(local.get("repo", ""))))
        repo = candidate if local.get("repo") and os.path.isdir(candidate) else None
        use_gh = bool(local.get("use_gh", True))
    except (OSError, ValueError):
        pass
    return Roots(vault=vault, repo=repo, use_gh=use_gh)


def under(path, root):
    return path == root or path.startswith(root + os.sep)


def resolved(path, cwd):
    return os.path.realpath(os.path.join(cwd, path))


def judge_real_path(real, shown, roots):
    if not any(under(real, root) for root in roots.readable()):
        deny(f"{shown} is outside the vault and the repo")
    for denied_dir in roots.denied_dirs():
        if under(real, denied_dir):
            deny(f"{shown} is in a refused directory")
    if f"{os.sep}.git{os.sep}" in real + os.sep:
        deny(f"{shown} is inside a .git directory")


def is_ancestor_of_denied(real, roots):
    return any(under(denied_dir, real) for denied_dir in roots.denied_dirs())


def check_path_tokens(tokens, cwd, roots):
    for token in tokens:
        if DOTDOT.search(token):
            deny("'..' path components are refused")
        if token.startswith("~"):
            deny("home-directory paths are refused")
        if token.startswith("-"):
            value = token.split("=", 1)[1] if "=" in token else ""
            if "/" in value:
                judge_real_path(resolved(value, cwd), value, roots)
            continue
        glob_at = next((index for index, character in enumerate(token) if character in GLOB_CHARACTERS), None)
        if glob_at is not None:
            literal = token[:glob_at]
            if "/" not in literal:
                if token.startswith("."):
                    deny("globs on dot-names are refused")
                continue
            prefix_dir = resolved(os.path.dirname(literal) or ".", cwd)
            judge_real_path(prefix_dir, token, roots)
            if is_ancestor_of_denied(prefix_dir, roots):
                deny(f"{token} could reach a refused directory")
            continue
        if "/" in token or os.path.exists(os.path.join(cwd, token)):
            judge_real_path(resolved(token, cwd), token, roots)


def positional(tokens):
    return [token for token in tokens if not token.startswith("-")]


def check_recursive(start_tokens, cwd, roots):
    starts = [token for token in start_tokens if os.path.isdir(resolved(token, cwd))] or ["."]
    if any(set(token) & GLOB_CHARACTERS for token in start_tokens):
        deny("recursive commands with globs are refused")
    for token in starts:
        real = resolved(token, cwd)
        if is_ancestor_of_denied(real, roots):
            deny(f"a recursive search from {token} could reach a refused directory; start lower")


def has_short_flag(tokens, flag_letters):
    return any(token.startswith("-") and not token.startswith("--") and set(token[1:]) & set(flag_letters) for token in tokens)


def check_git(tokens, cwd, roots):
    args = tokens[1:]
    work_dir = cwd
    if args[:1] == ["-C"]:
        if len(args) < 2:
            deny("git -C needs a path")
        work_dir = resolved(args[1], cwd)
        args = args[2:]
    if work_dir not in roots.readable():
        deny("git runs only in the vault or as git -C <repo>")
    if args[:1] == ["--no-pager"]:
        args = args[1:]
    if not args or args[0].startswith("-"):
        deny("git options before the subcommand are refused")
    subcommand, rest = args[0], args[1:]
    if subcommand not in GIT_SUBCOMMANDS:
        deny(f"git {subcommand} is not a read")
    for token in rest:
        if token.startswith(GIT_REFUSED_OPTIONS):
            deny(f"git option {token} is refused")
        if DOTDOT.search(token):
            deny("'..' path components are refused")
    if subcommand == "fetch" and (rest[:1] != ["origin"] or any(token not in GIT_FETCH_OPTIONS for token in rest[1:])):
        deny("only `git fetch origin` is allowed")
    if subcommand == "branch" and any(token not in GIT_BRANCH_OPTIONS and not token.startswith(("--format=", "--sort=")) for token in rest):
        deny("git branch is allowed only to list")


def check_gh(tokens, roots):
    if not roots.use_gh:
        deny("gh is disabled for this run (local.json use_gh: false)")
    args = tokens[1:]
    if args[:1] == ["pr"] and len(args) > 1 and args[1] in GH_PR_READS:
        if any(token in ("--web", "-w") for token in args[2:]):
            deny("gh --web is refused")
        return
    if args[:1] == ["api"]:
        rest = args[1:]
        for index, token in enumerate(rest):
            if GH_WRITE_FIELDS.match(token):
                deny("gh api with fields or input is refused")
            method = None
            if token in ("-X", "--method"):
                method = rest[index + 1] if index + 1 < len(rest) else ""
            elif token.startswith("--method="):
                method = token.split("=", 1)[1]
            elif token.startswith("-X") and len(token) > 2:
                method = token[2:]
            if method is not None and method.upper() != "GET":
                deny("gh api allows GET only")
        if any("graphql" in token for token in positional(rest)):
            deny("gh api graphql is refused")
        return
    deny("only gh pr list/view/checks/diff and gh api GET are allowed")


def check_python(tokens, cwd, roots):
    if len(tokens) < 3 or tokens[1] != "-I" or resolved(tokens[2], cwd) != roots.collector:
        deny("python3 runs only `python3 -I <vault>/.claude/auditor/collect.py`")
    rest, index = tokens[3:], 0
    while index < len(rest):
        if rest[index] == "--no-tests":
            index += 1
        elif rest[index] == "--at" and index + 1 < len(rest) and SHA.fullmatch(rest[index + 1]):
            index += 2
        else:
            deny("the collector takes only --at <sha> and --no-tests")


def check_segment(tokens, cwd, roots):
    if not tokens:
        deny("empty command")
    program, args = tokens[0], tokens[1:]
    if "=" in program or "/" in program:
        deny("environment prefixes and program paths are refused")
    if program == "git":
        check_git(tokens, cwd, roots)
        return
    if program == "gh":
        check_gh(tokens, roots)
        return
    if program == "python3":
        check_python(tokens, cwd, roots)
        return
    if program not in READ_PROGRAMS:
        deny(f"{program} is not an allowed read command")
    if program == "sed" and not (len(args) == 3 and args[0] == "-n" and SED_RANGE.fullmatch(args[1])):
        deny("sed is allowed only as sed -n 'START,ENDp' <file>")
    if program == "find":
        if any(token in FIND_REFUSED for token in args):
            deny("find actions that run or write are refused")
        starts = []
        for token in args:
            if token.startswith(("-", "(", "!")):
                break
            starts.append(token)
        check_recursive(starts, cwd, roots)
    if program == "grep" and (has_short_flag(args, "rR") or any(token in ("--recursive", "--dereference-recursive") for token in args)):
        check_recursive(positional(args)[1:], cwd, roots)
    if program == "ls" and has_short_flag(args, "R"):
        check_recursive(positional(args), cwd, roots)
    if program == "sort" and any(token.startswith(("-o", "--output")) for token in args):
        deny("sort -o writes a file")
    if program == "uniq" and len(positional(args)) > 1:
        deny("uniq with an output file is refused")
    if program == "date" and any(token.startswith(("-s", "--set")) for token in args):
        deny("date --set is refused")
    check_path_tokens(args, cwd, roots)


def check_bash(command, cwd, roots):
    if "\n" in command or "\r" in command:
        deny("multi-line commands are refused")
    command = STDERR_TO_NULL.sub(" ", " " + command)
    if "$" in command or "`" in command:
        deny("variables and command substitution are refused")
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        deny("unparseable command")
    segment = []
    for token in tokens:
        if token in SEGMENT_OPERATORS:
            check_segment(segment, cwd, roots)
            segment = []
        elif set(token) <= PUNCTUATION:
            deny("redirections, subshells and background jobs are refused")
        else:
            segment.append(token)
    check_segment(segment, cwd, roots)


def check_write(file_path, roots):
    real = os.path.realpath(file_path)
    if os.path.dirname(real) != roots.progress:
        deny("the auditor writes only in 08 Progress/")
    name = os.path.basename(real)
    if not (REPORT_NAME.fullmatch(name) or name == INDEX_NAME):
        deny("the auditor writes only <YYYY-MM-DD> <HHMM>.md reports and Progress.md")
    if os.path.exists(real):
        deny(f"{name} already exists; reports are never overwritten (edit Progress.md instead)")


def check_edit(file_path, roots):
    if os.path.realpath(file_path) != os.path.join(roots.progress, INDEX_NAME):
        deny("the auditor edits only 08 Progress/Progress.md")


def decide(payload, roots):
    tool_name = payload["tool_name"]
    tool_input = payload.get("tool_input") or {}
    cwd = os.path.realpath(payload.get("cwd") or roots.vault)
    if tool_name == "Bash":
        check_bash(str(tool_input["command"]), cwd, roots)
    elif tool_name == "Read":
        real = resolved(str(tool_input["file_path"]), cwd)
        judge_real_path(real, str(tool_input["file_path"]), roots)
    elif tool_name == "Write":
        check_write(str(tool_input["file_path"]), roots)
    elif tool_name == "Edit":
        check_edit(str(tool_input["file_path"]), roots)
    else:
        deny(f"{tool_name} is not available to the progress auditor")


def main():
    try:
        payload = json.load(sys.stdin)
        roots = load_roots()
        decide(payload, roots)
    except Denied as refusal:
        reason = str(refusal)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        reason = f"could not parse the tool call ({type(error).__name__}); refused"
    else:
        sys.exit(0)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": PREFIX + reason,
    }}))
    sys.exit(0)


if __name__ == "__main__":
    main()
