---
name: novel-status
description: 查看所有小说和原作的当前状态与进度
user_invocable: true
---

# 查看项目状态

## 交互规则
**展示完状态后，必须以编号选择题提供下一步操作选项。**

## 执行步骤

### 1. 扫描原作库
读取 `sources/` 下所有子目录的 `meta.json`，汇总：

```
📚 原作素材库
──────────────
1. {source-name}: {title} | {total_chapters}章 | 状态: {status}
2. ...
（如果为空：暂无原作素材）
```

### 2. 扫描小说库
读取 `novels/` 下所有子目录的 `meta.json`，汇总：

```
✏️ 小说创作进度
──────────────
1. {novel-name}: {title}
   参考原作: {source}
   进度: {current_chapter}/{total_chapters} ({百分比}%)
   状态: {status}
   最后更新: {updated_at}
2. ...
（如果为空：暂无创作中的小说）
```

### 3. 展示全局素材库统计
```
📦 全局素材库
──────────────
角色原型: {N}种（library/archetypes/）
世界观模板: {N}种（library/worlds/）
风格模板: {N}种（library/styles/）
情节桥段: {N}种（library/tropes/）
```

### 4. 提供下一步操作
```
你想做什么？
1. 导入并分析新原作（/analyze-source）
2. 基于原作创建新小说（/new-novel）
3. 继续写某本小说（/write-chapter）
4. 批量写作（/batch-write）
5. 审校章节（/review-chapter）
6. 不做了，看看就好
```
