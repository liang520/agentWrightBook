---
name: short
description: 短篇改编指令 — 将任意长度原作压缩改编为4.5万-5万字短篇。全自动无人参与流水线：分析→骨架提取→压缩规划→配置→写作→审校→校验→修复。支持子命令：status/analyze/plan/new/write/continue/review/compress/verify/fix/auto
---

# 短篇改编流程

## 全局规则

1. **全程自动，无人参与** — 所有阶段自动流转，不等待用户输入
2. **目标字数硬下限 45000 字** — 生成的压缩映射表总字数必须 ≥ 45000
3. **字数统计统一口径** — 所有涉及"字数"的统计均遵循 CLAUDE.md "字数统计规范"
4. **保持原书逻辑和关系** — 压缩的是描写、过渡、灌水，不是情节因果链
5. **新实体自动处理** — 遇到未映射的角色/设定，自动生成映射并在检查点汇报
6. **写作阶段默认持续自动** — 检查点只汇报不暂停
7. **事实锁定优先** — 所有具体数字、物理细节、角色身份阶段以 `config/details-lock.md` 为唯一真相源。Agent 不得编造锁定表中未列的具体数字/物理细节，需要新数字时使用模糊措辞。
8. **角色定义** — 本 Skill 中"协调进程"= 执行 /short auto 的主 Agent。"写作 Agent"和"提取 Agent"都是由主 Agent 通过 subagent 调用的子任务，不是独立服务。

## 优先级冲突规则

当信息源冲突时，按此优先级裁决：
```
details-lock.md（事实锁定表）
  > 已修复章节正文（经审校确认的正文）
    > event-ledger.md（由正文投影生成，是正文的派生物）
      > 未修复章节正文
        > 原作内容
          > Agent 自行编造（最低优先级）
```

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
| `/short auto` | 全自动流水线 1→2→3→4（含5/6自动触发）→7→7.5→8 |

**自动检测算法**（无子命令时）：
```
1. 扫描 novels/ 下所有 meta.json（mode="short"）
2. 扫描 sources/ 下所有 meta.json
3. 优先级判断：
   a. 存在 status="writing" 且 mode="short" → 恢复写作（Phase 4）
   a2. 存在 status="written" 且 mode="short" → 自动进入 Phase 7（终验）
   b. 存在 status="verifying"|"fixing" 且 mode="short" → 继续校验/修复
   b2. 存在 status="cross-reviewing" 且 mode="short" → 继续交叉审查（Phase 7.5）
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
| 名称 | 进度 | 状态 | 目标字数 | 压缩比 | Gemini 质量 |
|------|------|------|---------|--------|------------|
| ... | current/total (%) | writing/... | 50000 | 2.0x | avg:{score} low:{N} esc:{N} |

Gemini 质量列说明（仅 meta.json 含 chapters 数据时显示）：
  avg = 平均 review_score（null 按 0 计入）
  low = low_quality=true 的章节数
  esc = failed_escalated=true 的章节数（有则标红 [ESCALATED]）

📦 素材库（library/）
原型 {N} | 世界观 {N} | 风格 {N} | 桥段 {N}

请选择操作：
1. 分析新原作（Phase 1）
2. 压缩规划（Phase 2）
3. 全自动流水线（Phase 1→2→3→4→7→7.5→8）
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

## 差异化字数预算规则（Phase 2 compression-map 生成时应用）

compression-map 中每章的目标字数应按叙事功能差异化分配，不应统一。Phase 2 生成 compression-map 时，为每章标注叙事功能标签并据此分配字数：

| 叙事功能 | 目标字数范围 | 适用场景 |
|---------|------------|---------|
| 开篇引入 | 2000-2500 | 第1章，需建立世界观+人物+钩子 |
| 核心转折/高潮 | 1800-2200 | plot-skeleton 标记的高潮/转折章 |
| 终章 | 1500-2000 | 最后1-2章 |
| 角色弧重点章 | 1500-1800 | 配角独立弧核心章 |
| 常规推进 | 1300-1600 | 标准主线章 |
| 过渡/信息章 | 1200-1400 | 铺垫/转场章 |

**总和约束**：分配完成后必须验证 SUM(各章目标字数) ∈ [45000, 50000]。
IF 总和 < 45000 → 上调"常规推进"章节字数；IF 总和 > 50000 → 下调"过渡/信息章"字数。

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
   - **热门优先匹配**：如原作题材可映射到多个世界观，优先选择热门世界观
   - 热门世界观优先级（基于百度平台 Top 50 数据）：
     - eastern-xuanhuan.md — 玄幻/异界/大陆流原作优先匹配
     - urban-life.md — 都市/神医/退伍原作优先匹配
     - urban-rich.md — 言情/豪门/婚姻原作优先匹配
     - cultivation.md — 仙侠/修仙原作优先匹配
     - historical-fiction.md — 历史/朝堂/宫斗原作优先匹配
     - rebirth-era.md — 年代文/种田原作优先匹配
3. 自动选择语言风格（基于原作风格匹配 `library/styles/` 中最合适的）
   - **基于已选世界观推荐**：根据世界观→风格映射表，自动选择第一推荐风格
   - 世界观→风格推荐映射：
     - eastern-xuanhuan → passionate / passionate-humorous
     - cultivation → cold-hard / passionate
     - urban-life → humorous / passionate-humorous
     - urban-rich → sweet-romance / cold-hard
     - historical-fiction → cold-hard / sweet-romance
     - rebirth-era → sweet-romance / humorous
     - urban-mystic → mystic-sweet
     - urban-power → passionate / cold-hard
     - campus → sweet-romance / humorous
     - star-interstellar → sweet-romance
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
   - ⚠️ **必须使用2列格式**（| 原作 | 新设定 |），不允许第3列。3列格式会导致 map_parser 取"说明"列而非"新设定"列作为替换值。
   - ⚠️ **禁止同名映射**（原名=新名），会导致 verify-chapter.py 永远误报泄漏。
7. **伏笔追踪表** — 基于 plot-skeleton.md 的伏笔链，用**新作章号**填入
8. **输出改造方向建议**：配置完成后，输出一行改造方向提示
   - 格式："改造方向：{世界观名} · {流派标签} [{HOT/非热门}]"
   - 示例："改造方向：东方玄幻 · 废柴逆袭 [HOT Top50 占比28%]"
   - 示例："改造方向：都市玄学 · 驱邪甜宠 [非热门]"
9. **创建事实锁定表** `config/details-lock.md`：
   - 从 character-map、setting-map、plot-skeleton、compression-map 提取所有具体数字/物理细节
   - 填充6个区块：人物物理细节、场景/地点参数、数字/比例、身世统一版本、角色身份阶段表、关键道具归属表
   - 每个锁定值附"搜索关键词列表"（供方案D Grep扫描用）
   - 模板见 [references/details-lock-template.md](references/details-lock-template.md)
10. **扩展伏笔追踪表** `config/foreshadowing.md`：
    - 新增"角色设定承诺"区块（从 character-map 提取设定承诺，如"季阳暗投季野"，标注预计落实章）
    - 新增"道具归属承诺"区块（从 details-lock 道具归属表提取，标注需交代内容的道具）
11. **配置一致性校验**（必执行，门禁——不通过不允许进入 Phase 4）：
    - 扫描范围扩展到 details-lock.md（检查锁定值与其他配置文件无矛盾）
   - 从 setting-map.md 和 character-map.md 提取所有原作名词（左列）作为扫描词表
   - 扫描 plot-skeleton.md 全文 + compression-map.md 中所有非"对应原作章"列的文本
   - 不扫描：character-map/setting-map 的左列（映射查找用），不修改事件 ID 编号
   - 发现原作名词 → 以映射表右列为准替换，替换后重新扫描确认零残留
   - 输出："配置一致性校验通过，共扫描 N 个原作词，修正 H 处"
   - IF 仍有残留 → 阻断，输出残留清单（文件+行号），status 保持 "configuring"
   - **配置文件交叉一致性校验**（步骤11追加，同为门禁）：
     - details-lock ↔ character-map：核对年龄、外貌、超能力等锁定值是否与性格档案一致
     - details-lock ↔ plot-skeleton：核对身份阶段表的起止章号是否与骨架中的弧线章号匹配
     - foreshadowing ↔ plot-skeleton：核对伏笔的埋设/回收章号是否落在骨架对应弧线内
     - 发现矛盾 → 以 plot-skeleton 为准修正其他文件，修正后重新扫描确认零矛盾

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
│   ├── foreshadowing.md      (含承诺追踪扩展)
│   └── details-lock.md       (事实锁定表，Phase 3 新增)
├── context/
│   ├── memory-outline.md  (空模板)
│   ├── recent-context.md  (空模板)
│   ├── event-ledger.md    (事件账本，Phase 4 逐章追加)
│   ├── timeline.md       (时间线追踪，Phase 4 逐章追加)
│   ├── wave-plan.md       (波次分配表，Phase 4 新增)
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

### 5A：后台模式（每波次完成后无条件触发）

- 触发规则：每波次写作完成后无条件触发（不再依赖"每5章"计数器）
- 启动后台 Agent（subagent_type: code-reviewer）
- 检查范围：本波次全部章节 + 前后各1章（如存在）
- 检查项：
  1. **映射泄漏扫描**：按 [../shared/leak-scan.md](../shared/leak-scan.md) 完整流程执行（含全名、别名、子串、姓氏通称组合），扫描范围为本波次全部章节 + 前后各1章
  2. **术语一致性**：等级体系用词是否统一
  3. **逻辑漏洞**：角色状态矛盾、时间线错误
  4. **角色一致性**：人设偏移、称呼错误
  5. **风格漂移**：与 style.md 对照
  6. **压缩质量检查**（短篇专属）：
     - 信息完整性：压缩过程中是否丢失关键信息导致读者困惑
     - 节奏平衡：是否某段突然太赶或太慢
     - 因果链完整：是否因合并章节导致逻辑跳跃
  7. **details-lock 一致性**：从 details-lock.md 提取搜索关键词列表，Grep 扫描章节，检查锁定值是否被违反
  8. **event-ledger 状态连续性**：检查相邻章的6个状态维度是否连续
  9. **场景转换自然度**：上章结尾→本章开头是否有过渡
  10. **角色身份阶段合规性**：检查 details-lock 身份阶段表，确认角色称呼在正确阶段范围内
  11. **读者视角体验检查**（审校 Agent 切换为读者视角，不参考配置文件，只读正文）：
     - 首次阅读是否能理解剧情？标记信息铺垫不足导致困惑的段落
     - 是否有想跳过的段落？标记节奏拖沓或信息堆砌的位置
     - 对话是否自然？标记机械感、书面感过强的对话
     - 章尾是否有继续阅读的欲望？标记钩子失效的章节
     - 是否有明显的 AI 写作痕迹？（重复句式结构、模板化描写、"值得注意的是"类套话）
     - 读者视角发现的问题默认分级为 Suggestion，仅"完全看不懂"升为 Warning
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

## Phase 7：全书校验（24 维度）

**前置条件**：meta.json current_chapter == total_chapters 且总字数 ≥ 45000

**触发前**：如果 recent-context.md 有未归档章节，先执行 Phase 6

更新 meta.json status → "verifying"

**硬性要求：终验必须执行全部维度，不允许跳过任何维度。如果context不够，分批执行（先维度1-12，再维度13-24），但绝不允许跳过。"精简版终验"是被禁止的。**

24维度详细检查见 [references/verification.md](references/verification.md)

**输出**：写入 `novels/{name}/verification-report.md`

**转场**：Phase 7 完成后 → 自动进入 Phase 7.5（无论有无问题）

---

## Phase 7.5：独立交叉审查

详细流程见 [references/cross-review.md](references/cross-review.md)

更新 meta.json status → "cross-reviewing"

**门禁**：2个独立 Agent 均判定"可发布" →
  汇总 verification-report.md（Phase 7）+ 交叉审查新发现的问题清单
  IF 仍有未修复 Critical，或 Warning 合计 > 5 → Phase 8（修复）
  IF 全部 PASS 或仅 Suggestion → 执行素材自动回流（必执行：读取 [../shared/material-reflow.md](../shared/material-reflow.md) 并按流程执行）→ status → "complete"
存在未解决 Critical → 修复后复审（最多2轮）
2轮后仍有 Critical → 输出残留清单，标注"人工决定"

---

## Phase 8：修复

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

  7. 修复章节正文后，如涉及 details-lock 中的锁定值变更，需同步更新 details-lock 变更日志；如涉及事件/状态变更，需重新提取该章 delta 并更新 event-ledger。
  8. 修复完成后，执行定向复验（修复后验证闭环）：
     a. 收集本轮修改过的所有文件列表
     b. 确定扩展扫描范围：
        - 修改过的章节文件 ± 2 章（衔接检查）
        - 修改中涉及的 details-lock 关键词 → Grep 全书命中的所有章节
        - 修改过的配置文件 → 如改了 character-map/details-lock，全书扫描（不能定向）
     c. 在扩展范围内执行定向复验：
        - 交叉校验 details-lock/character-map/setting-map（数值/名词/年龄是否一致）
        - 修改处前后文通顺性（改写超过 3 句的章节重点检查）
        - 修改是否破坏了已通过的终验维度（维度1泄漏、维度5角色名、维度13数值链）
     d. 震荡检测：IF 同一文件在连续两轮中被反复修改 → 提前退出，标注"疑似修复震荡，建议人工审查"
     e. IF 定向复验 PASS → 进入步骤 11
     f. IF 发现新引入的问题 → 记录到问题清单，进入下一轮修复
  9. IF 发现新问题 且 修复轮次 < 3 → 继续循环
  10. IF 修复轮次 == 3 且仍有问题 → 输出最终报告，标注"部分问题未解决" → 完成
  11. IF 零残留 → 更新 verification-report.md（追加修复记录）
  12. 素材自动回流（必执行，不可跳过）：
      读取 ../shared/material-reflow.md 并按流程执行
      本 Skill 扫描范围：styles/ + archetypes/ + worlds/ + tropes/
      汇报回流结果（新增了哪些素材）
  13. 状态转换门禁：
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
  "status": "analyzing|planning|configuring|writing|written|verifying|cross-reviewing|fixing|complete",
  "target_words": 50000,
  "budget_words": 45000,
  "source_words": 102425,
  "compression_ratio": 2.05,
  "current_chapter": 0,
  "total_chapters": 35,
  "last_review_chapter": 0,
  "last_compress_chapter": 0,
  "ledger_version": 0,
  "wave_postprocess_step": "done",
  "parallel_mode": "normal|degraded",
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD",
  "chapters": {
    "001": {
      "status": "complete",
      "write_retries": 0,
      "verify_retries": 0,
      "review_retries": 0,
      "claude_retries": 0,
      "review_score": 8.0,
      "low_quality": false,
      "failed_escalated": false,
      "manual": false
    }
  }
}
```

**chapters 字段说明**（Gemini 集成新增）：
- 初始化：新建小说时 `chapters` 为空对象 `{}`，每章完成后追加
- 恢复：resume 时读取 chapters，跳过 `status="complete"` 的章
- `review_score`: Gemini 审查评分（null 表示审查失败，按 0 计入平均）
- `low_quality`: true 当 review_score < 6 或 review/claude_retries 耗尽
- `failed_escalated`: true 当 verify_retries ≥ 3 仍有泄漏（停止写作，等待用户处理）
- `manual`: true 当 Claude Code 直接写作（SAFETY/write_retries 耗尽时接管）
```

## 绝对禁止事项（分层加载）

**写作 Agent prompt 中加载的核心禁令（6条）**：
1. **绝不在成稿中出现原作角色名或设定名** — 最高优先级红线
2. **绝不跳过自查步骤** — 每章写完必须执行七项自查
5. **绝不在映射表不完整时继续** — 新实体必须先生成映射再写入章节
8. **绝不破坏情节因果链** — 压缩是删减描写，不是删减逻辑
9. **绝不编造 details-lock.md 中未列的具体数字/物理细节** — 需要新数字时使用模糊措辞
12. **绝不在角色尚未进入某身份阶段时使用该阶段的名称/称呼** — 检查 details-lock 身份阶段表

**波次后处理和审校时加载的扩展禁令**（写作 Agent 不加载）：
3. **绝不在记忆未加载时写作** — 必须先加载 memory-outline + recent-context
4. **绝不遗忘更新 meta.json** — 每章写完立即更新 current_chapter
6. **绝不让总字数超过 50000** — 硬上限
7. **绝不让总字数低于 45000** — 硬下限
10. **绝不跳过波次间的 Blocking Critical 门禁** — 最多2轮修复后降级串行
11. **绝不在终验中使用纯抽查模式** — 必须基于 event-ledger 做定向顺序通读

**禁令12审校方法说明**：核心禁令12要求不提前使用身份阶段名称 — 审校时从 details-lock 身份阶段表提取合法称呼，Grep 检查越界使用

**Gemini 集成新增禁令**：
13. **绝不在 failed_escalated 章节未处理时继续写作** — 必须先由用户决定（手动写作 or 检查映射表后重试）
14. **绝不跳过 /short 的任何章节** — 字数预算和 event-ledger 依赖完整覆盖，跳章会破坏全书一致性
15. **Claude Code 接管写作后必须走 verify 硬门禁** — 确保零泄漏保证对所有路径有效

## User-Learned Best Practices & Constraints

> **Auto-Generated Section**: This section is maintained by `skill-evolution-manager`. Do not edit manually.

### User Preferences
- prompt组装必须使用标准化模板文件（prompt-template.txt），禁止执行者手动压缩style.md系统提示词
- 三层验证循环改为分级模式：前4章+每5章抽检=全三层，其余=write+verify两层
- 前章正文注入必须自动化：读取N-1章末尾500字，不依赖执行者手写摘要
- 弧间过渡：compression-map标记弧线边界章节，对边界章prompt增加过渡衔接要求
- Gemini 2.5 Pro 需要去掉 thinkingBudget=0（Pro不支持），write-chapter.py 应根据模型名自动判断
- Pro 的 API timeout 需要 300s（Flash 用 180s 够了），应从 model-config.json 读取或根据模型自动设置
- Pro 速率限制严格，批量写作需要间隔 5s+，build-prompt.py 或批处理脚本应内置间隔
- temperature=1.0 + 正向引导 style.md 是当前最佳组合，不要回退到约束型风格

### Known Fixes & Workarounds
- review-chapter.py JSON解析100%失败：需修复JSON提取逻辑适配Gemini 2.5 Flash实际输出格式
- 字数持续偏低：在prompt-template中将字数要求提升到=== USER ===第一行最高优先级位置
- 泄漏重试被绕过：批处理模式必须实现至少1次verify重试，不能把verify失败当warning
- event-ledger/recent-context更新断裂：考虑脚本化自动更新，或在终验阶段增加记忆系统重建步骤
- ch31→ch32 重复问题：相邻章共享同一原作章节（038前半/后半）时，build-prompt.py 需注入更强的防重叠指令，明确区分前后半的事件边界
- 中后段摘要化：章节越往后 prompt 中 recent-context 越长，挤压了原作参考空间。考虑只注入最近3章摘要而非全部
- model-config.json 应支持 timeout 和 thinkingConfig 字段，让 write-chapter.py 读取而非硬编码

### Custom Instruction Injection

v4 Pro 实战：32章完成，Codex评分6.3/10（vs Flash 5.1）。Pipeline成熟，核心改善来自模型升级+style.md正向引导+伏笔系统。下一步：选新原作验证泛化能力。