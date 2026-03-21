---
name: compress
description: 压缩指令 — 对已完成小说进行大幅压缩（可合并章节、删支线），保持角色名和设定名不变。全自动无人参与流水线：分析→规划→写作→终验→修复。支持子命令：status/analyze/plan/write/continue/verify/fix/auto
user_invocable: true
---

# 压缩流程（压缩不改编）

## 全局规则

1. **全程自动，无人参与** — 所有阶段自动流转，不等待用户输入
2. **字数统计统一口径** — 所有涉及"字数"的统计均遵循 CLAUDE.md "字数统计规范"（去空格、去 Markdown 标记后的字符数，含标点）
3. **不改编，只压缩** — 角色名、设定名、世界观全部保持原样，不建 character-map / setting-map
4. **可合并章节、可删支线** — 与 `/condense` 的核心区别
5. **物理隔离** — 压缩稿存 `novels/{name}-compressed/`，原书目录严格只读
6. **复用原书 config** — style.md 只读引用；foreshadowing.md 复制后重映射章号
7. **写作阶段默认持续自动** — 检查点只汇报不暂停

## 原书文件访问权限

```
novels/{original-name}/           ← 整个目录严格只读
  config/*                        ← 只读引用（style.md 等）
  context/*                       ← 只读（初始化时复制 memory-outline）
  chapters/*                      ← 只读（Phase 3 每章读取原章作为输入）
  meta.json                       ← 只读

novels/{name}-compressed/         ← 所有写操作只发生在这里
  config/
    compress-plan.md              ← 写（压缩映射表 + 事件清单 + 伏笔重映射）
    foreshadowing.md              ← 写（从原书复制后重映射章号）
  context/
    memory-outline.md             ← 写（从事件清单重建，写作中每10章重建）
    recent-context.md             ← 写（空文件，逐章重建）
    archives/                     ← 写（从头建，每10章归档）
  chapters/                       ← 写（压缩后的章节）
  meta.json                       ← 写
  verification-report.md          ← 写
```

发现原书伏笔表有脏数据 → 只在 compress-plan.md 中标注，不修改原书 foreshadowing.md。
更新记忆 → 只写自己的 recent-context.md，不动原书的。

## 子命令路由

从用户消息中提取子命令，按下表路由：

| 用户输入 | 跳转 |
|---------|------|
| `/compress` | 自动检测（见下方算法） |
| `/compress status` | Phase 0：状态总览 |
| `/compress analyze` | Phase 1：分析 |
| `/compress plan` | Phase 2：压缩规划 |
| `/compress write` / `continue` | Phase 3：逐章压缩写作 |
| `/compress verify` | Phase 4：终验 |
| `/compress fix` | Phase 5：修复 |
| `/compress auto` | 全自动：Phase 1 → 2 → 3 → 4 → 5 |

### 自动检测算法

扫描 `novels/` 下所有 `meta.json`，筛选 `mode: "compress"`：

```
优先级（从高到低）：
1. status == "writing"    → Phase 3（从 current_chapter + 1 继续）
2. status == "verifying"  → Phase 4（重新执行终验）
3. status == "fixing"     → Phase 5（重新读取 verification-report.md 执行修复）
4. status == "planned"    → Phase 3（从第 1 章开始写作）
5. status == "analyzed"   → Phase 2（从压缩规划开始）
6. status == "init"       → Phase 1（从头开始分析）
7. status == "complete"   → Phase 0（显示完成状态）
8. 无 compress 项目       → Phase 0（显示可压缩的候选小说）

多项目冲突处理：如果同一优先级下有多个项目，按 updated_at 降序取最近更新的。
```

### 状态机

```
init → analyzed → planned → writing → verifying → fixing → complete
```

---

## Phase 0：状态总览

显示两个面板：

**面板 A — 可压缩的已完成小说**：
扫描 `novels/` 下 `status: "complete"` 且 `mode` 为 `novel`、`short` 或 `condense` 的项目。

```
═══ 可压缩候选 ═══
1. 全球异变（novel，45章，~95226字）
2. 寒渊觉醒（short，37章，~55650字）
═══════════════════
```

**面板 B — 进行中的压缩项目**（如有）：
```
═══ 压缩项目 ═══
- 全球异变-压缩版：写作中，12/25章
═══════════════
```

**操作选项**：
```
请选择：
1. 分析新项目（选择候选 → Phase 1）
2. 继续进行中的项目（→ 自动检测）
3. 全自动压缩（选择候选 → Phase 1~5 全自动）
```

---

## Phase 1-2：分析 + 压缩规划

Phase 1 逐章分析原稿（章节功能标注、骨架提取、事件清单、伏笔校准），输出 compress-plan.md 分析部分。
Phase 2 生成压缩映射表、字数预算分配、伏笔重映射、记忆大纲重建，并由独立 Agent 执行 6 项校验。
完成后 `status → "planned"`，自动进入 Phase 3。

详细流程见 [references/compress-planning.md](references/compress-planning.md)

---

## Phase 3：逐章压缩写作

按 compress-plan.md 映射表逐章压缩重写（保留/精炼、合并、浓缩三种策略），每章执行事件清单自检和字数检查。
每 5 章滚动预算检查，每 10 章记忆压缩归档。支持并行写作（相邻章不同批）。
写完全部章节后执行总字数校验，`status → "verifying"`，自动进入 Phase 4。

详细流程见 [references/compress-writing.md](references/compress-writing.md)

---

## Phase 4：终验（12 维度）

12 维度检查：总字数、章节完整性、伏笔完整性、因果链、情绪曲线、原作覆盖率、风格一致性、A/B 对照、原作名子串扫描、跨章状态一致性、数值链闭合、伏笔回收质量评估。
输出 verification-report.md；有 FAIL → `status → "fixing"` → 进入 Phase 5。全部 PASS → 执行素材自动回流（必执行：读取 [../shared/material-reflow.md](../shared/material-reflow.md) 并按流程执行，只扫描 styles/ 和 tropes/，汇报结果）→ `status → "complete"`。

详细维度见 [references/compress-verification.md](references/compress-verification.md)

---

## Phase 5：修复

### 前置条件

meta.json `status` 为 `"fixing"`

### 修复逻辑

读取 `verification-report.md`，按问题类型处理：

**1. 总字数超标**：
```
→ 按超标比例从高到低排序各章
→ 优先处理超标 >20% 的章节
→ 精简策略同 Phase 3 的浓缩手法
→ 每修一章重新统计总字数
→ 直到总字数 ≤ target_total
```

**2. 总字数不足**：
```
→ 找到压缩最狠的几章
→ 适当恢复环境描写或对话细节
→ 每修一章重新统计
→ 直到总字数 ≥ target_total × 0.95
```

**3. 伏笔遗漏**：
```
→ 定位遗漏的伏笔在原稿中的具体段落
→ 在压缩稿对应位置补回（用压缩后的风格改写）
→ 补回后重新检查该章字数，如超标则精简其他部分
```

**4. 因果链断裂**：
```
→ 定位断裂的因果链两端
→ 在压缩稿中补充衔接（可能需要恢复被删的过渡段）
→ 确认前后文逻辑通顺
```

**5. 情绪曲线问题**：
```
→ 定位情绪减弱的章节
→ 适当恢复被删的铺垫/渲染段落
→ 如超字数则从同章其他位置精简
```

**6. 覆盖率不足**：
```
→ 定位缺失的核心事件
→ 在对应新章中补回
→ 如超字数则精简同章其他冗余内容
```

**修复完成后**：
```
重新执行 Phase 4 终验
IF 仍有 FAIL 且修复轮次 < 3：
  → 继续修复
IF 修复轮次 == 3 且仍有 FAIL：
  → 输出最终报告，标注"部分问题未解决"
ELSE：
  → 更新 verification-report.md
素材自动回流（必执行，不可跳过）：
  读取 ../shared/material-reflow.md 并按流程执行
  本 Skill 扫描范围：styles/ + tropes/
  汇报回流结果（新增了哪些素材）
status → "complete"
```

---

## 记忆压缩

见 [../shared/memory-compress.md](../shared/memory-compress.md)

---

## 中断恢复机制

基于 `meta.json` 的 `status` 和 `current_chapter` 字段自动恢复：

| status | 恢复到 | 恢复行为 |
|--------|--------|---------|
| `writing` | Phase 3 | 从 `current_chapter + 1` 继续写作 |
| `verifying` | Phase 4 | 重新执行终验 |
| `fixing` | Phase 5 | 重新读取 verification-report.md 执行修复 |
| `planned` | Phase 3 | 从第 1 章开始写作 |
| `analyzed` | Phase 2 | 从压缩规划开始 |
| `init` | Phase 1 | 从头开始分析 |
| `complete` | Phase 0 | 显示完成状态 |

每次新会话执行 `/compress` 即可自动检测并恢复。

---

## meta.json 字段定义

```json
{
  "title": "string — 压缩版书名",
  "source_novel": "string — 原书路径（如 novels/global-anomaly）",
  "mode": "compress",
  "status": "init|analyzed|planned|writing|verifying|fixing|complete",
  "original_total_words": "number — 原稿总字数（统一口径）",
  "target_total_words": "number — 目标总字数",
  "original_chapters": "number — 原作章数",
  "compressed_chapters": "number — 压缩后章数",
  "current_chapter": "number — 已完成的最后一章（0=未开始）",
  "created_at": "string — 创建日期",
  "updated_at": "string — 最近更新日期"
}
```

---

## 绝对禁止事项

1. **绝不修改原书目录** `novels/{original-name}/` 下的任何文件（章节、config、context、meta.json）
2. **绝不改变角色名和设定名** — 压缩不是改编
3. **绝不删除主线事件** — 事件清单是底线
4. **绝不跳过事件清单自检** — 每章写完必须逐条核对
5. **绝不丢失伏笔** — 被删除章节的伏笔必须迁移到保留章
6. **绝不让总字数超过目标** — 硬上限 ≤ target_words，下限 ≥ target_words × 0.95
