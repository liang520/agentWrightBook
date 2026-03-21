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
| `/novel auto` | 全自动流水线 1→2→3→6→7（auto 模式下 Phase 1/2 的所有选择题由 AI 自动决定，不等待用户） |

**自动检测算法**（无子命令时）：
```
1. 扫描 novels/ 下所有 meta.json
2. 扫描 sources/ 下所有 meta.json
3. 优先级判断：
   a. 存在 status="writing" 的小说 → 提示恢复写作（Phase 3）
   b. 存在 status="verifying"|"fixing" → 继续校验/修复（Phase 6/7）
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
| 名称 | 进度 | 状态 |
|------|------|------|
| ... | current/total (%) | writing/complete/... |

📦 素材库（library/）
原型 {N} | 世界观 {N} | 风格 {N} | 桥段 {N}

请选择操作：
1. 分析新原作（Phase 1）
2. 配置新书（Phase 2）
3. 继续写作（Phase 3）
4. 审校章节（Phase 4）
5. 全书校验（Phase 6）
6. 全自动流水线（Phase 1→2→3→6→7）
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
3. 选择语言风格（扫描 `library/styles/`，展示示例对话）
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
├─ 5. 生成仿写章节
│    严格遵循：
│    - style.md 中的系统提示词（作者人格）
│    - character-map.md 的角色映射（包括性格、说话方式）
│    - setting-map.md 的设定映射（所有专有名词必须替换）
│    - memory-outline.md 的世界规则
│    - recent-context.md 的近期事实
│    质量要求：章末必有钩子、不违反已建立的世界规则
│
├─ 6. 六项自查（写完后立即执行）
│    ① 扫描本章：是否存在 character-map.md 左列（原作列）的任何角色名
│    ② 扫描本章：是否存在 setting-map.md 左列（原作列）的任何设定名
│    ③ 与 memory-outline.md 的事实是否矛盾
│    ④ 与 recent-context.md 的连续性是否断裂
│    ⑤ 章末是否有钩子
│    ⑥ 伏笔变更检测：本章是否有伏笔埋设或回收？
│       → 如有埋设：必须在 foreshadowing.md 新增条目（编号、内容、埋设章、预计回收章、状态=已埋设）
│       → 如有回收：必须更新 foreshadowing.md 对应条目（实际回收章、状态=已回收）
│       → 此项为强制执行，不可跳过
│       → 额外扫描：检查本章是否存在【】系统提示中的新悬念、对话中的承诺/预言、或未解释的异常现象
│       → 如发现疑似新伏笔但未在 foreshadowing.md 中登记 → 强制新增条目（编号、内容、埋设章、预计回收章、状态=已埋设）
│       → 判断标准：如果删除该信息不影响本章剧情，但读者会期待后续解释 → 视为伏笔
│    IF 发现泄漏 → 立即修正后再保存
│
├─ 7. 保存与更新
│    → 写入 novels/{name}/chapters/{NNN}.md
│    → 追加 recent-context.md（本章摘要：新增事实、角色状态、冲突、钩子）
│    → 更新 foreshadowing.md（如有新伏笔/回收伏笔）
│    → 更新 meta.json（current_chapter = N, updated_at = today）
│    → 追加 context/timeline.md：章号 | 故事内天数 | 倒计时状态 | 时间标记原文
│      （并行模式下跳过逐章写入，每批次完成后统一回填）
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

## Phase 7：修复

更新 meta.json status → "fixing"

**流程**：
```
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
  10. 素材自动回流（必执行，不可跳过）：
      读取 ../shared/material-reflow.md 并按流程执行
      本 Skill 扫描范围：styles/ + archetypes/ + worlds/ + tropes/
      汇报回流结果（新增了哪些素材）
  11. 更新 meta.json status → "complete"
```

---

## 中断恢复机制

```
任何时候中断（会话断开、context 耗尽、用户叫停）：
  → meta.json 的 current_chapter 指向最后完成的章节
  → memory-outline.md + recent-context.md 保持最新状态
  → 下次 /novel 自动检测到 status="writing"/"verifying"/"fixing"
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
  "status": "analyzing|configuring|writing|verifying|fixing|complete",
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
