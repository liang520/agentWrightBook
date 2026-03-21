# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 AI Agent 驱动的网络小说仿写系统。核心模式是**逐章对照仿写**：基于已有的优质短篇网文，分析其结构后，用新的设定、角色、世界观逐章改写生成新小说，最终发布到百度作家平台 (zuojia.baidu.com)。

## 架构

```
agentModifyBook/
├── library/                # 全局素材仓库（所有小说共用，动态扩展）
│   ├── archetypes/         # 角色原型库（男主/女主/反派/配角）
│   ├── worlds/             # 世界观模板（修仙/都市异能/豪门/校园）
│   ├── styles/             # 语言风格库（含系统提示词，定义"作者人格"）
│   └── tropes/             # 情节桥段库（打脸/拍卖/实力暴露/复仇/契约婚姻）
├── sources/                # 原作素材（每部原作一个子目录）
│   └── {source-name}/
│       ├── meta.json       # 原作基本信息与分析状态
│       ├── analysis.md     # 结构分析报告
│       └── chapters/       # 原作章节内容
├── novels/                 # 仿写/改编/精炼/压缩小说（每本小说一个子目录，支持多本并行）
│   └── {novel-name}/
│       ├── meta.json       # 进度状态（mode 字段区分 novel/short/condense/compress）
│       ├── config/         # 本书配置
│       │   ├── character-map.md    # 角色映射表 + 性格档案
│       │   ├── setting-map.md      # 设定映射表
│       │   ├── style.md            # 风格定调 + 系统提示词
│       │   ├── foreshadowing.md    # 伏笔追踪表
│       │   ├── plot-skeleton.md    # 情节骨架（短篇专属）
│       │   ├── compression-map.md  # 压缩映射表（短篇专属）
│       │   ├── condense-plan.md    # 精炼计划（condense 专属）
│       │   └── compress-plan.md    # 压缩计划（compress 专属）
│       ├── context/        # 三层记忆系统
│       │   ├── memory-outline.md   # 全书记忆大纲（≤2000字）
│       │   ├── recent-context.md   # 最近10章详细上下文
│       │   └── archives/           # 历史阶段归档（每10章一个）
│       └── chapters/       # 成稿章节
├── docs/                   # 模板文档
│   ├── source-template.md  # 原作分析模板
│   ├── novel-template.md   # 新小说创建模板（长篇仿写）
│   ├── short-template.md   # 短篇改编创建模板
│   ├── condense-template.md # 精炼创建模板
│   ├── compress-template.md # 压缩创建模板
│   ├── memory-template.md  # 三层记忆架构模板
│   └── skills-guide.md     # Skills使用说明
├── .claude/skills/         # Agent 技能（/novel + /short + /condense + /compress）
└── .claude/skills-archive/ # 已归档的旧 Skills（9个）
```

## 核心工作流

整个创作流程通过统一的 `/novel` 指令驱动，所有交互均为选择题：

### 统一指令 `/novel`

| 命令 | 功能 |
|------|------|
| `/novel` | 自动检测状态并跳转到合适阶段 |
| `/novel status` | 查看所有小说和原作的状态进度 |
| `/novel analyze` | 分析原作：逐章标注功能，提取角色、节奏 |
| `/novel new` | 配置新书：选原作→选世界观→选风格→建映射表 |
| `/novel write` / `continue` | 写作：持续自动仿写，每5章审校，每10章压缩 |
| `/novel review [范围]` | 审校：检查映射泄漏、一致性、伏笔、风格 |
| `/novel compress` | 记忆压缩：归档历史章节，重建大纲 |
| `/novel verify` | 全书校验：10维度检查整本书 |
| `/novel fix` | 修复：自动修复校验发现的问题 |
| `/novel auto` | 全自动流水线：分析→配置→写作→校验→修复 |

旧 Skill 文件已归档到 `.claude/skills-archive/`。

### 短篇改编指令 `/short`

将任意长度原作压缩改编为 4.5万-5万字短篇，全自动无人参与。

| 命令 | 功能 |
|------|------|
| `/short` | 自动检测状态并跳转 |
| `/short status` | 查看短篇项目状态 |
| `/short analyze` | 分析原作（含压缩标注：可压缩度、依赖关系） |
| `/short plan` | 骨架提取 + 压缩规划 + 独立 Agent 校验 |
| `/short new` | 自动配置新书 |
| `/short write` / `continue` | 按压缩映射表逐章改写 |
| `/short review [范围]` | 审校（含压缩质量检查） |
| `/short compress` | 记忆压缩 |
| `/short verify` | 全书校验（11维度，含压缩质量总评） |
| `/short fix` | 修复 |
| `/short auto` | 全自动流水线：分析→规划→配置→写作→校验→修复 |

### 精炼指令 `/condense`

对已完成的小说进行精炼压缩，保持内容不变、削减冗余至目标字数。

| 命令 | 功能 |
|------|------|
| `/condense` | 自动检测状态并跳转 |
| `/condense status` | 查看精炼项目状态 |
| `/condense diagnose` | 诊断原稿：精确统计 + 逐章分级 + 目标分配 |
| `/condense write` / `continue` | 逐章精炼重写 |
| `/condense verify` | 终验（5维度检查） |
| `/condense fix` | 修复终验发现的问题 |
| `/condense auto` | 全自动流水线：诊断→写作→终验→修复 |

### 压缩指令 `/compress`

对已完成的小说进行大幅压缩（可合并章节、删支线），保持角色名和设定名不变。

| 命令 | 功能 |
|------|------|
| `/compress` | 自动检测状态并跳转 |
| `/compress status` | 查看压缩项目状态 |
| `/compress analyze` | 分析原稿：骨架提取 + 章节分级 |
| `/compress plan` | 生成压缩映射表 + 伏笔重映射 |
| `/compress write` / `continue` | 逐章压缩重写 |
| `/compress verify` | 终验（8维度检查） |
| `/compress fix` | 修复终验发现的问题 |
| `/compress auto` | 全自动流水线：分析→规划→写作→终验→修复 |

## 风格化系统提示词

每种风格（`library/styles/*.md`）包含系统提示词，定义"你是什么样的作者"：
- **作者人格**：写作的核心信念和态度
- **写作原则**：该风格的核心要求
- **禁忌事项**：绝不能出现什么
- **语言规则**：句式、节奏、用词倾向

写章节时必须加载对应风格的系统提示词，作为创作的"人格底色"，确保全书风格一致。

## 三层记忆系统

解决长篇仿写的上下文管理问题：

| 层级 | 文件 | 内容 | 大小限制 | 更新频率 |
|------|------|------|---------|---------|
| 第一层 | `memory-outline.md` | 全书记忆大纲 | ≤2000字 | 每10章重建 |
| 第二层 | `recent-context.md` | 最近10章详细上下文 | 无硬限制 | 每章追加 |
| 第三层 | `archives/stage-*.md` | 历史阶段归档 | 每个≤500字 | 每10章归档 |

**自动化逻辑**：
- 每写完1章 → 自动更新 recent-context.md
- 每写完10章 → 自动压缩归档 + 重建 memory-outline.md
- 用户无需手动操作记忆管理

**写章节时加载顺序**：memory-outline.md → recent-context.md → config文件

## 仿写六要素

1. **角色映射表** — 原作角色→新角色，含性格、说话方式、口头禅
2. **设定映射表** — 所有专有名词的替换词典
3. **人物性格档案** — 嵌入角色映射表，确保角色有灵魂
4. **风格定调+系统提示词** — 语言基调 + 作者人格
5. **三层记忆系统** — 分层管理上下文，防止前后矛盾
6. **伏笔追踪表** — 哪章埋了什么、预计哪章回收

## 短篇改编额外要素

7. **情节骨架** — 主线弧线、支线取舍、角色保留/合并/删除清单
8. **压缩映射表** — 原作章节→新作章节的映射、压缩策略、字数目标

## 字数统计规范（全局统一口径）

所有 Skill（`/novel`、`/short`、`/condense`、`/compress`）中涉及"字数"的地方，统一使用以下口径：

**统计口径：去空格、去 Markdown 标记后的字符数（含汉字 + 标点符号）**

具体规则：
1. **去除所有空格**：包括全角空格、半角空格、制表符
2. **去除 Markdown 标记**：包括 `#`、`*`、`-`、`>`、`|`、`` ` ``、`[`、`]`、`(`、`)`、`!` 等 Markdown 语法符号
3. **去除空行**
4. **保留**：所有汉字、中英文标点符号、数字、英文字母

**统计方法**：读取文件全文 → 去除 Markdown 标记 → 去除所有空白字符 → 计算剩余字符数

所有 Skill 中出现"统计字数"的地方，均引用此规范，不再各自定义。

## 跨会话工作原则

- 所有状态存在文件中，`meta.json` 的 `status` 字段驱动自动恢复
- 每次新会话执行 `/novel`、`/short`、`/condense` 或 `/compress` 即可自动检测状态并从断点继续
- 三层记忆系统保证中断后无缝恢复上下文
- 写作阶段默认持续自动，检查点只汇报不暂停
- 新角色/新设定自动生成映射后继续，检查点汇报新增映射

## 质量红线

- 成稿中绝不能出现原作的角色名或设定名词
- 每章必须有章尾钩子
- 不能与 memory-outline.md 的世界规则和 recent-context.md 的事实矛盾
- 风格必须与 style.md 的系统提示词一致
- 新角色/新设定出现时必须更新映射表
