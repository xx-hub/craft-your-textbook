# 两条路线决策指引

> 设计期路线决策的依据和两路线差异详解。
> SKILL.md 只给一句话推荐，完整决策启发式和差异都在这里。
> **路线 id 取 `blueprint` / `human`**（写进 `meta.route` 的机器取值）；`pure-blueprint` / `human-readable` 是产品/路线名，**不是 `meta.route` 的值**。
> ⚠️ **但写作规范里那一行 `format:` 两套写法都认**（票 `skill-release-ready/09` 走查实测）：skill 侧的装配脚本 `merge_book.py` 把 `blueprint`／`pure-blueprint` 都归一成 blueprint、把 `human`／`human-readable` 都归一成 human-readable。推荐写这里的机器 id；写路线名也照常工作。

---

## 一、决策启发式

按优先级命中即走：

1. 用户原话含"我自己读/出版/给别人看/当书出/通读/给真人教师/我想先通读" → **human-readable**，告知理由
2. 书要喂给已成型的苏格拉底 AI 软件（Socratopia 平台等） → **pure-blueprint**
3. 用户不确定 → Agent 推荐 pure-blueprint（AI 教学精度最高），等用户拍板

不要替用户默认——必须在对话里呈现选择并等用户确认。

```dot
digraph route {
    rankdir=TB;
    "用户要造书" [shape=box];
    "原话含'我自己读/出版/当书出/给真人教师/通读'?" [shape=diamond];
    "喂给已成型的苏格拉底 AI 软件?" [shape=diamond];
    "human-readable" [shape=box];
    "pure-blueprint" [shape=box];
    "呈现两路线 + 推荐 pure-blueprint，等用户拍板" [shape=box];

    "用户要造书" -> "原话含'我自己读/出版/当书出/给真人教师/通读'?";
    "原话含'我自己读/出版/当书出/给真人教师/通读'?" -> "human-readable" [label="是"];
    "原话含'我自己读/出版/当书出/给真人教师/通读'?" -> "喂给已成型的苏格拉底 AI 软件?" [label="否"];
    "喂给已成型的苏格拉底 AI 软件?" -> "pure-blueprint" [label="是"];
    "喂给已成型的苏格拉底 AI 软件?" -> "呈现两路线 + 推荐 pure-blueprint，等用户拍板" [label="否/不确定"];
}
```

> **注意**：图里"呈现两路线 + 等确认"不是捷径的默认箭头——即使命中推荐，也必须把选择摆在用户面前等拍板。

---

## 二、两路线核心差异

| 维度 | pure-blueprint | human-readable |
|---|---|---|
| 第一读者 | AI 老师 | 人类读者（AI 第二读者） |
| 路线专属内容不变量 | I1-I6 | I1-I4 + H1-H3 |
| 过程不变量 | I7-I9（两条路线同等适用，见 invariants.md） | I7-I9 |
| 正文形态 | 结构化、可含元指令块、技术回溯、yaml frontmatter、emoji 标题 | 流畅 prose，不内嵌元指令 |
| 教学路线图位置 | 散布于各板块（💬引导方向/双脚本等） | 集中在章末教学区 |
| 章级 frontmatter | 可选且常用（grep 校验用） | 默认无，由写作规范显式声明 |
| 典型样本 | 英语七上教材 | PMP 认证教材、CPA 审计教材 |

> 表头两列用路线名；写进 `meta.route` 的机器 id 是 `blueprint` / `human`（见文首）。

---

## 三、板块语法设计差异要点

### pure-blueprint
- 元指令块可以出现在章内任何位置（如 PMP 的"【AI 老师提问脚本】"在章末，但英语教材的 💬引导方向在 📌知识锚定之下）
- 可以用 emoji 标题（🎬🧭📌…）做结构化标记，AI 解析高效
- yaml frontmatter 承载章级元数据（任务锚定/章节类型等），方便 grep 校验
- 技术回溯行内标注（"回溯 Ch2 原则6"）直接写在正文

### human-readable
- 正文读起来像一本正常的书——段落过渡、叙事桥梁、人物/案例展开
- 章末教学区是独立板块（markdown 二级标题分隔），包含练习/讨论题/思考题
- 技术回溯改为可读的交叉引用（"正如第 2 章讨论过的……"而非行内标签）
- Loader 指令（合并时由**装配脚本**自动注入成品书顶部——skill 侧是 `merge_book.py` 的 `LOADER_TEMPLATE`，本仓无脚本、由成品书的 `<!-- loader:begin -->` 区承载——可在那一处定制措辞）：

```
> **AI 老师使用说明**：本书是给人读的流畅教材。正文 prose 是素材库，用你自己的话重组教学；
> 每章末尾的思考题/练习区是提问路线图，请照那些问题的层次引导学生。
```

---

## 四、终检项目差异

交付前终检：
- **pure-blueprint**：检查必含板块计数、提问路线图齐备、yaml frontmatter 合法、无脚手架残留
- **human-readable**：检查章末教学区齐备、正文 prose 无内嵌元指令残留、loader 指令注入、无脚手架残留

---

## 五、诚实推荐

当用户不确定时推荐 pure-blueprint 的理由：
1. 这是 skill 的核心定位——为 AI 老师造教学蓝本
2. 结构化元指令让 AI 教学质量更可控
3. human-readable 的教学约束更少，更依赖 AI 老师自身发挥，质量方差更大

但不强制——如果用户明确要人读的体验，human-readable 是完全合法的产物。
