"""Contrast and per-diagram validation regressions."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/saan-diagram/scripts"
sys.path.insert(0, str(SCRIPTS))
import render as r
from spec_validation import SpecError


def single_node(kind="module", **node_options):
    return {"title": "Example", "language": "en",
            "columns": [{"id": "a", "label": "Stage", "lanes": 1}],
            "nodes": [{"id": "step", "label": "Step", "kind": kind,
                       "col": "a", "row": 1, **node_options}]}


def dark_zone(kind, **node_options):
    spec = single_node(kind, **node_options)
    spec["overlays"] = [{"kind": "zone", "label": "", "fill": "#4E5969",
                         "targets": ["step"]}]
    return spec


def core_nodes(limit=None):
    spec = single_node()
    spec["columns"][0]["lanes"] = 4
    spec["nodes"] = [{"id": f"n{i}", "label": f"Step {i}", "col": "a",
                      "lane": i, "row": 1, "core": True} for i in range(4)]
    if limit is not None:
        spec["core_limit"] = limit
    return spec


def layout_codes(diagram):
    return [code for code, _ in r.collect(diagram)[0]]


class ContrastTests(unittest.TestCase):
    def test_single_column_single_node_passes_all_titlebars(self):
        for orientation in ("horizontal", "vertical"):
            for titlebar in r.TITLEBARS:
                with self.subTest(orientation=orientation, titlebar=titlebar):
                    spec = dict(single_node(), orientation=orientation, titlebar=titlebar, brand="#1456F0")
                    self.assertEqual(r.collect(r.build_spec(spec)[0])[:2], ([], []))

    def test_single_column_flow_passes(self):
        spec = single_node()
        spec["nodes"] = [{"id": f"n{i}", "label": f"Step {i}", "col": "a",
                          "row": i * 2} for i in range(3)]
        spec["edges"] = [{"from": "n0", "to": "n1", "kind": "flow"},
                         {"from": "n1", "to": "n2", "kind": "flow"}]
        self.assertEqual(r.collect(r.build_spec(spec)[0])[:2], ([], []))

    def test_single_column_still_rejects_indistinguishable_node(self):
        spec = single_node("hub")
        spec["overlays"] = [{"kind": "zone", "label": "", "fill": r.NEUTRAL["hub"],
                             "targets": ["step"]}]
        self.assertIn("CT1", layout_codes(r.build_spec(spec)[0]))

    def test_unmarked_white_node_is_not_treated_as_titlebar(self):
        svg = '<svg><rect x="20" y="60" width="100" height="28" fill="#FFFFFF"/></svg>'
        self.assertIn("CT1", [code for code, _ in r.contrast_findings(svg)])

    def test_white_nonrectangular_nodes_in_dark_zone_have_readable_text(self):
        for kind in ("decision", "doc"):
            for options in ({}, {"sub": "ID-1"}, {"core": True}):
                with self.subTest(kind=kind, options=options):
                    d = r.build_spec(dark_zone(kind, **options))[0]
                    self.assertEqual(r.collect(d)[:2], ([], []))

    def test_unreadable_text_on_nonrectangular_nodes_is_still_rejected(self):
        for kind in ("decision", "doc"):
            for token, options in (("node_text", {}), ("soft", {"sub": "ID-1"})):
                with self.subTest(kind=kind, token=token):
                    d = r.build_spec(dark_zone(kind, **options))[0]
                    with patch.dict(d.t, {token: "#FFFFFF"}):
                        self.assertIn("CT2", layout_codes(d))

    def test_text_outside_nonrectangular_node_keeps_zone_background(self):
        for kind in ("decision", "doc"):
            with self.subTest(kind=kind):
                d, svg, *_ = r.build_spec(dark_zone(kind))
                n = d.nodes["step"]
                # Just inside the bounding box, outside the diamond/wavy document.
                x = n.x + 2
                y = n.y + 2 if kind == "decision" else n.b - 1
                svg = svg.replace("</svg>", f'<text x="{x}" y="{y + 6}" '
                                  'font-size="12" fill="#20252C">Outside</text></svg>')
                findings = r.contrast_findings(svg)
                self.assertTrue(any(code == "CT2" and "Outside" in msg for code, msg in findings), findings)

    def test_unbacked_label_in_dark_zone_is_still_rejected(self):
        self.assertIn("CT2", layout_codes(r.build_spec(dark_zone("label"))[0]))


class CoreLimitTests(unittest.TestCase):
    def test_building_default_diagram_does_not_tighten_existing_limit(self):
        generous = r.build_spec(core_nodes(4))[0]
        self.assertNotIn("F1", layout_codes(generous))
        r.build_spec(single_node())
        self.assertNotIn("F1", layout_codes(generous))

    def test_building_generous_diagram_does_not_relax_existing_default(self):
        strict = r.build_spec(core_nodes())[0]
        self.assertIn("F1", layout_codes(strict))
        r.build_spec(core_nodes(4))
        self.assertIn("F1", layout_codes(strict))

    def test_default_build_still_rejects_four_cores_after_generous_build(self):
        r.build_spec(core_nodes(4))
        self.assertIn("F1", layout_codes(r.build_spec(core_nodes())[0]))

    def test_invalid_spec_cannot_change_existing_limit(self):
        strict = r.build_spec(core_nodes())[0]
        with self.assertRaises(SpecError):
            r.build_spec(dict(core_nodes(10), columns="invalid"))
        self.assertIn("F1", layout_codes(strict))

    def test_direct_stage_constructor_uses_own_limit(self):
        r.build_spec(core_nodes(10))
        self.assertIn("F1", layout_codes(r.Diagram(core_nodes())))
        r.build_spec(single_node())
        self.assertNotIn("F1", layout_codes(r.Diagram(core_nodes(4))))

    def test_cross_layout_builds_do_not_change_stage_validation(self):
        for name in ("biz-platform", "procurement-er", "group-org", "bid-fishbone",
                     "platform-timeline", "ai-quadrant", "proc-idef0"):
            with self.subTest(name=name):
                generous = r.build_spec(core_nodes(4))[0]
                r.build_spec(r._load_example(name))
                self.assertNotIn("F1", layout_codes(generous))
                strict = r.build_spec(core_nodes())[0]
                r.build_spec(dict(r._load_example(name), core_limit=10))
                self.assertIn("F1", layout_codes(strict))

    def test_direct_other_layouts_respect_their_own_limit(self):
        cases = [
            ("layers", {"layout": "layers", "layers": [{"id": "a", "label": "Layer",
                "blocks": [{"title": f"Block {i}", "core": True, "items": ["Item"]} for i in range(4)]}]}),
            ("org", {"layout": "org", "orgs": [{"id": "root", "label": "Root", "core": True,
                "children": [{"id": f"n{i}", "label": f"Team {i}", "core": True} for i in range(3)]}]}),
            ("fishbone", {"layout": "fishbone", "effect": "Delay", "categories": [
                {"label": f"Cause {i}", "causes": [{"label": f"Root {i}", "root": True}]} for i in range(4)]}),
            ("timeline", {"layout": "timeline", "start": "2026-01", "end": "2027-01", "milestones": [
                {"label": f"Event {i}", "date": f"2026-0{i + 1}-15", "core": True} for i in range(4)]}),
            ("quadrant", {"layout": "quadrant", "x": {"label": "Ease"}, "y": {"label": "Value"},
                "items": [{"label": f"Item {i}", "x": i * 2 + 1, "y": 5, "core": True} for i in range(4)]}),
            ("idef0", {"layout": "idef0", "activities": [
                {"id": f"n{i}", "label": f"Task {i}", "core": True} for i in range(4)]}),
        ]
        for name, spec in cases:
            with self.subTest(layout=name):
                r.build_spec(core_nodes(10))
                strict = r.LAYOUTS[name](copy.deepcopy(spec))
                self.assertIn("F1", layout_codes(strict))
                r.build_spec(single_node())
                generous = r.LAYOUTS[name](dict(copy.deepcopy(spec), core_limit=4))
                self.assertNotIn("F1", layout_codes(generous))
                self.assertIn("F1", layout_codes(strict))

    def test_invalid_limits_are_rejected_by_build_and_direct_constructors(self):
        for limit in (0, -1, True, 1.5, "4", None):
            for constructor in (lambda sp: r.build_spec(sp)[0], r.Diagram):
                with self.subTest(limit=limit, constructor=constructor):
                    with self.assertRaisesRegex(SpecError, "core_limit"):
                        constructor(dict(core_nodes(), core_limit=limit))


class ValidationCLITests(unittest.TestCase):
    def run_cli(self, spec, *args):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        source = root / "sample.json"
        result = root / "sample.result.json"
        source.write_text(json.dumps(spec), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPTS / "render.py"), str(source),
                               "--result-json", str(result), *args], capture_output=True, text=True)
        return proc, json.loads(result.read_text()), root

    def test_regression_specs_pass_lint_and_export(self):
        for spec in (single_node(), dark_zone("decision"), dark_zone("doc")):
            with self.subTest(kind=spec["nodes"][0]["kind"]):
                proc, result, _ = self.run_cli(spec, "--lint")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(result["status"], "validated")
                with tempfile.TemporaryDirectory() as td:
                    svg, wb = Path(td) / "sample.svg", Path(td) / "sample.wb.json"
                    proc, result, root = self.run_cli(spec, "--svg", str(svg), "--wb", str(wb))
                    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                    self.assertEqual(result["status"], "generated")
                    self.assertEqual(set(result["artifacts"]), {"html", "svg", "whiteboard_dsl"})
                    self.assertTrue(all(a["status"] == "generated" for a in result["artifacts"].values()))
                    ET.parse(svg)
                    self.assertTrue(json.loads(wb.read_text()))
                    self.assertIn("<svg", (root / "sample.html").read_text())

    def test_invalid_diagrams_still_fail_lint(self):
        indistinct = single_node("hub")
        indistinct["overlays"] = [{"kind": "zone", "label": "", "fill": r.NEUTRAL["hub"],
                                  "targets": ["step"]}]
        for spec, code in ((indistinct, "CT1"), (dark_zone("label"), "CT2"), (core_nodes(), "F1")):
            with self.subTest(code=code):
                proc, result, _ = self.run_cli(spec, "--lint")
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(result["status"], "validation_failed")
                self.assertIn(code, [c for c, _ in result["findings"]["layout"]])


if __name__ == "__main__":
    unittest.main()
