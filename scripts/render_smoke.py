#!/usr/bin/env python3
"""Render every shipped YAML through the public CLI, with optional real PNGs."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--outdir", default="out/smoke")
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[1]
    skill = repo / "skills/saan-diagram"
    out = Path(args.outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    examples = sorted((skill / "assets").glob("*.yaml"))
    if len(examples) != 14:
        raise RuntimeError(f"Expected 14 shipped examples, found {len(examples)}")
    english = sorted((skill / "assets/en").glob("*.yaml"))
    if len(english) != 3:
        raise RuntimeError(f"Expected 3 English examples, found {len(english)}")
    examples += english
    for spec in examples:
        stem = spec.stem
        svg, wb = out / f"{stem}.svg", out / f"{stem}.wb.json"
        cmd = [sys.executable, str(skill / "scripts/render.py"), str(spec), "--outdir", str(out),
               "--svg", str(svg), "--wb", str(wb)]
        if args.png:
            cmd.append("--all")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f"{stem}: exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        root = ET.parse(svg).getroot()
        _, _, width, height = map(float, root.attrib["viewBox"].split())
        assert width > 0 and height > 0, stem
        assert json.loads(wb.read_text()), stem
        result = json.loads((out / f"{stem}.result.json").read_text())
        assert result["status"] == "generated", result
        assert all(x["status"] == "generated" for x in result["artifacts"].values()), result
        if args.png:
            data = (out / f"{stem}.png").read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n", stem
            assert all(n > 0 for n in struct.unpack(">II", data[16:24])), stem
        print(f"PASS {stem}: SVG + HTML + DSL" + (" + PNG" if args.png else ""), flush=True)
    print(f"PASS {len(examples)} examples")


if __name__ == "__main__":
    main()
