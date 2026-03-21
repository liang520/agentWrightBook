# 新小说创建模板

> 创建一本新小说时，按此模板在 novels/{novel-name}/ 下创建文件。

## 目录结构
```
novels/{novel-name}/
├── meta.json              # 状态与进度
├── config/
│   ├── character-map.md   # 角色映射表 + 性格档案
│   ├── setting-map.md     # 设定映射表
│   ├── style.md           # 风格定调（含系统提示词）
│   └── foreshadowing.md   # 伏笔追踪表
├── context/               # 三层记忆系统
│   ├── memory-outline.md  # 第一层：全书记忆大纲（≤2000字）
│   ├── recent-context.md  # 第二层：最近10章详细上下文
│   ├── timeline.md        # 时间线账本（每章一行）
│   └── archives/          # 第三层：历史阶段归档
│       ├── stage-001-010.md
│       └── ...
└── chapters/              # 成稿章节
    ├── 001.md
    ├── 002.md
    └── ...
```

## meta.json 格式
```json
{
  "title": "新小说标题",
  "source": "sources/{source-name}",
  "genre": "都市/修仙/甜宠/...",
  "style": "library/styles/{style-name}.md",
  "world": "library/worlds/{world-name}.md",
  "status": "analyzing|configuring|writing|verifying|fixing|complete",
  "current_chapter": 0,
  "total_chapters": 200,
  "last_review_chapter": 0,
  "last_compress_chapter": 0,
  "created_at": "2026-03-12",
  "updated_at": "2026-03-12"
}
```

## character-map.md 格式
```markdown
# 角色映射表

## 主要角色

| 原作角色 | 原作别名（可选） | 新角色 | 原型 | 性格关键词 | 说话方式 | 口头禅 |
|---------|---------------|--------|------|-----------|---------|--------|
| 张三(主角) | 三哥、老张 | 李明 | 扮猪吃虎型 | 低调、腹黑 | 随和，关键时刻冷酷 | "我只是运气好" |
| 王美(女主) | 小美 | 苏晴 | 傲娇千金型 | 嘴硬心软 | 毒舌但关心 | "谁关心你了" |

别名列为可选，多个别名用"、"分隔。如无别名可留空或省略此列。
别名列除了昵称，还应包括称谓方式（如"裴某""叶——""X城主"等）。

## 次要角色

| 原作角色 | 新角色 | 首次出场 | 功能 |
|---------|--------|---------|------|
| ... | ... | 第N章 | 打脸对象/盟友/... |
```

## setting-map.md 格式
```markdown
# 设定映射表

## 世界观
| 原作设定 | 新设定 |
|---------|--------|
| 修仙世界 | 都市异能 |
| 灵石 | 能量晶石 |

## 地点
| 原作地点 | 新地点 |
|---------|--------|
| 天剑宗 | 天盾局 |

## 等级/体系
| 原作等级 | 新等级 |
|---------|--------|
| 练气期 | D级觉醒者 |

## 道具/技能
| 原作 | 新设定 |
|------|--------|
| 炼丹 | 调配药剂 |
```

## foreshadowing.md 格式
```markdown
# 伏笔追踪表

| 伏笔内容 | 埋设章节 | 计划回收章节 | 实际回收章节 | 状态 |
|---------|---------|------------|------------|------|
| 主角手臂上的神秘纹身 | 第3章 | 第50章左右 | - | 待回收 |
```

## 三层记忆系统

详细格式参见 `docs/memory-template.md`。

**style.md 中的系统提示词**：从 `library/styles/` 复制对应风格的系统提示词部分，定义"你是什么样的作者"。每次生成章节时必须遵守此人格设定。

**记忆自动管理**：用户无需手动操作，`/novel write` 会自动更新 recent-context.md，每10章自动执行记忆压缩。
