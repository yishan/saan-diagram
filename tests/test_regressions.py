"""Behavioral regression checks. Publisher subprocesses never contact Feishu."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/saan-diagram/scripts"
sys.path.insert(0, str(SCRIPTS))
import render as r
import wb_publish as w
from spec_validation import SpecError


def flow():
    return {"columns": [{"id": "a", "label": "申请阶段"}, {"id": "b", "label": "执行阶段"}],
            "nodes": [{"id": "start", "label": "提交申请", "col": "a", "row": 0.5},
                      {"id": "end", "label": "执行支付", "col": "b", "row": 0.5}],
            "edges": [{"from": "start", "to": "end", "kind": "flow"}]}


def verify(spec):
    return r.verify_flow(r.build_spec(spec)[0])


class VerificationTests(unittest.TestCase):
    def test_empty_verify_enables_decision_check(self):
        sp = flow()
        sp["nodes"][0]["kind"] = "decision"
        sp["verify"] = {}
        self.assertIn("P4", [c for c, _ in verify(sp)[0]])

    def test_false_and_absent_disable_checks(self):
        for value in (False, None):
            sp = flow()
            sp["nodes"][0]["kind"] = "decision"
            sp["verify"] = value
            self.assertEqual(verify(sp), ([], []))

    def test_disconnected_step_not_inferred_as_valid_entry(self):
        sp = flow()
        sp["nodes"].append({"id": "lost", "label": "复核步骤", "col": "a", "row": 4})
        sp["verify"] = {}
        findings, ok = verify(sp)
        self.assertTrue(any(c == "P2" and "复核步骤" in msg for c, msg in findings))
        self.assertFalse(ok)

    def test_documents_and_path_headings_are_not_steps(self):
        sp = flow()
        sp["nodes"].append({"label": "申请单", "kind": "doc", "col": "a", "row": 4})
        sp["verify"] = {}
        self.assertEqual(verify(sp)[0], [])

    def test_scope_excludes_only_declared_nonprocess_nodes(self):
        sp = flow()
        sp["nodes"].append({"id": "lost", "label": "说明模块", "col": "a", "row": 4})
        sp["verify"] = {"nodes": ["start", "end"]}
        self.assertEqual(verify(sp)[0], [])

    def test_optional_and_ai_steps_are_not_silently_excluded(self):
        for kind in ("optional", "ai"):
            sp = flow()
            sp["nodes"].append({"id": "lost", "label": "复核步骤", "kind": kind, "col": "a", "row": 4})
            sp["verify"] = {}
            self.assertIn("P2", [c for c, _ in verify(sp)[0]])

    def test_stage_columns_cannot_prove_separation(self):
        sp = flow()
        sp["verify"] = {"separate": [["start", "end"]]}
        findings, ok = verify(sp)
        self.assertIn("P5", [c for c, _ in findings])
        self.assertFalse(any("不同角色" in line for line in ok))

    def test_same_actor_in_different_columns_fails(self):
        sp = flow()
        for n in sp["nodes"]:
            n["actor"] = "经办人"
        sp["verify"] = {"separate": [["start", "end"]]}
        self.assertIn("P5", [c for c, _ in verify(sp)[0]])

    def test_explicit_actors_override_same_column(self):
        sp = flow()
        sp["nodes"][0]["actor"] = "申请人"
        sp["nodes"][1].update(actor="出纳", col="a", row=3)
        sp["verify"] = {"separate": [["start", "end"]]}
        findings, ok = verify(sp)
        self.assertNotIn("P5", [c for c, _ in findings])
        self.assertTrue(any("声明了不同角色" in line for line in ok))

    def test_explicit_role_columns_work(self):
        sp = flow()
        sp["column_semantics"] = "roles"
        sp["columns"][0]["label"] = "申请人"
        sp["columns"][1]["label"] = "出纳"
        sp["verify"] = {"separate": [["start", "end"]]}
        self.assertEqual(verify(sp)[0], [])

    def test_unreachable_target_never_gets_verified_note(self):
        sp = flow()
        sp["nodes"].append({"id": "lost", "label": "复核步骤", "col": "a", "row": 4})
        sp["verify"] = {"must_pass": [{"before": "lost", "through": "start"}], "reachable": False}
        findings, ok = verify(sp)
        self.assertIn("P1", [c for c, _ in findings])
        self.assertFalse(any("必经" in line for line in ok))

    def test_control_bypass_remains_a_business_finding(self):
        sp = r._load_example("payment-audit")
        sp["edges"].append({"from": "提交付款申请", "to": "执行支付", "kind": "flow"})
        self.assertIn("P1", [c for c, _ in verify(sp)[0]])


class TimelineTests(unittest.TestCase):
    def timeline(self, status=None):
        m = {"label": "试点上线", "date": "2026-10-20"}
        if status is not None:
            m["status"] = status
        return r.build_spec({"layout": "timeline", "start": "2026-10", "end": "2026-11",
                             "today": "2026-10-23", "milestones": [m]})[0]

    def test_past_date_without_status_is_unknown(self):
        notes = " ".join(self.timeline().notes)
        self.assertIn("已完成 0 个", notes)
        self.assertIn("状态待确认 1 个", notes)

    def test_explicit_done(self):
        self.assertIn("已完成 1 个", " ".join(self.timeline("done").notes))

    def test_unknown_has_distinct_visual_marker(self):
        unknown_svg = self.timeline().svg("unknown")[0]
        pending_svg = self.timeline("pending").svg("pending")[0]
        self.assertIn('stroke-dasharray="3,3"', unknown_svg)
        self.assertNotIn('stroke-dasharray="3,3"', pending_svg)

    def test_past_pending_is_overdue(self):
        notes = " ".join(self.timeline("pending").notes)
        self.assertIn("已完成 0 个", notes)
        self.assertIn("到期未完成 1 个", notes)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.spec = self.root / "sample.yaml"
        self.result = self.root / "result.json"

    def run_cli(self, content, *args):
        self.spec.write_text(content, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPTS / "render.py"), str(self.spec),
                               "--result-json", str(self.result), *args], capture_output=True, text=True)

    def test_invalid_yaml_and_structure_exit_three(self):
        for content in ("", "columns: [", "- item", "columns:\n  - label: 采购", "columns: wrong", "today: 2026-13-40"):
            with self.subTest(content=content):
                p = self.run_cli(content, "--lint")
                self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
                self.assertNotIn("Traceback", p.stderr)
                self.assertEqual(json.loads(self.result.read_text())["status"], "invalid_spec")

    def test_invalid_reference_in_verify_exit_three(self):
        sp = flow()
        sp["verify"] = {"start": "unknown"}
        p = self.run_cli(r.yaml.safe_dump(sp), "--lint")
        self.assertEqual(p.returncode, 3)
        self.assertIn("verify.start", p.stdout)

    def test_invalid_dates_enum_and_types_have_field_paths(self):
        cases = [({"layout": "timeline", "milestones": [{"label": "上线", "date": "2026-13-40"}]}, "milestones[0].date"),
                 ({"layout": "timeline", "milestones": [{"label": "上线", "date": "2026-10", "status": "finished"}]}, "milestones[0].status"),
                 (dict(flow(), verify=[]), "verify"),
                 (dict(flow(), verify={"separate": [["start"]]}), "verify.separate[0]"),
                 (dict(flow(), orientation="diagonal"), "orientation"),
                 (dict(flow(), columns=[{"id": "a", "lanes": 0}]), "lanes")]
        for spec, path in cases:
            with self.subTest(path=path):
                p = self.run_cli(r.yaml.safe_dump(spec), "--lint")
                self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
                self.assertIn(path, p.stdout)

    def test_png_failure_is_partial_and_stale_file_is_not_success(self):
        self.spec.write_text(r.yaml.safe_dump(flow()))
        stale = self.spec.with_suffix(".png")
        stale.write_bytes(b"old picture")
        with patch.object(sys, "argv", ["render.py", str(self.spec), "--all", "--result-json", str(self.result)]), patch.object(r, "snapshot", side_effect=RuntimeError("browser unavailable")), contextlib.redirect_stdout(io.StringIO()):
            code = r.main()
        result = json.loads(self.result.read_text())
        self.assertEqual(code, 4)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["artifacts"]["png"]["status"], "failed")
        self.assertEqual(result["artifacts"]["html"]["status"], "generated")
        self.assertEqual(stale.read_bytes(), b"old picture")

    def test_html_and_svg_delivery_succeeds_without_png(self):
        svg = self.root / "output.svg"
        p = self.run_cli(r.yaml.safe_dump(flow()), "--svg", str(svg))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        ET.parse(svg)
        result = json.loads(self.result.read_text())
        self.assertEqual(result["status"], "generated")
        self.assertNotIn("png", result["artifacts"])

    def test_assets_and_guides_are_runtime_sources(self):
        for name in r.INIT_ALIAS:
            p = subprocess.run([sys.executable, str(SCRIPTS / "render.py"), "--init", name], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(r.yaml.safe_load(p.stdout), r.yaml.safe_load(r.EXAMPLES[r.INIT_ALIAS[name]]))
        for name, path in r.GUIDES.items():
            p = subprocess.run([sys.executable, str(SCRIPTS / "render.py"), "--guide", name], capture_output=True, text=True)
            self.assertEqual(p.stdout.strip(), path.read_text().strip())

    def test_missing_rule_coverage_fails_selftest(self):
        with patch.object(r, "ALL_CODES", r.ALL_CODES | {"NEW_RULE"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(r.selftest())


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dsl = self.root / "sample.wb.json"
        self.dsl.write_text('{"nodes": []}')
        self.result = self.root / "publish.json"
        self.calls = []
        self.update_code = 0
        self.export_code = 0
        self.preview_code = 0
        self.env = {"lark_cli": True, "logged_in": True, "whiteboard_cli": "global"}

    def args(self, **kw):
        args = dict(wb=str(self.dsl), token="fake-target", mode="append", passthrough=[],
                    verify_only=False, dry_run=False, result_json=str(self.result))
        args.update(kw)
        return SimpleNamespace(**args)

    def sh(self, cmd, timeout=120):
        self.calls.append(cmd)
        return (self.update_code, "simulated") if "+update" in cmd else (0, '{"errors":[]}')

    def export(self, token, path):
        self.calls.append(["export", token])
        if self.export_code == 0:
            Path(path).write_bytes(b"fresh preview")
        return self.export_code, "simulated export"

    def process(self, cmd, stdout=None, **kwargs):
        code = self.preview_code if "-o" in cmd else 0
        if "-o" in cmd and code == 0:
            Path(cmd[cmd.index("-o") + 1]).write_bytes(b"preview")
        if hasattr(stdout, "write"):
            stdout.write('{"nodes":[]}')
        return SimpleNamespace(returncode=code, communicate=lambda **kw: (None, ""), wait=lambda **kw: code, poll=lambda: code)

    def run_publish(self, **kw):
        with patch.object(w, "probe", return_value=self.env), patch.object(w, "wb_cmd", return_value=["fake-whiteboard"]), patch.object(w, "sh", side_effect=self.sh), patch.object(w.subprocess, "Popen", side_effect=self.process), patch.object(w, "export", side_effect=self.export), patch.object(w.time, "sleep"), contextlib.redirect_stdout(io.StringIO()):
            code = w.publish(self.args(**kw))
        return code, json.loads(self.result.read_text())

    def updates(self):
        return [c for c in self.calls if "+update" in c]

    def test_mutation_flags_cannot_be_passed_through(self):
        for flag in ("--overwrite", "--source=@other", "--whiteboard-token=other", "--as=bot", "--yes --overwrite"):
            with self.subTest(flag=flag):
                code, result = self.run_publish(passthrough=[flag])
                self.assertEqual(code, 3)
                self.assertEqual(result["write"], "not_attempted")
                self.assertEqual(self.calls, [])

    def test_allowlisted_confirmation_does_not_change_mode(self):
        code, result = self.run_publish(passthrough=["--yes"])
        self.assertEqual(code, 0)
        self.assertIn("--yes", self.updates()[0])
        self.assertNotIn("--overwrite", self.updates()[0])
        self.assertEqual(result["operation"]["mode"], "append")
        self.assertEqual(result["visual_review"], "not_performed")

    def test_explicit_overwrite_and_mode_specific_idempotency(self):
        _, append = self.run_publish()
        _, overwrite = self.run_publish(mode="overwrite")
        self.assertIn("--overwrite", self.updates()[-1])
        self.assertNotEqual(append["operation"]["idempotent_token"], overwrite["operation"]["idempotent_token"])

    def test_no_mode_previews_without_writing(self):
        code, result = self.run_publish(mode=None)
        self.assertEqual(code, 20)
        self.assertEqual(self.updates(), [])

    def test_confirmation_gate_never_auto_retries(self):
        self.update_code = 10
        code, result = self.run_publish()
        self.assertEqual(code, 10)
        self.assertEqual(len(self.updates()), 1)
        self.assertEqual(result["write"], "confirmation_required")

    def test_network_retry_reuses_operation_token(self):
        self.update_code = 124
        code, result = self.run_publish()
        self.assertEqual(code, 1)
        self.assertEqual(len(self.updates()), 2)
        self.assertEqual(self.updates()[0], self.updates()[1])
        self.assertEqual(result["write"], "outcome_unknown")

    def test_failed_readback_is_partial_without_rewriting(self):
        self.export_code = 1
        code, result = self.run_publish()
        self.assertEqual(code, 21)
        self.assertEqual(result["write"], "succeeded")
        self.assertEqual(result["status"], "written_unverified")
        self.assertEqual(len(self.updates()), 1)

    def test_verify_only_never_converts_or_writes(self):
        code, result = self.run_publish(verify_only=True)
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [["export", "fake-target"]])
        self.assertEqual(result["write"], "not_attempted")

    def test_failed_engine_preview_blocks_write(self):
        self.preview_code = 1
        code, result = self.run_publish()
        self.assertEqual(code, 1)
        self.assertEqual(self.updates(), [])
        self.assertEqual(result["conversion"]["status"], "failed")

    def test_dry_run_does_not_require_lark_login_or_write(self):
        self.env.update(lark_cli=False, logged_in=False)
        code, result = self.run_publish(dry_run=True)
        self.assertEqual(code, 0)
        self.assertEqual(self.updates(), [])
        self.assertEqual(result["status"], "converted")

    def test_conflicting_readback_and_dry_run_are_rejected(self):
        code, result = self.run_publish(verify_only=True, dry_run=True)
        self.assertEqual(code, 3)
        self.assertEqual(self.calls, [])

    def test_export_cannot_reuse_a_stale_preview(self):
        path = self.root / "old.png"
        path.write_bytes(b"stale")
        with patch.object(w, "sh", return_value=(0, "no output")):
            code, message = w.export("fake", path)
        self.assertEqual(code, 1)
        self.assertEqual(path.read_bytes(), b"stale")


if __name__ == "__main__":
    unittest.main()
