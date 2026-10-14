"""Progress-auditor guard: a PreToolUse hook that keeps the auditor read-only.

Reads one hook payload on stdin. Allows by exiting 0 silently; denies by printing a
permissionDecision of "deny". Fails closed: anything it can't parse is denied.
The auditor's only writes are a new 08 Progress/<YYYY-MM-DD> <HHMM>.md report and
08 Progress/Progress.md. Reads are limited to the vault and the repo, never the eval
answer key, a .git directory or ~/.claude.

Every command's options are matched against an exact allowlist (no abbreviations, no
bundled flags that are not listed): blocklists lost to option abbreviation and bundling.
Shell metacharacters that bash would expand (globs, braces, comments, history, escapes)
are refused outside quotes, so the guard sees the same words bash will run.
"""
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass, field

PREFIX = "progress-auditor guard: "
READ_PROGRAMS = {
    "ls", "cat", "head", "tail", "wc", "grep", "find", "sed", "sort", "uniq", "diff", "stat",
    "date", "basename", "dirname", "realpath", "pwd", "test", "nl", "cut", "tr", "comm",
}
# program -> (short flags, short flags that take a value, long flags, long flags that take a value)
OPTION_TABLE = {
    "ls": (set("lahA1trRSdF"), set(), set(), set()),
    "cat": (set("n"), set(), set(), set()),
    "head": (set(), set("nc"), set(), set()),
    "tail": (set(), set("nc"), set(), set()),
    "wc": (set("lwcm"), set(), set(), set()),
    "grep": (set("nicloLhHEFwxvrsq"), set("mABCe"), {"recursive"}, {"include", "exclude", "exclude-dir"}),
    "sort": (set("nrufb"), set("kt"), set(), set()),
    "uniq": (set("cdui"), set(), set(), set()),
    "diff": (set("uq"), set(), {"brief"}, set()),
    "stat": (set(), set("c"), set(), {"format"}),
    "date": (set("uIR"), set("d"), set(), set()),
    "cut": (set(), set("dfc"), set(), set()),
    "comm": (set("123"), set(), set(), set()),
    "tr": (set(), set(), set(), set()),
    "nl": (set(), set(), set(), set()),
    "basename": (set(), set(), set(), set()),
    "dirname": (set(), set(), set(), set()),
    "realpath": (set(), set(), set(), set()),
    "pwd": (set(), set(), set(), set()),
}
NUMERIC_OPTION_PROGRAMS = {"head", "tail"}
# Programs whose option values are patterns, delimiters or formats, never paths.
PATTERN_VALUE_PROGRAMS = {"grep", "cut", "sort", "stat", "date"}
TEST_PRIMARIES = {"-e", "-f", "-d", "-s"}
FIND_VALUE_PREDICATES = {"-name", "-iname", "-path", "-ipath", "-type", "-maxdepth", "-mindepth", "-newer", "-size", "-mtime"}
FIND_NO_VALUE_PREDICATES = {"-print"}

# git: the allowlist replaced the old option blocklist because git accepts unique
# abbreviations of long options (--open-files-in=x is --open-files-in-pager=x).
# subcommand -> (short flags, short flags with value, long flags, long flags with value)
GIT_OPTION_TABLE = {
    "log": (set("p"), set(), {"oneline", "name-only", "name-status", "stat", "no-merges", "first-parent", "reverse", "all"},
            {"format", "pretty", "since", "until", "author", "grep", "max-count", "date"}),
    "show": (set(), set(), {"stat", "name-only", "name-status", "oneline"}, {"format", "pretty"}),
    "ls-tree": (set("rdt"), set(), {"name-only"}, set()),
    "diff": (set(), set(), {"stat", "name-only", "name-status"}, set()),
    "rev-parse": (set(), set(), {"verify", "short", "abbrev-ref"}, set()),
    "branch": (set("rav"), set(), {"remotes", "all", "list", "merged", "no-merged"}, {"format", "sort"}),
    "grep": (set("niIEFwlch"), set("e"), set(), set()),
    "merge-base": (set(), set(), {"is-ancestor"}, set()),
    "cat-file": (set("tspe"), set(), set(), set()),
    "fetch": (set(), set(), {"prune", "quiet"}, set()),
}
# git option values that are patterns, never paths
GIT_PATTERN_VALUES = {"format", "pretty", "grep", "author", "date"}
# %G placeholders make git run gpg or ssh-keygen on commit signatures
GIT_FORMAT_VALUES = {"format", "pretty"}
GIT_SIGNATURE_PLACEHOLDER = "%G"
GIT_COUNT_OPTION = re.compile(r"-n?\d+")
# gh: (subcommand words) -> {option: takes a value}
GH_OPTION_TABLE = {
    ("pr", "list"): {
        "--repo": True, "-R": True, "--state": True, "-s": True, "--limit": True, "-L": True, "--json": True,
        "--jq": True, "-q": True, "--search": True, "-S": True, "--base": True, "-B": True, "--head": True,
        "-H": True, "--author": True, "-A": True, "--label": True, "-l": True,
    },
    ("pr", "view"): {"--repo": True, "-R": True, "--json": True, "--jq": True, "-q": True, "--comments": False},
    ("pr", "checks"): {"--repo": True, "-R": True},
    ("pr", "diff"): {"--repo": True, "-R": True, "--name-only": False},
    ("api",): {"--jq": True, "-q": True, "--paginate": False, "--cache": True},
}
GH_API_ENDPOINT_PREFIX = "repos/"
GH_REPO_OPTIONS = {"--repo", "-R"}
GH_JQ_OPTIONS = {"--jq", "-q"}
GH_JQ_REFUSED = "env"
SEGMENT_OPERATORS = {"|", "||", "&&", ";"}
PUNCTUATION = set("();<>|&")
STDERR_TO_NULL = re.compile(r"(?<=[ \t])2>/dev/null(?=[ \t]|$)")
SPECIAL_FILESYSTEMS = re.compile(r"^/(proc|dev)(/|$)")
DOTDOT = re.compile(r"(^|[/:=])\.\.(/|$)")
SED_RANGE = re.compile(r"\d+(,\d+)?p")
SHA = re.compile(r"[0-9a-f]{7,40}")
REPORT_NAME = re.compile(r"\d{4}-\d{2}-\d{2} \d{4}\.md")
GLOB_CHARACTERS = set("*?[")
UNQUOTED_REFUSED = set("#{}\\!*?[]")
ALWAYS_REFUSED = set("$`")
TAB = "\t"
WORD_START_CHARACTERS = set(" \t|&;()<>")
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
    github_repo: str = ""

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


@dataclass
class ParsedOptions:
    positionals: list = field(default_factory=list)
    values: list = field(default_factory=list)
    flags: set = field(default_factory=set)


def load_roots():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        deny("CLAUDE_PROJECT_DIR is not set; run the auditor from the vault root")
    vault = os.path.realpath(project_dir)
    repo, use_gh, github_repo = None, True, ""
    try:
        with open(os.path.join(vault, ".claude", "auditor", "local.json"), encoding="utf-8") as handle:
            local = json.load(handle)
        candidate = os.path.realpath(os.path.expanduser(str(local.get("repo", ""))))
        repo = candidate if local.get("repo") and os.path.isdir(candidate) else None
        use_gh = bool(local.get("use_gh", True))
        github_repo = str(local.get("github_repo", ""))
    except (OSError, ValueError):
        pass
    return Roots(vault=vault, repo=repo, use_gh=use_gh, github_repo=github_repo)


def under(path, root):
    return path == root or path.startswith(root + os.sep)


def resolved(path, cwd):
    return os.path.realpath(os.path.join(cwd, path))


def same_file(first, second):
    try:
        return os.path.samefile(first, second)
    except OSError:
        return True  # cannot tell, so treat as the same: fail closed


def ancestors_and_self(path):
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            return
        path = parent


def inside_refused(real, roots):
    """True if real is, or is under, a refused directory.

    The vault is on a case-insensitive Windows mount that also resolves 8.3 short names,
    so string comparison alone is not enough: compare casefolded, and by file identity
    wherever the paths exist.
    """
    folded = real.casefold()
    for refused in roots.denied_dirs():
        if under(folded, refused.casefold()):
            return True
    existing_refused = [refused for refused in roots.denied_dirs() if os.path.exists(refused)]
    for probe in ancestors_and_self(real):
        if os.path.exists(probe) and any(same_file(probe, refused) for refused in existing_refused):
            return True
    return False


def judge_real_path(real, shown, roots):
    if not any(under(real, root) for root in roots.readable()):
        deny(f"{shown} is outside the vault and the repo")
    if inside_refused(real, roots):
        deny(f"{shown} is in a refused directory")
    if f"{os.sep}.git{os.sep}" in (real + os.sep).casefold():
        deny(f"{shown} is inside a .git directory")


def is_ancestor_of_denied(real, roots):
    """True if real is, or contains, a refused directory (casefolded and by identity)."""
    folded = real.casefold()
    for refused in roots.denied_dirs():
        if under(refused.casefold(), folded):
            return True
        if os.path.exists(real) and any(
            os.path.exists(candidate) and same_file(real, candidate) for candidate in ancestors_and_self(refused)
        ):
            return True
    return False


def refuse_special_path(token):
    if SPECIAL_FILESYSTEMS.match(os.path.normpath(token)):
        deny("/proc and /dev paths are refused")


def scan_raw(command):
    """Refuse shell syntax that bash would expand or hide, judged on the raw string.

    Quote-aware: glob, brace, comment, history and escape characters are literal inside
    quotes, so they are refused only outside them.
    """
    if any(character in ALWAYS_REFUSED or (character < " " and character != TAB) for character in command):
        deny("variables, command substitution and control characters are refused")
    quote = None
    index = 0
    while index < len(command):
        character = command[index]
        if quote == "'":
            if character == "'":
                quote = None
        elif quote == '"':
            if character == "\\":
                index += 1
            elif character == '"':
                quote = None
        elif character in ("'", '"'):
            quote = character
        elif character in UNQUOTED_REFUSED:
            deny(f"unquoted {character!r} is refused")
        elif character == "~" and (index == 0 or command[index - 1] in WORD_START_CHARACTERS):
            deny("unquoted home-directory paths are refused")
        index += 1
    if quote is not None:
        deny("unterminated quote")


def check_path_tokens(tokens, cwd, roots):
    for token in tokens:
        if DOTDOT.search(token):
            deny("'..' path components are refused")
        if "~" in token:
            deny("'~' is refused (home directories and 8.3 short names)")
        refuse_special_path(token)
        if token == "-":
            continue
        if "/" in token or os.path.exists(os.path.join(cwd, token)):
            judge_real_path(resolved(token, cwd), token, roots)


def check_recursive(start_tokens, cwd, roots):
    starts = [token for token in start_tokens if os.path.isdir(resolved(token, cwd))] or ["."]
    if any(set(token) & GLOB_CHARACTERS for token in start_tokens):
        deny("recursive commands with globs are refused")
    for token in starts:
        real = resolved(token, cwd)
        if is_ancestor_of_denied(real, roots):
            deny(f"a recursive search from {token} could reach a refused directory; start lower")


def check_options(program, args, short_flags, short_with_value, long_flags, long_with_value, allow_numeric=False, inline_values_only=False):
    """Match every option against exact allowlists; return positionals, (name, value) pairs and flags seen.

    A value taken from the next token may never start with "-" (it would be a hidden option).
    With inline_values_only, long options take values only as --name=value.
    """
    parsed = ParsedOptions()
    index, options_ended = 0, False

    def take_value(name):
        nonlocal index
        if index >= len(args):
            deny(f"{program} option {name} needs a value")
        index += 1
        value = args[index - 1]
        if value.startswith("-"):
            deny(f"{program} option {name} cannot take a dash-leading value")
        return value

    while index < len(args):
        token = args[index]
        index += 1
        if options_ended or token == "-" or not token.startswith("-"):
            parsed.positionals.append(token)
        elif token == "--":
            options_ended = True
        elif token.startswith("--"):
            name, has_value, value = token[2:].partition("=")
            if name in long_flags and not has_value:
                parsed.flags.add(name)
            elif name in long_with_value:
                if not has_value and inline_values_only:
                    deny(f"{program} option {token} needs --name=value")
                parsed.values.append((name, value if has_value else take_value(token)))
                parsed.flags.add(name)
            else:
                deny(f"{program} option {token} is not allowed")
        elif allow_numeric and token[1:].isdigit():
            continue
        else:
            body = token[1:]
            for position, letter in enumerate(body):
                if letter in short_flags:
                    parsed.flags.add(letter)
                elif letter in short_with_value:
                    parsed.values.append((letter, body[position + 1:] or take_value(token)))
                    parsed.flags.add(letter)
                    break
                else:
                    deny(f"{program} option -{letter} is not allowed")
    return parsed


def check_git(tokens, cwd, roots):
    args = tokens[1:]
    if args[:1] != ["-C"] or len(args) < 2:
        deny("git runs only as git -C <repo>")
    work_dir = resolved(args[1], cwd)
    args = args[2:]
    if not roots.repo or work_dir != roots.repo:
        deny("git runs only as git -C <repo>")
    if args[:1] == ["--no-pager"]:
        args = args[1:]
    if not args or args[0].startswith("-"):
        deny("git options before the subcommand are refused")
    subcommand, rest = args[0], args[1:]
    if subcommand not in GIT_OPTION_TABLE:
        deny(f"git {subcommand} is not a read")
    for token in rest:
        if DOTDOT.search(token):
            deny("'..' path components are refused")
    if subcommand == "log":
        rest = [token for token in rest if not GIT_COUNT_OPTION.fullmatch(token)]
    parsed = check_options(f"git {subcommand}", rest, *GIT_OPTION_TABLE[subcommand], inline_values_only=True)
    check_path_tokens([value for name, value in parsed.values if "/" in value and name not in GIT_PATTERN_VALUES], cwd, roots)
    for name, value in parsed.values:
        if name in GIT_FORMAT_VALUES and GIT_SIGNATURE_PLACEHOLDER in value:
            deny("git %G placeholders run signature tools and are refused")
    for token in parsed.positionals:
        if token.startswith(("/", "~")):
            deny("git paths outside the repository are refused")
    if subcommand == "fetch" and parsed.positionals != ["origin"]:
        deny("only `git fetch origin` is allowed")
    if subcommand == "branch" and parsed.positionals and not parsed.flags & {"list", "merged", "no-merged"}:
        deny("git branch is allowed only to list")


def check_gh(tokens, roots):
    if not roots.use_gh:
        deny("gh is disabled for this run (local.json use_gh: false)")
    if not roots.github_repo:
        deny("gh is refused: local.json has no github_repo")
    args = tokens[1:]
    key = ("api",) if args[:1] == ["api"] else tuple(args[:2])
    allowed = GH_OPTION_TABLE.get(key)
    if allowed is None:
        deny("only gh pr list/view/checks/diff and gh api GET are allowed")
    rest, positionals, index, repo_given = args[len(key):], [], 0, False
    while index < len(rest):
        token = rest[index]
        index += 1
        if not token.startswith("-") or token == "-":
            positionals.append(token)
            continue
        name, separator, inline_value = token.partition("=") if token.startswith("--") else (token, "", "")
        if name not in allowed:
            deny(f"gh option {token} is not allowed")
        if not allowed[name]:
            if separator:
                deny(f"gh option {name} takes no value")
            continue
        value = inline_value
        if not separator:
            if index >= len(rest) or rest[index].startswith("-"):
                deny(f"gh option {name} needs a value")
            value = rest[index]
            index += 1
        if name in GH_REPO_OPTIONS:
            if value != roots.github_repo:
                deny("gh --repo must be the configured github_repo")
            repo_given = True
        if name in GH_JQ_OPTIONS and GH_JQ_REFUSED in value:
            deny("gh jq filters that mention env are refused")
    if key != ("api",):
        if not repo_given:
            deny("gh pr commands need --repo <github_repo>")
        if not all(positional.isdigit() for positional in positionals):
            deny("gh pr commands take only a PR number")
        return
    if (
        len(positionals) != 1
        or not positionals[0].startswith(f"{GH_API_ENDPOINT_PREFIX}{roots.github_repo}/")
        or "graphql" in positionals[0]
        or ".." in positionals[0]
    ):
        deny("gh api takes one repos/... endpoint, never graphql")


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


def check_find(args, cwd, roots):
    index = 0
    while index < len(args) and not args[index].startswith("-"):
        index += 1
    starts, predicates = args[:index], args[index:]
    position = 0
    while position < len(predicates):
        predicate = predicates[position]
        position += 1
        if predicate in FIND_NO_VALUE_PREDICATES:
            continue
        if predicate not in FIND_VALUE_PREDICATES or position >= len(predicates):
            deny(f"find {predicate} is not allowed")
        value = predicates[position]
        position += 1
        if predicate == "-newer":
            check_path_tokens([value], cwd, roots)
    check_recursive(starts, cwd, roots)
    check_path_tokens(starts, cwd, roots)


def check_listed_program(program, args, cwd, roots):
    parsed = check_options(program, args, *OPTION_TABLE[program], allow_numeric=program in NUMERIC_OPTION_PROGRAMS)
    positionals = parsed.positionals
    if program == "grep":
        if "e" not in parsed.flags:
            if not positionals:
                deny("grep needs a pattern")
            positionals = positionals[1:]
    elif program == "date":
        if any(not token.startswith("+") for token in positionals):
            deny("date takes only a +FORMAT")
        positionals = []
    elif program == "uniq" and len(positionals) > 1:
        deny("uniq with an output file is refused")
    recursive = (
        (program == "grep" and parsed.flags & {"r", "R", "recursive"})
        or (program == "ls" and "R" in parsed.flags)
    )
    if recursive:
        check_recursive(positionals, cwd, roots)
    check_path_tokens(positionals, cwd, roots)
    if program not in PATTERN_VALUE_PROGRAMS:
        check_path_tokens([value for name, value in parsed.values if "/" in value], cwd, roots)


def check_segment(tokens, cwd, roots):
    if not tokens:
        deny("empty command")
    program, args = tokens[0], tokens[1:]
    if "=" in program or "/" in program:
        deny("environment prefixes and program paths are refused")
    if program == "git":
        check_git(tokens, cwd, roots)
    elif program == "gh":
        check_gh(tokens, roots)
    elif program == "python3":
        check_python(tokens, cwd, roots)
    elif program not in READ_PROGRAMS:
        deny(f"{program} is not an allowed read command")
    elif program == "sed":
        if not (len(args) == 3 and args[0] == "-n" and SED_RANGE.fullmatch(args[1])):
            deny("sed is allowed only as sed -n 'START,ENDp' <file>")
        if args[2].startswith("-"):
            deny("sed's file argument cannot start with a dash")
        check_path_tokens(args[2:], cwd, roots)
    elif program == "test":
        if len(args) != 2 or args[0] not in TEST_PRIMARIES:
            deny("test is allowed only as test -e|-f|-d|-s <path>")
        check_path_tokens(args[1:], cwd, roots)
    elif program == "find":
        check_find(args, cwd, roots)
    else:
        check_listed_program(program, args, cwd, roots)


def check_bash(command, cwd, roots):
    command = STDERR_TO_NULL.sub(" ", " " + command)
    scan_raw(command)
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        deny("unparseable command")
    segment = []
    for token in tokens:
        if token == "":
            deny("empty argument")
        if "~" in token:
            deny("'~' is refused (home directories and 8.3 short names)")
        refuse_special_path(token)
        if token in SEGMENT_OPERATORS:
            check_segment(segment, cwd, roots)
            segment = []
        elif set(token) <= PUNCTUATION:
            deny("redirections, subshells and background jobs are refused")
        else:
            segment.append(token)
    check_segment(segment, cwd, roots)


def check_write(real, roots):
    if os.path.dirname(real) != roots.progress:
        deny("the auditor writes only in 08 Progress/")
    name = os.path.basename(real)
    if not (REPORT_NAME.fullmatch(name) or name == INDEX_NAME):
        deny("the auditor writes only <YYYY-MM-DD> <HHMM>.md reports and Progress.md")
    if os.path.exists(real):
        deny(f"{name} already exists; reports are never overwritten (edit Progress.md instead)")


def check_edit(real, roots):
    if real != os.path.join(roots.progress, INDEX_NAME):
        deny("the auditor edits only 08 Progress/Progress.md")


def decide(payload, roots):
    tool_name = payload["tool_name"]
    tool_input = payload.get("tool_input") or {}
    cwd = os.path.realpath(payload.get("cwd") or roots.vault)
    if not any(under(cwd, root) for root in roots.readable()):
        deny("the working directory is outside the vault and the repo")
    if tool_name in ("Read", "Write", "Edit"):
        file_path = str(tool_input["file_path"])
        if "~" in file_path:
            deny("'~' is refused in file paths")
        refuse_special_path(file_path)
    if tool_name == "Bash":
        check_bash(str(tool_input["command"]), cwd, roots)
    elif tool_name == "Read":
        real = resolved(str(tool_input["file_path"]), cwd)
        judge_real_path(real, str(tool_input["file_path"]), roots)
    elif tool_name == "Write":
        check_write(resolved(str(tool_input["file_path"]), cwd), roots)
    elif tool_name == "Edit":
        check_edit(resolved(str(tool_input["file_path"]), cwd), roots)
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
