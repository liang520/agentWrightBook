# Phase 4：写作核心循环

**这是最关键的阶段。**

**前置条件**：meta.json status="writing"，mode="short"，所有 config/ 文件存在

## 恢复逻辑

```
current = meta.json.current_chapter
start_from = current + 1
加载：style.md → memory-outline.md → recent-context.md
     → character-map.md → setting-map.md → foreshadowing.md
     → compression-map.md（关键：知道每章对应原作哪些章节）
     → details-lock.md（事实锁定表，分层加载）
     → event-ledger.md（事件账本，短篇全量加载）

恢复检查：
  IF meta.json.parallel_mode == "degraded" → 直接使用串行模式
  IF meta.json.wave_postprocess_step != "done" AND wave_postprocess_step != null
    → wave_postprocess_step 的值 = 最后完成的步骤（如 "c" 表示 c 已完成）
    → 从下一步骤开始恢复（如 "c" → 从 d 开始执行）
  IF context/wave-plan.md 存在 → 读取，跳过已完成波次，继续下一波次

  # Gemini 集成新增检查
  IF meta.json.chapters 中存在 failed_escalated=true 的章节：
    → 打印警告：[ESCALATED] 第 {NNN} 章：3 次重写仍有原作名泄漏
    → 暂停，等待用户决定：
      A) 手动写作该章（Claude Code 直接写，走 verify 硬门禁）
      B) 检查映射表后重试（重新进入验证循环）
      ⚠️ 不提供「跳过」选项 — /short 依赖每章存在（字数预算+event-ledger 连续性）

Gemini 模式检测（每次写作循环开始时执行一次）：
  REPO_ROOT=$(git rev-parse --show-toplevel)
  IF "$REPO_ROOT/scripts/model-config.json" 存在
     AND GOOGLE_APPLICATION_CREDENTIALS 环境变量已设置（或 model-config.json 含 key_file）
     AND "$REPO_ROOT/scripts/.venv/bin/python3" 存在
  → gemini_mode = true
  ELSE
  → gemini_mode = false（使用原始 Claude Code 写作流程）

Phase A 质量自动降级：
  IF gemini_mode = true AND current_chapter >= 10：
    计算已完成 Gemini 章节的 review_score 平均值（null 按 0 计）
    IF 平均 < 5 → gemini_mode = false，后续章节走原始流程
    已写的低分章节保留但标记 low_quality=true
```

## 执行模式：串行主干期 + 波次并行

### 阶段一：串行主干期（前 4 章必须串行）

```
ch1 → ch2 → ch3 → ch4 严格串行
目的：建立核心事实基线，填充 details-lock.md 和 event-ledger.md
完成后：details-lock 中的核心细节已固化，event-ledger 已有 4 条基线记录
每章按下方"每章写作流程"执行。
```

### 阶段二：波次并行期（第 5 章起）
# PHASE_A_SERIAL_DEGRADATION: Gemini 集成期间，波次并行暂时降级为全串行
# Phase B 恢复并行时搜索此标记，移除降级逻辑
⚠️ IF gemini_mode = true：所有章节按 ch5 → ch6 → ch7 → ... 顺序串行执行，
   每章走三层验证循环（同串行主干期）。波次后处理的 delta 提取逐章执行。
   以下波次并行逻辑在 gemini_mode=true 时跳过，gemini_mode=false 时正常执行。

**波次分配（启发式规则，输出 wave-plan.md）**：

```
主 Agent 按以下步骤分配波次（读表 → 判断 → 写表，无需图算法）：

步骤1：标记强耦合对
  扫描 compression-map，逐对检查相邻章(ch_i, ch_i+1)：
    IF ch_i 终止事件涉及角色A的状态变更（被抓/受伤/暴露/死亡）
       AND ch_i+1 起始事件涉及同一角色A
    → 标记 (ch_i, ch_i+1) 为强耦合

  扫描 foreshadowing.md（含承诺追踪表）：
    IF 埋设章与回收章间距 ≤ 5 → 标记为强耦合

  扫描 details-lock.md 道具归属表：
    IF 同一道具的两个转移章节间距 ≤ 5 → 标记为强耦合
    IF 间距 > 5 → 不标记，靠方案E全局约束扫描兜底

步骤2：归组
  将所有强耦合对合并为"串行组"（传递闭包：A-B强耦合、B-C强耦合 → A-B-C同组）
  组内按章号排序，标记为"串行"

步骤3：填入波次
  依次处理每个串行组和剩余独立章节：
    - 串行组整体放入一个波次，组内严格串行
    - 独立章节（无强耦合关系）填入最早的可用波次
    - 每波次上限 4-5 章（含串行组占用的位置）
    - 如果某串行组超过 5 章，该组独占一个波次

步骤4：输出 context/wave-plan.md
  | 波次 | 章号列表 | 模式 | 强耦合原因 |
  |------|---------|------|-----------|
  | 1    | 5,7     | 并行 | 无 |
  | 2    | 6,8     | 并行 | 无 |
  | 3    | 9,10    | 串行 | F06伏笔链(9→10) |
  | 4    | 11,13   | 并行 | 无 |
  | ...  | ...     | ...  | ... |
  | 8    | 20,21,22| 串行 | 季天成状态连续变更 |
```

**波次并行 Agent prompt 必须包含**：
  - 完整 config、memory-outline、recent-context、原作章节、自查要求
  - **details-lock.md（分层加载）**：
    - 加载：与当前章涉及的角色相关的物理细节条目
    - 加载：角色身份阶段表（全量，通常很短）
    - 加载：当前章涉及的道具归属条目
    - 不加载：与当前章无关的角色/道具条目
  - **event-ledger.md（最近 5 章）**：
    - 短篇（≤50章）：加载全量 event-ledger
    - 长篇（>50章）：只加载最近 20 条 + 涉及当前章核心角色的历史条目
  - **前章注入**：IF chapters/{N-1}.md 已存在 → 读取全文（超 3000 字取最后 1500 字）
  - **邻章边界**（从 compression-map 读取）：
    - 前章终止事件 ID：{prev_end_event_id}
    - 本章起始事件 ID / 终止事件 ID / 核心事件 ID 列表
    - 后章起始事件 ID：{next_start_event_id}（如已知）
  - **防越界硬指令**（逐字包含在 Agent prompt 中）：
    ```
    【防重叠规则 - 强制执行】
    1. 前章内容已给出。你必须从前章结尾处自然接续，绝不重复前章事件。
    2. 你只负责本章事件 ID 列表中的事件，不得越界。
    3. 写到本章终止事件落地即止。不写余波——余波属于下一章。
    4. 前章不存在时，以简短过渡开始，不展开完整场景。
    ```
  - **前章不存在时**：在 prompt 中标注"前一章尚未写作，本章开头需留出衔接空间，以简短过渡开始。"

**写作 Agent 输出规范**：
  - 输出章节正文（写入 chapters/{NNN}.md）
  - 输出简短的"本章摘要"（1-2 句话，用于 recent-context）
  - **不需要输出任何 JSON**。delta 由提取 Agent 后置生成。

**波次内执行**：
  - 同波次并行章节同时启动
  - 同波次串行组内按章号顺序串行执行
  - Agent 写作时跳过 recent-context.md 更新、定期压缩、current_chapter 更新

### 每波次后处理流水线（硬门禁，不可跳过）

每波次完成后，严格按 a→g 顺序执行。meta.json 的 `wave_postprocess_step` 字段记录当前步骤（用于断点恢复）。

```
a. 提取 chapter_delta
   主 Agent 为本波次每章调用提取 Agent。
   提取 Agent 输入：章节正文 + details-lock.md + 上一章的 event-ledger 条目
   提取 Agent 输出：chapters/{NNN}.delta.json
   JSON 必填字段：chapter(数字)、events(列表)、state_changes(对象)、end_states(对象)、new_characters(列表：本章首次出场角色)、new_concepts(列表：本章首次引入设定/能力)
   可选字段（默认[]）：new_facts_to_lock(列表：本章新产生的待锁定事实)、new_dependencies(列表：本章发现的新章间依赖，如["ch20→ch22"])
   校验：缺失任一必填字段 → 重新调用提取 Agent（最多2次）→ 仍缺失 → 主 Agent 人工补填；可选字段缺失时默认为空列表
   → 完成后更新 wave_postprocess_step = "a"

b. 合并写入 event-ledger.md                    ← 前置：a 全部完成
   1. 复制 event-ledger.md 为 event-ledger.prev.md（波次前备份）
   2. meta.json 中 ledger_version += 1
   3. 按章号顺序读取全部 .delta.json，合并写入 event-ledger.md
   4. 从 delta.json 的 new_characters + new_concepts 字段自动回写 context/character-appearances.md：
      | 章号 | 新登场角色 | 新引入概念 |
      波次 Agent prompt 加载此表。Agent 写作前检查本章涉及角色/概念是否已登场。
   → 完成后更新 wave_postprocess_step = "b"

c. 锁定待定事实                                ← 前置：b 完成
   汇总所有 delta.json 中的 new_facts_to_lock 字段
   裁决后写入 details-lock.md，回填章节中的模糊措辞
   → 完成后更新 wave_postprocess_step = "c"

d. 事实一致性 Grep 扫描                        ← 前置：c 完成（details-lock 已更新）
   从 details-lock.md 提取每个锁定值的"搜索关键词列表"
   用 Grep 跨全部已写章节扫描：
     - 同一锁定值的关键词是否一致
     - 时序性锁定值是否在正确章节范围内
     - 数字是否一致
   输出冲突报告。
   注意：LLM 归一化比对仅在终验时执行，此处只用 Grep。
   → 完成后更新 wave_postprocess_step = "d"

e. 状态连续性扫描                              ← 前置：b 完成（可与 d 并行）
   相邻章检查：
     收集所有已有 event-ledger 条目的章号，按章号排序
     FOR 每对相邻已有条目的章 (i, i+1)（跳过无 ledger 条目的章号）:
       比对 event-ledger 第 i 章结束状态 与 第 i+1 章开始状态
       检查6个维度：地点、人身自由、伤情、认知状态、关系状态、道具/资产
       发现断裂 → 标记
   全局状态约束检查：
     - "被拘留"期间不应出现在自由活动场景
     - "离开某地"后不应无交代地出现在该地
     - "道具被A拿走"后不应出现在原位置
   扫描范围：短篇全量扫描；长篇增量扫描（本波次 + 前后各5章 + event-ledger 变更涉及章）
   → 完成后更新 wave_postprocess_step = "e"

f. 审校触发 + 相邻章重叠扫描                   ← 前置：d + e 完成
   (1) 相邻章重叠扫描（保留现有成熟机制）：
       FOR 本波次每个已写章节 chN：
         IF ch(N-1) 已存在：
           判定1（结构）：检查 chN 和 ch(N-1) 的核心事件 ID 是否重复占用
           判定2（文本）：比对 ch(N-1) 最后一个场景 与 chN 第一个场景，
                         检查是否描写了相同角色+相同动作+相同场景
           IF 任一判定命中 → 标记 chN 为"需重写"
       冲突裁决：前章保留，后章重写
       重写时串行执行，注入前章全文 + 完整防越界指令 + 本章事件ID列表 + 邻章边界ID
       重写后复检，最多 1 轮。

   (2) 风格与行为一致性抽查：
       从本波次中均匀抽取 1-2 章（覆盖批次首尾），与 style.md 对照
       检查主角行为模式是否跨章一致
       检查反派智商是否被临时下调以配合收网
       发现问题 → 标记需修改

   (3) 审校检查（范围 = 本波次全部章节 + 前后各1章）：
       检查项（在原有6项基础上新增）：
         [新增] details-lock 一致性（消费步骤 d 的扫描结果）
         [新增] event-ledger 状态连续性（消费步骤 e 的扫描结果）
         [新增] 场景转换自然度
         [新增] 角色身份阶段合规性（从 details-lock 的身份阶段表提取合法称呼，Grep 检查越界使用）
       审校结果写入验证（后置子步骤）：
         审校完成后 → 追加写入 context/review-notes.md
         格式：## 波次 {wave_id} | 范围 ch{start}-ch{end} | {timestamp}
         内容：问题清单（如无问题则写"本波次无问题"）
         步骤 g 开始前检查 review-notes.md 中是否存在本波次记录
         IF 不存在 → 返回步骤 f(3) 重新执行审校（最多重试 2 次，仍失败则记录 Warning 并继续）

   汇总所有问题，按双层门禁分级。
   → 完成后更新 wave_postprocess_step = "f"

g. 门禁判定                                    ← 前置：f 完成
   双层门禁分级：

   Blocking Critical（硬阻断，必须修复才能继续下一波次）：
     - 人物生死状态矛盾（死人复活/活人消失）
     - 人身自由状态矛盾（被拘留的人出现在外面）
     - 地点硬冲突（上章逃离A地，下章无交代又出现在A地）
     - details-lock 中的锁定值被违反
     - 相邻章重叠扫描命中（重写后复检仍冲突）

   Non-blocking Critical（记录+修复队列，不阻断主流水线）：
     - 风格轻微漂移
     - 过渡不够自然（但不影响逻辑）
     - 称呼偶尔不统一
     - 次要角色行为轻微偏移

   Warning / Suggestion：
     - 记录到 review-notes.md
     - 全书完成后统一处理

   判定逻辑：
     IF 存在 Blocking Critical：
       → 修复问题章节（修复后同步更新 details-lock 变更日志 + 重新提取 delta）
       → 同一波次内 Blocking Critical 修复最多 2 轮
       → 2 轮修复后仍有 Blocking Critical → 自动降级为串行模式完成剩余章节
         降级状态记录到 meta.json："parallel_mode": "degraded"
     IF 相邻章重叠重写后复检仍冲突 → 立即降级为串行模式

     IF 无 Blocking Critical：
       → 扫描连续最大章号 → 更新 current_chapter
       → 重建 recent-context.md：读取最近 10 章已写内容，提取摘要覆盖写入
       → 滚动预算检查
       → 记忆压缩触发检查：
         WHILE current_chapter >= last_compress_chapter + 10：
           → 归档 last_compress_chapter+1 到 last_compress_chapter+10
           → last_compress_chapter += 10，更新 meta.json
       → 检查点汇报（如触发了记忆压缩）
       → 记忆系统强制验证（每 10 章）：
         IF current_chapter % 10 == 0 AND current_chapter > 0：
           读取 memory-outline.md 内容
           IF 仍为空模板（仅含占位符如"Phase 4 写作阶段逐步填充"）：
             → 强制执行记忆压缩（重建 memory-outline + 归档）
             → 压缩完成后再次检查 memory-outline.md 是否仍为空
             → IF 仍为空 → 记录 Warning（"记忆压缩失败"），更新 meta.json parallel_mode → "degraded"，以降级模式继续
           同时校验 meta.json.last_compress_chapter 是否 >= current_chapter - 9

   写作中新发现的依赖处理：
     提取 Agent 在 delta.json 的 new_dependencies 中标记（如 ["ch20→ch22"]）
     主 Agent 在下一波次分配时纳入考虑，必要时更新 wave-plan.md

   → 完成后更新 wave_postprocess_step = "done"
   → 进入下一波次
```

### event-ledger 恢复机制

```
合并前保存 event-ledger.prev.md（波次前版本）
扫描失败（步骤 d/e 发现 Blocking Critical）：
  → 用 event-ledger.prev.md 覆盖 event-ledger.md
  → meta.json 中 ledger_version 回退
  → 删除本波次的 .delta.json
  → 修复问题章节正文后，重新提取 delta → 重新合并 → 重新扫描
  → 最多恢复 2 轮，之后降级为串行模式
```

### 安全降级

```
触发降级的条件：
  - 相邻章重叠重写后复检仍冲突
  - 同一波次 Blocking Critical 修复超过 2 轮
  - event-ledger 恢复超过 2 轮

降级行为：
  - meta.json 记录 "parallel_mode": "degraded"
  - 剩余章节全部转串行模式
  - 恢复时检查：IF meta.json.parallel_mode == "degraded" → 直接使用串行模式
  - 串行模式下仍可并行执行：审校、泄漏扫描、字数统计、时间线提取
```

## 每章写作流程（新作第 N 章）

```
+-- 1. 加载上下文（静默）
|    读取所有 config + context 文件
|    details-lock.md 分层加载（仅当前章相关条目）
|    event-ledger.md 加载（短篇全量，长篇最近20条+相关角色历史）
|
+-- 2. 查询压缩映射表
|    找到新作第 N 章对应的原作章节范围
|    读取原作章节 + 压缩策略和目标字数
|
+-- 3. 分析原作章节结构（静默）
|    提取核心情节线、关键事件、新角色/新设定
|
+-- 4. 新实体检查
|    未映射的角色/设定 → 检查保留清单 → 自动生成映射或略过
|
+-- 5. 生成改编章节
|    ┌─────────────────────────────────────────────────────────────────┐
|    │ IF gemini_mode = true → 走 5-GEMINI 三层验证循环               │
|    │ IF gemini_mode = false → 走 5-ORIGINAL 原始流程                │
|    └─────────────────────────────────────────────────────────────────┘
|
|    === 5-ORIGINAL（gemini_mode=false 时执行，原始 Claude Code 流程）===
|    遵循：目标字数(+-10%)、压缩策略、style.md、映射表、记忆系统
|    质量：章末钩子、不违反世界规则、因果链完整
|    禁令：不编造 details-lock 中未列的具体数字/物理细节（用模糊措辞）
|    禁令：不在角色尚未进入某身份阶段时使用该阶段的名称/称呼
|    视角框架：配角独立弧段首尾必须有主角视角框架
|      → 配角独立弧定义：连续 ≥5 段以配角为中心、主角不在场的叙事
|      → 框架要求：以主角视角引入开始，以主角视角承接结束
|      → 豁免：plot-skeleton 或 wave-plan 中明确标注"配角独立弧"的章节
|      → 短暂切换（≤3 段）不受此限制
|    → 完成后进入 step 6（七项自查）
|
|    === 5-GEMINI（gemini_mode=true 时执行，三层验证循环）===
|
|    验证分级（实战优化 v2）：
|      FULL_VERIFY = (N <= 4) OR (N % 5 == 0) OR (N == total_chapters)
|        → 前4章 + 每5章 + 最后一章：执行完整三层（write→verify→review→claude check）
|      STANDARD_VERIFY = 其他章节
|        → 执行两层（write→verify）。verify 不通过必须重试至少1次（不能跳过）。
|      ⚠️ verify 泄漏是硬门禁，无论哪种模式都不能跳过重试。
|
|    ① 初始化
|       write_retries = 0, verify_retries = 0, review_retries = 0, claude_retries = 0
|       执行 mkdir -p {novel}/tmp/
|
|    ② 组装 prompt + review-context
|       ⚠️ 必须按 [references/prompt-template.md](references/prompt-template.md) 模板填充
|       ⚠️ 禁止手动压缩或重写 style.md 系统提示词——原文加载
|       write prompt → {novel}/tmp/ch-{NNN}-prompt.txt
|         === SYSTEM === 部分：读取 config/style.md "## 系统提示词" 到文件末尾，原文粘贴
|         === USER === 部分：按模板填充（字数第一优先、替换清单第二优先）
|         前章注入：读取 chapters/{N-1}.md 末尾500字原文（不是手写摘要）
|         弧间过渡：如果本章与前章属不同弧线，添加弧间过渡要求
|       review-context → {novel}/tmp/ch-{NNN}-review-context.txt
|         内容：style + character-map + memory-outline + recent-3章摘要(每章≤150字) + 待审章节占位
|
|    ③ [WRITE — Layer 0] 调用 Gemini
|       REPO_ROOT=$(git rev-parse --show-toplevel)
|       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/write-chapter.py" \
|         --prompt-file {novel}/tmp/ch-{NNN}-prompt.txt \
|         --output-file {novel}/tmp/ch-{NNN}-draft.txt
|       - exit 3 → 停止写作循环（认证失败）
|       - exit 2 (SAFETY) → Claude Code 接管（见「Claude 接管流程」）
|       - exit 1 → write_retries+1；若 < 3 → 回到 ③；否则 → Claude Code 接管
|       - exit 0 → 进入 ④
|
|    ④ [VERIFY — Layer 1：硬门禁] 名字/别名泄漏扫描
|       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/verify-chapter.py" \
|         --chapter-file {novel}/tmp/ch-{NNN}-draft.txt \
|         --character-map {novel}/config/character-map.md \
|         --setting-map {novel}/config/setting-map.md \
|         --report-file {novel}/tmp/ch-{NNN}-verify.json
|       - exit 2（空词列表）→ 停止写作循环，提示检查映射表格式
|       - exit 1（有泄漏）→ **重建** prompt（不是追加！将泄漏词列表写入 prompt 开头的【最高优先级】区块），
|         verify_retries+1；若 >= 3 → failed_escalated=true，停止
|         否则 → 回到 ③
|         ⚠️ 重要：每次重写时重新生成 prompt 文件，不要追加 feedback。
|         追加会导致 prompt 膨胀 → Gemini 输出越来越短。
|         正确做法：在 prompt 的 === USER === 开头添加【最高优先级】泄漏词替换清单。
|       - exit 0 → 进入 ⑤
|
|    IF STANDARD_VERIFY（非全量验证章节）→ 跳过 ⑤⑥⑥-POST，直接进入 ⑦
|
|    ⑤ [REVIEW — Layer 2：Gemini 评分]（仅 FULL_VERIFY 章节执行）
|       覆盖 review-context 的 === CHAPTER TO REVIEW === 节
|       "$REPO_ROOT/scripts/.venv/bin/python3" "$REPO_ROOT/scripts/review-chapter.py" \
|         --review-context-file {novel}/tmp/ch-{NNN}-review-context.txt \
|         --report-file {novel}/tmp/ch-{NNN}-review.json
|       - exit 1/2 → 接受章节继续，review_score=null（null 按 0 分计入质量平均）
|       - exit 0, passed=false → **重建** prompt（将 review issues 写入 prompt 开头），
|         review_retries+1；若 >= 2 → low_quality=true，进入 ⑥
|         否则 → 回到 ②（重新生成 prompt，不追加）
|       - exit 0, passed=true → 进入 ⑥
|
|    ⑥ [CLAUDE CODE 智能校验 — Layer 3] Claude Code 读取 draft 执行检查：
|       ⑥-A 事实矛盾：对照 memory-outline + details-lock
|       ⑥-B 连续性：对照 recent-context + event-ledger
|       ⑥-C 章末钩子：最后两段是否有悬念/期待感
|       ⑥-D 伏笔变更检测（不触发重写，只更新 foreshadowing.md）
|            → 新伏笔 → 新增条目；旧伏笔回收 → 更新条目
|            → 额外扫描：未登记的悬念/承诺/预言 → 强制新增
|       ⑥-E 字数检查（超标>10%→重写精简；不足>15%→重写补充）
|
|       IF ⑥-A/B/C/E 任一失败：
|         构造 CLAUDE_FEEDBACK，**重建** prompt（将 feedback 写入 prompt 开头，不追加）
|         格式：[FACT_CONFLICT]/[CONTINUITY_BREAK]/[MISSING_HOOK]/[WORD_COUNT] + 具体描述
|         claude_retries+1；若 >= 2 → low_quality=true，进入 ⑥-POST
|         否则 → 回到 ②（重新生成 prompt）
|       IF 全部通过 → 进入 ⑥-POST
|
|    ⑥-POST [确定性检查 — Grep 层]（Layer 3 通过后、写入前执行）
|       (a) details-lock 一致性：从 details-lock.md 提取搜索关键词，Grep 扫描 draft
|           发现违反 → 追加 CLAUDE_FEEDBACK [DETAILS_LOCK_VIOLATION]，
|           claude_retries+1；若 >= 2 → low_quality=true，进入 ⑦
|           否则 → 回到 ③
|       (b) 身份阶段合规性：从 details-lock 身份阶段表提取当前章合法称呼，Grep 扫描 draft
|           发现越界使用 → 追加 CLAUDE_FEEDBACK [IDENTITY_STAGE_VIOLATION]，
|           claude_retries+1；若 >= 2 → low_quality=true，进入 ⑦
|           否则 → 回到 ③
|       注意：(a)(b) 与 ⑥-A/B/C/E 共享 claude_retries 计数器（总预算 max 2）
|       全部通过 → 进入 ⑦
|
|    ⑦ 写入 novels/{novel}/chapters/{NNN}.md
|
|    独立预算：write_retries(max 3) / verify_retries(max 3) / review_retries(max 2) / claude_retries(max 2)
|    retries=N 意味着已重试 N 次（初始写作不计入）
|
|    Claude 接管流程（SAFETY/write_retries 耗尽时）：
|      Claude Code 自行写作本章
|      → 必须走 verify-chapter.py 硬门禁（确保零泄漏保证）
|        IF verify 通过 → 写入 novels/，meta.json 记录 manual=true，继续下一章
|        IF verify 不通过 → Claude Code 修正后重新 verify（最多 3 次，与主流程一致）
|          仍不通过 → failed_escalated=true，**停止写作循环**
|          （不继续下一章 — 与禁令 #13 一致：failed_escalated 必须等待用户处理）
|      → 跳过 Layer 2 和 Layer 3（Claude Code 自身即 LLM 质量保证）
|
|    === 5-GEMINI 结束 → 跳过 step 6（自查已在三层循环中完成），进入 step 7 ===
|
+-- 6. 七项自查（仅 gemini_mode=false 时执行；gemini_mode=true 时由 5-GEMINI 的三层循环覆盖）
|    (1) character-map 左列角色名泄漏 → [gemini: Layer 1 verify-chapter.py]
|    (2) setting-map 左列设定名泄漏 → [gemini: Layer 1 verify-chapter.py]
|    (3) 与 memory-outline 事实矛盾 → [gemini: Layer 3 ⑥-A]
|    (4) 与 recent-context 连续性断裂 → [gemini: Layer 3 ⑥-B]
|    (5) 章末钩子 → [gemini: Layer 3 ⑥-C]
|    (6) 伏笔变更检测 + 状态追加更新（强制） → [gemini: Layer 3 ⑥-D]
|       a. 扫描本章新增伏笔：
|          → 额外扫描【】系统提示中的新悬念、对话承诺、未解释异常
|          → 疑似伏笔未登记 → 强制新增到 foreshadowing.md，状态="已埋设"
|       b. 扫描本章是否回收了已有伏笔：
|          → 读取 foreshadowing.md 中预计回收章 ≤ 当前章号的条目
|          → 本章正文包含回收内容 → 追加更新状态为"已回收"，标注实际回收章号
|       c. 设定承诺/道具归属同理追加更新
|       注：仅扫描本章，不做全量比对。追加模式，不重写整个文件。
|    (7) 字数检查（超标>10%→精简；不足>15%→补充） → [gemini: Layer 3 ⑥-E]
|
+-- 7. 保存与更新（全部必执行，不可跳过）
|    → chapters/{NNN}.md — 保存章节
|    → meta.json — 更新 current_chapter + chapters[NNN] 条目
|    → recent-context.md — 追加本章摘要（2-3句话：核心事件+新登场角色+关键事实变更）
|      ⚠️ 此步骤不可跳过。即使在批处理/提速模式下也必须执行。
|      如果 context 不够写完整摘要，至少写一行："{章号}:{核心事件关键词}"
|    → foreshadowing.md — 更新伏笔状态
|    → Gemini 模式额外字段（gemini_mode=true 时写入 meta.json）：
|        chapters[NNN].write_retries / verify_retries / review_retries / claude_retries
|        chapters[NNN].review_score = scores.overall（或 null）
|        chapters[NNN].low_quality = (review_score < 6 OR retries 耗尽)
|        chapters[NNN].manual = true（仅 Claude Code 接管时）
|        chapters[NNN].failed_escalated = true（仅 verify 3 次失败时）
|    → low_quality=true 的章节：recent-context 仅写精简事实摘要（不加载全文，防污染）
|    → 追加 context/timeline.md：章号 | 故事内天数 | 倒计时状态 | 时间标记原文
|      （波次并行模式下跳过逐章写入，每波次后处理统一回填）
|    → 【串行模式 event-ledger/timeline 强制更新】：
|      串行/降级模式下，每章写完后执行：
|        → 调用提取 Agent 生成本章 delta → 合并写入 event-ledger.md
|        → 追加 timeline.md 时间标记
|        → 写下一章前验证上一章的 ledger 条目和 timeline 条目是否存在
|        → IF 上一章条目缺失 → 重新调用提取 Agent 补充（最多1次）
|      波次并行模式下：
|        由波次后处理步骤 a/b 统一处理（已有逻辑）
|        步骤 b 完成后追加检查：本波次每章是否都有 ledger 条目
|        IF 任一章缺失 → 重新调用提取 Agent 补充
|
+-- 8. 定期任务
|    波次并行模式：审校+预算检查+记忆压缩在波次后处理流水线中统一触发（步骤d-f）
|    串行/降级模式：每5章后台审校+滚动预算检查；每10章记忆压缩+检查点汇报
|    最后一章：跳转写作结束条件
|
+-- 继续下一章
```

## 检查点汇报格式（每 10 章）

```
=== 检查点：第 {N} 章 / 共 {total} 章（{percent}%）===
累计总字数：{total_words} 字 / 目标 45000-50000 字
预算追踪：偏差 {deviation}%
新增映射/伏笔：{list or "无"}
=== 继续写作... ===
```

## 写作结束条件

`current_chapter == total_chapters` 时：
1. **总字数校验**：>50000 则精简超标章节；<45000 则扩写
2. **归档完整性检查**：
   FOR i = 10, 20, 30, ... 直到 total_chapters：
     段落范围 = max(上段末+1, 1) 到 min(i, total_chapters)
     IF 对应 archives/stage-*.md 不存在 → 执行该段归档（最后一段允许不足10章）
3. **强制记忆重建**：recent-context + archives + memory-outline 全部重建
4. 更新 meta.json status → "written"（不是 complete）→ 自动进入 Phase 7

## 滚动预算检查逻辑

```
偏差率 = (已写字数 - 预期字数) / 预期字数
> +5%：下调后续目标（剩余平均<800时回头精简已写章节）
< -10%：上调后续目标
-10% ~ +5%：不调整
```
