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


if __name__ == "__main__":
    unittest.main()
