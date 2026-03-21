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
```

## 执行模式选择

```
remaining = total_chapters - current_chapter

IF remaining <= 5 → 串行模式（逐章写作，每章更新记忆）
ELSE → 并行模式（多 Agent 批量写作，写完后统一重建记忆）
```

**串行模式**：严格按下方"每章写作流程"执行。
**并行模式**：分成若干批次（每批 3-5 章），按批次顺序启动。
  - 同批次内不得包含相邻章节（防止共享上下文边界导致重叠）
  - 如果相邻章约束导致批次 ≤2 章，退化为串行
  - batch1 完成 → 后处理 → batch2 → ...

**并行模式 Agent prompt 必须包含**：
  - 完整 config、memory-outline、recent-context、原作章节、自查要求
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

**并行模式特殊处理**：
  - Agent 写作时跳过 recent-context.md 更新、定期压缩、current_chapter 更新
  - **每批次完成后（注意顺序！）**：
    1. **相邻章重叠扫描**（在 context 重建之前执行！防止有问题的章节污染上下文）：
       FOR 本批次每个已写章节 chN：
         IF ch(N-1) 已存在：
           判定1（结构）：检查 chN 和 ch(N-1) 的核心事件 ID 是否重复占用
           判定2（文本）：比对 ch(N-1) 最后一个场景 与 chN 第一个场景，
                         检查是否描写了相同角色+相同动作+相同场景
           IF 任一判定命中 → 标记 chN 为"需重写"
       冲突裁决：前章保留，后章重写
       重写时串行执行，注入前章全文 + 完整防越界指令 + 本章事件ID列表 + 邻章边界ID
       重写后复检，最多 1 轮。复检仍冲突 → 立即降级为串行模式完成剩余章节
       降级状态记录到 meta.json："parallel_mode": "degraded"
       恢复时检查：IF meta.json.parallel_mode == "degraded" → 直接使用串行模式
    2. 扫描连续最大章号 → 更新 current_chapter
    3. **重建 recent-context.md**：读取最近 10 章已写内容，提取摘要覆盖写入
    4. timeline.md 回填：读取本批次章节，提取时间标记，逐章追加
    5. 滚动预算检查
    6. **风格与行为一致性抽查**（每批次必做）：
       - 从本批次中均匀抽取 1-2 章（覆盖批次首尾），与 style.md 对照
       - 检查主角行为模式是否跨章一致（如"先苟着"的角色不应突然变成"无脑硬刚"，除非有明确的成长转折）
       - 检查反派智商是否被临时下调以配合收网（如间谍角色不应无故自曝全部罪行）
       - 发现问题 → 标记需修改，在下一批次启动前修复
    7. **审校触发检查**：
       WHILE current_chapter >= last_review_chapter + 5：
         → 启动 Phase 5A（范围：last_review_chapter+1 到 last_review_chapter+5）
         → last_review_chapter += 5，更新 meta.json
       （后台审校的修复结果在下一批次启动前处理）
    8. **记忆压缩触发检查**：
       WHILE current_chapter >= last_compress_chapter + 10：
         → 执行 Phase 6（归档 last_compress_chapter+1 到 last_compress_chapter+10）
         → last_compress_chapter += 10，更新 meta.json
    9. **检查点汇报**（如触发了步骤8）：
       输出检查点汇报（格式见下方）
  - 全部完成后必须执行全量记忆重建

**安全降级**：如果重叠检测触发重写后仍冲突，剩余章节全部转串行正文模式。
串行模式下仍可并行执行：审校、泄漏扫描、字数统计、时间线提取。

## 每章写作流程（新作第 N 章）

```
┌─ 1. 加载上下文（静默）
│    读取所有 config + context 文件
│
├─ 2. 查询压缩映射表
│    找到新作第 N 章对应的原作章节范围
│    读取原作章节 + 压缩策略和目标字数
│
├─ 3. 分析原作章节结构（静默）
│    提取核心情节线、关键事件、新角色/新设定
│
├─ 4. 新实体检查
│    未映射的角色/设定 → 检查保留清单 → 自动生成映射或略过
│
├─ 5. 生成改编章节
│    遵循：目标字数(±10%)、压缩策略、style.md、映射表、记忆系统
│    质量：章末钩子、不违反世界规则、因果链完整
│
├─ 6. 七项自查
│    ① character-map 左列角色名泄漏
│    ② setting-map 左列设定名泄漏
│    ③ 与 memory-outline 事实矛盾
│    ④ 与 recent-context 连续性断裂
│    ⑤ 章末钩子
│    ⑥ 伏笔变更检测（强制登记新伏笔）
│       → 额外扫描【】系统提示中的新悬念、对话承诺、未解释异常
│       → 疑似伏笔未登记 → 强制新增到 foreshadowing.md
│    ⑦ 字数检查（超标>10%→精简；不足>15%→补充）
│
├─ 7. 保存与更新
│    → chapters/{NNN}.md、recent-context.md、foreshadowing.md、meta.json
│    → 追加 context/timeline.md：章号 | 故事内天数 | 倒计时状态 | 时间标记原文
│      （并行模式下跳过逐章写入，每批次完成后统一回填）
│
├─ 8. 定期任务
│    每5章：后台审校 + 滚动预算检查
│    每10章：记忆压缩 + 检查点汇报
│    最后一章：跳转写作结束条件
│
└─ 继续下一章
```

## 检查点汇报格式（每 10 章）

```
═══ 检查点：第 {N} 章 / 共 {total} 章（{percent}%）═══
累计总字数：{total_words} 字 / 目标 45000-50000 字
预算追踪：偏差 {deviation}%
新增映射/伏笔：{list or "无"}
═══ 继续写作... ═══
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
