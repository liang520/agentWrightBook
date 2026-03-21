---
name: short
description: 短篇改编指令 — 将任意长度原作压缩改编为4.5万-5万字短篇。全自动无人参与流水线：分析→骨架提取→压缩规划→配置→写作→审校→校验→修复。支持子命令：status/analyze/plan/new/write/continue/review/compress/verify/fix/auto
user_invocable: true
---

# 短篇改编流程

## 全局规则

1. **全程自动，无人参与** — 所有阶段自动流转，不等待用户输入
2. **目标字数硬下限 45000 字** — 生成的压缩映射表总字数必须 ≥ 45000
3. **字数统计统一口径** — 所有涉及"字数"的统计（目标字数、单章字数、总字数等）均遵循 CLAUDE.md "字数统计规范"（去空格、去 Markdown 标记后的字符数，含标点）
4. **保持原书逻辑和关系** — 压缩的是描写、过渡、灌水，不是情节因果链
5. **新实体自动处理** — 遇到未映射的角色/设定，自动生成映射并在检查点汇报
6. **写作阶段默认持续自动** — 检查点只汇报不暂停

## 子命令路由

从用户消息中提取子命令，按下表路由：

| 用户输入 | 跳转 |
|---------|------|
| `/short` | 自动检测（见下方） |
| `/short status` | Phase 0 |
| `/short analyze` | Phase 1 |
| `/short plan` | Phase 2 |
| `/short new` | Phase 3 |
| `/short write` 或 `/short continue` | Phase 4 |
| `/short review [范围]` | Phase 5 |
| `/short compress` | Phase 6 |
| `/short verify` | Phase 7 |
| `/short fix` | Phase 8 |
| `/short auto` | 全自动流水线 1→2→3→4（含5/6自动触发）→7→8 |

**自动检测算法**（无子命令时）：
```
1. 扫描 novels/ 下所有 meta.json（mode="short"）
2. 扫描 sources/ 下所有 meta.json
3. 优先级判断：
   a. 存在 status="writing" 且 mode="short" → 恢复写作（Phase 4）
   a2. 存在 status="written" 且 mode="short" → 自动进入 Phase 7（终验）
   b. 存在 status="verifying"|"fixing" 且 mode="short" → 继续校验/修复
   c. 存在 status="planning" 且 mode="short" → 继续压缩规划（Phase 2）
   d. 存在 status="configuring" 且 mode="short" → 继续配置（Phase 3）
   e. 存在 status="analyzed"|"ready" 的 source 但无对应 short novel：
      IF analysis.md 同时包含"可压缩度"和"依赖关系"字段 → 直接进入 Phase 2
      ELSE → 进入 Phase 1（重新分析以补充压缩标注字段）
   e2. 存在 status="raw" 的 source → 提示"发现未分析的原作，建议先执行分析"
   f. 存在 status="analyzing" 的 source → 继续分析（Phase 1）
   g. 以上都不满足 → 显示 Phase 0 总览

多项目冲突处理：如果同一优先级下有多个项目，按 updated_at 降序取最近更新的。
```

---

## Phase 0：状态总览

显示面板：

```
═══ 短篇改编系统 ═══

📚 原作素材（sources/）
| 名称 | 状态 | 章数 | 字数 |
|------|------|------|------|
| ... | analyzing/analyzed | N | XXXXX |

📖 短篇改编（novels/，mode=short）
| 名称 | 进度 | 状态 | 目标字数 | 压缩比 |
|------|------|------|---------|--------|
| ... | current/total (%) | writing/... | 50000 | 2.0x |

📦 素材库（library/）
原型 {N} | 世界观 {N} | 风格 {N} | 桥段 {N}

请选择操作：
1. 分析新原作（Phase 1）
2. 压缩规划（Phase 2）
3. 全自动流水线（Phase 1→2→3→4→7→8）
```

---

## Phase 1：逐章分析（含压缩标注）

**前置条件**：`sources/{name}/chapters/` 下有原作章节文件

**流程**：
1. 选择待分析的 source（如只有一个则直接选中）
2. 确认题材类型（自动判断，不等待用户）
3. **逐章读取并标注**

   每章标注格式：
   ```
   第NNN章：【功能标签】一句话概括
   - 章节功能: [主线推进|支线展开|人物塑造|世界观铺垫|过渡/灌水]
   - 核心事件: 一句话
   - 可压缩度: [不可压缩|可合并|可删减]
   - 依赖关系: [无|被第X/Y/Z章依赖（原因）]
   - 关键角色: [角色列表]
   - 伏笔: [埋设/回收/无]
   ```

   功能标签集：开局引入、背景交代、角色引入、冲突触发、打脸爽点、实力展示、升级突破、获得机缘、感情推进、误会制造、真相揭露、伏笔埋设、高潮对决、阶段收尾、新篇开启

   每 10 章汇报一次进度

4. 提取角色列表 → 对照 `library/archetypes/` 归类原型
5. 节奏分析（每章平均字数、爽点密度、高潮间隔、钩子类型）
6. **统计原作总字数**：遍历 `sources/{name}/chapters/` 全部章节，按 CLAUDE.md "字数统计规范"统计总字数，写入 source `meta.json` 的 `word_count` 字段
7. 生成 `sources/{name}/analysis.md`，更新 `meta.json` status → "analyzed"

**特别说明**：如果该 source 已有 analysis.md（由 `/novel` 生成，status="ready"），需要重新分析以补充压缩标注字段（可压缩度、依赖关系等）。分析完成后 status 更新为 "analyzed"。

**转场**：完成后自动进入 Phase 2

---

## Phase 2：骨架提取 + 压缩规划（核心阶段）

**进入时**：如果 novels/{name}/ 目录已存在（中断恢复场景），跳过目录创建；否则创建 novels/{name}/ 并写入 meta.json（`status: "planning"`, `mode: "short"`）使恢复分支可达。

**前置条件**：source 的 analysis.md 存在且包含压缩标注，source meta.json 包含 `word_count` 字段

**前置检查**：
```
IF source meta.json.word_count <= 45000:
  → 终止，提示"原作字数 ≤ 45000，无需压缩，建议使用 /novel 进行等长仿写"
IF source meta.json.word_count <= 50000:
  → 警告"原作字数接近目标下限，压缩空间有限"，但继续执行
```

详细流程见 [references/planning.md](references/planning.md)

---

## Phase 3：配置新书

**前置条件**：compression-map.md 和 plot-skeleton.md 已生成且校验通过

**全自动流程**（不等待用户输入）：

1. 读取 source 的 analysis.md 和 plot-skeleton.md
2. 自动选择世界观模板（基于原作题材匹配 `library/worlds/` 中最合适的）
3. 自动选择语言风格（基于原作风格匹配 `library/styles/` 中最合适的）
4. 自动生成书名（生成5个候选，选第1个）
5. **角色映射** — 基于 plot-skeleton.md 的角色保留清单：
   - 保留角色：自动生成新名字、性格、说话方式
   - 合并角色：生成合并后的新角色
   - 删除角色：不生成映射
   - **龙套角色登记**：配置时从 analysis.md 提取全部出场角色（含龙套）：
     - 出场超过1章的角色：必须登记到 character-map（含别名列）
     - 仅出场1次的龙套：登记到 character-map 末尾"龙套列表"区块
       （格式：| 原作名 | 原作别名 | 新名 | 出场章 |，无需性格档案）
     - 终验时映射泄漏扫描同时读取龙套列表
6. **设定映射表** — 基于原作分析 + 选定世界观自动生成
7. **伏笔追踪表** — 基于 plot-skeleton.md 的伏笔链，用**新作章号**填入
8. **配置一致性校验**（必执行，门禁——不通过不允许进入 Phase 4）：
   - 从 setting-map.md 和 character-map.md 提取所有原作名词（左列）作为扫描词表
   - 扫描 plot-skeleton.md 全文 + compression-map.md 中所有非"对应原作章"列的文本
   - 不扫描：character-map/setting-map 的左列（映射查找用），不修改事件 ID 编号
   - 发现原作名词 → 以映射表右列为准替换，替换后重新扫描确认零残留
   - 输出："配置一致性校验通过，共扫描 N 个原作词，修正 H 处"
   - IF 仍有残留 → 阻断，输出残留清单（文件+行号），status 保持 "configuring"

**创建文件**：
```
novels/{name}/
├── meta.json          (status: "writing", mode: "short", current_chapter: 0, total_chapters: 从 compression-map.md 映射表行数读取)
├── config/
│   ├── plot-skeleton.md      (Phase 2 已创建)
│   ├── compression-map.md    (Phase 2 已创建)
│   ├── character-map.md
│   ├── setting-map.md
│   ├── style.md
│   └── foreshadowing.md
├── context/
│   ├── memory-outline.md  (空模板)
│   ├── recent-context.md  (空模板)
│   └── archives/
└── chapters/
```

**转场**：完成后自动进入 Phase 4

---

## Phase 4：写作核心循环

**这是最关键的阶段。**

**前置条件**：meta.json status="writing"，mode="short"，所有 config/ 文件存在

详细流程见 [references/writing-loop.md](references/writing-loop.md)

---

## Phase 5：审校

### 5A：后台模式（Phase 4 每 5 章自动触发）

- 启动后台 Agent（subagent_type: code-reviewer）
- 检查范围：最近 5 章
- 检查项：
  1. **映射泄漏扫描**：按 [../shared/leak-scan.md](../shared/leak-scan.md) 完整流程执行（含全名、别名、子串、姓氏通称组合），扫描范围为最近 5 章
  2. **术语一致性**：等级体系用词是否统一
  3. **逻辑漏洞**：角色状态矛盾、时间线错误
  4. **角色一致性**：人设偏移、称呼错误
  5. **风格漂移**：与 style.md 对照
  6. **压缩质量检查**（短篇专属）：
     - 信息完整性：压缩过程中是否丢失关键信息导致读者困惑
     - 节奏平衡：是否某段突然太赶或太慢
     - 因果链完整：是否因合并章节导致逻辑跳跃
- 结果保存至 `novels/{name}/context/review-notes.md`（追加模式，标注审校范围和时间）
- 在下一个检查点汇报中呈现
- Phase 7 维度 9 从此文件读取审校历史

### 5B：前台模式（`/short review [范围]`）

- 同上检查项，展示结果
- 自动修复全部可修复问题

---

## Phase 6：记忆压缩

触发时机：Phase 4 每 10 章 / 全书完成时 / 手动。详细流程见 [../shared/memory-compress.md](../shared/memory-compress.md)

---

## Phase 7：全书校验（23 维度）

**前置条件**：meta.json current_chapter == total_chapters 且总字数 ≥ 45000

**触发前**：如果 recent-context.md 有未归档章节，先执行 Phase 6

更新 meta.json status → "verifying"

**硬性要求：终验必须执行全部维度，不允许跳过任何维度。如果context不够，分批执行（先维度1-12，再维度13-23），但绝不允许跳过。"精简版终验"是被禁止的。**

23维度详细检查见 [references/verification.md](references/verification.md)

**输出**：写入 `novels/{name}/verification-report.md`

**转场**：
- 发现 Critical/Warning → 自动进入 Phase 8
- 全部通过 → 执行素材自动回流（必执行：读取 [../shared/material-reflow.md](../shared/material-reflow.md) 并按流程执行，扫描全部 4 类素材，汇报结果）→ status → "complete"

---

## Phase 8：修复

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

  5. 字数问题：
     a. 总字数 < 45000（不足）：
        → 找到字数最少的几章
        → 扩写补充内容直到总字数达标
     b. 总字数 > 50000（超标）：
        → 计算需削减字数 = 总字数 - 50000
        → 按各章超标比例从高到低排序
        → 优先处理超标 >20% 的章节
        → 精简策略：删除冗余环境描写、压缩非关键对话、合并重复叙述
        → 绝不删除：推动情节的事件、因果链节点、伏笔埋设/回收、角色关系变化、章尾钩子
        → 每章精简后：重新通读检查逻辑衔接是否完整，确认与前后章无矛盾
        → 每修一章重新统计总字数
        → 直到总字数 ≤ 50000

  6. Suggestion：
     → 仅记录，不修改

  7. 修复完成后，重新 grep 扫描受影响的章节
  8. IF 发现新问题 且 修复轮次 < 3 → 继续循环
  9. IF 修复轮次 == 3 且仍有问题 → 输出最终报告，标注"部分问题未解决" → 完成
  10. IF 零残留 → 更新 verification-report.md（追加修复记录）
  11. 素材自动回流（必执行，不可跳过）：
      读取 ../shared/material-reflow.md 并按流程执行
      本 Skill 扫描范围：styles/ + archetypes/ + worlds/ + tropes/
      汇报回流结果（新增了哪些素材）
  12. 状态转换门禁：
      IF verification-report.md 不存在 → 终止，提示"请先运行 /short verify"
      IF 仍有未修复的 Critical 或 Warning → 终止，提示"仍有问题未修复"
      ELSE → 更新 meta.json status → "complete"
```

---

## 中断恢复机制

```
任何时候中断（会话断开、context 耗尽、用户叫停）：
  → meta.json 的 current_chapter 指向最后完成的章节
  → memory-outline.md + recent-context.md 保持最新状态
  → 下次 /short 自动检测到 status + mode="short"
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
  "mode": "short",
  "status": "analyzing|planning|configuring|writing|written|verifying|fixing|complete",
  "target_words": 50000,
  "budget_words": 45000,
  "source_words": 102425,
  "compression_ratio": 2.05,
  "current_chapter": 0,
  "total_chapters": 35,
  "last_review_chapter": 0,
  "last_compress_chapter": 0,
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

## 绝对禁止事项

1. **绝不在成稿中出现原作角色名或设定名** — 最高优先级红线
2. **绝不跳过自查步骤** — 每章写完必须执行七项自查（含伏笔变更检测+字数检查）
3. **绝不在记忆未加载时写作** — 必须先加载 memory-outline + recent-context
4. **绝不遗忘更新 meta.json** — 每章写完立即更新 current_chapter
5. **绝不在映射表不完整时继续** — 新实体必须先生成映射再写入章节
6. **绝不让总字数超过 50000** — 这是硬上限，超标必须在修复阶段精简（不破坏情节因果链）
7. **绝不让总字数低于 45000** — 如果低于，在修复阶段扩写补足
8. **绝不破坏情节因果链** — 压缩是删减描写，不是删减逻辑
