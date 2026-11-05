# 参考模式库

> 21 张模式卡，按"教学问题"组织（不按学科）。每张卡解决一个具体的教学设计问题。
> 这些不是"你必须套用"的模板，是"你可以选/混搭/新造"的解决方案菜单。

---

## 什么时候读我

- **设计期第 3 步·模式选型时**：全读本 README + 按教学问题翻对应卡
- **铺章时**：按写作规范里选定的卡，重读具体卡的写法示例

## 卡的分层

- **整书架构层**（`structure/`）：设计章节骨架时先翻这组——地基章、收网章、跨章引用、附录汇编、多源裁决、主题低音线
- **章内板块层**（其他目录）：设计章内板块语法时翻
  - `concept-anchoring/`：概念锚定类（精确呈现、误区桩、苏格拉底提问、事实vs判断分离、深度铺陈）
  - `assessment/`：评估/练习类（判断题、速判题、推理题、例题、练习梯度、必背锚）
  - `narrative/`：叙事结构类（情境钩子、贯穿案例、主角）
  - `language-learning/`：语言学习特化（词汇分层）

## 注意力引导（按教学目标提示优先看哪些卡）

根据设计期第 1 步识别的教学目标，提示 Agent 优先看：
- **认证应试目标**（PMP/CPA/法考）→ 优先看 `assessment/judgment-card`、`assessment/quick-judgment`、`concept-anchoring/fact-vs-judgment`、`concept-anchoring/depth-elaboration`、`assessment/deterministic-anchor`、`structure/multi-source-arbitration`、`structure/foundation-chapter`、`structure/capstone-chapter`、`structure/appendix-compilation`
- **技能掌握目标**（编程/数学/写作）→ 优先看 `assessment/worked-example`、`assessment/application-problem`、`concept-anchoring/socratic-questioning`、`concept-anchoring/depth-elaboration`
- **概念理解目标**（哲学/经济学入门）→ 优先看 `concept-anchoring/precise-definition`、`concept-anchoring/misconception`、`concept-anchoring/depth-elaboration`、`narrative/character-protagonist`、`narrative/running-case`、`structure/recurring-leitmotif`
- **语言学习目标**（英语/外语）→ 优先看 `language-learning/vocabulary-dimension`、`concept-anchoring/socratic-questioning`、`narrative/scenario-hook`

这不是强制，是注意力引导——Agent 仍需遍历所有卡判断适用性。

---

## 模式选型流程三步

1. **带问题翻卡**：带设计期第 1 步识别的"教学问题"翻卡，每张卡判断"这张卡解决的问题本书有没有"
2. **回答两个强制问题**（写进写作规范 §模式选型说明）：
   - 我考虑过哪些模式、拒绝了哪些、为什么拒绝？
   - 所选每个模式对应本书哪个具体教学问题？
3. **或从预装配包出发再定制**（见下）

审计时核对：声称用了某模式但写作规范板块语法里没有对应板块 = 失败。

---

## 参考架构起点（预装配包）

不想从 21 张原子卡拼装时，可以从这三个预装配包出发再定制。选用时在写作规范里说明"为什么这个起点适合本书、做了哪些定制"。

### 认证应试蓝本
**适合**：PMP/CPA/法考/医师资格等认证类
**预打包**：precise-definition + misconception + judgment-card + quick-judgment + fact-vs-judgment + deterministic-anchor + practice-gradient + multi-source-arbitration + foundation-chapter + capstone-chapter + cross-ref-trace + appendix-compilation + scenario-hook + running-case（可选 character-protagonist）
**典型样本**：PMP 认证蓝本

### 叙事入门教材
**适合**：通俗科普/入门教材
**预打包**：precise-definition + misconception + socratic-questioning + application-problem + worked-example + scenario-hook + character-protagonist + running-case + recurring-leitmotif（含判断/选择类知识点时加 fact-vs-judgment）
**典型样本**：CPA 审计教材

### AI 教学蓝本（K-12/技能）
**适合**：英语教材/编程入门/数学
**预打包**：socratic-questioning + precise-definition + worked-example + scenario-hook + vocabulary-dimension（语言类）+ cross-ref-trace
**典型样本**：英语七上教材样本

---

## 已完成书的选型示例

### PMP 认证蓝本（human-readable，认证应试起点）
**选用**：precise-definition、misconception、judgment-card（"PMI 会怎么选"板块）、quick-judgment（速判脚本）、fact-vs-judgment（硬记锚 vs 判断分离铁律）、deterministic-anchor（本章硬记锚）、practice-gradient（探索脚本→速判脚本二级梯度）、multi-source-arbitration（ECO/PMBOK7/过程组三源冲突表述范式）、foundation-chapter（Ch2 十二原则/Ch3 八绩效域）、capstone-chapter（Ch18 PMI 思维总集）、cross-ref-trace（"回溯 Ch2 原则6"行内回溯）、appendix-compilation（附录 A/B/C 从硬记锚/速判/eco_tasks 汇编）、scenario-hook（锦程建工医院项目）、running-case（锦程建工贯穿项目）
**拒绝**：character-protagonist（认证类不需要第二人称主角）、socratic-questioning（被探索脚本+速判脚本替代）

### CPA 审计教材（human-readable，叙事入门起点）
**选用**：precise-definition（Definition 双讲）、misconception（Common Misconception）、socratic-questioning（探索脚本）、application-problem（Application Problems）、worked-example（审计程序设计题）、scenario-hook（华明制造开章）、character-protagonist（老周/注册会计师视角）、running-case（华明制造贯穿案例）、recurring-leitmotif（职业怀疑/风险→程序→证据→结论/华明低音线）
**拒绝**：judgment-card（CPA 不考"四选项都对选首选"）、quick-judgment（CPA 考长推理不考 77 秒反射）

### 英语七上教材（pure-blueprint，AI 教学蓝本起点）
**选用**：socratic-questioning（💬三类引导问题）、precise-definition（📌知识锚定）、scenario-hook（🎬场景）、vocabulary-dimension（🎯弹药库词汇表）、cross-ref-trace（🔗跨单元连接表）
**拒绝**：judgment-card、quick-judgment（英语不考判断题）、fact-vs-judgment（英语无判断vs事实分离需求）

---

## 全部卡索引（按教学问题分组）

### 概念锚定类（concept-anchoring/）
| 卡 | 解决什么问题 |
|---|---|
| precise-definition | 权威术语/公式/分类怎么呈现才防幻觉又促理解（原文+大白话双讲） |
| misconception | 学习者的常见误区怎么提前暴露和拆解 |
| socratic-questioning | 怎么设计提问路线图引导学生自己推导 |
| fact-vs-judgment | 确定性知识（要背）和判断（要推理）怎么分离才不混淆 |
| depth-elaboration | 核心概念怎么写才有深度（机理/脉络/边界/专家视角） |

### 评估/练习类（assessment/）
| 卡 | 解决什么问题 |
|---|---|
| judgment-card | 有明确权威偏好的判断题怎么呈现（首选+why-not+判断依据） |
| quick-judgment | 限时/短情境选择题怎么设计教反射 |
| application-problem | 长情境多步推理题怎么设计 |
| worked-example | 例题/代码/计算题怎么做"示范解题" |
| practice-gradient | 练习怎么按 recall→transfer→open 梯度分层 |
| deterministic-anchor | 必背/确定知识清单怎么组织 |

### 叙事结构类（narrative/）
| 卡 | 解决什么问题 |
|---|---|
| scenario-hook | 章首怎么用具体情境开章 |
| running-case | 怎么用一个贯穿案例做连续情境语料 |
| character-protagonist | 要不要用主角/第二人称戏剧化 |

### 整书架构类（structure/）
| 卡 | 解决什么问题 |
|---|---|
| foundation-chapter | 要不要为其他章单独设"判断根供给"地基章 |
| capstone-chapter | 要不要设总结/收网章 |
| cross-ref-trace | 跨章引用用什么形式（行内回溯/连接表） |
| appendix-compilation | 附录从哪些章末板块汇编、怎么汇编 |
| multi-source-arbitration | 多份权威源冲突时怎么表述和裁决 |
| recurring-leitmotif | 贯穿全书的主题低音线怎么设（非人物非案例） |

### 语言学习特化（language-learning/）
| 卡 | 解决什么问题 |
|---|---|
| vocabulary-dimension | 词汇怎么按 L1-L4 分层管理 |
