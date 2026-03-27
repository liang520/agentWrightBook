# 小说 Agent 系统：四大流程可视化梳理

> 面向新人的一图看懂版。四条指令分别解决不同场景，共用底层模块。

---

## 一、四大指令：定位一览

| 指令 | 中文名 | 输入 | 输出 | 核心特点 |
|------|--------|------|------|---------|
| `/novel` | **改写仿写** | 原作 txt | 全新小说（角色/设定全换） | 有人参与，选择题驱动 |
| `/short` | **短篇改编** | 原作 txt | 4.5-5万字短篇（角色/设定全换） | 全自动，并行写作 |
| `/compress` | **大幅压缩** | 已完成小说 | 同名压缩版（合章/删支线） | 全自动，不改名不改编 |
| `/condense` | **精炼缩字** | 已完成小说 | 精炼版（纯删冗余） | 全自动，字词级别 |

---

## 二、选哪个？决策树

```mermaid
flowchart TD
    A["我手上有什么？"] --> B{"原作 txt（还没改过）"}
    A --> C{"已完成的仿写小说"}

    B --> D{"目标是什么？"}
    D -->|"换角色名换世界观，改成全新的书"| E["📘 novel — 改写仿写"]
    D -->|"保留原名，压缩改编成短篇"| G["📗 short — 短篇改编（4.5-5万字）"]

    C --> H{"要做什么？"}
    H -->|"内容情节完全不变，只删废话冗余"| I["📙 condense — 精炼缩字"]
    H -->|"可合并章节、可删支线，大幅压缩"| J["📕 compress — 大幅压缩"]

    style E fill:#4A90D9,color:#fff
    style G fill:#7B68EE,color:#fff
    style I fill:#50C878,color:#fff
    style J fill:#FF8C00,color:#fff
```

---

## 三、/novel 改写仿写：主流程

**场景**：手上有原作 txt，想改成全新小说（新角色、新世界观、新名字）

```mermaid
flowchart TD
    START([用户: /novel]) --> P0

    P0["**Phase 0：状态总览**\n扫描 novels/ + sources/\n展示面板"] --> DETECT{自动检测状态}

    DETECT -->|有未分析原作| P1
    DETECT -->|source已ready| P2
    DETECT -->|小说写作中| P3
    DETECT -->|写完待校验| P6

    P1["**Phase 1：分析原作**\n① 逐章标注功能标签\n② 提取角色列表→归类原型\n③ 节奏分析（爽点/钩子密度）\n④ 生成 analysis.md\n⑤ source.meta.json → ready"] --> P2

    P2["**Phase 2：配置新书**\n① 选世界观（热门优先）\n② 选语言风格（推荐匹配）\n③ 生成5个候选书名\n④ 角色映射表（主角/配角/龙套）\n⑤ 设定映射表\n⑥ 伏笔追踪表初始化\n创建完整目录结构"] --> P3

    P3["**Phase 3：写作核心循环** 🔁\n每章：\n① 加载上下文（静默）\n② 读原作第N章\n③ 新实体检查→自动生成映射\n④ 生成仿写章节\n⑤ 六项自查（泄漏/矛盾/钩子/伏笔）\n⑥ 保存+更新三层记忆\n每5章→后台审校\n每10章→记忆压缩"] --> CHECK3{N == total?}

    CHECK3 -->|否| P3
    CHECK3 -->|是| P6

    P4A["**Phase 4A：后台审校**\n（每5章自动触发）\n检查：泄漏/术语/逻辑/角色/风格\n结果在下个检查点汇报"] -.->|并行| P3

    P5["**Phase 5：记忆压缩**\n（每10章自动触发）\n归档旧内容→重建全书大纲\n压缩优先级：事件>角色>伏笔>规则>细节"] -.->|并行| P3

    P6["**Phase 6：全书校验（20维度）**\n必须全部执行，不可跳过\n覆盖：映射泄漏/伏笔闭合\n情绪曲线/因果链/时间线等\n生成 verification-report.md"] --> P65

    P65["**Phase 6.5：独立交叉审查**\n2个独立Agent并行审查\n（不看校验报告，避免锚定）\n门禁：无Critical且Warning≤5 → 通过"] --> CHECK65{通过?}

    CHECK65 -->|否| P7
    CHECK65 -->|是| REFLOW

    P7["**Phase 7：修复**\n① 全书关联扫描\n② Critical→自动替换\n③ Warning→修复记录\n④ 最多3轮循环\n⑤ 定向复验（修改处±2章）"] --> REFLOW

    REFLOW["**素材自动回流**\n优质角色/风格/桥段\n回写进 library/ 供下次复用"] --> DONE

    DONE([✅ complete — meta.json 状态=complete])

    style P3 fill:#FF6B6B,color:#fff
    style P6 fill:#4A90D9,color:#fff
    style REFLOW fill:#50C878,color:#fff
```

**关键状态转换**：
```
raw → analyzing → ready → configuring → writing → verifying → cross-reviewing → fixing → complete
```

---

## 四、/short 短篇改编：主流程

**场景**：原作很长，要压缩改编成 4.5-5万字的新书（同样换角色换设定）

```mermaid
flowchart TD
    START([用户: /short auto]) --> P1

    P1["**Phase 1：逐章分析**\n标注5维度：\n功能标签/核心事件\n可压缩度(1-5)/依赖关系\n关键角色/伏笔\n统计原作总字数"] --> P2

    P2["**Phase 2：骨架提取+压缩规划**\n① 提取情节骨架\n   保留：主线因果链、关键角色、伏笔链\n   删除：支线、重复爽点、过渡灌水\n② 生成压缩映射表（章号→合并方案）\n   计算每个新章的字数预算\n③ 独立校验Agent执行8项检查：\n   字数范围/覆盖率/伏笔链\n   节奏比例/因果链/密度等"] --> P3

    P3["**Phase 3：配置新书（全自动）**\n无选择题，AI自动决定：\n选热门世界观→选推荐风格\n→生成书名（取第1个）\n→角色映射+龙套登记\n→设定映射+伏笔扩展\n创建 details-lock.md\n   锁定所有具体数字/物理细节\n   Agent不得自行编造锁定表外的数值\n配置完整性双重门禁校验"] --> P4

    P4["**Phase 4：写作核心循环** 🔁\n分两期："] --> SERIAL

    SERIAL["**串行主干期（第1-4章）**\n严格顺序写\n建立事实基线\n填充 details-lock + event-ledger"] --> WAVE

    WAVE["**波次并行期（第5章起）**\n① 划分波次（4-5章/波，强耦合章归同组）\n② 同波次内并行写作\n③ 每章注入前章内容+防越界指令\n④ 每波次完成后执行7步后处理：\n   提取事件delta→合并账本\n   锁定新事实→Grep一致性扫描\n   状态连续性检查→审校触发\n⑤ 门禁判定：Blocking Critical→串行重写"] --> CHECK4{写完?}

    CHECK4 -->|否| WAVE
    CHECK4 -->|是| P7

    P5["**Phase 5：后台审校**\n每波次无条件触发\n11项检查（含details-lock一致性）\n结果追加到 review-notes.md"] -.->|并行| WAVE

    P7["**Phase 7：全书校验（24维度）**\n在20维度基础上新增：\n压缩跳跃检测/反转落地交代\n反派智商审计\n生成 verification-report.md"] --> P75

    P75["**Phase 7.5：独立交叉审查**\n同 /novel Phase 6.5\n2个Agent并行审查"] --> P8

    P8["**Phase 8：修复**\n关联扫描→分级修复\n→定向复验→素材回流"] --> DONE

    DONE([✅ complete])

    style SERIAL fill:#FF8C00,color:#fff
    style WAVE fill:#FF6B6B,color:#fff
    style P7 fill:#4A90D9,color:#fff
```

**与 /novel 的核心区别**：
- Phase 2 多了**压缩规划**（先算好哪些章合并）
- Phase 3 多了**details-lock**（事实锁定表，防AI编造数字）
- Phase 4 多了**波次并行**（更快写完）+ **event-ledger**（事件账本）
- 校验是 24 维度（比 /novel 多 4 个）

---

## 五、/compress 大幅压缩：主流程

**场景**：已有一本仿写完的小说，想大幅压缩（可合并章节、删支线），**保留原有角色名和设定名**

```mermaid
flowchart TD
    START([用户: /compress auto]) --> P1

    P1["**Phase 1：分析压缩目标**\n① 统计原书总字数\n② 逐章标注功能标签\n③ 识别支线/灌水/可合并章节\n④ 生成分析报告"] --> P2

    P2["**Phase 2：压缩规划**\n① 生成压缩映射表\n   原章号 → 新章号（多对一或一对一）\n② 计算每个新章的字数预算\n③ 伏笔重映射（章号更新）\n④ 独立校验Agent验证规划\n写入 compress-plan.md"] --> P3

    P3["**Phase 3：逐章压缩写作** 🔁\n原书目录：严格只读\n成品目录：name-compressed/\n每章流程：\n① 读取对应原章（可能是多章合并）\n② 按压缩映射表生成新章\n③ 五项自查（泄漏/矛盾/钩子等）\n④ 更新记忆系统\n每10章→记忆压缩"] --> CHECK{写完?}

    CHECK -->|否| P3
    CHECK -->|是| P4

    P4["**Phase 4：终验**\n检查压缩质量\n映射泄漏/伏笔闭合\n字数是否达到目标\n生成 verification-report.md"] --> P5

    P5["**Phase 5：修复**\n关联扫描→分级修复\n→素材回流→complete"] --> DONE

    DONE([✅ complete — 输出到 novels/name-compressed/])

    style P3 fill:#FF8C00,color:#fff
```

> ⚠️ 关键约束：① 角色名/设定名全部保持原样 ② 不建 character-map / setting-map ③ 原书目录严格只读，所有写操作在 `-compressed/` 下

---

## 六、/condense 精炼缩字：主流程

**场景**：已有一本仿写完的小说，内容和情节完全不变，只删掉废话、冗余描写，达到目标字数

```mermaid
flowchart TD
    START([用户: /condense auto]) --> P1

    P1["**Phase 1：诊断**\n① 精确统计每章字数\n② 逐章四级分级：\n   A级（重度砍25%+）：大量废话、重复场景\n   B级（中度10-25%）：过度描写、对话拖沓\n   C级（轻度5-10%）：措辞冗余\n   D级（保留）：高质量章节\n③ 分配各章目标字数\n④ 提取每章核心事件清单\n⑤ 创建 condense-plan.md"] --> P2

    P2["**Phase 2：逐章精炼重写** 🔁\n成品目录：name-condensed/\n原书目录：严格只读\n每章按等级处理：\n D级 → 直接复制，不修改\n C级 → 措辞精炼（长句拆短、删形容词）\n B级 → 删废话+压缩心理描写+合并过渡\n A级 → 环境1句/战斗只留结果/删重复对话\n绝不动：事件清单要点/伏笔句/章尾钩子\n写完自检字数（超10%→精简，不足85%→恢复）\n每5章→预算检查 / 每10章→记忆压缩"] --> CHECK{达到目标字数?}

    CHECK -->|否，偏差>10%| ADJ["调整后续章节分级\n重新分配预算"]
    ADJ --> P2
    CHECK -->|是| P3

    P3["**Phase 3：终验（9维度）**\n① 总字数是否达标\n② 伏笔完整性（埋/回都在）\n③ 情绪曲线是否保持\n④ A/B级章对照原文抽检\n⑤ 因果链完整性\n⑥ 跨章状态一致性\n⑦ 数值链闭合\n⑧ 原作名残留扫描\n⑨ 伏笔表校准\n生成 verification-report.md"] --> P4

    P4["**Phase 4：修复**\n字数超标→精简\n字数不足→恢复关键描写\n伏笔遗漏→补回\n因果断裂→补衔接句\n最多3轮→素材回流→complete"] --> DONE

    DONE([✅ complete — 输出到 novels/name-condensed/])

    style P2 fill:#50C878,color:#fff
```

> ⚠️ 关键约束：① 情节/角色/因果链完全不变 ② 只精炼文字表达 ③ 不合并章节、不删支线（这是与 `/compress` 的核心区别）

---

## 七、共用底层模块

```mermaid
flowchart LR
    subgraph Skills["四大指令"]
        N["novel\n改写仿写"]
        S["short\n短篇改编"]
        CM["compress\n大幅压缩"]
        CD["condense\n精炼缩字"]
    end

    subgraph Shared["共用模块 shared/"]
        MEM["memory-compress.md\n三层记忆压缩\n（每10章自动触发）"]
        LEAK["leak-scan.md\n原作名泄漏扫描\n（全名+别名+子串+姓氏）"]
        REFLOW["material-reflow.md\n素材自动回流\n（完成后必执行）"]
    end

    subgraph Library["library/ 素材库"]
        ARC["archetypes/\n角色原型"]
        WLD["worlds/\n世界观模板"]
        STY["styles/\n语言风格"]
        TRP["tropes/\n情节桥段"]
    end

    N --> MEM
    S --> MEM
    CM --> MEM
    N --> LEAK
    S --> LEAK
    CM --> LEAK
    N --> REFLOW
    S --> REFLOW
    CM --> REFLOW
    CD --> REFLOW

    REFLOW --> ARC
    REFLOW --> WLD
    REFLOW --> STY
    REFLOW --> TRP

    ARC --> N
    ARC --> S
    WLD --> N
    WLD --> S
    STY --> N
    STY --> S
    STY --> CM
    STY --> CD
    TRP --> N
    TRP --> S
```

---

## 八、全局状态机（meta.json status 字段）

```mermaid
stateDiagram-v2
    [*] --> raw : 导入原作

    state "原作处理" as SOURCE {
        raw --> analyzing : novel analyze
        analyzing --> ready : 分析完成
    }

    state "novel 改写流程" as NOVEL {
        ready --> configuring : novel new
        configuring --> writing : 配置完成
        writing --> verifying : 写完所有章节
        verifying --> cross_reviewing : Phase 6完成
        cross_reviewing --> fixing : 有Critical
        cross_reviewing --> complete1 : 全通过
        fixing --> complete1 : 修复完成
    }

    state "short 短篇流程" as SHORT {
        analyzed --> planning : short plan
        planning --> configuring2 : 规划完成
        configuring2 --> writing2 : 配置完成
        writing2 --> written : 写完
        written --> verifying2 : short verify
        verifying2 --> cross2 : Phase 7完成
        cross2 --> fixing2 : 有Critical
        cross2 --> complete2 : 全通过
        fixing2 --> complete2 : 修复完成
    }

    state "compress 压缩流程" as COMPRESS {
        comp_init --> comp_analyzed : Phase 1完成
        comp_analyzed --> comp_planning : compress plan
        comp_planning --> comp_writing : 规划完成
        comp_writing --> comp_verifying : 写完
        comp_verifying --> comp_fixing : 有问题
        comp_verifying --> comp_complete : 通过
        comp_fixing --> comp_complete
    }

    state "condense 精炼流程" as CONDENSE {
        cd_init --> diagnosed : condense diagnose
        diagnosed --> cd_writing : condense write
        cd_writing --> cd_verifying : 写完
        cd_verifying --> cd_fixing : 有问题
        cd_verifying --> cd_complete : 通过
        cd_fixing --> cd_complete
    }
```

---

## 九、三层记忆系统（/novel 和 /short 共用）

```
每次写章节时加载顺序：
┌─────────────────────────────────────────┐
│  第一层：memory-outline.md（≤2000字）    │  ← 全书大纲，每10章重建
│  全书走向、关键转折、当前局势、角色状态   │
├─────────────────────────────────────────┤
│  第二层：recent-context.md（无硬限制）   │  ← 最近10章详细上下文，每章追加
│  新增事实、角色状态、冲突、钩子           │
├─────────────────────────────────────────┤
│  第三层：archives/stage-*.md（每个≤500字）│  ← 历史归档，每10章压缩一次
│  已归档的早期章节压缩摘要                │
└─────────────────────────────────────────┘

写完→追加第二层 → 每10章→第二层最早内容压缩进第三层 + 重建第一层
```
