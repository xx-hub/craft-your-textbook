# 练习三级梯度（Practice Gradient）

## 解决什么教学问题
章末练习怎么按认知梯度分层设计，从记忆到迁移到开放推理，而不是平铺一堆同构题。

## 什么时候用 / 什么时候不用
- 用：章末有练习题/教学脚本时（几乎所有书）
- 不用：纯参考手册/字典式工具书（没练习）
- 典型搭配：quick-judgment、application-problem、deterministic-anchor——梯度决定这些卡的题在章末怎么排

## 长什么样（结构示例）

CPA Ch1 章末（三级梯度的典型）：
```markdown
### Concept Check  ← recall 层：记忆/识别
[3 道选择题，考核心概念记忆]

### Application Problems  ← transfer 层：应用/迁移
[2 道多步推理题，考多概念综合应用]

### Think Deeper  ← open reasoning 层：开放推理
[2 道讨论题，没有唯一答案，考批判性思考]
```

> ⚠️ **这些英文块名只属于 blueprint 档「带读手册」内部**：它们住在章末 H2 教学区里、
> 带读手册四个子项之二的「三档题与提示分级」下面。human 档的教学区**零改动**——原样保留
> 本书自己的三层问题链（如「回忆层／迁移层／开放层」），⛔ 不套用本卡的英文块名。
> 正文（教学区之前）是给人读的散文，⛔ 不出现 `Concept Check`／`Think Deeper` 这类「短行＋冒号」
> 块头；本书板块表声明的是中文名时，手册内部也用本书声明的名字。契约的 H2 那一份：
> 本仓 dsh＝`resources/references/invariants.md`／skill 侧＝`references/invariants.md`；「带读手册」见 `file-contracts.md`。

PMP 章末（二级梯度，认证类不需要开放讨论）：
```markdown
### 探索脚本：引导式问题链  ← recall+transfer
[8 问，从情境暴露直觉→推导出 PMI 取向]

### 速判脚本  ← transfer+反射
[5 道四选一短情境，考跨行业迁移的反射]
```

三级梯度（由浅到深）：
1. **Recall/记忆层**：核心概念识别、事实确认、术语回忆。Concept Check/探索脚本前半。
2. **Transfer/迁移层**：把概念用到新情境、跨领域迁移、多概念综合。Application Problems/速判脚本。
3. **Open Reasoning/开放推理层**：无唯一答案的讨论题、批判性反思、边界探讨。Think Deeper。

### PMP 与 CPA 的梯度差异
- **PMP（认证类）**：二级梯度（探索脚本 → 速判脚本）。不需要 open reasoning 层——考试不考开放讨论，需要的是从暴露直觉到形成反射。
- **CPA（叙事教材）**：三级梯度全有（Concept Check → Application Problems → Think Deeper）。入门教材需要 recall 打底、transfer 练手、open reasoning 培养批判性思维。

## 已知陷阱
- ❌ 所有题在 recall 层（"什么是 X？""定义 Y"）→ 学生背得熟但不会用
- ❌ 一开始就 open reasoning → 学生没地基讨论不出东西
- ❌ 三级都必须有 → 认证类书（如 PMP）可两级，入门读物可三级全有

## 变体
- **认证类**：二级（探索→速判），不需要 open reasoning（考试不考）
- **技能类**：二级（worked-example 示范→application-problem 练习）
- **叙事教材**：三级全有

## 不要这样用
- ❌ 把梯度当硬模板每章必套三级——按书的教学目标选级数