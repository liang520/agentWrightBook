---
name: condense
description: 精炼指令 — 对已完成小说进行精炼压缩，保持内容不变、削减冗余至目标字数。全自动无人参与流水线：诊断→精炼→终验→修复。支持子命令：status/diagnose/write/continue/verify/fix/auto
user_invocable: true
---

# 精炼流程

## 全局规则

1. **全程自动，无人参与** — 所有阶段自动流转，不等待用户输入
2. **字数统计统一口径** — 遵循 CLAUDE.md "字数统计规范"（去空格、去 Markdown 标记后的字符数，含标点）
3. **不改编，只精炼** — 角色名、设定名、情节走向、因果链全部保持原样，仅精炼文字表达
4. **物理隔离** — 精炼稿存在 `novels/{name}-condensed/`，原书目录严格只读
5. **复用原书 config** — style.md、foreshadowing.md、character-map.md、setting-map.md 从原书只读引用，不复制
6. **写作阶段默认持续自动** — 检查点只汇报不暂停

## 原书文件访问权限

```
novels/{original-name}/        ← 整个目录严格只读
  config/*                     ← 只读引用（style.md, foreshadowing.md 等）
  context/*                    ← 只读（初始化时复制 memory-outline + archives）
  chapters/*                   ← 只读（Phase 2 每章读取原章作为精炼输入）
  meta.json                    ← 只读（Phase 1 读取元数据）

novels/{name}-condensed/       ← 所有写操作只发生在这里
  config/condense-plan.md、context/*、chapters/*、meta.json、verification-report.md
```

发现原书伏笔表有脏数据 → 只在 condense-plan.md 中标注，不修改原书。
更新记忆 → 只写自己的 recent-context.md，不动原书的。

## 子命令路由

| 用户输入 | 跳转 |
|---------|------|
| `/condense` | 自动检测（见下方算法） |
| `/condense status` | Phase 0：状态总览 |
| `/condense diagnose` | Phase 1：诊断 |
| `/condense write` / `continue` | Phase 2：逐章精炼 |
| `/condense verify` | Phase 3：终验 |
| `/condense fix` | Phase 4：修复 |
| `/condense auto` | 全自动：Phase 1 → 2 → 3 → 4 |

### 自动检测算法

扫描 `novels/` 下所有 `meta.json`，筛选 `mode: "condense"`：

```
优先级：writing→Phase2 | verifying→Phase3 | fixing→Phase4 | diagnosed→Phase2 | init→Phase1 | complete→Phase0 | 无项目→Phase0
多项目冲突：按 updated_at 降序取最近更新的。
```

---

## Phase 0：状态总览

扫描 `novels/` 下 `status: "complete"` 且 `mode` 为 `novel`/`short` 的项目，显示可精炼候选列表。同时显示进行中的精炼项目（如有）。提供选项：诊断新项目 / 继续进行中 / 全自动精炼。

---

## Phase 1：诊断

精确统计原稿字数 → 逐章 A/B/C/D 四级分级 → 分配目标字数 → 生成事件清单 → 写入精炼硬约束 → 伏笔表校准。

完成后创建 `novels/{name}-condensed/` 目录结构，写入 condense-plan.md 和 meta.json，更新 `status → "diagnosed"`。

详细诊断步骤见 [references/diagnose-steps.md](references/diagnose-steps.md)

**转场**：自动进入 Phase 2。

---

## Phase 2：逐章精炼重写

### 前置条件

meta.json `status` 为 `"diagnosed"` 或 `"writing"`

### 恢复逻辑

```
current = meta.json.current_chapter（0 表示尚未开始）
从第 current + 1 章开始
```

更新 `status → "writing"`

### 上下文加载顺序

每章精炼前加载（静默，不输出）：

```
1. novels/{name}-condensed/context/memory-outline.md     # 全书大纲
2. novels/{name}-condensed/context/recent-context.md      # 最近章节上下文
3. novels/{source_novel}/config/style.md                  # 风格（只读引用原书）
4. novels/{name}-condensed/config/condense-plan.md        # 本章策略+事件清单
5. novels/{source_novel}/chapters/{NNN}.md                # 原章内容
```

### 每章精炼流程（第 N 章）

**Step 1：读取策略** — 从 condense-plan.md 读取等级、目标字数、事件清单、精炼方向。

**Step 2：D 级跳过** — 等级 D 且目标=原字数 → 直接复制原章，跳到 Step 6。

**Step 3：精炼重写**

**A 级（重度精炼，砍 25%+）**：
- 环境描写：3-5 句铺排 → 1 句精准意象（保留首次出现的场景锚点）
- 战斗描写：删逐招回合流水账，保留"招式名 + 结果 + 旁观者反应"
- 心理活动：大段内心独白 → 1-2 句点睛（只保留转折点的心理）
- 对话：删零信息量来回，保留推动情节和展现性格的
- 重复信息：同一信息说了两遍的，只留更好的那遍

**B 级（中度精炼，砍 10-25%）**：
- 环境描写压缩但保留氛围感；删废话对话；适度压缩心理描写；合并过渡段

**C 级（轻度精炼，砍 5-10%）**：
- 仅做措辞精炼：长句拆短、删冗余形容词/副词，不动结构

**所有等级"绝不动"清单**：
- 事件清单中的每一条（情节推动、因果节点）
- 伏笔的埋设句和回收句
- 章尾钩子（最后 1-3 段）
- 角色的口头禅和标志性说话方式
- 情绪最高点/最低点的段落

**Step 4：事件清单自检** — 逐条确认事件清单要点在精炼稿中存在，缺失则补回。

**Step 5：字数检查** — 超目标 10%+ 则进一步精简；不足 85% 则适当恢复。

**Step 6：保存并更新** — 写入章节文件、追加 recent-context.md、更新 meta.json。

### 定期任务

**每 5 章（N % 5 == 0 且 N < total_chapters）：滚动预算检查**

注意：`N == total_chapters` 时跳过（避免除零）。

```
偏差率 = (已写总字数 - 预期进度字数) / 预期进度字数

超预算 >+5%：
  → 剩余平均目标 < 原字数×0.60 → 回头精简超标最多的2-3章
  → 否则 → 更新后续章节目标
严重不足 <-10%：上调后续目标（不超原字数）
-10%~+5%：正常，不调整
```

**每 10 章（N % 10 == 0）：记忆压缩归档 + 检查点汇报**

归档 recent-context → archives/stage-{N}.md，重建 memory-outline.md，输出进度汇报（累计字数、偏差率、各等级削减概况）。

### 写作结束条件

```
当 current_chapter == total_chapters：
1. 总字数校验：超标5%+→逐章精简；不足5%+→恢复内容
2. 强制记忆重建
3. status → "verifying"，自动进入 Phase 3
```

---

## Phase 3：终验（9 维度）

总字数 → 伏笔完整性 → 情绪曲线 → A/B对照抽检 → 因果链完整性 → 跨章状态一致性 → 数值链闭合 → 原作名子串扫描。

结果写入 `novels/{name}-condensed/verification-report.md`。全部 PASS → `status → "complete"`；有 FAIL → `status → "fixing"` → Phase 4。

详细维度见 [references/condense-verification.md](references/condense-verification.md)

---

## Phase 4：修复

读取 `verification-report.md`，按问题类型处理：

| 问题 | 修复策略 |
|------|---------|
| 总字数超标 | 按超标比例降序逐章精简（A级手法），直到 ≤ target×1.05 |
| 总字数不足 | 找精简最狠的章节恢复内容，直到 ≥ target×0.95 |
| 伏笔遗漏 | 从原稿定位段落，在精炼稿对应位置补回 |
| 因果链断裂 | 补充衔接过渡段，确认前后文逻辑通顺 |
| 情绪曲线减弱 | 恢复被删的铺垫/渲染段落 |

修复后重新终验。最多 3 轮；3 轮仍有 FAIL → 标注"部分未解决"+ warning。

**完成后（无论终验直接 PASS 还是修复后通过）**：
1. 素材自动回流（必执行，不可跳过）：读取 [../shared/material-reflow.md](../shared/material-reflow.md) 并按流程执行。本 Skill 只扫描 styles/ 和 tropes/。汇报回流结果。
2. 更新 `status → "complete"`

---

## meta.json 字段定义

```json
{
  "title": "string — 精炼版书名",
  "source_novel": "string — 原书路径",
  "mode": "condense",
  "status": "init|diagnosed|writing|verifying|fixing|complete",
  "original_total_words": "number",
  "target_total_words": "number",
  "current_chapter": "number（0=未开始）",
  "total_chapters": "number",
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

## 中断恢复

基于 meta.json 的 `status` + `current_chapter` 自动恢复：init→Phase1 | diagnosed→Phase2(ch1) | writing→Phase2(ch+1) | verifying→Phase3 | fixing→Phase4 | complete→显示状态。每次新会话执行 `/condense` 即可。

---

## 绝对禁止事项

1. **绝不修改原书目录** `novels/{original-name}/` 下的任何文件
2. **绝不改变角色名、设定名、情节走向** — 精炼是文字层面的，不是内容层面的
3. **绝不删除事件清单中的任何要点** — 事件清单是精炼的底线
4. **绝不跳过事件清单自检** — 每章精炼后必须逐条核对
5. **绝不让总字数偏离目标超过 ±5%** — 超出则必须在 Phase 2 结束条件或 Phase 4 中修复
