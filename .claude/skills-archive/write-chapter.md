---
name: write-chapter
description: 逐章仿写 — 读取原作章节，结合配置，生成新章节。自动管理记忆和提示词。
user_invocable: true
---

# 逐章仿写

## 触发条件
用户要为某本小说写下一章（或指定章节）。

## 交互规则
**所有需要用户选择或确认的环节，必须以编号选择题形式呈现，用户只需回复数字即可。**

## 执行步骤

### 1. 选择小说
如果 `novels/` 下有多本小说，展示选择题：
```
请选择要写的小说：
1. 都市逆袭王（当前第45章，共200章）
2. 校园甜宠记（当前第12章，共150章）
3. 上次写的：都市逆袭王（继续第46章）
```
如果只有一本小说，直接选中。

### 2. 加载上下文（自动执行）
按顺序读取以下文件（全部必读）：
1. `novels/{novel-name}/meta.json` — 确认当前进度、对应的 source
2. `novels/{novel-name}/config/style.md` — **风格定调 + 系统提示词**（作为本次创作的"人格底色"）
3. `novels/{novel-name}/context/memory-outline.md` — **全书记忆大纲**（知道整体走向）
4. `novels/{novel-name}/context/recent-context.md` — **最近10章详细上下文**（知道最近发生什么）
5. `novels/{novel-name}/config/character-map.md` — 角色映射表
6. `novels/{novel-name}/config/setting-map.md` — 设定映射表
7. `novels/{novel-name}/config/foreshadowing.md` — 伏笔表

**注意**：style.md 中的系统提示词部分定义了"你是什么样的作者"，在整个章节生成过程中必须始终遵守该人格设定。

### 3. 读取原作对应章节
- 从 meta.json 确定 current_chapter + 1 = 要写的章节号 N
- 读取 `sources/{source-name}/chapters/{N}.md`（原作第N章）
- 读取 `sources/{source-name}/analysis.md` 中第N章的功能标注

### 4. 章节分析
在写之前先输出：
```
【原作第N章分析】
- 章节功能：{功能标签}
- 关键情节点：1. ... 2. ... 3. ...
- 出场角色：{原作角色} → {新角色}
- 涉及的设定：{原作设定} → {新设定}
- 章尾钩子：{原作怎么收尾的}
- 伏笔：{是否埋了伏笔/回收了伏笔}
```

展示确认：
```
以上分析是否准确？
1. ✅ 正确，开始写
2. 🔄 需要调整（告诉我哪里不对）
```

### 5. 生成新章节
基于以上分析，按照以下规则生成新章节：
- **风格人格**: 严格遵守 style.md 中的系统提示词，以该"作者人格"写作
- **角色替换**: 严格按照 character-map.md 替换，包括性格和说话方式
- **设定替换**: 严格按照 setting-map.md 替换所有专有名词
- **上下文一致**: 检查 memory-outline.md 的世界规则和 recent-context.md 的近期事实，确保不矛盾
- **情节对应**: 保留原作本章的功能和情节结构，但用新设定重新演绎
- **伏笔处理**: 如果原作本章有伏笔，在新章中对应埋设，记录到 foreshadowing.md

### 6. 输出与确认
将新章节写入 `novels/{novel-name}/chapters/{NNN}.md`，展示给用户，然后：
```
第{N}章已生成，请确认：
1. ✅ 满意，保存并继续
2. 🔄 不满意，重写（告诉我哪里需要改）
3. ✏️ 局部修改（告诉我修改哪段）
4. ➡️ 满意，直接写下一章
```

### 7. 更新状态（用户确认后自动执行）

#### 7a. 更新进度
- 更新 `novels/{novel-name}/meta.json` 的 current_chapter 和 updated_at

#### 7b. 更新记忆
- 追加更新 `novels/{novel-name}/context/recent-context.md`，记录：
  - 新增事实
  - 角色状态变化
  - 新增/解决的冲突
  - 使用的桥段
  - 章尾钩子

#### 7c. 更新伏笔
- 如有新伏笔，追加到 `novels/{novel-name}/config/foreshadowing.md`
- 如有回收伏笔，更新对应条目的状态

#### 7d. 自动记忆压缩检查
- 检查 current_chapter 是否是 10 的倍数
- 如果是 → **自动调用 `/compress-memory` 流程**：
  1. 将 recent-context.md 中最早10章压缩归档到 archives/
  2. 清理 recent-context.md
  3. 重建 memory-outline.md
  4. 汇报压缩结果
- 如果不是 → 跳过，继续

### 8. 新角色/新设定处理
如果原作本章出现了映射表中没有的新角色或新设定，暂停并展示：
```
⚠️ 发现新角色「{原作角色名}」，映射表中没有对应。
请选择处理方式：
1. 为TA创建映射（进入角色创建流程）
2. 这是不重要的路人，用通用名称代替
3. 跳过，我稍后处理
```

新设定同理：
```
⚠️ 发现新设定「{原作设定名}」，映射表中没有对应。
请选择：
1. 添加映射（AI生成3个候选→选择）
2. 跳过，我稍后处理
```

## 质量检查点
每章写完后自查：
- [ ] 所有角色名是否用的新名字（不能出现原作角色名）
- [ ] 所有设定名词是否已替换
- [ ] 与 memory-outline.md 的世界规则和 recent-context.md 的事实是否矛盾
- [ ] 风格是否与 style.md 的系统提示词一致
- [ ] 章尾是否有钩子
