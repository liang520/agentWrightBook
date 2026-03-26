---
name: novel
description: 统一小说仿写指令 — 分析/配置/写作/审校/压缩/校验/修复全流程。支持子命令：status/analyze/new/write/continue/review/compress/verify/fix/auto
user_invocable: true
---

# 统一小说仿写流程

## 全局规则

1. **所有选择以编号选项呈现**，用户只需回复数字
2. **开放式问题先 AI 生成候选项**，末尾附"N. 自定义"
3. **写作阶段默认持续自动**，不等待用户输入，检查点只汇报不暂停
4. **新实体自动处理**：遇到未映射的角色/设定，自动生成映射并在检查点汇报
5. **字数统计统一口径** — 所有涉及"字数"的统计均遵循 CLAUDE.md "字数统计规范"（去空格、去 Markdown 标记后的字符数，含标点）

## 子命令路由

从用户消息中提取子命令，按下表路由：

| 用户输入 | 跳转 |
|---------|------|
| `/novel` | 自动检测（见下方） |
| `/novel status` | Phase 0 |
| `/novel analyze` | Phase 1 |
| `/novel new` | Phase 2 |
| `/novel write` 或 `/novel continue` | Phase 3 |
| `/novel review [范围]` | Phase 4 |
| `/novel compress` | Phase 5 |
| `/novel verify` | Phase 6 |
| `/novel fix` | Phase 7 |
| `/novel auto` | 全自动流水线 1→2→3→6→6.5→7（auto 模式下 Phase 1/2 的所有选择题由 AI 自动决定，不等待用户） |

**自动检测算法**（无子命令时）：
```
1. 扫描 novels/ 下所有 meta.json
2. 扫描 sources/ 下所有 meta.json
3. 优先级判断：
   a. 存在 status="writing" 的小说 → 提示恢复写作（Phase 3）
   b. 存在 status="verifying"|"fixing" → 继续校验/修复（Phase 6/7）
   b2. 存在 status="cross-reviewing" → 继续交叉审查（Phase 6.5）
   c. 存在 status="complete" 但无 verification-report.md → 建议校验（Phase 6）
   d. 存在 status="configuring" → 继续配置（Phase 2）
   e. 存在 status="ready" 的 source 但无对应 novel → 建议配置新书（Phase 2）
   e2. 存在 status="raw" 的 source → 提示"发现未分析的原作，建议先执行分析"
   f. 存在 status="analyzing" 的 source → 继续分析（Phase 1）
   g. 以上都不满足 → 显示 Phase 0 总览

多项目冲突处理：如果同一优先级下有多个项目，按 updated_at 降序取最近更新的。
```

---

## Phase 0：状态总览

显示面板：

```
═══ 小说仿写系统 ═══

📚 原作素材（sources/）
| 名称 | 状态 | 章数 |
|------|------|------|
| ... | analyzing/ready | N |

📖 仿写小说（novels/）
| 名称 | 进度 | 状态 | Gemini 质量 |
|------|------|------|------------|
| ... | current/total (%) | writing/complete/... | avg:{score} low:{N} esc:{N} |

Gemini 质量列说明（仅 meta.json 含 chapters 数据时显示）：
  avg = 平均 review_score（跳过 null）
  low = low_quality=true 的章节数
  esc = failed_escalated=true 的章节数（有则标红 [ESCALATED]）

📦 素材库（library/）
原型 {N} | 世界观 {N} | 风格 {N} | 桥段 {N}

请选择操作：
1. 分析新原作（Phase 1）
2. 配置新书（Phase 2）
3. 继续写作（Phase 3）
4. 审校章节（Phase 4）
5. 全书校验（Phase 6）
6. 全自动流水线（Phase 1→2→3→6→6.5→7）
```

---

## Phase 1：分析原作

**前置条件**：`sources/{name}/chapters/` 下有原作章节文件

**流程**：
1. 选择待分析的 source（选择题，如只有一个则直接选中；`/novel auto` 模式下自动选择唯一 source 或最近更新的）
2. 确认题材类型（选择题：都市/玄幻修仙/甜宠言情/校园/悬疑/其他；`/novel auto` 模式下 AI 自动判断，不等待用户）
3. 逐章读取并标注功能标签
   - 功能标签：开局引入、背景交代、角色引入、冲突触发、打脸爽点、实力展示、升级突破、获得机缘、感情推进、误会制造、真相揭露、伏笔埋设、高潮对决、阶段收尾、新篇开启
   - 格式：`第NNN章：【标签】一句话概括`
   - 每 10 章汇报一次进度
4. 提取角色列表 → 对照 `library/archetypes/` 归类原型 → 用户确认（`/novel auto` 模式下 AI 自动确认）
5. 节奏分析（每章平均字数、爽点密度、高潮间隔、钩子类型）
6. 生成 `sources/{name}/analysis.md`，更新 `meta.json` status → "ready"

**转场**：
- `/novel auto` 模式：自动进入 Phase 2（不提示）
- 非 auto 模式：提示 "是否基于此原作创建新书？(1)是 (2)分析另一部 (3)返回"

---

## Phase 2：配置新书

**前置条件**：对应 source 的 status="ready"，analysis.md 存在

**进入时**：创建 novels/{name}/ 目录并写入 meta.json（`status: "configuring"`, `mode: "novel"`），使中断后可恢复到 Phase 2。`/novel auto` 模式下以下所有选择题由 AI 自动决定。

**全选择题流程**（非 auto 模式）/ **全自动流程**（auto 模式）：
1. 选择原作 source
2. 选择世界观模板（扫描 `library/worlds/`，展示选择题）
   - **热门优先排序**：热门世界观排在选项前面，标记 [HOT]
   - 热门世界观（基于百度平台 Top 50 数据）：
     - eastern-xuanhuan.md [HOT] — Top50 占比 28%，适合废柴逆袭/诸天/武道类原作
     - urban-life.md [HOT] — Top50 占比 10%，适合神医/高手下山/都市类原作
     - urban-rich.md [HOT] — Top50 占比 10%，适合追妻/先婚后爱/萌宝类原作
     - cultivation.md [HOT] — Top50 占比 8%，适合凡人流/扮猪吃虎类原作
     - historical-fiction.md [HOT] — Top50 占比 4%，适合权谋/种田/宫斗类原作
   - 非热门世界观正常展示，不标记
   - `/novel auto` 模式下：AI 优先选择与原作题材匹配的热门世界观
3. 选择语言风格（扫描 `library/styles/`，展示示例对话）
   - **基于已选世界观推荐**：根据世界观→风格映射表，推荐 1-2 个最匹配的风格，标记 [推荐]
   - 世界观→风格推荐映射：
     - eastern-xuanhuan → passionate / passionate-humorous [推荐]
     - cultivation → cold-hard / passionate [推荐]
     - urban-life → humorous / passionate-humorous [推荐]
     - urban-rich → sweet-romance / cold-hard [推荐]
     - historical-fiction → cold-hard / sweet-romance [推荐]
     - rebirth-era → sweet-romance / humorous [推荐]
     - urban-mystic → mystic-sweet [推荐]
     - urban-power → passionate / cold-hard [推荐]
     - campus → sweet-romance / humorous [推荐]
     - star-interstellar → sweet-romance [推荐]
   - `/novel auto` 模式下：AI 自动选择推荐风格中的第一个
4. 生成 5 个候选书名 → 用户选择（+ 自定义选项）
5. **角色映射** — 按重要度分批：
   - 主角：选原型 → 选名字（AI 生成 5 候选）→ 选说话方式
   - 女主：同上
   - 反派们：逐个或批量
   - 配角们：AI 自动映射 → 用户确认
   - **龙套角色登记**：配置时从 analysis.md 提取全部出场角色（含龙套）：
     - 出场超过1章的角色：必须登记到 character-map（含别名列）
     - 仅出场1次的龙套：登记到 character-map 末尾"龙套列表"区块
       （格式：| 原作名 | 原作别名 | 新名 | 出场章 |，无需性格档案）
     - 终验时映射泄漏扫描同时读取龙套列表
6. **设定映射表** — AI 根据原作分析 + 选定世界观自动生成 → 用户确认
7. **伏笔追踪表初始化** — 从 analysis.md 中提取已识别的伏笔（功能标签为"伏笔埋设"的章节），预填 foreshadowing.md 的首版数据（编号、伏笔内容、埋设章、预计回收章、状态=待埋设）。绝不创建空表。
8. 最终配置确认（展示摘要）

**创建文件**：
```
novels/{name}/
├── meta.json          (status: "writing", mode: "novel", current_chapter: 0)
├── config/
│   ├── character-map.md
│   ├── setting-map.md
│   ├── style.md       (基于所选风格 + 主角个性化调整)
│   └── foreshadowing.md (从 analysis.md 提取已识别的伏笔预填初始化，不创建空表)
├── context/
│   ├── memory-outline.md  (空模板)
│   ├── recent-context.md  (空模板)
│   └── archives/          (空目录)
└── chapters/              (空目录)
```

**转场**：完成后自动进入 Phase 3

---

## Phase 3：写作核心循环

**这是最关键的阶段。**

**前置条件**：meta.json status="writing"，所有 config/ 文件存在

### 恢复逻辑

```
current = meta.json.current_chapter
start_from = current + 1
加载：style.md → memory-outline.md → recent-context.md
     → character-map.md → setting-map.md → foreshadowing.md

# 检查 failed_escalated 章节（Gemini 验证循环新增）
IF meta.json.chapters 中存在 failed_escalated=true 的章节：
  → 打印警告：[ESCALATED] 第 {NNN} 章：3 次重写仍有原作名泄漏
  → 暂停，等待用户决定：
    A) 手动写作该章（Claude Code 直接写，标记 manual=true）
    B) 跳过该章继续
    C) 检查映射表后重试（重新进入验证循环）
```

### 每章写作流程（第 N 章）

```
┌─ 1. 加载上下文（静默）
│    读取所有 config + context 文件
│
├─ 2. 读取原作第 N 章
│    sources/{source}/chapters/{NNN}.md
│
├─ 3. 分析原作章节结构（静默）
│    提取：章节功能标签、关键情节点、新角色/新设定
│
├─ 4. 新实体检查
│    IF 原作章节出现 character-map.md 或 setting-map.md 中未映射的角色/设定：
│      → 基于原型库 + 已有映射风格自动生成新映射
│      → 追加到 character-map.md / setting-map.md
│      → 记录到检查点汇报中（不暂停）
│
├─ 5. 生成仿写章节（三层验证循环）
│    ┌─────────────────────────────────────────────────────────────────┐
│    │ Layer 1: verify-chapter.py  → 硬门禁（名字/别名泄漏扫描）        │
│    │ Layer 2: review-chapter.py  → Gemini 评分（5维度，overall≥6）    │
│    │ Layer 3: Claude Code 智能校验 → 事实/连续性/钩子/伏笔            │
│    │ 三层全部通过后才写入 novels/                                     │
│    └─────────────────────────────────────────────────────────────────┘
│
│    ① 初始化
│       write_retries = 0, verify_retries = 0, review_retries = 0, claude_retries = 0
│       如 meta.json 无 phase_a_start_ts → 写入当前时间戳
│       执行 mkdir -p {novel}/tmp/
│
│    ② 组装 prompt + review-context
│       组装 write prompt → {novel}/tmp/ch-{NNN}-prompt.txt
│         格式：=== SYSTEM === {style.md 系统提示词} === USER === {原作章节+映射表+上下文}
│       组装 review-context → {novel}/tmp/ch-{NNN}-review-context.txt
│         内容：style + character-map + memory-outline + recent-3章摘要(每章≤150字) + 待审章节占位
│
│    ③ [WRITE — Layer 0] 调用 Gemini 生成章节
│       REPO_ROOT=$(git rev-parse --show-toplevel)
│       MODEL=$(cat "$REPO_ROOT/scripts/model-config.json" | python3 -c "import sys,json;print(json.load(sys.stdin)['model'])")
│       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/write-chapter.py" \
│         --prompt-file {novel}/tmp/ch-{NNN}-prompt.txt \
│         --output-file {novel}/tmp/ch-{NNN}-draft.txt
│       - exit 3 → "API 认证失败" → 停止整个写作循环
│       - exit 2 (SAFETY) → Claude Code 接管本章，meta.json 记录 manual=true，继续下一章
│       - exit 1 → write_retries+1；若 < 3 → 回到 ③；否则 → Claude Code 接管
│       - exit 0 → 进入 ④
│
│    ④ [VERIFY — Layer 1：硬门禁] 扫描原作名泄漏
│       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/verify-chapter.py" \
│         --chapter-file {novel}/tmp/ch-{NNN}-draft.txt \
│         --character-map {novel}/config/character-map.md \
│         --setting-map {novel}/config/setting-map.md \
│         --report-file {novel}/tmp/ch-{NNN}-verify.json
│       - exit 2（词列表为空）→ 映射表解析失败，停止写作循环，提示用户检查格式
│       - exit 1（有泄漏）→ 追加 "VERIFY FEEDBACK: {泄漏词列表}" 到 prompt，
│         verify_retries+1；若 >= 3 → failed_escalated=true，停止，不写入 novels/
│         否则 → 回到 ③
│       - exit 0 → 进入 ⑤
│
│    ⑤ [REVIEW — Layer 2：Gemini 评分] 独立质量审查
│       覆盖 review-context 的 === CHAPTER TO REVIEW === 节
│       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/review-chapter.py" \
│         --review-context-file {novel}/tmp/ch-{NNN}-review-context.txt \
│         --report-file {novel}/tmp/ch-{NNN}-review.json
│       - exit 1/2 → 接受章节继续，review_score=null
│       - exit 0, passed=false → 追加 "REVIEW FEEDBACK: {issues}" 到 prompt，
│         review_retries+1；若 >= 2 → low_quality=true，进入 ⑥
│         否则 → 回到 ③
│       - exit 0, passed=true → 进入 ⑥
│
│    ⑥ [CLAUDE CODE 智能校验 — Layer 3] Claude Code 读取 draft 执行 4 项检查：
│       ⑥-A 事实矛盾：对照 memory-outline.md，检查已确立事实是否被矛盾描述
│            （已死角色复活、能力等级不符、地理位置矛盾 → 失败）
│       ⑥-B 连续性：对照 recent-context.md，检查角色状态/场景/情绪是否断裂
│            （上章结尾在A地，本章开头在B地且无转场 → 失败）
│       ⑥-C 章末钩子：最后两段是否有未解决的紧张感或期待感（无 → 失败）
│       ⑥-D 伏笔检测（不触发重写，只更新文件）：
│            → 新伏笔埋设 → 新增 foreshadowing.md 条目
│            → 旧伏笔回收 → 更新 foreshadowing.md 条目
│            → 额外扫描：未登记的悬念/承诺/预言 → 强制新增
│            → 判断标准：删除该信息不影响本章剧情，但读者会期待后续解释 → 视为伏笔
│       IF ⑥-A/B/C 任一失败：
│         构造 CLAUDE_FEEDBACK 追加到 prompt（格式：[FACT_CONFLICT]/[CONTINUITY_BREAK]/[MISSING_HOOK] + 具体描述）
│         claude_retries+1；若 >= 2 → low_quality=true，进入 ⑦
│         否则 → 回到 ③（带 CLAUDE_FEEDBACK 重写）
│       IF 全部通过 → 进入 ⑦
│
│    独立预算设计：verify_retries(max 3 硬门禁) / review_retries(max 2 软指标) / claude_retries(max 2 智能校验) 互不占用
│    retries=N 意味着已重试 N 次（初始写作不计入）
│
├─ 6. 写入与记忆更新
│    → 写入 novels/{name}/chapters/{NNN}.md
│    → 更新 meta.json：
│        current_chapter = N, updated_at = today
│        chapters[NNN].status = "complete"
│        chapters[NNN].write_retries / verify_retries / review_retries / claude_retries
│        chapters[NNN].review_score = scores.overall（或 null）
│        chapters[NNN].low_quality = (review_score < 6 OR review/claude_retries 耗尽)
│        chapters[NNN].manual = true（仅 Claude Code 接管时）
│    → 追加 recent-context.md：
│        正常章节：完整摘要（新增事实、角色状态、冲突、钩子）
│        low_quality 章节：仅精简事实摘要（"本章发生了X、Y、Z"），不加载全文
│    → 更新 foreshadowing.md（如 ⑥-D 有变更）
│    → 追加 context/timeline.md：章号 | 故事内天数 | 倒计时状态 | 时间标记原文
│      （并行模式下跳过逐章写入，每批次完成后统一回填）
│    → 保留 {novel}/tmp/ch-{NNN}-*.txt/.json（不删除，便于中断恢复）
│
├─ 8. 并行模式特殊处理（如使用 Agent 批量写作）
│    - 同批次内不得包含相邻章节（防重叠）；批次 ≤2 章时退化为串行
│    - Agent 写作时跳过 recent-context.md 更新、timeline.md 追加、meta.json 更新
│    - Agent prompt 额外包含：
│      · 前章注入：IF ch(N-1) 已存在 → 读取全文（超 3000 字取最后 1500 字）
│      · 读取原作第 N-1 章最后 3 段 + 原作第 N+1 章前 3 段（衔接参考）
│      · 防越界硬指令（逐字包含）：
│        ┌─────────────────────────────────────────────────┐
│        │ 【防重叠规则 - 强制执行】                          │
│        │ 1. 前章内容已给出。从前章结尾处自然接续，绝不重复    │
│        │    前章已描写的事件、对话或场景。                   │
│        │ 2. 你只负责原作第 N 章的内容范围，不得越界描写       │
│        │    原作第 N-1 章或第 N+1 章的事件。                │
│        │ 3. 写到本章对应原作章节的结尾即止。不写余波——        │
│        │    余波属于下一章。                               │
│        │ 4. 前章不存在时，以简短过渡开始，不展开完整场景。    │
│        └─────────────────────────────────────────────────┘
│    - 每批次完成后（注意顺序！）：
│      1. 相邻章重叠扫描（双判定）：
│         - 文本判定：比对 ch(N-1) 最后一个场景与 chN 第一个场景
│         - 检查是否描写了相同角色+动作+场景
│         - 命中 → 后章重写（串行，注入前章全文+完整防越界指令+原作N-1/N/N+1章边界参考）
│         - 重写后复检最多 1 轮，仍冲突 → 立即降级串行模式
│         - 降级状态记录到 meta.json："parallel_mode": "degraded"
│      2. 扫描 chapters/ 找到连续最大章号，更新 current_chapter
│      3. 重建 recent-context.md：读取最近 10 章已写内容，提取摘要覆盖写入
│      4. timeline.md 回填：读取本批次章节，提取时间标记，逐章追加
│      5. 滚动预算检查（如适用）
│    - 全部完成后必须执行全量记忆重建
│    - 安全降级：重叠重写后仍冲突 → 剩余章节转串行正文（审校/扫描仍可并行）
│    - 恢复时检查：IF meta.json.parallel_mode == "degraded" → 直接使用串行模式
│
├─ 9. 定期任务
│    IF N % 5 == 0：启动后台审校 Agent（Phase 4A）
│    IF N % 10 == 0：执行记忆压缩（Phase 5）→ 输出检查点汇报
│    IF N == total_chapters：跳转 Phase 6
│
└─ 继续下一章（不暂停）
```

### 检查点汇报格式（每 10 章，不暂停）

```
═══ 检查点：第 {N} 章 / 共 {total} 章（{percent}%）═══
本批新增：{word_count} 字
累计总字数：{total_words} 字
新增角色映射：{list or "无"}
新增伏笔：{list or "无"}
回收伏笔：{list or "无"}
后台审校状态：{已完成/进行中/待启动}
记忆压缩：已完成，outline {char_count} 字
═══ 继续写作... ═══
```

### 写作结束条件

- `current_chapter == total_chapters` → 自动进入 Phase 6
- 用户手动叫停 → 保存进度，meta.json 保持 status="writing"
- context 耗尽 → meta.json 已更新到最后完成的章节，下次 `/novel` 自动恢复

---

## Phase 4：审校

### 4A：后台模式（Phase 3 每 5 章自动触发）

- 启动后台 Agent（subagent_type: code-reviewer）
- 检查范围：最近 5 章
- 检查项：
  1. **映射泄漏扫描**：从 setting-map.md 和 character-map.md 提取所有左列原作词，grep 全部目标章节
  2. **术语一致性**：等级体系用词是否统一、有无其他体系术语混入
  3. **逻辑漏洞**：角色状态矛盾、时间线错误
  4. **角色一致性**：人设偏移、称呼错误
  5. **风格漂移**：与 style.md 对照

- 结果在下一个检查点汇报中呈现

### 4B：前台模式（`/novel review [范围]`）

- 用户选择章节范围（选择题：最新5章 / 最近10章 / 全部 / 自定义范围）
- 同上 5 项检查，交互式展示结果
- 提供修复选项：(1)自动修复全部 (2)逐个确认 (3)仅记录

---

## Phase 5：记忆压缩

详细流程见 [../shared/memory-compress.md](../shared/memory-compress.md)

---

## Phase 6：全书校验（20 维度）

对全书执行 20 维度质量检查，覆盖映射泄漏、结构完整性、伏笔闭合、风格一致性、情绪曲线、因果链等。

**硬性要求：终验必须执行全部维度，不允许跳过任何维度。如果context不够，分批执行（先维度1-10，再维度11-20），但绝不允许跳过。"精简版终验"是被禁止的。**

详细维度见 [references/novel-verification.md](references/novel-verification.md)

---

## Phase 6.5：独立交叉审查

详细流程见 [../short/references/cross-review.md](../short/references/cross-review.md)（与 /short 共用同一流程）

更新 meta.json status → "cross-reviewing"

**门禁**：2个独立 Agent 均判定"可发布" →
  汇总 verification-report.md（Phase 6）+ 交叉审查新发现的问题清单
  IF 仍有未修复 Critical，或 Warning 合计 > 5 → Phase 7（修复）
  IF 全部 PASS 或仅 Suggestion → 执行素材自动回流（必执行：读取 ../shared/material-reflow.md 并按流程执行）→ status → "complete"
存在未解决 Critical → 修复后复审（最多2轮）
2轮后仍有 Critical → 输出残留清单，标注"人工决定"

---

## Phase 7：修复

更新 meta.json status → "fixing"

**流程**：
```
  0. 修复任何数字/名词/设定值时，必须执行"全书关联扫描"：
     → Grep 全书所有包含该值的引用
     → 列出全部引用位置，逐一同步修改
     → 修改后再次 Grep 确认零残留

LOOP:
  1. 读取 verification-report.md 的问题清单
  2. 按严重度分组：Critical / Warning / Suggestion

  3. Critical（名词泄漏、设定泄漏）：
     → 在 character-map.md 或 setting-map.md 中找到对应映射
     → 自动执行 find-and-replace（Edit 工具 replace_all）
     → 上下文相关的（不能简单替换）：改写整句

  4. Warning（术语不一致、称呼错误等）：
     → 自动修复并记录

  5. Suggestion：
     → 仅记录，不修改

  6. 修复完成后，重新 grep 扫描受影响的章节
  7. IF 发现新问题 且 修复轮次 < 3 → 继续循环
  8. IF 修复轮次 == 3 且仍有问题 → 输出最终报告，标注"部分问题未解决" → 完成
  9. IF 零残留 → 更新 verification-report.md（追加修复记录）
  10. 状态转换门禁：
      IF verification-report.md 不存在 → 终止，提示"请先运行 /novel verify"
      IF 仍有未修复的 Critical 或 Warning → 终止，提示"仍有问题未修复"，status 保持 "fixing"
      ELSE → 继续
  11. 素材自动回流（必执行，不可跳过）：
      读取 ../shared/material-reflow.md 并按流程执行
      本 Skill 扫描范围：styles/ + archetypes/ + worlds/ + tropes/
      汇报回流结果（新增了哪些素材）
  12. 更新 meta.json status → "complete"
```

---

## 中断恢复机制

```
任何时候中断（会话断开、context 耗尽、用户叫停）：
  → meta.json 的 current_chapter 指向最后完成的章节
  → memory-outline.md + recent-context.md 保持最新状态
  → 下次 /novel 自动检测到 status="writing"/"verifying"/"cross-reviewing"/"fixing"
  → 加载对应状态 → 从断点继续
```

## meta.json 字段定义

```json
{
  "title": "书名",
  "source": "sources/source-name",
  "genre": "题材",
  "style": "library/styles/xxx.md",
  "world": "library/worlds/xxx.md",
  "mode": "novel",
  "status": "analyzing|configuring|writing|verifying|cross-reviewing|fixing|complete",
  "current_chapter": 0,
  "total_chapters": 45,
  "last_review_chapter": 0,
  "last_compress_chapter": 0,
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

## 绝对禁止事项

1. **绝不在成稿中出现原作角色名或设定名** — 这是最高优先级红线
2. **绝不跳过自查步骤** — 每章写完必须执行六项自查（含伏笔变更检测）
3. **绝不在记忆未加载时写作** — 必须先加载 memory-outline + recent-context
4. **绝不遗忘更新 meta.json** — 每章写完立即更新 current_chapter
5. **绝不在映射表不完整时继续** — 新实体必须先生成映射再写入章节
