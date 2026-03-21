# Phase 1 诊断 — 详细步骤

## 前置条件

- 用户指定或自动选择一本 `status: "complete"` 的小说（记为 `source_novel`）

## Step 1：精确统计

按 CLAUDE.md "字数统计规范"逐章统计字数：

```
遍历 novels/{source_novel}/chapters/*.md
每章：读取全文 → 去除 Markdown 标记 → 去除所有空白字符 → 计算字符数
汇总：original_total = 各章字数之和
```

确定目标字数（`target_total`）：
- `/condense auto` 模式：自动采用默认值 50000，不等待用户输入
- 非 auto 模式（如 `/condense diagnose`）：提示用户确认，默认 50000

计算需削减总量 = `original_total - target_total`。

如果 `original_total ≤ target_total`：提示"原稿字数已在目标范围内，无需精炼"，终止。

## Step 2：逐章 A/B/C/D 四级分级

逐章阅读，根据内容密度和可精炼程度评定等级：

| 等级 | 定义 | 典型特征 | 压缩幅度 |
|------|------|---------|---------|
| A 高度可精炼 | 大量冗余内容 | 铺排式环境描写、逐招战斗流水账、重复信息、灌水对话 | 砍 25%+ |
| B 中度可精炼 | 有一定精简空间 | 描写偏长但有价值、部分废话对话、过长心理独白 | 砍 10-25% |
| C 轻度可精炼 | 基本紧凑 | 措辞可以更精炼，但结构和内容密度合理 | 砍 5-10% |
| D 不可精炼 | 已经非常精炼 | 高密度情节、关键转折、高潮对决、字数已 <1000 | 0%（原样保留） |

## Step 3：分配目标字数

```
1. D 级章节：target = original（不动）
2. C 级章节：target = original × 0.95（最多砍 5%）
3. 计算 D/C 级未消化的削减量 = 需削减总量 - D级削减(0) - C级削减
4. 将未消化量按 A:B = 6:4 的比例分配
5. A 级章节按比例分摊较多削减量
6. B 级章节按比例分摊较少削减量
7. 硬约束：任何章节 target ≥ original × 0.60（避免过度压缩）
8. 如果硬约束导致分配不完，上调 C 级的削减比例（从 5% 到 10%）
9. 验证：所有章节 target 之和 = target_total（允许 ±1%）
```

## Step 4：生成事件清单

逐章提取 3-8 个要点，作为 Phase 2 精炼时的"不可删除清单"：

- 关键事件（推动情节的动作/决策）
- 角色关系变化（结盟/反目/暴露身份）
- 伏笔埋设/回收点
- 因果节点（A 导致 B 的关键连接）
- 情绪转折点
- 章尾钩子

## Step 5：写入精炼硬约束

以下 6 条写入 condense-plan.md，Phase 2 每章精炼时必须加载：

```
1. 不改变任何角色名和设定名
2. 不改变情节走向和因果链
3. 不删除任何伏笔的埋设和回收句
4. 不改变角色性格和说话方式（保留口头禅、标志性语气）
5. 保持每章的章尾钩子
6. 保持风格一致（遵循原书 style.md 的系统提示词）
```

## Step 6：伏笔表校准

```
0. 空表检测：读取原书 foreshadowing.md
   IF 文件存在但无数据行（只有表头）：
     → 检查原书 memory-outline.md 的"活跃伏笔列表"
     → IF memory-outline 有伏笔条目：
       → 从 memory-outline + 章节扫描回填 foreshadowing.md（写入原书目录的一个临时副本到 condense-plan.md 中，不修改原书文件）
       → 在 condense-plan.md 中标注"原书伏笔表为空，已从 memory-outline 回填 {N} 条"
     → IF memory-outline 也无伏笔：
       → 标注"原书无伏笔记录"，后续伏笔校验标记 N/A
1. 读取原书 foreshadowing.md（或回填后的版本）
2. 逐条在实际章节中搜索确认：
   - 埋设事件是否在标注的章节中存在
   - 回收事件是否在标注的章节中存在
3. 标记脏数据（表中有记录但章节中找不到对应内容）
4. 生成校准后的伏笔状态表，写入 condense-plan.md
```

## 输出

**创建目录结构**：

```
novels/{name}-condensed/
├── meta.json
├── config/
│   └── condense-plan.md
├── context/
│   ├── memory-outline.md     ← 从原书复制（故事走向不变，大纲适用）
│   ├── recent-context.md     ← 空文件（精炼后逐章重建）
│   └── archives/             ← 从原书复制（历史归档仍准确）
└── chapters/                 ← 空（Phase 2 逐章写入）
```

**condense-plan.md 格式**：

```markdown
# 精炼计划 — {title}

## 精炼参数
- 原书：novels/{source_novel}
- 原稿总字数：{original_total}（统计口径见 CLAUDE.md）
- 目标总字数：{target_total}
- 需削减字数：{cut_total}
- 总章数：{total_chapters}

## 逐章分级与目标

| 章号 | 原字数 | 等级 | 目标字数 | 削减量 | 主要精炼方向 |
|------|--------|------|---------|--------|------------|
| 1    | 1509   | B    | 1280    | 229    | 环境描写+心理 |
| ...  | ...    | ...  | ...     | ...    | ...         |

**合计目标字数：{target_total}**

## 事件清单

### 第1章
1. [事件要点1]
2. [事件要点2]
...

### 第2章
...

## 精炼硬约束
1. 不改变任何角色名和设定名
2. 不改变情节走向和因果链
3. 不删除任何伏笔的埋设和回收句
4. 不改变角色性格和说话方式（保留口头禅、标志性语气）
5. 保持每章的章尾钩子
6. 保持风格一致（遵循原书 style.md）

## 校准后伏笔状态表
（从 foreshadowing.md 对账后的结果）
```

**meta.json**：

```json
{
  "title": "{原书名}-精炼版",
  "source_novel": "novels/{original-name}",
  "mode": "condense",
  "status": "diagnosed",
  "original_total_words": 55650,
  "target_total_words": 50000,
  "current_chapter": 0,
  "total_chapters": 37,
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

更新 `status → "diagnosed"`。

**转场**：自动进入 Phase 2。
