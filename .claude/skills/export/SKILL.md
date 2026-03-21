---
name: export
description: 成品导出指令 — 合并章节为单文件、生成发布素材（书名+简介+封面提示词）、复制到剪贴板。用法：/export {小说名} [格式]
user_invocable: true
---

# 成品导出流程

## 全局规则

1. **字数统计统一口径** — 遵循 CLAUDE.md "字数统计规范"（去空格、去 Markdown 标记后的字符数，含标点）
2. **只导出已完成的小说** — status 必须为 "complete"

## 用法

```
/export {小说名}              → 默认导出为 md 格式
/export {小说名} md           → 导出为 Markdown 格式
/export {小说名} txt          → 导出为纯文本格式（去 Markdown 标记）
/export {小说名} clipboard    → 复制到剪贴板（纯文本格式）
/export {小说名} all          → 同时生成 md + txt + 发布素材
```

小说名为 `novels/` 下的目录名（如 `frost-awakening`、`frost-awakening-condensed`、`global-anomaly-compressed`）。

## 核心流程

### Step 1：验证小说状态

```
1. 从用户消息中提取小说名参数和可选的格式参数
2. 读取 novels/{小说名}/meta.json
3. 验证 status == "complete"
   → 如果不是 "complete"：提示"该小说尚未完成（当前状态：{status}），请先完成写作和校验"，终止
4. 读取 meta.json 中的 title、total_chapters（或 compressed_chapters）等基本信息
5. 确定格式参数（默认 md）
```

### Step 2：合并全部章节

```
1. 扫描 novels/{小说名}/chapters/ 下所有 .md 文件
2. 按文件名数字顺序排序（001.md, 002.md, ..., NNN.md）
3. 验证章节连续性（无遗漏）
4. 逐章读取内容
5. 合并为单个文件：
   - 首行：# {书名}（从 meta.json 的 title 字段读取）
   - 空行
   - 各章内容之间以空行分隔
   - 保留每章的 # 标题行
```

### Step 3：生成发布素材

```
1. 读取合并后的全文内容（或至少前 10 章 + 后 3 章 + config 文件）
2. 读取 config/ 下的相关文件（style.md、character-map.md 等，如存在）

3. 生成 5 个候选书名：
   - 基于小说的核心冲突、主角特质、世界观特色
   - 风格要求：抓眼球、有悬念感、适合网文平台
   - 每个书名附带一句推荐理由

4. 生成简介（200 字以内）：
   - 开头用悬念或冲突钩住读者
   - 点出主角身份和核心矛盾
   - 暗示故事走向但不剧透
   - 结尾留悬念
   - 风格匹配小说本身的语言调性

5. 生成封面提示词（英文，适用于 Midjourney/DALL-E）：
   - 描述核心视觉元素（主角形象、关键场景、氛围）
   - 风格关键词（如 cinematic, dark fantasy, anime style 等）
   - 色调和构图建议
   - 格式示例：
     "A [character description] standing in [scene], [action/pose], [atmosphere], [art style], [color palette], --ar 2:3 --v 6"
```

### Step 4：输出文件

根据用户指定的格式输出：

**md 格式**：
```
1. 创建 novels/{小说名}/export/ 目录（如不存在）
2. 写入 novels/{小说名}/export/full.md
   - 内容：合并后的完整 Markdown 文本
3. 写入 novels/{小说名}/export/publish-materials.md
   - 内容：候选书名 + 简介 + 封面提示词
```

**txt 格式**：
```
1. 创建 novels/{小说名}/export/ 目录（如不存在）
2. 对合并后的文本执行去 Markdown 标记处理：
   - 去除 # 标题标记（保留标题文字）
   - 去除 **粗体**、*斜体* 标记（保留内容文字）
   - 去除 > 引用标记
   - 去除 - 列表标记
   - 去除 ``` 代码块标记
   - 去除 [链接](url) 格式（保留链接文字）
   - 去除 | 表格标记
3. 写入 novels/{小说名}/export/full.txt
4. 写入 novels/{小说名}/export/publish-materials.txt（同样去 Markdown 标记）
```

**clipboard 格式**：
```
1. 对合并后的文本执行去 Markdown 标记处理（同 txt）
2. 跨平台复制到剪贴板：
   - macOS: cat novels/{小说名}/export/full.txt | pbcopy
   - Linux: cat novels/{小说名}/export/full.txt | xclip -selection clipboard（需安装 xclip）
   - 其他平台: 提示"已保存到 full.txt，请手动复制"
   自动检测当前平台（uname）选择对应命令。
   注意：如果文本过长（>1MB），提示"文本过长，已保存到 full.txt，请手动复制"
3. 同时将 publish-materials.txt 保存到文件（不复制到剪贴板）
```

**all 格式**：
```
1. 同时执行 md + txt 格式的输出
2. 生成 publish-materials.md
```

### Step 5：统计与汇报

```
1. 统计最终字数（统一口径）：
   - 读取导出的文件 → 去除 Markdown 标记 → 去除空白字符 → 计算字符数

2. 输出汇报：

═══ 导出完成 ═══
小说：{title}
总章数：{total_chapters}
总字数：{final_word_count}（统一口径）

导出文件：
  - novels/{小说名}/export/full.md       （{size}）
  - novels/{小说名}/export/full.txt       （{size}）
  - novels/{小说名}/export/publish-materials.md

发布素材预览：

📖 候选书名：
  1. {书名1} — {理由}
  2. {书名2} — {理由}
  3. {书名3} — {理由}
  4. {书名4} — {理由}
  5. {书名5} — {理由}

📝 简介：
{200字以内的简介}

🎨 封面提示词（Midjourney/DALL-E）：
{英文提示词}
═══════════════════
```

## 错误处理

```
- 小说名不存在 → 提示"未找到小说：{小说名}"，列出 novels/ 下所有目录供选择
- status 非 complete → 提示当前状态并建议完成流程
- chapters/ 目录为空 → 提示"该小说无章节文件"，终止
- 章节编号不连续 → 警告并继续（在汇报中标注缺失章节）
- 剪贴板复制失败 → 提示保存到文件，不终止
```

## 注意事项

1. 导出不修改原始章节文件，只读取和合并
2. export/ 目录下的文件可以被反复覆盖（每次 /export 都重新生成）
3. 发布素材每次重新生成（因为 AI 生成的内容可能每次不同）
4. 如果小说是 condense/compress 产出（目录名含 -condensed/-compressed），从对应目录读取
