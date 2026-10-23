# 写入飞书画板

> 用 `python3 render.py --guide feishu` 输出本文。写入只能通过 `scripts/wb_publish.py`，**不要直接拼 lark-cli 写入命令**：安全规矩写在脚本里，绕开脚本就等于绕开规矩。

```bash
python3 wb_publish.py --probe                                   # 探测环境（缓存 12 小时）
python3 wb_publish.py --resolve-doc <文档链接>                    # 列出文档里已有的画板 token
python3 wb_publish.py pay.wb.json --token <wbcn…>                # 首次：校验转换 + 导出现有画板，停下（退出码 20）
python3 wb_publish.py pay.wb.json --token <wbcn…> --mode append  # 确认后写入，写后导出核验图
```

## 流程

1. **探测**：`--probe`。没装 lark-cli 或没登录 → 问用户一次："现在登录，还是先只要 HTML + PNG？"。用户选登录时，按 lark-cli 的授权流程执行 `lark-cli auth login`，授权链接配二维码一起展示。
2. **找画板**：
   - 用户给了画板 token（`wbcn…`）→ 直接用；
   - 给了文档链接 → `--resolve-doc <链接>`；有多块画板时问用户写哪一块；
   - 文档里没有画板 → 用户同意后 `--resolve-doc <链接> --create-board`，在**该文档**末尾追加一块空画板；
   - **什么都没给 → 问用户写进哪个文档。不要自己新建文档。** 用户不想指定，就只交付 HTML + PNG，并说明原因。
3. **首次运行不带 `--mode`**：脚本校验画板数据（错误必须为 0）、用画板引擎渲染预览（`<slug>.wb.png`）、转换格式，然后导出现有画板到 `<slug>.before.png`，以**退出码 20** 停下。用 Read 看这张图：
   - 空画板 → `--mode append` 重跑；
   - 非空 → 问用户：追加，还是覆盖（`--mode overwrite`，整板重建、不可撤回）。**用户没有明确同意，不得覆盖。**
   - 刚用 `--create-board` 新建的画板是空的，可以直接 `--mode append`。
4. **写入**：
   - **退出码 10** 是 lark-cli 的高风险确认门禁，不是报错。把脚本打印的提示原样告诉用户，用户同意后用 `--pass <它要求的参数>` 重跑。脚本不会自己追加任何参数。
   - 写入编号由内容哈希生成，重试自动复用同一个；网络失败脚本会自动重试 1 次。
5. **核验**：成功后脚本导出 `<slug>.board.png`。用 Read 看过再回复用户。

退出码：0 成功 · 2 环境不满足 · 3 画板数据校验失败 · 10 需要用户确认 · 20 需要决定写入方式 · 1 其他失败。连续失败 2 次就停下，如实说明卡在哪一步，改为交付 HTML + PNG。第一次在新环境使用，可以先加 `--dry-run`（只校验转换，不写入）。

## 其他

- **没有 Node.js**：画板数据转换不了。改用 `render.py <spec> --svg <slug>.svg` 输出 SVG，再 `lark-cli whiteboard +update --input_format svg`（这是唯一允许直接调用 lark-cli 写入的情况，同样要先导出现有画板、确认后再写）。代价是文字与形状分离、连线不绑定节点，交付时要说明。
- **提速**：`npm i -g @larksuite/whiteboard-cli@^0.2.13` 装一次，脚本会优先用全局命令，省掉每次 npx 解析（首次约 10 秒）。是否安装由用户决定。
- 环境里有官方 `lark-whiteboard` / `lark-shared` skill 时，写入前先读它们对 `+update` 的说明；与本文冲突时，以更严格的那条为准。

## 把"只能通过脚本"变成硬限制（可选，由用户自己设置）

说明文字只能约束模型，权限设置才能真正拦住。在 Claude Code 的 `.claude/settings.json`（项目级）或 `~/.claude/settings.json`（个人级）里加：

```json
{
  "permissions": {
    "deny": [
      "Bash(lark-cli whiteboard +update *)",
      "Bash(lark-cli docs +update *)"
    ]
  }
}
```

这样模型在命令行里直接调用这两条写入命令会被拒绝；`wb_publish.py` 在脚本内部调用 lark-cli，不受影响。权限规则检查的是模型直接发出的命令，不检查脚本内部启动的子进程，所以这条规则正好只拦"绕开脚本"的那条路。
