"""Tests for the progress auditor's collector. Stdlib unittest; run from the vault root:
python3 -m unittest discover -s .claude -p "test_*.py"
"""
import datetime
import json
import tempfile
import unittest
from pathlib import Path

from auditor import collect

UTC = datetime.timezone.utc
DAY1 = datetime.date(2026, 10, 14)

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
        'MODEL = "global.anthropic.claude-x"\nREGION = "eu-west-1"\nOTHER = "us-east-1"\nKEY = "AKIAABCDEFGHIJKLMNOP"\n'
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


if __name__ == "__main__":
    unittest.main()
