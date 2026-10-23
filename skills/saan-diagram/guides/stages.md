# 阶段类图示：架构视图 / 主流程 / 路径对比 / 泳道图

> 用 `python3 scripts/render.py --guide stages` 输出本文；起步模板用 `--init <示例名>`。

## 画布与方向
**泳道是可选的。** `columns` 永远是排版网格；画不画成可见泳道（列框和列头）由 `swimlane` 决定：

| 图示 | 默认 | 理由 |
|---|---|---|
| 泳道图、审计流程图（列 = 角色 / 部门） | 画 | 列就是"谁来做"，是图的主轴 |
| 架构视图、路径对比（列 = 生命周期阶段） | 画 | 强阶段控制，读者要按阶段对齐看 |
| 机会流程图（列 = 增值 / 非增值） | 画 | 两列的分界就是结论 |
| 单条主流程（只有一行 `paths`） | 不画 | 箭头已经表达先后，列框只会切碎流程 |
| 数据流图（`profile: dfd`） | 不画 | 符号（实体 / 处理 / 存储）已经说明角色 |

需要时用 `swimlane: true | false` 覆盖默认值。**不画泳道时，列只是网格，节点要等距排**：单条流程用一个宽列（如 `lanes: 9`），节点 `lane` 按固定步长递增（如 0、1.5、3 …），别沿用"每阶段一列"的写法，否则间距会忽大忽小。

- 顶部是标题栏，默认**白底线框**（`titlebar: outline`：1px 中性灰边框、深色字，不占用颜色预算）。也可以用 `gray`（浅灰底）、`brand`（VI 主色底，文字黑白自动按对比度选）或 `dark`（深色底）。
- **横向**（默认）：阶段从左到右成列，列头在顶部，`row` 往下走。
- **竖向**（`orientation: vertical`）：阶段从上到下成带，阶段名在左侧表头，`row` 往右走。同一份 spec 两个方向都能出图：`lane` 永远沿阶段宽度方向，`row` 永远跨阶段方向，走线方向（`h`↔`v`、`hv`↔`vh`、`ll`↔`tt`…）自动转置。换方向后要重新跑 `--lint`，个别间距可能需要微调。
- 所有结构尺寸都在 **4px 网格**上：泳道 112×48、节点高 28（带副标签 40）、系统块高 36、连线圆角 8。
- 图例自动生成，放在底部横条，只列图中实际用到的类型，放不下自动换行。

## 节点
| kind | 样式 | 用于 |
|---|---|---|
| `hub` | 深一档灰底，字重 600 | 主线节点、汇聚点 |
| `module`（默认） | 浅灰底 | 功能模块、业务对象 |
| `decision` | 白底菱形、细线描边 | 判断点，标签以"？"结尾，出线标"是 / 否" |
| `optional` | 白底虚线框 | 可选或条件触发的环节 |
| `system` + `owner: internal` | **VI 主色圆角矩形**（圆角 8），白字 | 内部系统 |
| `system` + `owner: external` | **VI 主色提亮 45%** 的圆角矩形，文字按对比度自动选黑白 | 外部服务（R4：深浅由归属决定，不由画图人决定） |
| `special`（旧写法 `ai`） | 浅橙底 | **重点能力**：这张图想特别突出的一类能力，最常见的是新增的 AI 能力（可选，见「叠加层」） |
| `doc` | 白底、底边波浪 | 单据 / 文档（申请单、验收单、发票、凭证），审计流程图用 |
| `store` | 右侧开口的矩形，左侧编号格（`sub: D1`） | 数据存储，数据流图用 |

**控制点 `control: K1` + `risk: 风险描述`**（任何节点都可加）：节点右上角出现深色编号标签，图例下方自动列出"控制点 → 防范的风险"清单。审计读者真正要看的是这张清单，所以 `risk` 必填（AU1）。

系统块是全图唯一用实心主色的元素，所以它们一眼就能和业务节点区分开。业务节点保持中性灰，颜色只留给"系统"和"核心"两种信号。

**核心业务底色 `core: true`**（节点和分组都可以用）：主色浅调底加主色描边，字重 600。
- 规则同 diagram-design 的焦点色：**全图最多 3 处**（F1）。超过 3 处就等于没有重点，先想清楚哪些才是真核心。
- 分组 `core: true` 会给整个区域铺浅底，用来标出"这一片是核心业务域"。

**副标签 `sub`**：只写技术值（协议、端口、技术栈，如 `SHA-256`、`MySQL`），用等宽字体 9px。**不写中文**（S1）。

## 分组与方框
`groups` 只是一种排版手段：把若干条目按网格摆在一起。**默认不画框。**

只有框本身能说明问题时，才加 `frame: true`：
- 这些条目共享同一个触发或边界，例如"都消费同一个事件""同一套数据隔离""同一个外部平台"；
- 原图里方框代表一个业务域，读者需要按域来理解。

如果只是"同一阶段的几个功能"，阶段本身已经说明了归属，再加框是重复，不加。

规则：
- 无框分组不可见，所以**不能当连线端点**（B1），要连就连它里面的主线节点。
- 两个可见分组不能交叠（G4）。
- `type: process` 的分组需要标 `main`，跨组的主流程只挂在 main 上（R1）。
- 主干节点推荐单独放一行（同一个 `row`），细节分组放在各自阶段下方。这样主流程是一条直线，不会穿过兄弟节点。
- 分组内部要画上下箭头时，用 `row_step: 1.3` 拉开组内行距。

## 连线（对应 diagram-design 的连线规则）
| kind | 样式 | 语义 |
|---|---|---|
| `flow` | 深色实线 1.5px | 业务主流程，有强先后关系 |
| `data` | 灰色点线 | 数据下发、系统集成、消息推送 |
| `return` | 灰色点线 | 回退、重做（用 `rr` / `ll` / `tt` 绕开主线） |
| `bidir` | 双向点线 | 双方交互 |
| `meta` | 紫色虚线，**必须带标签**（E3） | 配置依赖、受托关系，不是业务流 |
| 任意 kind + `emphasis: true` | 主色 2px | 关键路径，**全图只标一条路径** |

硬规则（lint 检查）：
1. **只用正交折线**，拐角是半径 8 的圆角，不画斜线。
2. **标签放在线旁，不压在线上**：横线的标签在线上方，竖线的标签在线右侧，都留 6px 间隙，并有白色遮罩。
3. **两条线不叠在一起**（G3）：平行段至少错开 12px。多条线共用一个起点做总线时，用 `bus: true` 显式声明。
4. **同一条边上的多个接点自动错开**（间距 12px）。
5. **线不穿过非端点节点**（G2）：先改走线绕开。
6. **标签不压住节点**（L2）。
7. **箭头要有地方显示**（A1）：带箭头的末段 ≥ 24px，其余每段 ≥ 12px。有箭头相连的两个元素要拉开间距：
   - 上下相连：`row` 至少差 **1.4**；判断菱形较高，进出菱形的上下连线至少差 **1.6**。
   - 左右相连：两个节点宽度都超过 88px（6 字以上）时，`lane` 至少差 1.2，或者精简措辞。
   - 走线的中间拐点没指定时，renderer 会自动把拐点往起点挪，给箭头段留够 24px。

## 叠加层（可选）
- `kind: special`（旧写法 `kind: ai`，两者等价）：浅橙铺底，标出**重点能力**。
  - 在 spec 顶层给它命名：`special: {label: AI 能力, prefix: AI}`。`label` 是图例名称，不写时默认"重点能力"。`prefix` 可选，写了就要求所有重点能力的标签以它开头（R5）。
  - 旧 spec 只写了 `kind: ai`、没声明 `special` 时，按 `{label: AI 能力, prefix: AI}` 处理，老图不用改。
  - 一张图只突出一类能力。AI 和数据能力都想突出，说明重点没想清楚：拆成两张图，或者二选一。
- `kind: scope`：虚线描边、不填色，用来标"二期范围""试点单位"等。
- 叠加层只覆盖它真正作用的范围。铺多了就等于没标。
- 标签默认在右下角；附近有连线标签时，用 `title_pos: top` 放到顶部。

## 路径视图 / 主流程视图（可选）
- `paths.rows` 每行是一个流程，步骤对齐到阶段。各行跳过了哪些阶段，一眼可见（R6：只能向前推进，要回头必须用 `break: true` 换行）。
- 放在架构视图下方时会自动画分隔线；**单独使用时**只写 `paths`，不写 `nodes` / `groups`，就是一张主流程图。
- 单条主流程默认不画泳道（见本文「画布与方向」），节点按固定步长等距排。
- `edge_kind: flow` 让主流程用实线（默认是点线，表示"示意路径"）。步骤上写 `in_label` 可以给进入这一步的线加标签，例如判断的"否"。

## Spec 写法

```yaml
title: 网盘上传与存储流程
desc: 一句话说明内容（无障碍描述）
orientation: horizontal           # horizontal（默认）| vertical
swimlane: true                    # 画不画泳道；不写按「画布与方向」的默认值
brand: "#3370FF"                  # VI 主色，可省略
titlebar: outline                 # outline（默认，白底线框）| gray | brand | dark
special: {label: AI 能力, prefix: AI}   # 可选：重点能力的名称（默认"重点能力"）和标签前缀
columns:                          # 阶段：横向时从左到右，竖向时从上到下（泳道图里写角色）
  - {id: pre,  label: 上传预处理, lanes: 3}
  - {id: tran, label: 传输与接入, lanes: 3}
nodes:                            # 主干推荐放同一 row
  - {label: 计算文件哈希, kind: hub, col: pre, lane: 0.5, row: 0.8, sub: SHA-256}
  - {label: 秒传命中？, kind: decision, col: pre, lane: 2, row: 0.8, core: true}
  - {label: 分片并行上传, kind: hub, col: tran, lane: 1, row: 0.8, core: true}
  - {label: 用户中心, kind: system, owner: internal, col: pre, lane: 0.5, row: 4.4}
  - {label: CDN 分发, kind: system, owner: external, col: tran, lane: 1, row: 4.4}
groups:                           # 默认无框；frame/core 按需开启
  - {id: pre_detail, col: pre, lane: 0.5, row: 2.2, grid: 2, items: [分片切割, 空间配额校验, 获取上传凭证]}
  - {id: post_async, frame: true, col: post, lane: 0.5, row: 2.6, grid: 2, items: [预览转码, 病毒扫描]}
  - id: award                     # 流程型分组：有主线；组内有上下箭头时拉开行距
    type: process
    frame: true
    col: proc
    lane: 0
    row: 2
    row_step: 1.3
    grid: 3
    items: [{label: 定标, main: true}, 成交候选人, "", "", 确定成交人, ""]   # "" = 空格子
edges:                            # from/to：唯一 label、节点 id、或有框/底色的分组 id
  - {from: 计算文件哈希, to: 秒传命中？, kind: flow}
  - {from: 秒传命中？, to: 分片并行上传, kind: flow, label: 否}
  - {from: 用户中心, to: 获取上传凭证, kind: data, label: 签发令牌}
overlays:                         # 可选
  - {kind: scope, label: 二期范围, targets: [post_async], title_pos: top}
paths:                            # 可选；单独使用 = 主流程图
  row: 11
  label: 上传方式路径
  tag_col: client                 # 行名标签所在阶段（主流程图可省略）
  edge_kind: data                 # 主流程图用 flow
  rows:
    - name: 秒传
      height: 2
      steps:
        - {label: 计算哈希, col: pre, lane: 0.5}
        - {id: hit, label: 秒传命中？, kind: decision, col: pre, lane: 1.8}
        - {label: 分片上传, col: tran, lane: 1, in_label: 否}
        - {label: 引用计数+1, col: proc, lane: 1, drow: 1.6, break: true}
  edges:                          # 路径节点只能用 id 引用：<行名>.<id 或 label>
    - {from: 秒传.hit, to: 秒传.引用计数+1, kind: flow, route: vh, label: 是, label_at: start}
```

**泳道图写法**：`columns` 写角色（每个 `lanes: 1`），节点按时间顺序放 `row: 0.4, 2.0, 3.6 …`（步长 1.6），跨角色交接用 `route: vh` 或 `vhv`，回退用 `ll`（`offset ≥ 16`）。

**走线 `route`**（按横向描述，竖向时自动转置）：
- `auto`（默认）
- `h` / `v`：直线
- `hvh` 配 `mid_x`，`vhv` 配 `mid_row`
- `hv` / `vh`：一个拐角
- `ll` / `rr` / `tt` / `bb`：U 形绕行，配 `offset`（`ll` / `rr` 也可以配 `mid_x`，`tt` / `bb` 配 `mid_row`）

**其他参数**：
- `mid_x` 可以写 `"阶段id:泳道"`（负数或小数表示阶段间缝隙）
- `port_a` / `port_b`：端点沿边平移（px）
- `label_at`：`start | end | longest | 段号`
- `bus`、`emphasis`、`no_arrow`

**命令行**：`--orient horizontal|vertical`、`--brand "#RRGGBB"`、`--titlebar outline|gray|brand|dark` 覆盖 spec 里的同名设置。`--orient` 只对 stages 布局有效；`--brand` / `--titlebar` / `--wb` 所有布局都支持。
