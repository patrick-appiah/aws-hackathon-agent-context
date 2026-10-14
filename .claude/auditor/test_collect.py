"""Tests for the progress auditor's collector. Stdlib unittest; run from the vault root:
python3 -m unittest discover -s .claude -p "test_*.py"
"""
import contextlib
import dataclasses
import datetime
import io
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from auditor import collect

UTC = datetime.timezone.utc
DAY1 = datetime.date(2026, 10, 14)
# Built at runtime so no literal key-shaped string lives in this file (secret scanners).
FAKE_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_ASIA_KEY = "ASIA" + "ABCDEFGHIJKLMNOP"

BUILD_ORDER_SAMPLE = """# Build order
Milestones (`docs/TEAM_PLAN.md` §4):
- **M0** D1 10:30: contracts frozen.
- **M1** D1 12:00: stacks deploy empty.
- **M2** D1 18:00: walking skeleton live in AWS.
- **M3** D2 12:00: Cognito go/no-go, real critic and retry, publish.
"""


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp.name)
        self.repo = self.config_dir / "repo"
        (self.repo / ".git").mkdir(parents=True)
        (self.config_dir / "timeline.json").write_text(json.dumps({"day1": "2026-10-14", "utc_offset": "+00:00"}))

    def tearDown(self):
        self.temp.cleanup()

    def write_local(self, content):
        (self.config_dir / "local.json").write_text(json.dumps(content))

    def test_loads_a_valid_config(self):
        self.write_local({"repo": str(self.repo), "github_repo": "Amali-Tech/cloud-9-hackathon"})
        config = collect.load_config(self.config_dir)
        self.assertEqual(config.repo, self.repo)
        self.assertEqual(config.github_repo, "Amali-Tech/cloud-9-hackathon")
        self.assertTrue(config.use_gh)
        self.assertEqual(config.day1, DAY1)
        self.assertEqual(config.utc_offset, datetime.timedelta(0))

    def test_use_gh_false_is_kept(self):
        self.write_local({"repo": str(self.repo), "github_repo": "Amali-Tech/cloud-9-hackathon", "use_gh": False})
        self.assertFalse(collect.load_config(self.config_dir).use_gh)

    def test_missing_local_json_names_the_fix(self):
        with self.assertRaisesRegex(collect.ConfigError, "copy local.example.json to local.json"):
            collect.load_config(self.config_dir)

    def test_repo_that_is_not_a_clone_is_refused(self):
        self.write_local({"repo": str(self.config_dir / "nowhere"), "github_repo": "Amali-Tech/cloud-9-hackathon"})
        with self.assertRaisesRegex(collect.ConfigError, "not a git clone"):
            collect.load_config(self.config_dir)

    def test_bad_github_repo_is_refused(self):
        self.write_local({"repo": str(self.repo), "github_repo": "not a repo; rm"})
        with self.assertRaisesRegex(collect.ConfigError, "github_repo"):
            collect.load_config(self.config_dir)

    def test_offsets(self):
        self.assertEqual(collect.parse_offset("+00:00"), datetime.timedelta(0))
        self.assertEqual(collect.parse_offset("-05:30"), -datetime.timedelta(hours=5, minutes=30))
        with self.assertRaises(ValueError):
            collect.parse_offset("Africa/Accra")


class MilestoneTests(unittest.TestCase):
    def test_parses_ids_times_sources_and_next(self):
        now = datetime.datetime(2026, 10, 14, 15, 0, tzinfo=UTC)
        milestones = collect.parse_milestones(BUILD_ORDER_SAMPLE, DAY1, now)
        ids = [milestone["id"] for milestone in milestones["items"]]
        self.assertEqual(ids, ["M0", "M1", "M2", "M3"])
        first = milestones["items"][0]
        self.assertEqual(first["due"], "2026-10-14T10:30:00+00:00")
        self.assertEqual(first["label"], "contracts frozen")
        self.assertTrue(first["passed"])
        self.assertEqual(first["source"], "07 Build/Build order.md:3")
        self.assertEqual(milestones["items"][3]["due"], "2026-10-15T12:00:00+00:00")
        self.assertEqual(milestones["next"], "M2")

    def test_no_next_after_the_last_milestone(self):
        now = datetime.datetime(2026, 10, 16, 9, 0, tzinfo=UTC)
        self.assertIsNone(collect.parse_milestones(BUILD_ORDER_SAMPLE, DAY1, now)["next"])

    def test_report_stamp_is_windows_safe(self):
        now = datetime.datetime(2026, 10, 14, 9, 5, tzinfo=UTC)
        self.assertEqual(collect.report_stamp(now), "2026-10-14 0905")


import subprocess

GIT_IDENTITY = ["-c", "user.name=Test Author", "-c", "user.email=test@example.com"]


def git_in(repo, *args):
    subprocess.run(["git", *GIT_IDENTITY, *args], cwd=repo, check=True, capture_output=True, text=True)


def build_repo(root):
    """A small repo with a [TBC], a fake AWS key, a global. model ID, a us-east-1 string,
    a commit with an attribution line and one without, and branches with good and bad prefixes."""
    repo = Path(root) / "repo"
    repo.mkdir()
    git_in(repo, "init", "-q", "-b", "develop")
    (repo / "business").mkdir()
    (repo / "business" / "business-case.md").write_text("Payback: [TBC]\n")
    (repo / "COST.md").write_text("# Cost\nTODO measure\n")
    (repo / "config.py").write_text(
        f'MODEL = "global.anthropic.claude-x"\nREGION = "eu-west-1"\nOTHER = "us-east-1"\nKEY = "{FAKE_KEY}"\n'
    )
    git_in(repo, "add", ".")
    git_in(repo, "commit", "-q", "-m", "Add the business case and settings")
    (repo / "README.md").write_text("# Readme\n")
    git_in(repo, "add", "README.md")
    git_in(repo, "commit", "-q", "-m", "Add the readme\n\nCo-Authored-By: Someone <x@example.com>")
    git_in(repo, "branch", "feature/good-name")
    git_in(repo, "branch", "seat3/bad-name")
    return repo


class GitFactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = build_repo(self.temp.name)
        self.sha = collect.resolve_sha(self.repo, "develop", collect.run_command)

    def tearDown(self):
        self.temp.cleanup()

    def test_resolve_sha_is_full_hex(self):
        self.assertRegex(self.sha, r"^[0-9a-f]{40}$")

    def test_unknown_ref_is_unavailable(self):
        with self.assertRaises(collect.Unavailable):
            collect.resolve_sha(self.repo, "no-such-ref", collect.run_command)

    def test_tree_lists_every_path_with_its_source(self):
        tree = collect.collect_tree(self.repo, self.sha, collect.run_command)
        self.assertIn("business/business-case.md", tree["paths"])
        self.assertEqual(tree["source"], f"git ls-tree -r --name-only {self.sha[:7]}")

    def test_commits_carry_attribution_and_files(self):
        commits = collect.collect_commits(self.repo, self.sha, collect.run_command, limit=10)["items"]
        self.assertEqual(len(commits), 2)
        newest, oldest = commits
        self.assertEqual(newest["subject"], "Add the readme")
        self.assertTrue(newest["attribution"])
        self.assertEqual(newest["files"], ["README.md"])
        self.assertEqual(newest["author"], "Test Author")
        self.assertFalse(oldest["attribution"])
        self.assertEqual(oldest["body_lines"], 0)

    def test_branches_flag_bad_prefixes(self):
        branches = collect.collect_branches_from_refs(["origin/HEAD", "origin/develop", "origin/main", "origin/feature/good-name", "origin/seat3/bad-name"])
        by_name = {branch["name"]: branch["prefix_ok"] for branch in branches}
        self.assertEqual(by_name, {"feature/good-name": True, "seat3/bad-name": False})

    def test_greps(self):
        greps = collect.collect_greps(self.repo, self.sha, collect.run_command)
        self.assertEqual(greps["tbc"]["hits"], [{"path": "business/business-case.md", "line": 1, "text": "Payback: [TBC]"}])
        self.assertEqual([hit["path"] for hit in greps["todo_in_docs"]["hits"]], ["COST.md"])
        self.assertEqual([hit["path"] for hit in greps["non_eu_model_ids"]["hits"]], ["config.py"])
        self.assertEqual([hit["line"] for hit in greps["region_strings"]["hits"]], [3])

    def test_secret_hits_never_include_the_text(self):
        secrets = collect.collect_greps(self.repo, self.sha, collect.run_command)["secrets"]
        self.assertEqual(secrets["hits"], [{"path": "config.py", "line": 4}])
        self.assertNotIn("AKIA", json.dumps(secrets))

    def test_failed_command_raises_unavailable_with_the_reason(self):
        def failing_runner(argv, cwd, timeout, env=None):
            return collect.CommandResult(128, "", "fatal: not a git repository\nmore")
        with self.assertRaisesRegex(collect.Unavailable, "fatal: not a git repository"):
            collect.collect_tree(self.repo, self.sha, failing_runner)


PR_JSON = json.dumps([{
    "number": 8, "title": "Add minimal CI", "state": "OPEN", "isDraft": True,
    "headRefName": "chore/ci-minimal-checks", "baseRefName": "develop",
    "author": {"login": "someone"}, "createdAt": "2026-10-14T11:35:16Z", "mergedAt": None,
    "statusCheckRollup": [{"name": "jenkins", "conclusion": "FAILURE", "status": "COMPLETED"}],
    "files": [{"path": "Jenkinsfile"}],
}])

PYTEST_OUTPUT = """........
---------- coverage: platform linux, python 3.11.14-final-0 ----------
Name    Stmts   Miss  Cover
TOTAL    1200     60    95%
160 passed in 12.34s
"""


class FakeRunner:
    """Real git for everything except the commands given canned results."""

    def __init__(self, canned):
        self.canned = canned
        self.calls = []

    def __call__(self, argv, cwd, timeout, env=None):
        self.calls.append((list(argv), env))
        for prefix, result in self.canned.items():
            if tuple(argv[: len(prefix)]) == prefix:
                return result
        return collect.run_command(argv, cwd, timeout, env)


class PrTests(unittest.TestCase):
    def test_prs_are_summarised(self):
        runner = FakeRunner({("gh", "pr", "list"): collect.CommandResult(0, PR_JSON, "")})
        prs = collect.collect_prs("Amali-Tech/cloud-9-hackathon", Path("."), runner)
        self.assertEqual(prs["items"][0], {
            "number": 8, "title": "Add minimal CI", "state": "OPEN", "draft": True,
            "head": "chore/ci-minimal-checks", "base": "develop", "author": "someone",
            "created": "2026-10-14T11:35:16Z", "merged": None,
            "checks": [{"name": "jenkins", "result": "FAILURE"}], "files": ["Jenkinsfile"],
        })

    def test_gh_failure_is_unavailable(self):
        runner = FakeRunner({("gh",): collect.CommandResult(4, "", "gh: To get started, please run: gh auth login")})
        prs = collect.collect_prs("Amali-Tech/cloud-9-hackathon", Path("."), runner)
        self.assertEqual(prs, {"status": "unavailable", "reason": "gh pr list failed: gh: To get started, please run: gh auth login"})


class PytestParseTests(unittest.TestCase):
    def test_counts_and_coverage(self):
        parsed = collect.parse_pytest(PYTEST_OUTPUT, 0, "a" * 40)
        self.assertEqual((parsed["passed"], parsed["failed"], parsed["errors"], parsed["coverage_total"]), (160, 0, 0, 95))

    def test_failures_are_counted(self):
        parsed = collect.parse_pytest("3 failed, 157 passed, 1 error in 9.1s\nTOTAL 10 1 90%\n", 1, "a" * 40)
        self.assertEqual((parsed["passed"], parsed["failed"], parsed["errors"], parsed["coverage_total"]), (157, 3, 1, 90))

    def test_unrecognised_output_is_unavailable(self):
        self.assertEqual(collect.parse_pytest("uv: command not found", 127, "a" * 40)["status"], "unavailable")


class TestRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = build_repo(self.temp.name)
        self.sha = collect.resolve_sha(self.repo, "develop", collect.run_command)

    def tearDown(self):
        self.temp.cleanup()

    def worktrees(self):
        return collect.run_command(["git", "worktree", "list"], self.repo, 30).stdout.strip().splitlines()

    def test_worktree_run_reports_results_and_cleans_up(self):
        runner = FakeRunner({("uv",): collect.CommandResult(0, PYTEST_OUTPUT, "")})
        tests = collect.collect_tests(self.repo, self.sha, runner)
        self.assertEqual(tests["passed"], 160)
        self.assertEqual(len(self.worktrees()), 1)

    def test_aws_variables_are_dropped(self):
        runner = FakeRunner({("uv",): collect.CommandResult(0, PYTEST_OUTPUT, "")})
        os.environ["AWS_PROFILE"] = "hackathon"
        try:
            collect.collect_tests(self.repo, self.sha, runner)
        finally:
            del os.environ["AWS_PROFILE"]
        uv_env = [env for argv, env in runner.calls if argv[0] == "uv"][0]
        self.assertNotIn("AWS_PROFILE", uv_env)

    def test_timeout_is_unavailable_and_still_cleans_up(self):
        runner = FakeRunner({("uv",): collect.CommandResult(collect.TIMEOUT_EXIT_CODE, "", "timed out after 300s")})
        tests = collect.collect_tests(self.repo, self.sha, runner)
        self.assertEqual(tests, {"status": "unavailable", "reason": "pytest timed out after 300s"})
        self.assertEqual(len(self.worktrees()), 1)


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        (self.vault / "06 Workstreams").mkdir()
        (self.vault / "06 Workstreams" / "Good.md").write_text("Body\n\nRelated: [[Workstreams]]\n")
        (self.vault / "06 Workstreams" / "No footer.md").write_text("Body\n")
        (self.vault / "08 Progress").mkdir()
        (self.vault / "08 Progress" / "Progress.md").write_text("Related: [[Workstreams]]\n")
        (self.vault / "08 Progress" / "2026-10-14 0900.md").write_text("Related: [[Progress]]\n")
        (self.vault / "08 Progress" / "2026-10-14 1300.md").write_text("Related: [[Progress]]\n")
        (self.vault / ".git").mkdir()
        (self.vault / ".git" / "ignored.md").write_text("no footer, but inside .git\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_unsafe_names_and_missing_footers(self):
        runner = FakeRunner({("git",): collect.CommandResult(0, " M 06 Workstreams/Good.md\n", "")})
        vault = collect.collect_vault(self.vault, runner, names=["Bad: name.md", "Fine.md"])
        self.assertEqual(vault["unsafe_names"], ["Bad: name.md"])
        self.assertEqual(vault["missing_related_footer"], ["06 Workstreams/No footer.md"])
        self.assertEqual(vault["git_status"], [" M 06 Workstreams/Good.md"])

    def test_previous_report_is_the_newest(self):
        self.assertEqual(collect.previous_report(self.vault), "08 Progress/2026-10-14 1300.md")


class RunCommandTests(unittest.TestCase):
    def test_timeout_returns_the_timeout_code_quickly(self):
        started = time.monotonic()
        result = collect.run_command(["sleep", "5"], Path("."), 1)
        self.assertEqual(result.returncode, collect.TIMEOUT_EXIT_CODE)
        self.assertLess(time.monotonic() - started, 3)

    def test_timeout_kills_the_grandchildren_too(self):
        self.assertIsNotNone(shutil.which("pgrep"), "pgrep is needed for this test")
        result = collect.run_command(["sh", "-c", "sleep 30 & wait"], Path("."), 1)
        self.assertEqual(result.returncode, collect.TIMEOUT_EXIT_CODE)
        survivors = subprocess.run(["pgrep", "-f", "sleep 30"], capture_output=True, text=True)
        self.assertNotEqual(survivors.returncode, 0, f"surviving processes: {survivors.stdout}")

    def test_missing_working_directory_is_not_found(self):
        result = collect.run_command(["true"], Path("/no-such-directory-for-audit"), 5)
        self.assertEqual(result.returncode, collect.NOT_FOUND_EXIT_CODE)


class SectionTests(unittest.TestCase):
    def test_each_failure_kind_becomes_a_one_line_unavailable(self):
        def raise_os_error():
            raise OSError("disk\nfull")

        def raise_value_error():
            raise ValueError("bad milestone")

        def raise_unavailable():
            raise collect.Unavailable("git failed: boom")

        self.assertEqual(collect.section(raise_os_error), {"status": "unavailable", "reason": "OSError: disk"})
        self.assertEqual(collect.section(raise_value_error), {"status": "unavailable", "reason": "ValueError: bad milestone"})
        self.assertEqual(collect.section(raise_unavailable), {"status": "unavailable", "reason": "git failed: boom"})
        self.assertEqual(collect.section(lambda: 42), 42)


class UseGhTypeTests(unittest.TestCase):
    def test_string_false_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            config_dir = Path(temp)
            repo = config_dir / "repo"
            (repo / ".git").mkdir(parents=True)
            (config_dir / "timeline.json").write_text(json.dumps({"day1": "2026-10-14", "utc_offset": "+00:00"}))
            (config_dir / "local.json").write_text(json.dumps({
                "repo": str(repo), "github_repo": "Amali-Tech/cloud-9-hackathon", "use_gh": "false",
            }))
            with self.assertRaisesRegex(collect.ConfigError, "use_gh must be true or false"):
                collect.load_config(config_dir)


class PytestFixTests(unittest.TestCase):
    def test_errors_only_are_reported_as_errors(self):
        parsed = collect.parse_pytest("1 error in 0.5s\n", 2, "a" * 40)
        self.assertNotIn("status", parsed)
        self.assertEqual((parsed["passed"], parsed["failed"], parsed["errors"]), (0, 0, 1))

    def test_duration_is_rounded_to_a_tenth(self):
        parsed = collect.parse_pytest(PYTEST_OUTPUT, 0, "a" * 40, duration_s=12.34)
        self.assertEqual(parsed["duration_s"], 12.3)


class SecretLineTests(unittest.TestCase):
    def test_a_secret_line_loses_the_text_of_other_hits(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "mixed"
            repo.mkdir()
            git_in(repo, "init", "-q", "-b", "develop")
            (repo / "notes.md").write_text(f"Payback [TBC] key {FAKE_KEY}\nASIA line {FAKE_ASIA_KEY}\n")
            git_in(repo, "add", ".")
            git_in(repo, "commit", "-q", "-m", "Mixed lines")
            sha = collect.resolve_sha(repo, "develop", collect.run_command)
            greps = collect.collect_greps(repo, sha, collect.run_command)
        self.assertEqual(greps["tbc"]["hits"], [{"path": "notes.md", "line": 1, "text_withheld": True}])
        self.assertEqual(greps["secrets"]["hits"], [{"path": "notes.md", "line": 1}, {"path": "notes.md", "line": 2}])
        self.assertNotIn(FAKE_KEY, json.dumps(greps))
        self.assertNotIn(FAKE_ASIA_KEY, json.dumps(greps))


def write_build_order(vault, text=None):
    (vault / "07 Build").mkdir(parents=True, exist_ok=True)
    body = text if text is not None else "- **M0** D1 10:30: contracts frozen.\n- **M1** D2 12:00: stacks deploy.\n"
    (vault / "07 Build" / "Build order.md").write_bytes(body.encode("utf-8") if isinstance(body, str) else body)


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        origin = build_repo(root)
        git_in(origin, "checkout", "-q", "feature/good-name")
        (origin / "feature.txt").write_text("feature\n")
        git_in(origin, "add", "feature.txt")
        git_in(origin, "commit", "-q", "-m", "Feature work")
        git_in(origin, "checkout", "-q", "develop")
        self.clone = root / "clone"
        subprocess.run(["git", "clone", "-q", str(origin), str(self.clone)], check=True, capture_output=True, text=True)
        self.vault = root / "vault"
        write_build_order(self.vault)
        self.config = collect.Config(
            repo=self.clone, github_repo="Amali-Tech/cloud-9-hackathon", use_gh=True,
            day1=DAY1, utc_offset=datetime.timedelta(0),
        )
        self.now = datetime.datetime(2026, 10, 14, 15, 0, tzinfo=UTC)

    def tearDown(self):
        self.temp.cleanup()

    def run_collect(self, runner, config=None, run_tests=False):
        return collect.collect(config or self.config, self.vault, None, run_tests, runner, self.now)

    def test_gh_failure_leaves_the_other_sections_in_place(self):
        runner = FakeRunner({("gh",): collect.CommandResult(4, "", "gh: not logged in")})
        facts = self.run_collect(runner)
        self.assertEqual(facts["prs"], {"status": "unavailable", "reason": "gh pr list failed: gh: not logged in"})
        self.assertIn("paths", facts["tree"])
        self.assertIn("items", facts["commits"])
        self.assertEqual(len(facts["milestones"]["items"]), 2)
        self.assertIn("hits", facts["greps"]["tbc"])
        self.assertEqual(facts["tests"], {"status": "unavailable", "reason": "skipped (--no-tests)"})

    def test_use_gh_false_never_calls_gh(self):
        config = dataclasses.replace(self.config, use_gh=False)
        runner = FakeRunner({})
        facts = self.run_collect(runner, config=config)
        self.assertIn("use_gh", facts["prs"]["reason"])
        self.assertFalse(any(argv[0] == "gh" for argv, _env in runner.calls))

    def test_pytest_runs_with_the_plain_argv_and_no_prune(self):
        runner = FakeRunner({("uv",): collect.CommandResult(0, PYTEST_OUTPUT, "")})
        sha = collect.resolve_sha(self.clone, "origin/develop", collect.run_command)
        tests = collect.collect_tests(self.clone, sha, runner)
        uv_calls = [argv for argv, _env in runner.calls if argv[0] == "uv"]
        self.assertEqual(uv_calls, [["uv", "run", "--locked", "pytest"]])
        self.assertNotIn(["git", "worktree", "prune"], [argv for argv, _env in runner.calls])
        self.assertIsInstance(tests["duration_s"], float)

    def test_summary_names_the_unavailable_sections(self):
        runner = FakeRunner({("gh",): collect.CommandResult(4, "", "gh: not logged in")})
        facts = self.run_collect(runner)
        lines = collect.summary_lines(facts, Path("runs/x.json")).splitlines()
        unavailable_line = [line for line in lines if line.startswith("unavailable:")][0]
        self.assertIn("prs", unavailable_line)
        self.assertIn("tests", unavailable_line)
        self.assertNotIn("tree", unavailable_line)

    def test_open_pr_commits_lists_the_branch_commits(self):
        runner = FakeRunner({})
        develop_sha = collect.resolve_sha(self.clone, "origin/develop", runner)
        prs = {"items": [
            {"number": 8, "state": "OPEN", "head": "feature/good-name"},
            {"number": 9, "state": "MERGED", "head": "seat3/bad-name"},
        ]}
        by_pr = collect.open_pr_commits(self.clone, prs, develop_sha, runner)
        self.assertEqual(list(by_pr), ["8"])
        self.assertEqual([item["subject"] for item in by_pr["8"]["items"]], ["Feature work"])

    def test_missing_build_order_is_unavailable_and_the_run_continues(self):
        (self.vault / "07 Build" / "Build order.md").unlink()
        facts = self.run_collect(FakeRunner({("gh",): collect.CommandResult(4, "", "no gh")}))
        self.assertEqual(facts["milestones"], {"status": "unavailable", "reason": "07 Build/Build order.md not found"})
        self.assertIn("paths", facts["tree"])

    def test_undecodable_build_order_is_unavailable_and_the_run_continues(self):
        write_build_order(self.vault, text=b"\xff\xfe not utf-8")
        facts = self.run_collect(FakeRunner({("gh",): collect.CommandResult(4, "", "no gh")}))
        self.assertEqual(facts["milestones"]["status"], "unavailable")
        self.assertIn("paths", facts["tree"])


class MainExitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config_dir = root / "auditor"
        self.config_dir.mkdir()
        self.vault = root / "vault"
        write_build_order(self.vault)
        self.repo = build_repo(root)
        (self.config_dir / "timeline.json").write_text(json.dumps({"day1": "2026-10-14", "utc_offset": "+00:00"}))
        for name, value in (("VAULT", self.vault), ("CONFIG_DIR", self.config_dir)):
            patcher = mock.patch.object(collect, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.temp.cleanup()

    def run_main(self, argv):
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            return collect.main(argv)

    def write_local(self):
        (self.config_dir / "local.json").write_text(json.dumps({
            "repo": str(self.repo), "github_repo": "Amali-Tech/cloud-9-hackathon", "use_gh": False,
        }))

    def test_missing_local_json_exits_2(self):
        self.assertEqual(self.run_main(["--no-tests"]), 2)

    def test_bad_at_sha_exits_4(self):
        self.write_local()
        self.assertEqual(self.run_main(["--at", "zzz"]), 4)

    def test_existing_report_for_this_minute_exits_3(self):
        self.write_local()
        for _attempt in range(2):
            now = datetime.datetime.now(UTC).replace(microsecond=0)
            report = self.vault / "08 Progress" / f"{collect.report_stamp(now)}.md"
            report.parent.mkdir(exist_ok=True)
            report.write_text("existing\n")
            if self.run_main(["--no-tests"]) == 3:
                return
        self.fail("main() did not exit 3 for an existing report in the current minute")


if __name__ == "__main__":
    unittest.main()
