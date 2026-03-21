# 短篇改编创建模板

> 创建一本短篇改编时，按此模板在 novels/{novel-name}/ 下创建文件。

## 目录结构
```
novels/{novel-name}/
├── meta.json
├── config/
│   ├── plot-skeleton.md       # 情节骨架（短篇专属）
│   ├── compression-map.md     # 压缩映射表（短篇专属）
│   ├── character-map.md       # 角色映射表 + 性格档案
│   ├── setting-map.md         # 设定映射表
│   ├── style.md               # 风格定调（含系统提示词）
│   └── foreshadowing.md       # 伏笔追踪表
├── context/                   # 三层记忆系统
│   ├── memory-outline.md
│   ├── recent-context.md
│   └── archives/
└── chapters/
```

## meta.json 格式

注：所有字数字段（target_words、budget_words、source_words）统计口径见 CLAUDE.md "字数统计规范"（去空格去 Markdown 标记）。

```json
{
  "title": "新小说标题",
  "source": "sources/{source-name}",
  "genre": "题材",
  "style": "library/styles/{style-name}.md",
  "world": "library/worlds/{world-name}.md",
  "mode": "short",
  "status": "analyzing|planning|configuring|writing|verifying|fixing|complete",
  "target_words": 50000,
  "budget_words": 47500,
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

## plot-skeleton.md 格式

```markdown
# 情节骨架

## 原作概况
- 原作：{source_title}
- 总章数：{N}章
- 总字数：{N}字
- 目标字数：45000-50000字（硬上限 50000，统计口径见 CLAUDE.md "字数统计规范"）

## 主线弧线
1. 【起】第X-Y章：{开局描述}
2. 【承】第X-Y章：{发展描述}
3. 【转】第X-Y章：{转折描述}
4. 【合】第X-Y章：{高潮+结局描述}

## 保留支线
| 支线名称 | 涉及章节 | 与主线的关联 | 保留理由 |
|---------|---------|-------------|---------|

## 删除/弱化支线
| 支线名称 | 涉及章节 | 处理方式 | 理由 |
|---------|---------|---------|------|

## 角色保留清单
| 角色 | 处理方式 | 理由 |
|------|---------|------|

## 伏笔链完整性检查
| 伏笔 | 埋设章 | 回收章 | 压缩后保留？ | 处理 |
|------|--------|--------|-------------|------|
```

## compression-map.md 格式

```markdown
# 压缩映射表

## 压缩参数
- 原作字数：{source_words}
- 目标字数：45000-50000字（硬上限 50000）
- 分配预算：{budget_words} 字（= 50000 × 0.95，预留 5% 余量）（统计口径见 CLAUDE.md "字数统计规范"）
- 压缩比：{ratio}:1
- 新作章数：{chapters}章
- 平均单章字数：约{avg}字（基于分配预算计算）

## 映射表

| 新作章 | 对应原作章 | 压缩策略 | 目标字数 | 核心保留内容 |
|--------|-----------|---------|---------|------------|
| 第1章 | 原1-2章 | 合并 | 1500 | ... |
| ... | ... | ... | ... | ... |

**合计目标字数：{total} 字（硬上限 50000）**
```

## 其他文件格式

character-map.md、setting-map.md、foreshadowing.md、三层记忆系统均与 `docs/novel-template.md` 和 `docs/memory-template.md` 一致。
