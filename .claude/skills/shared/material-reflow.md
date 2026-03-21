# 素材自动回流

写作完成后（status 即将更新为 "complete" 时），自动执行素材回流。

## 回流范围

| Skill 类型 | styles/ | archetypes/ | worlds/ | tropes/ |
|-----------|---------|-------------|---------|---------|
| /novel, /short | ✓ | ✓ | ✓ | ✓ |
| /condense, /compress | ✓ | — | — | ✓ |

> condense/compress 不改编角色和设定，无新映射产出，因此不扫描 archetypes/ 和 worlds/。

## 回流流程

```
1. 风格回流（所有 Skill）
   → 读取本书 config/style.md 的核心参数（作者人格、写作原则、语言规则）
   → 与 library/styles/ 下所有已有文件对比
   → 如果不匹配任何已有文件 → 以 {风格名}.md 格式新建到 library/styles/

2. 角色原型回流（仅 /novel 和 /short）
   → 扫描 character-map.md 中有代表性的新模式（新的说话方式模板、新的性格组合）
   → 以追加模式写入 library/archetypes/ 对应文件

3. 世界观回流（仅 /novel 和 /short）
   → 扫描 setting-map.md 中的世界观设定
   → 如果包含 library/worlds/ 中不存在的题材 → 新建 {题材名}.md

4. 情节桥段回流（所有 Skill）
   → 扫描章节中反复出现的情节模式（如"身份暴露+打脸"、"拍卖竞价+反转"）
   → 与 library/tropes/ 对比
   → 如果匹配到不存在的桥段 → 新建 {桥段名}.md

5. 汇报回流结果（新增了哪些素材到 library/ 的哪些目录），不暂停
```
