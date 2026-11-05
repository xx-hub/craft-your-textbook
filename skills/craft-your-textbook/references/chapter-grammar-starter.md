# 章节语法起点——从模式卡组合章结构的走查示例

> 这不是硬模板，是一个"怎么从模式卡组合出章节语法"的示范走查。
> 设计期第 3 步设计板块语法时参考这个走查思路，不要照抄结构。
> 示范对象：PMP 一章（以 Ch4 冲突·领导·团队为例）。

---

## 走查过程

### 第一步：从预装配包出发

PMP 是认证类，选"认证应试蓝本"预装配包，拿到 14 张候选卡。

### 第二步：本书特化裁剪

1. **砍小说层**：认证类不需要人物情感弧线 → 拒绝 character-protagonist
2. **替代提问卡**：认证类需要应试反射 → 用 quick-judgment（速判）+ judgment-card（首选卡）组合，替代 socratic-questioning（探索脚本保留但作为 judgment 配套）
3. **加硬记/判断分离**：PMP 有大量"框架名要背、何时用要推"的知识 → fact-vs-judgment 必选

### 第三步：把选的卡映射为板块

选出的卡 → 章内板块位置：

| 模式卡 | 在章内的位置/板块名 |
|---|---|
| scenario-hook | 章首（无编号，引用块） |
| precise-definition | 每小节内的 `### Definition: X` 子板块（循环单元内） |
| misconception | 每小节内的 `### Common Misconception` 子板块 |
| judgment-card | 每小节内的 `### PMI 会怎么选` 子板块 |
| fact-vs-judgment | 章末 `## 本章硬记锚`（放事实）+ judgment-card（放判断），分离 |
| deterministic-anchor | 章末硬记锚里的条目 |
| practice-gradient | 章末双脚本：探索脚本→速判脚本（recall→transfer 梯度） |
| quick-judgment | 章末速判脚本里的题 |
| cross-ref-trace | judgment-card 内"判断依据：回溯 Ch2 原则6"行内回溯 |
| running-case | scenario-hook 挂靠锦程建工项目 |
| multi-source-arbitration | 写作规范里的三源范式（本书级，非章内板块） |

### 第四步：确定章骨架

得到 PMP Ch4 的骨架：

```markdown
# Chapter 4 · 冲突、领导、团队与基本规则——副标题
---
eco_tasks: [...]
chapter_type: ...
pmbok7_anchor: ...
---
> [锦程建工情境钩子]

（注：PMP 虽为 human-readable 路线，但因认证类多源校验需要，写作规范显式声明了章级 frontmatter schema，是 human-readable 路线的例外，见 two-routes.md。）

## 4.1 [小节标题]
[叙事 prose]
### Definition: [概念]（precise-definition）
[PMBOK 原文定义]
用通俗的话说：[大白话]
### Common Misconception（misconception）
### PMI 会怎么选（judgment-card + cross-ref-trace）

## 4.2 ...（同上循环）

## 本章硬记锚（fact-vs-judgment + deterministic-anchor）
[必背框架清单，只放事实不放判断]

## 【AI 老师提问脚本】（practice-gradient）
### 探索脚本：[问题链]
### 速判脚本：[四选一短情境]（quick-judgment）
```

> ⚠️ **这个「AI 老师提问脚本」块住在章末 H2 教学区里**（human 档的带读手册就是这个教学区本身；
> blueprint 档是教学区内部第一块的四个子项）。`### 探索脚本`／`### 速判脚本` 这类块名只属于
> 手册内部，⛔ 不进正文（正文是给人读的散文）。human 档的教学区**零改动**：原样保留三层问题链
> 与内嵌提示，⛔ 不因为这张卡另加段落。契约的 H2 那一份：本仓 dsh＝`resources/references/invariants.md`／
> skill 侧＝`references/invariants.md`；「带读手册」见 `file-contracts.md`。

### 第五步：声明可选板块

在写作规范里声明：`judgment-card` 是可选板块——技术性小节无 PMI 偏好时允许略去，不硬凑。

---

## 关键思路

1. **先选卡再映射为板块**，不是先列板块再找卡填
2. **同一张卡可以出现在不同位置**（precise-definition 在小节内，cross-ref-trace 行内嵌入）
3. **卡是原子的，板块是组合的**——章骨架是卡组合后的结构，不是卡的平铺
4. **每章有可选板块的弹性**——声明哪些板块可略去，避免硬凑
5. **整书级卡（foundation-chapter/multi-source-arbitration/appendix-compilation）不进章骨架**，它们是章节骨架层面的设计

用同样的走查方法，CPA 一章的骨架会映射为：
- scenario-hook + character-protagonist → 章首老周视角叙事
- precise-definition → `### Definition: X`
- misconception → `### Common Misconception`
- application-problem + worked-example → 章末 Exercises（Concept Check/Application Problems/Think Deeper 三级）
- recurring-leitmotif → prose 里行内点题
