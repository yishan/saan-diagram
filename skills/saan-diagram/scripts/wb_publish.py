#!/usr/bin/env python3
"""saan-diagram v1.0 · 飞书画板写入：把画板 DSL（*.wb.json）安全地写进飞书画板。

模型只能通过本脚本写画板，不要直接拼 lark-cli 写入命令。

一条命令完成：探测 → 校验与转换 → （首次）预览现有画板并停下 → 写入 → 导出核验图。
安全规矩写在脚本里，不靠模型记得：
  · 不新建文档：只往用户给的画板或文档里写；
  · 没有 --mode 就不写：先导出现有画板预览，退出码 20，由模型看图、问用户；
  · overwrite 只在 --mode overwrite 时才加，且必须是用户明确同意过；
  · lark-cli 退出码 10（高风险确认门禁）原样返回 10，不自动追加任何参数；
  · 幂等 token 由内容哈希生成，重试自动复用同一个。

退出码：0 成功 · 2 环境不满足 · 3 DSL 校验失败 · 10 需要用户确认（lark-cli 门禁）· 20 需要决定写入方式 · 1 其他失败
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

WB_PKG = "@larksuite/whiteboard-cli@^0.2.13"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "saan-diagram" / "probe.json"
CACHE_TTL = 12 * 3600


def sh(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"未找到命令：{cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"超时：{' '.join(cmd)}"


def wb_cmd():
    """优先用全局安装的 whiteboard-cli（省掉每次 npx 解析），否则 npx。"""
    exe = shutil.which("whiteboard-cli")
    return [exe] if exe else ["npx", "-y", WB_PKG]


def probe(fresh=False):
    if not fresh and CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_TTL:
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass
    r = {"lark_cli": False, "logged_in": False, "node": bool(shutil.which("node")),
         "whiteboard_cli": "global" if shutil.which("whiteboard-cli") else ("npx" if shutil.which("npx") else None)}
    code, out = sh(["lark-cli", "--version"], 20)
    r["lark_cli"] = code == 0
    if r["lark_cli"]:
        code, out = sh(["lark-cli", "auth", "status"], 20)
        r["logged_in"] = code == 0 and not re.search(r"not logged|未登录|unauth", out, re.I)
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(r))
    except Exception:
        pass
    return r


def summary(r):
    if not r["lark_cli"]:
        return "未安装 lark-cli：选飞书需要先安装并登录"
    if not r["logged_in"]:
        return "已安装 lark-cli，但未登录：选飞书需要先登录（lark-cli auth login）"
    if not r["whiteboard_cli"]:
        return "已登录飞书，但没有 Node.js：只能用 SVG 降级写法（文字与形状分离）"
    return "已检测到 lark-cli 并已登录，可直接写入画板"


def resolve_doc(url, create=False):
    code, out = sh(["lark-cli", "docs", "+fetch", "--doc", url, "--as", "user"])
    if code != 0:
        return code, {"error": out.strip()[-400:]}
    toks = re.findall(r'<whiteboard[^>]*token="([^"]+)"', out)
    if toks or not create:
        return 0, {"whiteboards": toks}
    doc_id = re.sub(r"[?#].*$", "", url).rstrip("/").split("/")[-1]
    code, out = sh(["lark-cli", "docs", "+update", "--doc", doc_id, "--command", "append",
                    "--content", '<whiteboard type="blank"></whiteboard>', "--as", "user"])
    if code != 0:
        return code, {"error": out.strip()[-400:]}
    m = re.search(r'"block_token"\s*:\s*"([^"]+)"', out)
    return (0, {"whiteboards": [m.group(1)], "created": True}) if m else (1, {"error": "已追加画板，但没读到 block_token：" + out[-300:]})


def export(token, path):
    return sh(["lark-cli", "whiteboard", "+export", "--whiteboard-token", token,
               "--output-type", "preview", "--output", str(path), "--as", "user"])


def publish(a):
    wb = Path(a.wb)
    slug = wb.name.replace(".wb.json", "").replace(".json", "")
    outdir = wb.parent
    r = probe()
    if not (r["lark_cli"] and r["logged_in"]):
        print("ENV:", summary(r))
        return 2
    if not r["whiteboard_cli"]:
        print("ENV: 没有 Node.js，无法转换画板 DSL。改用 render.py --svg 输出 SVG，再 lark-cli whiteboard +update --input_format svg（文字与形状分离，需向用户说明）")
        return 2
    W = wb_cmd()
    # ① 校验
    code, out = sh(W + ["-i", str(wb), "--check"], 180)
    errs = re.findall(r'"errors?"\s*:\s*(\[[^\]]*\]|"[^"]*"|\d+)', out)
    if code != 0 or any(e not in ('""', "[]", "0") for e in errs):
        print("CHECK FAIL:\n" + out.strip()[-1500:])
        return 3
    # ② 转换：画板引擎预览图 + openapi，两条并行
    oa, pv = outdir / f"{slug}.openapi.json", outdir / f"{slug}.wb.png"
    p1 = subprocess.Popen(W + ["-i", str(wb), "-o", str(pv)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(oa, "w") as fh:
        p2 = subprocess.Popen(W + ["-i", str(wb), "--to", "openapi", "--format", "json"], stdout=fh, stderr=subprocess.PIPE, text=True)
        _, err2 = p2.communicate(timeout=180)
    p1.wait(timeout=180)
    if p2.returncode != 0 or oa.stat().st_size == 0:
        print("CONVERT FAIL:\n" + (err2 or "")[-800:])
        return 1
    print(f"画板引擎预览：{pv}")
    if a.dry_run:
        print(f"DRY RUN：已生成 {oa}，未写入飞书")
        return 0
    # ③ 没决定写入方式：先看现有画板
    if not a.mode:
        before = outdir / f"{slug}.before.png"
        code, out = export(a.token, before)
        print(f"NEEDS_DECISION：现有画板预览已导出到 {before}" if code == 0 else f"NEEDS_DECISION：导出现有画板失败（{out.strip()[-200:]}）")
        print("  看图：空画板 → 用 --mode append 重跑；非空 → 问用户追加（append）还是覆盖（overwrite，整板重建、不可撤回）")
        return 20
    # ④ 写入（幂等 token 由内容决定，重试自动复用）
    key = "saan-" + hashlib.sha1((a.token + oa.read_text()).encode()).hexdigest()[:16]
    cmd = ["lark-cli", "whiteboard", "+update", "--whiteboard-token", a.token, "--input_format", "raw",
           "--source", f"@{oa}", "--idempotent-token", key, "--as", "user"]
    if a.mode == "overwrite":
        cmd.append("--overwrite")
    cmd += a.passthrough or []
    for attempt in (1, 2):
        code, out = sh(cmd, 300)
        if code == 10:
            print("CONFIRM_REQUIRED（lark-cli 高风险确认门禁）：停下来把下面的提示原样告诉用户，用户同意后用 --pass 追加它要求的参数重跑。")
            print(out.strip()[-1200:])
            return 10
        if code == 0:
            break
        if attempt == 2:
            print(f"WRITE FAIL（重试 1 次后仍失败，幂等 token {key}）：\n{out.strip()[-1200:]}")
            return 1
        time.sleep(2)
    # ⑤ 核验
    after = outdir / f"{slug}.board.png"
    code, out = export(a.token, after)
    print(f"OK 已写入画板 {a.token}（{a.mode}，token {key}）")
    print(f"  写入后核验图：{after}" if code == 0 else f"  写入成功，但导出核验图失败：{out.strip()[-200:]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="把 *.wb.json 安全写入飞书画板")
    ap.add_argument("wb", nargs="?", help="render.py --all 生成的 <slug>.wb.json")
    ap.add_argument("--token", help="目标画板 token（wbcn…）")
    ap.add_argument("--mode", choices=["append", "overwrite"], help="写入方式；不给就先导出现有画板并停下（退出码 20）")
    ap.add_argument("--pass", dest="passthrough", action="append", help="lark-cli 门禁要求追加的参数（用户确认后才加）")
    ap.add_argument("--dry-run", action="store_true", help="只校验和转换，不写入")
    ap.add_argument("--probe", action="store_true", help="探测环境（结果缓存 12 小时）")
    ap.add_argument("--fresh", action="store_true", help="忽略探测缓存")
    ap.add_argument("--resolve-doc", metavar="URL", help="列出文档里已有的画板 token")
    ap.add_argument("--create-board", action="store_true", help="与 --resolve-doc 同用：文档里没有画板时，在该文档末尾追加一块空画板（不新建文档）")
    a = ap.parse_args()
    if a.probe:
        r = probe(a.fresh)
        print(json.dumps(r, ensure_ascii=False))
        print(summary(r))
        return 0
    if a.resolve_doc:
        code, res = resolve_doc(a.resolve_doc, a.create_board)
        print(json.dumps(res, ensure_ascii=False))
        return code
    if not (a.wb and a.token):
        ap.error("需要 <slug>.wb.json 和 --token；或用 --probe / --resolve-doc")
    return publish(a)


if __name__ == "__main__":
    sys.exit(main())
