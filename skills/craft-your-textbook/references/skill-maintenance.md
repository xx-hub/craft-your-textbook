# 维护本 skill：RED-GREEN-REFACTOR 编辑规矩

> 改本 skill 跟改代码一样要 TDD。**没跑基线不许改；改后重测全绿才收工。**

## 铁律

**NO SKILL EDIT WITHOUT A FAILING TEST FIRST**（改哪条纪律就跑哪个场景）。

改本 skill 的纪律/结构 = 改文档。文档也会"漂"——不测试就改，等于盲改。原则：**如果你没看过 agent 在没有这条规则时怎么翻车，你就不知道这条规则在防什么。**

> **派工口径（仅 dsh 形态 · 本节只对造书工作台读者有效）**：日常造书派工按 `references/mechanism.md` §派发（`workbench_act(action=agent-assign, dispatchKind=…)`）；skill 侧没有派单机器，按 SKILL 正文直接派子代理。**压力场景仍用 fresh subagent**——下面流程里说的 `spawn fresh subagent` 是跑测的派工，不是日常造书的派工路径。
>
> ⚠️ **skill 侧读者读到这里就停**：上面那句里的 `workbench_act(...)` 是**造书工作台（dsh）的命令**，你手上没有这个工具、也不要照抄去执行。skill 侧日常派工＝按 SKILL 正文直接派子代理；`spawn fresh subagent` 对两种形态都成立（那是跑压力测试的派工，不是日常造书路径）。

## 流程（RED-GREEN-REFACTOR）

1. **RED（基线）**：改之前，用 `tests/` 里覆盖改动范围的压力场景跑当前 skill——`tests/pressure-*.md`，spawn fresh subagent（模型钉死、场景文本冻结），记录行为。违规 = RED。
2. **GREEN（改）**：按翻车点改 skill。**借口表只收实测原话**——编造借口 = 交付物造假。新增红旗/借口表条目必须能指回一条真实跑测记录。
3. **REFACTOR（重测）**：带改后的 skill 重跑同一场景，≥2 次复现。新翻车点 → 补计数器 → 再重测。封顶 3 轮。
4. **全绿判据**：同场景同模型下 ①选择正确 ②引用加固条款 ③承认诱惑但守规则。

## 跑测控制

- fresh subagent，绝不复用（防污染）
- 模型钉死（RED/GREEN/REFACTOR 同一模型，比较才有效）
- 场景文本冻结，不中途改（改场景本身 = 重新走一遍整个流程）
- 通过场景 ≥2 次复现（单次会撒谎）
- 跑测记录写 `tests/README.md` 战役日志（含场景 hash 防漂移）

## 各宿主技能目录

`SKILL.md` 是纯 Markdown 技能：**任何能读技能目录的 agent 都能装**，装法都是「把整个 `craft-your-textbook` 文件夹放进那个目录」。差别只在目录名：

| 宿主 | 用户级技能目录 | 说明 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | 项目级形态是 `<项目>/.claude/skills/`；已知宿主里只有它支持插件市场安装（`/plugin marketplace add` ＋ `/plugin install`，2026-11-04 核） |
| 造书工作台（dsh） | `~/.dsh/skills/` | 这里是它的**技能**目录；模式不走这个目录（dsh 的模式由插件包里的声明行在启动时算出，不需要在盘上建目录） |
| Hermes | `~/.hermes/skills/<分类>/` | 目录下再分一层分类（如 `~/.hermes/skills/mattpocock/`），技能文件夹放分类层里 |
| 其余 | 见它自己的文档 | 判断标准只有一条：那个目录里的文件夹，能以 `SKILL.md` 为入口被找到 |

skill 侧那份 README（组装后落在包根）**不写这张表**：它是给终端用户的一页纸，只给 Claude Code 那一格当例子。⛔ 别把本表抄进那份 README——它的正文不许出现 `dsh`（机器判据只禁这一个词；其余宿主名靠人守，别为了「通用」给某一家的名字开新口子）。

## 发布前实测台账

skill 侧 README 的装法节只留两处极短标注；每条命令**在哪台机器、验到什么程度**记在这里。原句逐条照抄改写前的那一份（`1aaada6c:skill/README.md` 里「实测」出现 **10** 次、分布在 **9** 行上；其中 `:78` 那一行长句里有 2 次），今天的落点写在同一行。

### 落点一：装法节末那一行（「① 拷目录」之后）

合并了原文 `:34 :35 :44 :52 :59` 这 5 条（取样：`git show 1aaada6c:skill/README.md | sed -n '34p;35p;44p;52p;59p'`，下同）：

| # | 原句（改写前） | 结论 |
| --- | --- | --- |
| 1 | 已按产物实测（2026-11-04）：把刚组装好的产物目录当一个本地仓库 clone 下来，三条命令全部返回 0。clone 出来的可见顶层是 `LICENSE`、`README.md`、`skills`（另有隐藏项 `.claude-plugin/`、`.gitignore`、`.git/`，安装用不到）。自查那行打印 `<用户目录>/.claude/skills/craft-your-textbook/SKILL.md`；装完目录里是 `SKILL.md`、`README.md`、`references/`、`scripts/`、`tests/`。 | **实测通过**（夹具仓＝组装产物，非真网址） |
| 2 | ⚠️ 没实测的那一段：`git clone` 走的是**真网址**（`https://github.com/xx-hub/craft-your-textbook.git`）还是本地夹具仓——真网址只验证了可达（`git ls-remote` 拿到 HEAD），没有把整棵树拉下来；仓里的内容用组装产物代替，两者应当是同一份。 | **没实测**（真网址只到「可达」） |
| 3 | 已按产物实测（2026-11-04）：`<项目>` 换成一个真目录后跑，`<项目>/.claude/skills/craft-your-textbook/SKILL.md` 就位。 | **实测通过** |
| 4 | 已按产物实测（2026-11-04）：链接指向 clone 目录，`readlink -f .../SKILL.md` 解析到真文件。⚠️ 同一个位置只留一个：已经 `cp` 过就先删掉那份再建链接，两个同名目录不能共存。 | **实测通过** |
| 5 | 压缩包这条：**未实测**——写这份说明的机器没有图形界面，点不了 `Code → Download ZIP`。它下到的就是 `git clone` 拿到的同一棵树，解压后的结构与上面一样（`skills/craft-your-textbook/`）。 | **没实测**（要图形界面） |

### 落点二：插件市场那两条之后

原文 `:68` 这 1 条（取样：`git show 1aaada6c:skill/README.md | sed -n '68p'`）：

| # | 原句（改写前） | 结论 |
| --- | --- | --- |
| 6 | 这两条**未实测**：写这份说明的机器上没有装 Claude Code，没法在它里面执行 `/plugin` 命令。命令本身是插件市场的标准写法，装完效果与「拷 skills 目录」相同；真跑过的只有上面那几条。 | **没实测**（机器上没有 Claude Code） |

### 落点三：第二步的两条（改成处置顺序后不再逐条标注）

原文 `:78 :93`（取样：`git show 1aaada6c:skill/README.md | sed -n '78p;93p'`）：

| # | 原句（改写前） | 结论 |
| --- | --- | --- |
| 7 | ⚠️ 这条**未实测成功（2026-11-04 收口走查又跑了一次，仍失败）**：在一台 Ubuntu 24.04 上跑，`pip` 以退出码 1 拒绝，报 `externally-managed-environment`（PEP 668，系统 Python 不许 pip 直接装包）。同一台机器上 `pip install --break-system-packages requests` 返回 0（那台本来就有）。**`--user` 也挡不住**——同一天实测 `pip install --user requests` 同样退出 1、同一个 PEP 668 提示（先前这行写「或用 `--user`」，是错的，已改）；`python3 -m venv` 也建不起来（缺 `python3-venv`，报 `ensurepip is not available`）。⇒ **真跑成功过的只有「脚本会明确报错并让你装」这一半**（`01_pdf_to_md.py` 缺库时打印「请先安装：pip install requests」后退出，不是悄悄失败）；`pip install requests` 在**你的**机器上跑不跑得通，取决于你用的 Python 是怎么装的——Mac／Windows 的官方 Python、或任何虚拟环境里，它通常是可用的；Linux 发行版自带的系统 Python 会用 PEP 668 挡住你，那时要么装 `python3-venv` 建虚拟环境，要么用 `--break-system-packages`（**它真的动系统 Python**，在你自己机器上再决定）。 | **实测失败**（PEP 668；`--user` 同样失败；`--break-system-packages` 通过但本机已有该库）。已按执行附录的口径改成三步处置顺序，并删掉「`python3 -m venv` 也建不起来」这句普遍化断言——那是缺 `python3-venv` 的一次本机事故 |
| 8 | 拿 Token 这一步**未实测**：要注册账号，写这份说明时手上没有 token。 | **没实测**（要注册账号）。这一条是「没账号」，与命令对不对无关；README 里的正向说法（Token 只走环境变量）另有 `01_pdf_to_md.py` 的缺变量提示句背书 |

### 落点四：第三步那一节（改成一句指路，不再标「未实测」）

原文 `:107`（取样：`git show 1aaada6c:skill/README.md | sed -n '107p'`）：

| # | 原句（改写前） | 结论 |
| --- | --- | --- |
| 9 | 这一节**未实测**：要在 Claude Code 里真发一轮对话才算，写这份说明的机器上没有 Claude Code。问路线、三个拍板关卡、章节建议，都在安装后的 skill 说明里写着（`SKILL.md` 与 `references/`）。 | **没实测**（机器上没有 Claude Code）。它描述的是流程，不是一条命令，改写后并入正文的一句指路 |

计数对账：改写前 **10** 次（分布在 9 行上）、改写后 **1** 次（1 行）。这两个数是**当日读数**，⛔ 不写进任何判据；重跑要在本仓源码树里跑（`git show <改写前那个提交>:skill/README.md | grep -o '实测' | wc -l` 与 `grep -o '实测' skill/README.md | wc -l`）——随包发布的这一份没有 git 历史，那两条命令在包里跑不出来。

## 工作示例：2026-08-05 改造战役（v2.1.0 → v3.0.0）

本 skill 的 v3.0.0 改造就是这么做的：

- **RED**：6 场景 × 当前 skill，6/6 已守——但每跑逐字供述了内心诱惑（"你看着办就是授权""设计扎实不用金标准""我审过就是审计"……）
- **供述诱惑 → 加固**：anti-patterns 6 条红旗 + 借口表（每条借口可溯源到跑测记录）
- **GREEN**：SDO description、铁律置顶、流程图、速查表、prompt 模板、试教改造
- **REFACTOR**：12 跑（6 场景 × 2 复现）全绿，每跑引用新加固条款作为管住自己的依据
- 完整战役记录：`docs/superpowers/reform-trace.md`（git-ignored 工作产物）

## 改动分类与测试流派

| 改动类型 | 用什么验证 |
|---|---|
| 纪律规则（铁律/红旗/借口表/审计纪律） | `tests/pressure-*.md` 压力场景 |
| description / 触发词 | 检索测试（给触发请求看是否加载 skill + 跟随正文而非 description） |
| 模板/契约（prompt 模板/质量门） | 形状测试（槽位齐全、单一事实源） |
| 流程图/速查表 | 可用性检查（按图走一遍能到终点） |
