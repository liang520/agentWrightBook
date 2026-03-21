---
name: recommend
description: 智能选题推荐 — 从13000+本评分数据中自动筛选最适合改写的书。支持按题材/字数/频道筛选。用法：/recommend [筛选条件]
user_invocable: true
---

# 智能选题推荐

## 用法

```
/recommend              → 推荐5本最适合改写的书（默认）
/recommend 都市          → 按题材筛选
/recommend 5-10万字      → 按字数范围筛选
/recommend 女频          → 按频道筛选（自动映射题材）
/recommend 男频 悬疑      → 组合筛选
```

## 数据源

评分 JSON 文件位于 `/Users/liang/CodeSelf/novelOrignal/`：
- `scores.json`（~9900 本，20万字+）
- `scores_5to10w.json`（~586 本，5-10万字）
- `scores_10to20w.json`（~2600 本，10-20万字）

每本书包含 10 维度评分：hook(钩子)、conflict(冲突)、pacing(节奏)、shuang(爽点)、suspense(悬念)、protagonist(主角)、condensability(可压缩度)、novelty(新颖度)、emotion(情感)、readability(可读性) + total(总分) + genre(题材) + word_count(字数) + path(文件相对路径)

## 核心流程

### Step 1：加载数据

```
1. 加载 3 个评分 JSON 文件，合并为统一列表
2. 路径标准化：所有 path 拼接根目录 /Users/liang/CodeSelf/novelOrignal/
3. 路径验证：检查文件是否存在，标记失效路径
4. 去除路径失效的条目（不推荐找不到文件的书）
```

### Step 2：排除已改写的书

```
扫描 novels/*/meta.json，提取每本已完成小说的 source 字段
  → 从 source 字段找到 sources/{slug}/meta.json
  → 读取 sources/{slug}/meta.json 的 title
  → 将该 title 加入排除列表
也直接扫描 sources/*/meta.json 的 title 加入排除列表（已导入的也排除）

对评分列表按 title 匹配排除
```

### Step 3：应用用户筛选条件

```
解析用户参数，支持：
  - 题材筛选：直接匹配 genre 字段（如"都市""悬疑""穿越"）
  - 字数范围：解析"X-Y万字"格式，匹配 word_count
  - 频道筛选：按映射规则转换为题材列表
    女频 → ["现代言情", "古代言情", "耽美/BL", "穿越"]
    男频 → ["都市", "玄幻", "游戏竞技", "武侠", "悬疑", "科幻/科技", "历史"]
  - 如无参数，不做题材限制
```

### Step 4：多维度加权排序

```
对每本书计算推荐分：

recommend_score =
    total * 0.50                    # 综合评分权重最高
  + condensability * 0.20           # 可压缩度（越高越好改编）
  + word_fit_score * 0.15           # 字数适配度
  + diversity_bonus * 0.15          # 题材多样化奖励

字数适配度计算：
  5-20万字（最适合 /short）   → 100分
  20-50万字（/short 可截取）  → 80分
  50-100万字                  → 60分
  >100万字                    → 40分

题材多样化奖励：
  统计已改写书的题材分布
  当前候选的题材如果已有3本以上 → 0分
  已有2本 → 30分
  已有1本 → 60分
  全新题材 → 100分
```

### Step 5：输出 Top 5 候选

```
取排序后 Top 5，每本输出：

═══ 推荐 #{N} ═══
书名：{title}
作者：{author}
题材：{genre} | 字数：{word_count/10000:.1f}万字
总分：{total} | 可压缩度：{condensability}
推荐分：{recommend_score:.1f}

评分卡：
  钩子:{hook} 冲突:{conflict} 节奏:{pacing} 爽点:{shuang} 悬念:{suspense}
  主角:{protagonist} 压缩:{condensability} 新颖:{novelty} 情感:{emotion} 可读:{readability}

推荐理由：{comment}
建议 Skill：{/novel 或 /short}
文件路径：{full_path}（✓存在 / ✗不存在）
═══════════════

Skill 建议逻辑：
  字数 < 50000 → /novel（等长仿写）
  字数 >= 50000 → /short（短篇改编，/short 会自动决定截取策略）
```

### Step 6：用户选择

```
展示 5 本候选后，提示：
  选择数字 1-5 开始改写
  或输入其他条件重新筛选

用户选择后自动执行：
  1. /import {文件路径}
  2. 根据建议 Skill 执行 /short auto 或 /novel auto
```

## 错误处理

```
- 评分 JSON 不存在 → 提示路径，终止
- 筛选后候选 < 5 本 → 降低筛选条件，或提示"符合条件的书不足5本，当前找到{N}本"
- 所有候选路径失效 → 提示"评分数据中的文件路径大量失效，请检查原作目录"
```
