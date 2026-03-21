# 压缩创建模板

> 对已完成小说进行大幅压缩（可合并章节、删支线）时，按此模板在 `novels/{novel-name}-compressed/` 下创建文件。

## 目录结构

```
novels/{novel-name}-compressed/
├── meta.json                  # 压缩项目元数据
├── config/
│   ├── compress-plan.md       # 压缩计划（分析+映射表+事件清单+伏笔重映射）
│   └── foreshadowing.md       # 伏笔追踪表（从原书复制后重映射章号）
├── context/                   # 三层记忆系统
│   ├── memory-outline.md      # 从事件清单重建（非简单复制）
│   ├── recent-context.md      # 空文件，逐章重建
│   └── archives/              # 从头建，每10章归档
├── chapters/                  # 压缩后的章节
└── verification-report.md     # 终验报告（Phase 4 生成）
```

## meta.json 格式

注：所有字数字段统计口径见 CLAUDE.md "字数统计规范"（去空格去 Markdown 标记，含标点）

```json
{
  "title": "{原书名}-压缩版",
  "source_novel": "novels/{original-name}",
  "mode": "compress",
  "status": "init",
  "original_total_words": 0,
  "target_total_words": 50000,
  "original_chapters": 0,
  "compressed_chapters": 0,
  "current_chapter": 0,
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

## compress-plan.md 格式

```markdown
# 压缩计划 — {title}

## 压缩参数
- 原书：novels/{source_novel}
- 原稿总字数：{original_total}（统计口径见 CLAUDE.md "字数统计规范"）
- 目标总字数：{target_total}
- 需削减字数：{cut_total}
- 原作章数：{original_chapters}
- 压缩后章数：{compressed_chapters}

## 章节分析表

| 章号 | 原字数 | 功能 | 可压缩度 | 依赖关系 | 伏笔 | 可删除 |
|------|--------|------|---------|---------|------|--------|
| 1    | 2100   | 主线推进 | B | 被ch3依赖 | 埋F01 | 否 |
| ...  | ...    | ...  | ...     | ...     | ...  | ...    |

## 骨架

### 主线弧线
1. 【起】第X-Y章：{描述}
2. 【承】第X-Y章：{描述}
3. 【转】第X-Y章：{描述}
4. 【合】第X-Y章：{描述}

### 支线清单
| 支线名称 | 涉及章节 | 关联度 | 取舍建议 |
|---------|---------|--------|---------|

### 角色出场清单
| 角色 | 首次出场 | 关键章节 | 可删除 |
|------|---------|---------|--------|

## 压缩映射表

| 新章号 | 对应原作章 | 压缩策略 | 目标字数 | 核心保留事件 |
|--------|-----------|---------|---------|------------|
| 1 | 原1-3章 | 合并+精炼 | 1500 | 事件A、事件B |
| - | 原6章 | 删除 | - | （支线，无依赖） |

**合计目标字数：{budget_total} 字（硬上限：{target_total}）**

## 事件清单

### 新章1（对应原作第1-3章）
1. [事件要点]
2. [事件要点]
...

### 新章2（对应原作第4-5章）
...

## 压缩硬约束
1. 不改变任何角色名和设定名
2. 不改变情节走向和因果链
3. 不删除任何伏笔的埋设和回收句
4. 不改变角色性格和说话方式（保留口头禅、标志性语气）
5. 保持每章的章尾钩子
6. 保持风格一致（遵循原书 style.md）

## 校准后伏笔状态表（重映射后）

| 编号 | 伏笔内容 | 原埋设章 | 新埋设章 | 原回收章 | 新回收章 | 校准状态 | 备注 |
|------|---------|---------|---------|---------|---------|---------|------|
| F01  | ...     | 1       | 1       | 15      | 8       | 已确认   |      |
| F02  | ...     | 6       | 3       | 32      | 18      | 已迁移   | 原ch6被删，埋设迁移到新ch3 |
```

## 复用的原书文件

压缩只读引用原书的以下文件（不复制）：

| 文件 | 原书路径 | 用途 |
|------|---------|------|
| style.md | `novels/{original}/config/style.md` | 风格一致性参照 |

以下文件从原书复制后重映射/重建（存在压缩版目录中）：

| 文件 | 压缩版路径 | 说明 |
|------|-----------|------|
| foreshadowing.md | `novels/{name}-compressed/config/foreshadowing.md` | 章号重映射后的版本 |
| memory-outline.md | `novels/{name}-compressed/context/memory-outline.md` | 从事件清单重建 |

**重要**：所有原书文件严格只读，压缩过程中发现的问题只记录在 compress-plan.md 中。
