# 写入飞书画板

> 用 `uv run scripts/render.py --guide feishu` 输出本文。写入只能通过 `scripts/wb_publish.py`，**不要直接拼 lark-cli 写入命令**：安全规矩写在脚本里，绕开脚本就等于绕开规矩。

```bash
python3 scripts/wb_publish.py --probe                                   # 探测环境（缓存 12 小时）
python3 scripts/wb_publish.py --resolve-doc <文档链接>                    # 列出文档里已有的画板 token
python3 scripts/wb_publish.py pay.wb.json --token <wbcn…>                # 首次：校验转换 + 导出现有画板，停下（退出码 20）
python3 scripts/wb_publish.py pay.wb.json --token <wbcn…> --mode append  # 确认后写入，写后导出核验图
```

## 流程

1. **探测**：`--probe`。没装 lark-cli 或没登录 → 问用户一次："现在登录，还是先只要 HTML + PNG？"。用户选登录时，按 lark-cli 的授权流程执行 `lark-cli auth login`，授权链接配二维码一起展示。
2. **找画板**：
   - 用户给了画板 token（`wbcn…`）→ 直接用；
   - 给了文档链接 → `--resolve-doc <链接>`；有多块画板时问用户写哪一块；
   - 文档里没有画板 → 用户同意后 `--resolve-doc <链接> --create-board`，在**该文档**末尾追加一块空画板；
   - **什么都没给 → 问用户写进哪个文档。不要自己新建文档。** 用户不想指定，就只交付 HTML + PNG，并说明原因。
3. **首次运行不带 `--mode`**：脚本校验画板数据（错误必须为 0）、用画板引擎渲染预览（`<slug>.wb.png`）、转换格式，然后导出现有画板到 `<slug>.before.png`，以**退出码 20** 停下。用当前平台的图像工具查看这张图：
   - 空画板 → `--mode append` 重跑；
   - 非空 → 问用户：追加，还是覆盖（`--mode overwrite`，整板重建、不可撤回）。**用户没有明确同意，不得覆盖。**
   - 刚用 `--create-board` 新建的画板是空的，可以直接 `--mode append`。
4. **写入**：
   - **退出码 10** 是 lark-cli 的高风险确认门禁，不是报错。把脚本打印的提示原样告诉用户，只有门禁要求 `--yes` 且用户同意后才用 `--pass=--yes` 重跑；其他透传参数会被拒绝。脚本不会自己追加任何参数。
   - 写入编号由目标、写入方式和内容共同生成，重试自动复用同一个；网络失败脚本会自动重试 1 次。
5. **核验**：成功后脚本导出 `<slug>.board.png`。用当前平台的图像工具看过再回复用户。

退出码：0 本次转换或回读完成（具体看结果文件） · 21 写入成功但核验图导出失败 · 2 环境不满足 · 3 画板数据校验失败 · 10 需要用户确认 · 20 需要决定写入方式 · 1 其他失败。写入连续失败 2 次就停下，先确认远端状态；回读失败只用 `--verify-only` 重试回读，不能重写。其他失败停下，如实说明卡在哪一步，改为交付 HTML + PNG。第一次在新环境使用，可以先加 `--dry-run`（只校验转换，不写入）。

## 其他

- **没有 Node.js**：画板数据转换不了。安装依赖后重试，或交付本地 HTML/SVG；不得改用裸 lark-cli 命令绕过发布脚本。
- **提速**：`npm i -g @larksuite/whiteboard-cli@^0.2.13` 装一次，脚本会优先用全局命令，省掉每次 npx 解析（首次约 10 秒）。是否安装由用户决定。
- 环境里有官方 `lark-whiteboard` / `lark-shared` skill 时，写入前先读它们对 `+update` 的说明；与本文冲突时，以更严格的那条为准。

## 结果与回读

默认写出 `<slug>.wb.publish.json`，也可用 `--result-json PATH` 指定。分别记录 validation、conversion、write、readback 和 visual_review。`readback.status: exported` 只证明本次核验图已导出，`visual_review: not_performed` 表示脚本没有检查图像内容。

```bash
python3 scripts/wb_publish.py pay.wb.json --token <wbcn…> --verify-only
```

该命令只重新导出画板，不转换、不重复写入。`--dry-run` 只校验和转换，本地转换不要求飞书登录，但仍需 Node.js / whiteboard-cli。预览图生成失败会阻止写入。

脚本约束命令参数，不能代替用户授权或平台权限。不要把限制顶层 Bash 命令的配置描述为完整安全隔离；外部权限以宿主平台和飞书权限为准。
