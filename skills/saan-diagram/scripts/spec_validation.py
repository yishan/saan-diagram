"""Input validation before layout. Business findings remain renderer rules."""
import datetime
import math
import re
from pathlib import Path

import yaml


class SpecError(ValueError):
    pass


def fail(path, message):
    raise SpecError(f"{path}: {message}")


def mapping(value, path):
    if not isinstance(value, dict):
        fail(path, "需要对象（键值表）")
    return value


def text(value, path):
    if not isinstance(value, str) or not value.strip():
        fail(path, "需要非空字符串")


def required(obj, keys, path):
    for key in keys:
        if key not in obj:
            fail(f"{path}.{key}", "缺少必填字段")


def records(obj, key, required_keys=(), path="spec"):
    value = obj.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        fail(f"{path}.{key}", "需要列表")
    for i, item in enumerate(value):
        loc = f"{key}[{i}]" if path == "spec" else f"{path}.{key}[{i}]"
        mapping(item, loc)
        required(item, required_keys, loc)
    return value


def references(value, path):
    values = value if isinstance(value, list) else [value]
    if not values:
        fail(path, "需要至少一个节点引用")
    for i, ref in enumerate(values):
        text(ref, f"{path}[{i}]")


def date_value(value, path):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    try:
        parts = [int(p) for p in str(value).replace("/", "-").replace(".", "-").split("-")]
        if len(parts) == 2:
            parts.append(1)
        if len(parts) != 3:
            raise ValueError()
        return datetime.date(*parts)
    except (TypeError, ValueError, OverflowError):
        fail(path, "需要有效日期 YYYY-MM 或 YYYY-MM-DD")


def load_spec(path):
    try:
        spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as ex:
        raise SpecError(f"{path}: 无法读取 spec（{ex.__class__.__name__}）") from ex
    except yaml.YAMLError as ex:
        mark = getattr(ex, "problem_mark", None)
        location = f"第 {mark.line + 1} 行，第 {mark.column + 1} 列" if mark else "格式错误"
        raise SpecError(f"{path}: YAML {location}；{getattr(ex, 'problem', '无法解析')}") from ex
    except (ValueError, OverflowError) as ex:
        raise SpecError(f"{path}: YAML 标量值无效（例如日期越界）：{ex}") from ex
    validate_spec(spec)
    return spec


def validate_spec(spec):
    mapping(spec, "spec")
    layout = spec.get("layout", "stages")
    if layout not in ("stages", "layers", "er", "org", "fishbone", "timeline", "quadrant", "idef0"):
        fail("layout", "无效的图示布局")
    for key, choices in {
        "orientation": ("horizontal", "vertical"),
        "language": ("en", "zh-CN"),
        "titlebar": ("outline", "gray", "brand", "dark"),
        "column_semantics": ("roles", "stages", "layout"),
        "profile": ("dfd", "audit", "opportunity"),
    }.items():
        if key in spec and spec[key] not in choices:
            fail(key, "可选值：" + " / ".join(choices))
    if "brand" in spec and (not isinstance(spec["brand"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", spec["brand"])):
        fail("brand", "需要 #RRGGBB 色值")

    # Shared scalar fields, including nested nodes, blocks and path steps.
    def walk(value, path="spec"):
        if isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")
        elif isinstance(value, dict):
            for key, item in value.items():
                loc = f"{path}.{key}"
                if key in ("id", "label", "actor", "title", "sub") and item is not None:
                    if not isinstance(item, str):
                        fail(loc, "需要字符串")
                    if key in ("id", "actor"):
                        text(item, loc)
                if key in ("core", "main", "frame", "break", "swimlane", "vertical") and not isinstance(item, bool):
                    fail(loc, "需要 true 或 false")
                numeric = key in ("row", "lane", "drow", "width", "entity_w", "lanes", "grid", "row_step", "cols", "height", "w", "size", "step_wrap") or (key in ("x", "y") and path != "spec")
                if numeric and item is not None:
                    if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
                        fail(loc, "需要有限数值")
                    if key in ("width", "entity_w", "lanes", "grid", "row_step", "cols", "height", "w", "size", "step_wrap") and item <= 0:
                        fail(loc, "必须大于 0")
                    if key in ("lanes", "grid", "cols", "span") and int(item) != item:
                        fail(loc, "需要整数")
                walk(item, loc)
    walk(spec)

    if layout == "stages":
        cols = records(spec, "columns", ("id",))
        if not cols:
            fail("columns", "需要至少一个阶段或角色列")
        ids = []
        for i, col in enumerate(cols):
            text(col["id"], f"columns[{i}].id")
            if col["id"] in ids:
                fail(f"columns[{i}].id", "列 id 重复")
            ids.append(col["id"])
        def node(n, path):
            required(n, ("label", "col"), path)
            text(n["label"], path + ".label")
            if n["col"] not in ids:
                fail(path + ".col", "引用了不存在的列")
        for i, n in enumerate(records(spec, "nodes")):
            node(n, f"nodes[{i}]")
        for key in ("groups", "containers"):
            for i, group in enumerate(records(spec, key, ("id", "col", "items"))):
                if not isinstance(group["items"], list):
                    fail(f"{key}[{i}].items", "需要列表")
                for j, item in enumerate(group["items"]):
                    if isinstance(item, dict):
                        required(item, ("label",), f"{key}[{i}].items[{j}]")
                    elif item is not None and not isinstance(item, str):
                        fail(f"{key}[{i}].items[{j}]", "需要文字或节点对象")
        if "paths" in spec:
            paths = mapping(spec["paths"], "paths")
            for i, row in enumerate(records(paths, "rows", path="paths")):
                for j, n in enumerate(records(row, "steps", path=f"paths.rows[{i}]")):
                    node(n, f"paths.rows[{i}].steps[{j}]")
            records(paths, "edges", ("from", "to"), "paths")
        records(spec, "edges", ("from", "to"))
    elif layout == "layers":
        def items(obj, key, path):
            value = obj.get(key, [])
            if not isinstance(value, list):
                fail(path + "." + key, "需要列表")
            for j, item in enumerate(value):
                loc = f"{path}.{key}[{j}]"
                if isinstance(item, dict):
                    required(item, ("label",), loc)
                    if item.get("kind", "chip") not in ("chip", "white", "internal", "external", "core", "ai", "special", "more"):
                        fail(loc + ".kind", "无效的分层图条目样式")
                else:
                    text(item, loc)
        for i, layer in enumerate(records(spec, "layers", ("id", "blocks"))):
            for j, block in enumerate(records(layer, "blocks", path=f"layers[{i}]")):
                loc = f"layers[{i}].blocks[{j}]"
                items(block, "items", loc)
                for k, stage in enumerate(records(block, "stages", ("steps",), loc)):
                    items(stage, "steps", f"{loc}.stages[{k}]")
                    if not stage["steps"]:
                        fail(f"{loc}.stages[{k}].steps", "需要至少一个步骤")
        for i, side in enumerate(records(spec, "side", ("id",))):
            for j, section in enumerate(records(side, "sections", path=f"side[{i}]")):
                loc = f"side[{i}].sections[{j}]"
                items(section, "items", loc)
                if "span" in section and (not isinstance(section["span"], list) or len(section["span"]) != 2):
                    fail(loc + ".span", "需要起始层和结束层两个引用")
        if "rails" in spec:
            rails = mapping(spec["rails"], "rails")
            for side in ("left", "right"):
                if side in rails:
                    items(rails, side, "rails")
        records(spec, "links", ("from", "to"))
    elif layout == "er":
        for i, entity in enumerate(records(spec, "entities", ("id", "label"))):
            if "fields" in entity and not isinstance(entity["fields"], list):
                fail(f"entities[{i}].fields", "需要列表")
        records(spec, "relations", ("from", "to"))
    elif layout == "org":
        def orgs(obj, key, path):
            for i, item in enumerate(records(obj, key, ("label",), path)):
                orgs(item, "children", f"{path}.{key}[{i}]")
        orgs(spec, "orgs", "spec")
        records(spec, "scopes")
        records(spec, "grants", ("from", "to"))
    elif layout == "fishbone":
        required(spec, ("effect",), "spec")
        text(spec["effect"], "effect")
        for i, cat in enumerate(records(spec, "categories", ("label",))):
            if "causes" in cat and not isinstance(cat["causes"], list):
                fail(f"categories[{i}].causes", "需要列表")
            for j, cause in enumerate(cat.get("causes") or []):
                if isinstance(cause, dict):
                    required(cause, ("label",), f"categories[{i}].causes[{j}]")
                else:
                    text(cause, f"categories[{i}].causes[{j}]")
    elif layout == "timeline":
        for key in ("start", "end", "today"):
            if key in spec:
                date_value(spec[key], key)
        if "start" in spec and "end" in spec and date_value(spec["start"], "start") > date_value(spec["end"], "end"):
            # A month end includes the entire month, matching the renderer.
            end_text = str(spec["end"])
            same_month = str(spec["start"])[:7] == end_text[:7] and len(end_text) == 7
            if not same_month:
                fail("end", "时间轴结束不能早于开始")
        for i, m in enumerate(records(spec, "milestones", ("label", "date"))):
            for key in ("date", "plan"):
                if key in m:
                    date_value(m[key], f"milestones[{i}].{key}")
            if "status" in m and m["status"] not in ("done", "pending", "unknown"):
                fail(f"milestones[{i}].status", "可选值：done / pending / unknown")
        for i, phase in enumerate(records(spec, "phases", ("label", "from", "to"))):
            for key in ("from", "to"):
                date_value(phase[key], f"phases[{i}].{key}")
    elif layout == "quadrant":
        for key in ("x", "y"):
            required(spec, (key,), "spec")
            mapping(spec[key], key)
            required(spec[key], ("label",), key)
        if "quadrants" in spec:
            mapping(spec["quadrants"], "quadrants")
        if "focus" in spec:
            references(spec["focus"], "focus")
        for i, item in enumerate(records(spec, "items", ("label", "x", "y"))):
            if "from" in item:
                value = item["from"]
                if not isinstance(value, list) or len(value) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
                    fail(f"items[{i}].from", "需要两个有限坐标值")
    elif layout == "idef0":
        records(spec, "activities", ("label",))
        records(spec, "inputs", ("to",))
        records(spec, "outputs", ("from",))
        records(spec, "flows", ("from", "to"))
        for key in ("controls", "mechanisms"):
            for i, obj in enumerate(records(spec, key, ("to",))):
                if not isinstance(obj["to"], list):
                    fail(f"{key}[{i}].to", "需要活动引用列表")

    verify = spec.get("verify")
    if verify is not None and verify is not False:
        if layout != "stages":
            fail("verify", "只支持阶段类图示")
        if verify is not True:
            mapping(verify, "verify")
            for key in ("start", "end", "nodes"):
                if key in verify:
                    references(verify[key], f"verify.{key}")
            for key in ("reachable", "terminates"):
                if key in verify and not isinstance(verify[key], bool):
                    fail(f"verify.{key}", "需要 true 或 false")
            for i, rule in enumerate(records(verify, "must_pass", ("before", "through"), "verify")):
                text(rule["before"], f"verify.must_pass[{i}].before")
                references(rule["through"], f"verify.must_pass[{i}].through")
            pairs = verify.get("separate", [])
            if not isinstance(pairs, list):
                fail("verify.separate", "需要岗位分离配对列表")
            for i, pair in enumerate(pairs):
                if not isinstance(pair, list) or len(pair) != 2:
                    fail(f"verify.separate[{i}]", "需要恰好两个节点引用")
                references(pair, f"verify.separate[{i}]")
    for i, accepted in enumerate(records(spec, "accept", ("code",))):
        for key in ("code", "match", "note"):
            if key in accepted:
                text(accepted[key], f"accept[{i}].{key}")
