"""Tests for the progress-auditor guard: an allowed and a refused case for every rule."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "auditor_guard.py"
SHA7 = "abc1234"
GITHUB_REPO = "Amali-Tech/cloud-9-hackathon"
DRVFS_PARENT = Path(__file__).resolve().parents[2] / ".superpowers"


def make_fixture(root, use_gh=True):
    root = Path(root)
    vault, repo = root / "vault", root / "repo"
    for directory in [
        vault / ".git", vault / ".claude" / "auditor" / "runs", vault / "06 Workstreams",
        vault / "07 Build" / "Progress auditor" / "evals" / "cases", vault / "08 Progress", repo / ".git",
    ]:
        directory.mkdir(parents=True)
    (vault / ".git" / "config").write_text("[core]\n")
    (vault / ".claude" / "auditor" / "collect.py").write_text("")
    (vault / ".claude" / "auditor" / "local.json").write_text(json.dumps({"repo": str(repo), "use_gh": use_gh, "github_repo": GITHUB_REPO}))
    (vault / "06 Workstreams" / "Brief.md").write_text("brief\n")
    (vault / "07 Build" / "Progress auditor" / "evals" / "cases" / "c1.md").write_text("answer key\n")
    (vault / "08 Progress" / "2026-10-14 0900.md").write_text("old report\n")
    try:
        (vault / "escape").symlink_to("/etc")
    except OSError:
        pass
    (repo / "AGENTS.md").write_text("agents\n")
    (repo / ".git" / "config").write_text("[core]\n")
    return vault, repo


class GuardTestCase(unittest.TestCase):
    use_gh = True

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.vault, cls.repo = make_fixture(cls.temp.name, cls.use_gh)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def decide(self, tool_name, tool_input, raw=None, env_vault=True):
        payload = raw if raw is not None else json.dumps({"tool_name": tool_name, "tool_input": tool_input, "cwd": str(self.vault)})
        env = {key: value for key, value in os.environ.items() if key != "CLAUDE_PROJECT_DIR"}
        if env_vault:
            env["CLAUDE_PROJECT_DIR"] = str(self.vault)
        result = subprocess.run([sys.executable, "-I", str(GUARD)], input=payload, capture_output=True, text=True, env=env, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return "allow"
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertTrue(decision["permissionDecisionReason"].startswith("progress-auditor guard: "))
        return decision["permissionDecision"]

    def bash(self, command):
        return self.decide("Bash", {"command": command})

    def assert_bash(self, expected, commands):
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command), expected)


class BashTests(GuardTestCase):
    def test_allowed_reads(self):
        vault, repo = self.vault, self.repo
        self.assert_bash("allow", [
            f"git -C {repo} log --oneline -5 origin/develop",
            f"git -C {repo} show {SHA7}:AGENTS.md | head -40",
            f"git -C {repo} fetch origin",
            f"git -C {repo} fetch origin 2>/dev/null",
            f"git -C {repo} log origin/develop..origin/feature/x --oneline",
            f"git -C {repo} ls-tree -r --name-only {SHA7} tools",
            f"git -C {repo} --no-pager log -1",
            f"git -C {repo} branch -r",
            "gh pr view 8 --repo Amali-Tech/cloud-9-hackathon --json state",
            "gh pr list --repo Amali-Tech/cloud-9-hackathon --state all",
            "gh api repos/Amali-Tech/cloud-9-hackathon/pulls/8",
            f'grep -n "TBC" "{vault}/06 Workstreams/Brief.md"',
            f'grep -n "a.*b" "{vault}/06 Workstreams/Brief.md"',
            f'grep -rn "M0" "{vault}/06 Workstreams"',
            f"sed -n '1,40p' \"{vault}/06 Workstreams/Brief.md\"",
            f'ls "{vault}/08 Progress"',
            f'wc -l "{vault}/06 Workstreams/Brief.md"',
            f"python3 -I {vault}/.claude/auditor/collect.py",
            f"python3 -I {vault}/.claude/auditor/collect.py --at {SHA7} --no-tests",
        ])

    def test_refused_paths(self):
        vault = self.vault
        self.assert_bash("deny", [
            f'cat "{vault}/07 Build/Progress auditor/evals/cases/c1.md"',
            f'grep -rn x "{vault}/07 Build"',
            "grep -rn x .",
            f'grep -rn x "{vault}"',
            f'find "{vault}/07 Build" -name "*.md"',
            "find . -name x",
            f'ls -R "{vault}/07 Build"',
            f'cat "{vault}/07 Build/Progress auditor/"*/cases/c1.md',
            f"cat {vault}/../outside",
            "cat /etc/passwd",
            f"cat {vault}/escape/passwd",
            "cat ~/.claude/settings.json",
            f"cat {vault}/.git/config",
            f"cat {self.repo}/.git/config",
            "ls .gi*",
        ])

    def test_refused_shell_features(self):
        vault = self.vault
        self.assert_bash("deny", [
            "cat $HOME/x",
            "cat `which x`",
            f'echo hi > "{vault}/x"',
            f'cat "{vault}/06 Workstreams/Brief.md" >> "{vault}/y"',
            f'ls "{vault}" | tee "{vault}/z"',
            f'ls "{vault}" & ls',
            f'(ls "{vault}")',
            f'ls "{vault}"\nrm -rf "{vault}"',
            f'X=1 ls "{vault}"',
            f'awk 1 "{vault}/06 Workstreams/Brief.md"',
            f'ls "{vault}" | xargs rm',
            f'rm "{vault}/06 Workstreams/Brief.md"',
            "curl https://example.com",
            f'sort -o "{vault}/out" "{vault}/06 Workstreams/Brief.md"',
            f'uniq "{vault}/06 Workstreams/Brief.md" "{vault}/out"',
            f'sed -i s/a/b/ "{vault}/06 Workstreams/Brief.md"',
            f'sed -n 1,5p "{vault}/06 Workstreams/Brief.md" extra',
            f'find "{vault}/06 Workstreams" -delete',
            f'find "{vault}/06 Workstreams" -fprint "{vault}/out"',
            "echo 'unbalanced",
            "date -s 2020-01-01",
        ])

    def test_refused_git(self):
        repo = self.repo
        self.assert_bash("deny", [
            "git -C /tmp log",
            f"git -C {repo} push origin x",
            f"git -C {repo} checkout develop",
            f"git -C {repo} -c core.pager=x log",
            f"git -C {repo} diff --output=/tmp/x",
            f"git -C {repo} diff --no-index /etc/passwd x",
            f"git -C {repo} branch -D x",
            f"git -C {repo} fetch origin develop:develop",
            f"git -C {repo} grep -O x",
            f"git -C {repo} worktree add /tmp/x",
            f"git -C {repo} show {SHA7}:../../etc/passwd",
        ])

    def test_refused_gh(self):
        self.assert_bash("deny", [
            "gh pr merge 8",
            "gh pr comment 8 --body hi",
            "gh pr view 8 --web",
            "gh api -X POST repos/x/y/issues",
            "gh api --method=PATCH repos/x/y/pulls/8",
            "gh api repos/x/y/issues -f title=x",
            "gh api graphql -F query=x",
            "gh issue create --title x",
        ])

    def test_refused_python(self):
        vault = self.vault
        self.assert_bash("deny", [
            'python3 -c "print(1)"',
            f"python3 {vault}/.claude/auditor/collect.py",
            "python3 -I /tmp/collect.py",
            f"python3 -I {vault}/.claude/auditor/collect.py --at zzz",
            f"python3 -I {vault}/.claude/auditor/collect.py --other",
        ])


class AllowlistTests(GuardTestCase):
    """Fix round 1: every payload from the security review, plus the allowlist edges."""

    def test_review_payloads_refused(self):
        vault, repo = self.vault, self.repo
        self.assert_bash("deny", [
            "ls x#; whoami",
            'ls "a" #; whoami',
            "ls a#b",
            "cat 07*/Progress*/evals/cases/c1.md",
            "cat */*/evals/cases/c1.md",
            "cat */config",
            "cat {/etc/hostname,x}",
            f'cat "{vault}/07 Build/Progress auditor/"{{evals,x}}/cases/c1.md',
            f"git -C {repo} grep --open-files-in=true x",
            f"git -C {repo} grep --open=true x",
            f"git -C {repo} diff --outp=/tmp/x",
            f"git -C {repo} diff --ext-d",
            f"git -C {repo} log --textconv",
            f"sort -ro {vault}/f {vault}/06 Workstreams/Brief.md",
            "sort --outp=f g",
            "sort -T d g",
            "sort --compress-program=true x",
            "gh pr view 8 -cw",
            "gh api repos/x/y/issues -iftitle=x",
            "gh api repos/x/y -XPOST",
            "date -us 2020-01-01",
            "date --se=2020",
        ])

    def test_extra_refused(self):
        vault = self.vault
        self.assert_bash("deny", [
            "ls a\\ b",
            "ls !x",
            "cat ~root/x",
            f'grep -n a*b "{vault}/06 Workstreams/Brief.md"',
            f'find "{vault}/06 Workstreams" -name x -o -exec rm {{}} ;',
            f'tail -f "{vault}/06 Workstreams/Brief.md"',
            f'head --bytes=5 "{vault}/06 Workstreams/Brief.md"',
        ])

    def test_extra_allowed(self):
        vault, repo = self.vault, self.repo
        self.assert_bash("allow", [
            f'grep -rn --include="*.md" "M0" "{vault}/06 Workstreams"',
            f'find "{vault}/06 Workstreams" -name "*.md" -type f',
            f'head -n 40 "{vault}/06 Workstreams/Brief.md"',
            f'tail -20 "{vault}/06 Workstreams/Brief.md"',
            f"git -C {repo} log --format=%h%x20%s -n5 origin/develop",
            f"git -C {repo} log --since=2026-10-14 --no-merges --name-only abc1234",
            "gh pr list --repo Amali-Tech/cloud-9-hackathon --state all --limit 50 --json number,state",
            "date +%Y-%m-%d",
            f'sort -k2 -t, "{vault}/06 Workstreams/Brief.md"',
        ])

    def test_relative_write_resolves_against_payload_cwd(self):
        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "08 Progress/2026-10-14 1530.md", "content": "x"},
            "cwd": str(self.vault),
        })
        self.assertEqual(self.decide("Write", {}, raw=payload), "allow")
        elsewhere = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "08 Progress/2026-10-14 1530.md", "content": "x"},
            "cwd": str(self.repo),
        })
        self.assertEqual(self.decide("Write", {}, raw=elsewhere), "deny")


class RoundTwoTests(GuardTestCase):
    """Fix round 2: option values, dash-leading paths, git only in the repo, minors."""

    def test_refused(self):
        vault, repo = self.vault, self.repo
        self.assert_bash("deny", [
            f"git -C {repo} log -1 --pretty --output=/home/noblet/.bashrc --pretty=format:x",
            f"git -C {repo} log --format --output=/tmp/x",
            f"git -C {repo} log --since --output=/tmp/x",
            f"git -C {repo} log --since=/etc/passwd",
            'sed -n 1p "-ew .claude/settings.json"',
            'sed -n 1p "-f/tmp/x"',
            'git show "HEAD:07 Build/Progress auditor/evals/cases/c1.md"',
            "git log -1",
            f'grep -Rn x "{vault}/06 Workstreams"',
            "gh pr list --repo A/B --json number --jq env",
            "gh pr list --repo A/B --json number -q .env",
            "gh api repos/../user",
            f'grep --include=~/x y "{vault}/06 Workstreams/Brief.md"',
            f'cat "" "{vault}/06 Workstreams/Brief.md"',
            f'head -n -5 "{vault}/06 Workstreams/Brief.md"',
        ])

    def test_cwd_outside_roots_refused(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": "/etc"})
        self.assertEqual(self.decide("Bash", {}, raw=payload), "deny")

    def test_still_allowed(self):
        repo = self.repo
        self.assert_bash("allow", [
            f"git -C {repo} log -1 --pretty=format:x",
            f"git -C {repo} log --format=%h -n5",
        ])


class RoundThreeTests(GuardTestCase):
    """Fix round 3: case-insensitive refused dirs, tilde, gh pinned to the repo, minors."""

    def test_refused(self):
        vault, repo = self.vault, self.repo
        self.assert_bash("deny", [
            f'cat "{vault}/07 BUILD/Progress Auditor/evals/cases/c1.md"',
            "cat 07BUIL~1/x",
            'cat "a~b"',
            f'cat "{vault}/.GIT/config"',
            f'cat "{repo}/.Git/config"',
            "gh pr view https://evil.example/o/r/pull/1",
            "gh pr list --repo evil.example/o/r",
            "gh api repos/other/repo/pulls",
            "gh pr view 8",
            f"gh pr view abc --repo {GITHUB_REPO}",
            f"cat x{chr(0)}y",
            f"ls{chr(1)}",
            f"cat README.md{chr(11)}2>/dev/null",
            f"cat README.md{chr(12)}2>/dev/null",
            "diff -r a b",
            f'git -C {repo} log "--format=%G?" -1',
            f'git -C {repo} show "--pretty=%GS" {SHA7}',
            "cat /proc/self/cwd/Brief.md",
            "cat /dev/zero",
        ])

    def test_allowed(self):
        self.assert_bash("allow", [
            f"gh pr view 8 --repo {GITHUB_REPO} --json state",
            f"gh api repos/{GITHUB_REPO}/pulls/8",
        ])

    def test_file_tools(self):
        for tool_name, tool_input in [
            ("Read", {"file_path": f"{self.vault}/x~1"}),
            ("Read", {"file_path": f"{self.vault}/07 BUILD/Progress Auditor/evals/cases/c1.md"}),
            ("Read", {"file_path": "/proc/self/cwd/AGENTS.md"}),
            ("Write", {"file_path": f"{self.vault}/08 Progress/Progress~1.md", "content": "x"}),
            ("Edit", {"file_path": f"{self.vault}/08 Progress/Progress~1.md", "old_string": "a", "new_string": "b"}),
        ]:
            with self.subTest(tool_name=tool_name, tool_input=tool_input):
                self.assertEqual(self.decide(tool_name, tool_input), "deny")


class DrvFsTests(GuardTestCase):
    """The real vault is on a case-insensitive Windows mount; the /tmp fixture is not."""

    @classmethod
    def setUpClass(cls):
        if not DRVFS_PARENT.is_dir():
            raise unittest.SkipTest("no DrvFs-backed scratch directory")
        cls.temp = tempfile.TemporaryDirectory(dir=DRVFS_PARENT)
        cls.vault, cls.repo = make_fixture(cls.temp.name)
        if not (cls.vault / "07 build").exists():
            cls.temp.cleanup()
            raise unittest.SkipTest("scratch directory is case-sensitive")

    def test_case_variants_refused(self):
        vault = self.vault
        self.assert_bash("deny", [
            'cat "07 build/progress auditor/evals/cases/c1.md"',
            'grep -r x "07 build"',
            f'cat "{vault}/.GIT/config"',
            'ls -R "07 BUILD"',
        ])
        self.assertEqual(self.decide("Read", {"file_path": f"{vault}/07 build/progress auditor/evals/cases/c1.md"}), "deny")
        self.assertEqual(self.decide("Read", {"file_path": f"{vault}/06 workstreams/Brief.md"}), "allow")


class FileToolTests(GuardTestCase):
    def test_reads(self):
        self.assertEqual(self.decide("Read", {"file_path": f"{self.vault}/06 Workstreams/Brief.md"}), "allow")
        self.assertEqual(self.decide("Read", {"file_path": f"{self.repo}/AGENTS.md"}), "allow")
        self.assertEqual(self.decide("Read", {"file_path": f"{self.vault}/.claude/auditor/runs/2026-10-14 1000.json"}), "allow")
        for path in [
            f"{self.vault}/07 Build/Progress auditor/evals/cases/c1.md",
            "/etc/passwd",
            f"{self.vault}/escape/passwd",
            f"{self.vault}/.git/config",
            f"{self.repo}/.git/config",
            str(Path.home() / ".claude" / "settings.json"),
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.decide("Read", {"file_path": path}), "deny")

    def test_writes(self):
        progress = self.vault / "08 Progress"
        self.assertEqual(self.decide("Write", {"file_path": f"{progress}/2026-10-14 1530.md", "content": "x"}), "allow")
        self.assertEqual(self.decide("Write", {"file_path": f"{progress}/Progress.md", "content": "x"}), "allow")
        for path in [
            f"{progress}/2026-10-14 0900.md",
            f"{progress}/notes.md",
            f"{progress}/sub/2026-10-14 1000.md",
            f"{progress}/2026-10-14 15:30.md",
            f"{self.vault}/06 Workstreams/Brief.md",
            "/tmp/2026-10-14 1530.md",
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.decide("Write", {"file_path": path, "content": "x"}), "deny")

    def test_edits(self):
        self.assertEqual(self.decide("Edit", {"file_path": f"{self.vault}/08 Progress/Progress.md", "old_string": "a", "new_string": "b"}), "allow")
        self.assertEqual(self.decide("Edit", {"file_path": f"{self.vault}/06 Workstreams/Brief.md", "old_string": "a", "new_string": "b"}), "deny")
        self.assertEqual(self.decide("Edit", {"file_path": f"{self.vault}/08 Progress/2026-10-14 0900.md", "old_string": "a", "new_string": "b"}), "deny")

    def test_other_tools_and_bad_payloads(self):
        self.assertEqual(self.decide("Grep", {"pattern": "x"}), "deny")
        self.assertEqual(self.decide("Glob", {"pattern": "**/*.md"}), "deny")
        self.assertEqual(self.decide("NotebookEdit", {"notebook_path": "x"}), "deny")
        self.assertEqual(self.decide("Bash", {}, raw="{not json"), "deny")
        self.assertEqual(self.decide("Read", {"file_path": f"{self.vault}/06 Workstreams/Brief.md"}, env_vault=False), "deny")


class NoGhTests(GuardTestCase):
    use_gh = False

    def test_gh_refused_when_disabled(self):
        self.assertEqual(self.bash("gh pr view 8 --repo Amali-Tech/cloud-9-hackathon --json state"), "deny")
        self.assertEqual(self.bash(f"git -C {self.repo} log -1"), "allow")


if __name__ == "__main__":
    unittest.main()
