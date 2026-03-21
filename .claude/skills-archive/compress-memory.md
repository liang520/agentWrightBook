---
name: compress-memory
description: 记忆压缩 — 将最近章节归档，重建全书记忆大纲。每10章自动触发，也可手动调用。
user_invocable: true
---

# 记忆压缩

## 触发条件
- **自动触发**：`/write-chapter` 或 `/batch-write` 在写完第10、20、30...章时自动调用
- **手动触发**：用户直接执行 `/compress-memory`

## 交互规则
**自动触发时不需要用户交互，静默执行后汇报结果。手动触发时以选择题确认。**

## 执行步骤

### 1. 确定小说
如果有多本小说，展示选择题（手动触发时）：
```
请选择要压缩记忆的小说：
1. 都市逆袭王（当前第50章）
2. 校园甜宠记（当前第20章）
```
自动触发时直接使用当前正在写的小说。

### 2. 检查压缩范围
- 读取 `novels/{novel-name}/meta.json` 获取 current_chapter
- 读取 `novels/{novel-name}/context/recent-context.md` 获取当前记录的章节范围
- 确定需要归档的章节范围（最早的10章）

### 3. 生成阶段归档
- 读取 `recent-context.md` 中需要归档的10章内容
- 压缩为不超过500字的摘要，格式参照 `docs/memory-template.md` 中的归档格式
- 写入 `novels/{novel-name}/context/archives/stage-{NNN}-{NNN}.md`

压缩时需要保留的信息（优先级从高到低）：
1. 影响后续剧情的关键事件（不能丢）
2. 角色状态/关系的变化（不能丢）
3. 伏笔的埋设和回收（不能丢）
4. 新确立的世界规则（不能丢）
5. 具体的对话和场景细节（可以丢，只保留结果）

### 4. 清理 recent-context.md
- 移除已归档的章节记录
- 保留最近10章的详细记录

### 5. 重建 memory-outline.md
- 读取所有 `archives/stage-*.md` 文件
- 读取当前 `recent-context.md`
- 读取 `config/foreshadowing.md` 中的活跃伏笔
- 综合提炼为不超过2000字的全书记忆大纲
- 覆盖写入 `novels/{novel-name}/context/memory-outline.md`

memory-outline.md 必须包含：
- 故事进展摘要（从第1章到当前的整体走向）
- 关键转折点列表
- 当前局势描述
- 核心角色状态表
- 活跃伏笔列表
- 已建立的世界规则

### 6. 汇报结果
```
📦 记忆压缩完成
──────────────
归档范围：第{start}-{end}章 → archives/stage-{NNN}-{NNN}.md
归档大小：{X}字（压缩前{Y}字）
当前记忆窗口：第{start2}-{end2}章（recent-context.md）
全书大纲：{Z}字（memory-outline.md）
活跃伏笔：{N}个

1. ✅ 继续写作
2. 📖 查看归档内容
3. 📖 查看记忆大纲
```
