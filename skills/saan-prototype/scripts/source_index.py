"""Find the IDs a source specification defines, and the line that defines each one."""
import re

DEFAULT_PATTERNS = {"open": r"Q-\d+", "acceptance": r"AC-\d+", "rule": r"FR-[A-Z]*\d+"}


def patterns(manifest):
    p = dict(DEFAULT_PATTERNS)
    p.update(manifest.get("id_patterns") or {})
    return p


def index(text, pats):
    """Return {kind: {id: definition}}. The definition is the first table row whose
    first cell is the ID; otherwise the first line that mentions it."""
    lines = text.splitlines()
    out = {}
    for kind, pat in pats.items():
        rx = re.compile(rf"(?<![A-Za-z0-9-])({pat})(?![A-Za-z0-9])")
        found = {}
        for line in lines:
            for m in rx.finditer(line):
                found.setdefault(m.group(1), None)
        for i in found:
            row = re.compile(rf"^\|\s*\**{re.escape(i)}\**\s*\|")
            line = next((l for l in lines if row.match(l.strip())), None) or next(l for l in lines if i in l)
            found[i] = clean(line)
        out[kind] = found
    return out


def clean(line, limit=300):
    line = line.strip()
    if line.startswith("|"):
        line = " | ".join(c.strip() for c in line.strip("|").split("|") if c.strip())
    return line[:limit]


def all_ids(idx):
    return {i for ids in idx.values() for i in ids}
