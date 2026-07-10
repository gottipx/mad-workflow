from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "integrations/hermes/plugin/mad-workflow/cli.py"

spec = importlib.util.spec_from_file_location("mad_cli", CLI_PATH)
assert spec is not None and spec.loader is not None
mad_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mad_cli)


def sample_contract(**overrides):
    data = yaml.safe_load((ROOT / "examples/hermes-task-contract.yaml").read_text())
    data.update(overrides)
    return data


class ContractValidationTests(unittest.TestCase):
    def test_rejects_empty_semantic_fields(self):
        errors, warnings = mad_cli.validate_contract(sample_contract(task_id="", goal=""))
        self.assertTrue(any("task_id must not be empty" in e for e in errors), errors)
        self.assertTrue(any("goal must not be empty" in e for e in errors), errors)

    def test_requires_report_format(self):
        data = sample_contract()
        data.pop("report_format")
        errors, warnings = mad_cli.validate_contract(data)
        self.assertIn("missing required field: report_format", errors)

    def test_rejects_placeholders_before_dispatch(self):
        data = sample_contract(allowed_scope=["TODO: define allowed files/globs before dispatch"])
        errors, warnings = mad_cli.validate_contract(data)
        self.assertTrue(any("placeholder" in e for e in errors), errors)


class ReportValidationTests(unittest.TestCase):
    def test_completion_requires_candidate_revision_and_passed_result(self):
        report = yaml.safe_load((ROOT / "examples/hermes-completion-report.yaml").read_text())
        report.pop("revision")
        report["test_result"] = "not_run"
        errors, warnings = mad_cli.validate_report_data("completion", report, sample_contract())
        self.assertTrue(any("revision" in e for e in errors), errors)
        self.assertTrue(any("test_result: passed" in e for e in errors), errors)

    def test_missing_required_checks_is_error(self):
        report = yaml.safe_load((ROOT / "examples/hermes-completion-report.yaml").read_text())
        report["tests_run"] = []
        errors, warnings = mad_cli.validate_report_data("completion", report, sample_contract())
        self.assertTrue(any("required checks" in e for e in errors), errors)

    def test_passing_qa_cannot_have_failed_checks(self):
        report = yaml.safe_load((ROOT / "examples/hermes-quality-gate-report.yaml").read_text())
        report["failed_checks"] = ["pytest tests/example"]
        errors, warnings = mad_cli.validate_report_data("qa", report, sample_contract())
        self.assertTrue(any("failed_checks" in e for e in errors), errors)

    def test_behavioral_impact_requires_revalidation(self):
        report = yaml.safe_load((ROOT / "examples/hermes-impact-report.yaml").read_text())
        report["change_type"] = "behavioral"
        report["required_revalidation"] = []
        errors, warnings = mad_cli.validate_report_data("impact", report, sample_contract())
        self.assertTrue(any("required_revalidation" in e for e in errors), errors)

    def test_qa_must_match_completion_revision(self):
        completion = yaml.safe_load((ROOT / "examples/hermes-completion-report.yaml").read_text())
        qa = yaml.safe_load((ROOT / "examples/hermes-quality-gate-report.yaml").read_text())
        qa["target_revision"] = "different-sha"
        errors = mad_cli._completion_qa_consistency_errors(completion, qa)
        self.assertTrue(any("does not match completion revision" in e for e in errors), errors)


class ScopeDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init"], cwd=self.tmp, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.tmp, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.tmp, check=True)
        (self.tmp / "README.md").write_text("base\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.tmp, check=True, capture_output=True, text=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_untracked_files_are_included(self):
        (self.tmp / "new-file.txt").write_text("untracked\n")
        files, errors = mad_cli._git_changed_files(self.tmp, "HEAD")
        self.assertEqual(errors, [])
        self.assertIn("new-file.txt", files)

    def test_invalid_base_fails_closed(self):
        files, errors = mad_cli._git_changed_files(self.tmp, "missing-base")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
