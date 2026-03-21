# 精炼创建模板

> 对已完成小说进行精炼压缩时，按此模板在 `novels/{novel-name}-condensed/` 下创建文件。

## 目录结构

```
novels/{novel-name}-condensed/
├── meta.json                  # 精炼项目元数据
├── config/
│   └── condense-plan.md       # 精炼计划（诊断阶段生成）
├── context/                   # 三层记忆系统
│   ├── memory-outline.md      # 从原书复制（故事走向不变）
│   ├── recent-context.md      # 空文件，逐章重建
│   └── archives/              # 从原书复制（历史归档）
└── chapters/                  # 精炼后的章节
```

## meta.json 格式

注：所有字数字段统计口径见 CLAUDE.md "字数统计规范"（去空格去 Markdown 标记，含标点）

```json
{
  "title": "{原书名}-精炼版",
  "source_novel": "novels/{original-name}",
  "mode": "condense",
  "status": "init",
  "original_total_words": 0,
  "target_total_words": 50000,
  "current_chapter": 0,
  "total_chapters": 0,
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD"
}
```

## condense-plan.md 格式

```markdown
# 精炼计划 — {title}

## 精炼参数
- 原书：novels/{source_novel}
- 原稿总字数：{original_total}（统计口径见 CLAUDE.md "字数统计规范"）
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
1. [事件要点]
2. [事件要点]
...

## 精炼硬约束
1. 不改变任何角色名和设定名
2. 不改变情节走向和因果链
3. 不删除任何伏笔的埋设和回收句
4. 不改变角色性格和说话方式（保留口头禅、标志性语气）
5. 保持每章的章尾钩子
6. 保持风格一致（遵循原书 style.md）

## 校准后伏笔状态表

| 编号 | 伏笔内容 | 埋设章 | 回收章 | 校准状态 | 备注 |
|------|---------|--------|--------|---------|------|
| F01  | ...     | 1      | 2      | 已确认   |      |
| F02  | ...     | 1      | 32     | 脏数据   | 章节中未找到 |
```

## 复用的原书文件

精炼不创建独立的 config 文件，而是直接只读引用原书的：

| 文件 | 原书路径 | 用途 |
|------|---------|------|
| style.md | `novels/{original}/config/style.md` | 风格一致性参照 |
| foreshadowing.md | `novels/{original}/config/foreshadowing.md` | 伏笔校准基准 |
| character-map.md | `novels/{original}/config/character-map.md` | 角色自检参考 |
| setting-map.md | `novels/{original}/config/setting-map.md` | 设定自检参考 |

**重要**：所有原书文件严格只读，精炼过程中发现的问题只记录在 condense-plan.md 中。
