# Phase 3：逐章压缩写作

## 前置条件

meta.json `status` 为 `"planned"` 或 `"writing"`

## 恢复逻辑

```
current = meta.json.current_chapter（0 表示尚未开始）
从第 current + 1 章开始
```

更新 `status → "writing"`

## 上下文加载顺序

每章写作前加载（静默，不输出）：

```
1. novels/{name}-compressed/context/memory-outline.md     # 全书大纲
2. novels/{name}-compressed/context/recent-context.md      # 最近章节上下文
3. novels/{original}/config/style.md                       # 风格（只读引用原书）
4. novels/{name}-compressed/config/compress-plan.md        # 本章策略+事件清单
5. novels/{name}-compressed/config/foreshadowing.md        # 重映射后伏笔表
6. novels/{original}/chapters/{对应原作章}.md               # 一个或多个原章
```

## 每章写作流程（新作第 N 章）

**Step 1：读取策略**

从 compress-plan.md 读取本章的映射信息：
- 对应原作章节（可能1-5章）
- 压缩策略（保留/精炼、合并、浓缩）
- 目标字数
- 核心保留事件

**Step 2：加载原章内容**

读取映射的所有原作章节。

**Step 3：压缩重写**

根据压缩策略：

- **"保留/精炼"**（单章→单章，轻微压缩，砍 5-25%）：
  - 环境描写：压缩但不删除，保留氛围感
  - 对话：删废话和过渡性对话，核心对话不动
  - 心理描写：适度压缩，保留情绪转折
  - 措辞：长句拆短、删冗余形容词/副词
  - 过渡段：合并或缩短场景转换

- **"合并"**（多章→单章）：
  - 提取每个原章的核心事件（参照事件清单）
  - 将多章的核心事件编织成一个完整章节
  - 删除章间重复的过渡段、重复信息
  - 确保合并后仍有完整的起承转合
  - 保持角色名、设定名完全不变

- **"浓缩"**（单章大幅压缩，砍 25%+）：
  - 环境描写：3-5 句铺排 → 1 句精准意象
  - 战斗描写：删逐招流水账，保留"招式名 + 结果 + 旁观者反应"
  - 心理活动：大段独白 → 1-2 句点睛（只保留转折点心理）
  - 对话：删零信息量来回，保留推动情节和展现性格的
  - 重复信息：同一信息说了两遍的，只留更好的那遍

**"绝不动"清单**：
- 事件清单中的每一条
- 伏笔的埋设句和回收句
- 章尾钩子
- 角色口头禅和标志性说话方式
- 情绪高/低点段落

**Step 4：事件清单自检**

```
逐条读取本章事件清单（compress-plan.md 中的要点）
对每条要点：在压缩后的文本中确认存在
IF 任何要点缺失：
  → 在压缩稿中补回该要点
  → 重新检查字数
```

**Step 5：字数检查**

```
统计压缩后字数（统一口径）
chapter_target = compress-plan.md 中本章目标字数

IF 字数 > chapter_target × 1.10（超出 10%）：
  → 进一步精简冗余（不动事件清单中的内容）
  → 重新统计

IF 字数 < chapter_target × 0.85（不足 15%）：
  → 可能压缩过度，适当恢复环境描写或对话细节
  → 重新统计
```

**Step 6：保存并更新**

```
1. 写入 novels/{name}-compressed/chapters/{NNN}.md（三位数零填充）
   标题格式：# 第N章 {原章标题}（与原书标题保持一致；合并章取第一个原章标题）
2. 追加 recent-context.md（本章摘要：新增事实、角色状态、冲突、钩子）
3. 更新 meta.json：current_chapter = N, updated_at = 今日日期
   注意：并行模式下 Agent 不更新 meta.json（见下方并行模式说明）
```

## 定期任务

**每 5 章（N % 5 == 0 且 N < compressed_chapters）：滚动预算检查**

注意：当 `N == compressed_chapters` 时跳过此检查（最后一章由"写作结束条件"单独处理，避免 remaining=0 导致除零）。

```
1. 统计已写章节总字数 = words_written
2. 计算预期进度字数 = target_total × (N / compressed_chapters)
3. 计算偏差率 = (words_written - 预期进度字数) / 预期进度字数

IF 偏差率 > +5%（超预算）：
  → 计算剩余预算 = target_total - words_written
  → 剩余章节的平均目标 = 剩余预算 / (compressed_chapters - N)
  → IF 平均目标 < 800（逻辑完整性下限）：
    → 回头精简已写章节中超标最多的 2-3 章
    → 每精简一章后重新统计，重复直到平均目标合理
  → ELSE：
    → 更新 compress-plan.md 中后续章节的目标字数

IF 偏差率 < -10%（严重不足）：
  → 后续章节目标适当上调（但不超过原始目标）
  → 更新 compress-plan.md

IF -10% ≤ 偏差率 ≤ +5%：正常，不调整
```

**每 10 章（N % 10 == 0）：记忆压缩归档 + 检查点汇报**

1. 将 recent-context.md 中第 (N-9) 到第 N 章的摘要归档到 `archives/stage-{N}.md`
2. 重建 memory-outline.md（基于压缩后的章节内容）
3. 输出检查点汇报：

```
═══ 压缩检查点：第 {N} 章 / 共 {compressed_chapters} 章 ═══
累计字数：{words_written} / 目标 {target_total}
已压缩原作章：{mapped_original_chapters} / {original_chapters}
偏差率：{deviation}%
本批概况：
  - 合并章 {n} 章，平均字数 {avg}
  - 精炼章 {n} 章，平均削减 {avg}%
  - 浓缩章 {n} 章，平均削减 {avg}%
═══ 继续压缩... ═══
```

## 写作结束条件

```
当 current_chapter == compressed_chapters：

1. 总字数校验：
   统计全部章节总字数 = final_total

   IF final_total > target_total（超标）：
     → 按超标比例从高到低排序各章
     → 逐章精简，每修一章重新统计
     → 直到 final_total ≤ target_total

   IF final_total < target_total × 0.95（不足 5%+）：
     → 找到压缩最狠的几章
     → 适当恢复内容
     → 重新执行本步骤

2. 强制记忆重建：归档所有未归档章节，重建 memory-outline.md

3. 更新 status → "verifying"

4. 自动进入 Phase 4
```

## 并行/串行选择

- 剩余 ≤5 章：串行
- 剩余 >5 章：按批次并行（每批 3-5 章），批次间执行预算检查
- **相邻章约束**：同一批次内不得包含相邻章节（如新章3和新章4不能同批），因为相邻章共享上下文边界，并行写作时会使用过期的 recent-context。如果批次大小受此约束缩减到 ≤2 章，则退化为串行。

**并行模式 Agent prompt 必须包含**：
- 完整 config + memory-outline + recent-context + 原作章节 + 自查要求
- **前章注入**：IF chapters/{N-1}.md 已存在 → 读取全文（超 3000 字取最后 1500 字）
- **邻章边界**（从 compress-plan.md 读取）：
  - 前章终止事件 ID / 本章起始·终止事件 ID / 后章起始事件 ID
- **防越界硬指令**（逐字包含在 Agent prompt 中）：
  ```
  【防重叠规则 - 强制执行】
  1. 前章内容已给出。你必须从前章结尾处自然接续，绝不重复前章事件。
  2. 你只负责本章事件 ID 列表中的事件，不得越界。
  3. 写到本章终止事件落地即止。不写余波——余波属于下一章。
  4. 前章不存在时，以简短过渡开始，不展开完整场景。
  ```

**并行模式下的特殊处理**：
- Agent 写作时**跳过** recent-context.md 更新（Agent 之间无法协调共享文件）
- Agent 写作时**跳过** 定期压缩（同理）
- Agent 写作时**跳过** meta.json 的 current_chapter 更新（防止写入竞争导致章号回退）
- **每批次完成后（注意顺序！）**：
  1. **相邻章重叠扫描**（在 context 重建之前！防止有问题的章节污染上下文）：
     FOR 本批次每个已写章节 chN：
       IF ch(N-1) 已存在：
         判定1（结构）：检查 chN 和 ch(N-1) 的核心事件 ID 是否重复占用
         判定2（文本）：比对 ch(N-1) 最后一个场景 与 chN 第一个场景
         IF 任一命中 → 标记 chN 为"需重写"
     冲突裁决：前章保留，后章重写
     重写时串行执行，注入前章全文 + 完整防越界指令 + 本章事件ID列表 + 邻章边界ID
     重写后复检最多 1 轮。仍冲突 → 立即降级串行模式完成剩余章节
     降级状态记录到 meta.json："parallel_mode": "degraded"
     恢复时检查：IF meta.json.parallel_mode == "degraded" → 直接使用串行模式
  2. 扫描 chapters/ 目录，找到从第 1 章起**连续存在**的最大章号
  3. 将 current_chapter 更新为该连续最大章号
  4. **重建 recent-context.md**：读取最近 10 章已写内容，提取摘要覆盖写入
  5. timeline.md 回填
  6. 执行滚动预算检查
  - 原因：如果中断发生在批次中间（如已写 6/8/10 但 7/9 未完成），恢复时从 current_chapter+1 继续不会跳过未完成章节
- 全部批次完成后，**必须执行一次全量记忆重建**
- **安全降级**：重叠重写后仍冲突 → 剩余章节全部转串行正文（审校/扫描仍可并行）
