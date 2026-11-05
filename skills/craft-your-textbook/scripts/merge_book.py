# -*- coding: utf-8 -*-
"""
合并脚本【示例模板】：将 chapters/ 下所有章 + appendix/ 下所有附录合并为 BOOK.md。

★★ 本文件是示例模板。造书时复制进项目（<项目根>/scripts/）→ 按需改顶部 LOADER_TEMPLATE 再跑。
    脚本自动扫描 chapters/ 和 appendix/ 目录，按文件名字典序合并。

用法：
    python merge_book.py [项目根目录] [--strip-frontmatter]

设计要点：
- 读 META.md 顶部 YAML format 字段判断路线
- human-readable 路线在 BOOK.md 顶部注入 loader 指令
- 可重跑
- ⚠️ 合并前先核「章正文是不是当前分片拼出来的」（票 `skill-release-ready/14`）：分片与章正文之间
  那一跳（`assemble_chapter.py`）原先不在任何判据的射程里——改一片分片、不重拼、只再 merge，
  前后 `md5sum BOOK.md` **完全相同**，而书里还是旧正文。所以本脚本在写 BOOK.md 之前把每一章的
  章正文与「按分片重拼一遍」的结果逐字比；不一致（或只有分片、没有章正文）就非零退出并点名，
  一个字节都不写。⛔ 它**不替你重拼**（那是 `assemble_chapter.py` 的活），只把退路放在工具里。
"""
import os
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_BASE_DIR = "."


# 路线取值有两套写法，**两套都要认**（票 `skill-release-ready/09` 走查实测的静默分叉）：
# `references/two-routes.md` 顶部写死「路线 id 取 `blueprint` / `human`」（写进 `meta.route` 的
# **机器取值**），而本脚本历史上只认 `pure-blueprint` / `human-readable`（那是路线**名**）。
# 按文档写 `format: human` 时，旧代码静默判成 pure-blueprint、loader 一个字不注入，退出码照样 0
# ——「文档说是什么」与「盘上实际是什么」对不上，而且两边都不报错。归一化只认这四写法，
# 遇到别的值原样返回（主笔看得见自己写错了，不替它猜）。
ROUTE_ALIASES = {
    "blueprint": "pure-blueprint",
    "pure-blueprint": "pure-blueprint",
    "human": "human-readable",
    "human-readable": "human-readable",
}


def read_meta_format(base_dir):
    """读 META.md 顶部 YAML 的 format 字段（机器 id 与路线名都认，见 `ROUTE_ALIASES`）。"""
    meta_path = Path(base_dir) / "META.md"
    if not meta_path.exists():
        return "pure-blueprint"
    content = meta_path.read_text(encoding="utf-8")
    # 匹配顶部 --- ... --- 之间的 YAML
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return "pure-blueprint"
    yaml_text = m.group(1)
    fm = re.search(r"^format:\s*(.+)$", yaml_text, re.MULTILINE)
    if not fm:
        return "pure-blueprint"
    return ROUTE_ALIASES.get(fm.group(1).strip().strip("'\""), fm.group(1).strip())


# 只有这种名字才算**章正文**（`assemble_chapter.py` 写出来的就是它）。`chapters/` 下别的
# `.md`（审计报告、进度账、笔记）一律不进 BOOK.md——它们是过程件，不是书的内容。
CHAPTER_FILE_RE = re.compile(r"^chapter-\d+\.md$")

# 分片名的**识别口径**与 `assemble_chapter.py` 那一条正则一致（序号位是 `\d+`，不是恰好两位：
# 宁可认下，也别把写者少补一个零的东西静默丢掉）。⛔ 别在这里另写一个更窄的正则——两处口径分家时，
# 拼章脚本认得出的片、合并脚本看不见，guard 就会对着一批「没有分片」的章放行。
# ⚠️ **只同步「名字怎么认」，不同步「片怎么判」**：拼章脚本还判片号重复与空片，本脚本不判
# （见 `load_shard_groups` 的窄处；那两条归拼章脚本）。
SHARD_FILE_RE = re.compile(r"^chapter-(\d+)-(\d+)\.md$")
SHARD_DIR_PARTS = ("chapters", "shards")


def load_chapters(base_dir):
    """递归扫描 chapters/ 下所有 *.md（排除进度 ledger progress.md 与分片目录），按文件名字典序排序。

    ⚠️ `chapters/shards/` 是**章正文的原料**，不是章（票 `skill-release-ready/12`）：不排除它，
    拼好的 `chapters/chapter-NN.md` 与它那几片分片会被各收一遍 ⇒ BOOK.md 里同一段正文出现两次。
    只改**输入面**，合并顺序与章节语义一个字没动。
    """
    chapters_dir = Path(base_dir) / "chapters"
    if not chapters_dir.exists():
        return []
    files = []
    skipped = []
    # ⚠️ **只认 chapters/ 直属层**，不用 `rglob`（票 09 收口 review 抓到的）：`rglob` 会把
    # `chapters/_旧版产物/chapter-01.md` 这类归档副本也当章收进来，同一章在书里出现两遍。
    # `shards/` 因此天然不在面内（它是一层子目录），不必再单独排除——本条由「一位数分片名」
    # 与「分片不进书」两格判据守着。
    for f in sorted(chapters_dir.glob("*.md")):
        if f.name == "progress.md":
            continue
        # ⚠️ 审计报告不是章（票 `skill-release-ready/09` 走查实测：`chapters/audit-01.md`
        # 会被当章收进 BOOK.md，书里凭空多一节「# 第 1 章审计报告」）。章正文的名字是
        # `chapter-<NN>.md`（见 `assemble_chapter.py`）。
        if CHAPTER_FILE_RE.match(f.name):
            files.append(f)
        else:
            skipped.append(f)
    # ⚠️ 被排除的要**说一声**（票 09 走查的教训：静默排除会让「我明明写了章却没进书」
    # 变成一个查不出来的黑洞）。这条 warn 只印不判——`preface.md` 这类有意为之的
    # 非章文件不该让合并失败，但写错名字的章必须被人看见。
    for f in skipped:
        print(f"[warn] 跳过（不是章正文 chapter-<NN>.md）：{f}", file=sys.stderr)
    return files


def load_appendices(base_dir):
    """扫描 appendix/ 下所有 *.md，按文件名字典序排序。"""
    app_dir = Path(base_dir) / "appendix"
    if not app_dir.exists():
        return []
    files = sorted(app_dir.glob("*.md"))
    return files


def load_shard_groups(base_dir):
    r"""`chapters/shards/` 下的分片按章号分组（认名字的**形状**与 `assemble_chapter.py` 相同）。

    只读**一层**、只认 `chapter-<NN>-<MM>.md`（序号位 `\d+`）。子目录里的、名字不像分片的一律
    看不见——与拼章脚本同一个窄处，guard 不在这里比它多认几种名字（多认一种就是两套口径）。
    返回 `{章号: [{"m": 片号, "path": Path}, …]}`，每组已按片号升序。

    ⚠️ **它只照名字分组，不重判分片的形状**（票 `skill-release-ready/14` 的 standard review 抓到
    这里原先自称「同一枚举面」，那是**假话**）：`assemble_chapter.py` 还会因**片号重复**
    （`chapter-02-01.md` ＋ `chapter-2-1.md`）与**空片**非零退出，本函数对那两种不判——重号的两片会
    各算一片、空片照收。那两条是拼章脚本的红，不是本 guard 的（本 guard 只比「正文是不是这几片按
    接缝拼出来的」）。实际后果：重号／空片时正文多半与旧正文对不上 ⇒ 本 guard 仍会红，只是点名的
    是「不一致」，要人去跑 `assemble_chapter.py` 才看到那条精确的「片号重复」／「空片」报错。
    """
    shard_dir = Path(base_dir).joinpath(*SHARD_DIR_PARTS)
    if not shard_dir.is_dir():
        return {}
    groups = {}
    for entry in sorted(shard_dir.iterdir()):
        if not entry.is_file():
            continue
        matched = SHARD_FILE_RE.match(entry.name)
        if matched is None:
            continue
        n = int(matched.group(1))
        m = int(matched.group(2))
        if n < 1 or m < 1:
            continue
        groups.setdefault(n, []).append({"m": m, "path": entry})
    for shards in groups.values():
        shards.sort(key=lambda shard: (shard["m"], shard["path"].name))
    return groups


def outdated_chapter_problems(base_dir):
    """逐章核「章正文是不是当前分片拼出来的」。返回问题清单，空数组＝这趟合并的输入是新的。

    ⚠️ 名字说的是**这一格要判的事**（章正文过期了没有），判法比名字宽：它比的是**内容**是否
    逐字相等，不是 mtime（「新／旧」在下面那段解释为什么不能用 mtime 判）。

    ## 病（票 `skill-release-ready/14`）

    文档第 ⑦ 项原来说「交付前重跑 `merge_book.py`，前后 `md5sum BOOK.md` 相同 ⇒ 过」。但 md5 只证
    「merge 前后成品没变」，证不到「成品里是**当前**分片拼出来的」：改一片分片、**不重拼**、只再
    merge 一次 ⇒ 前后 md5 **完全相同**，而 `BOOK.md` 里还是旧正文。分片与章正文之间那一跳
    （`assemble_chapter.py`）原先不在任何判据的射程里。

    ⇒ 判据落在**合并的输入面**上：章正文必须逐字等于「当前那几片分片按拼章口径拼出来的结果」。
    不是 ⇒ 这一趟 merge 非零退出、点名第 N 章，并且**一个字节都不写**（不替人重拼，也不把旧内容
    再抄一遍；重拼是 `assemble_chapter.py` 的活）。没有分片目录的老书不在面内（那里章正文自己
    就是写作单元，没有「重拼」这一步）。

    ⚠️ **比内容，不比 mtime**：「分片新于章正文」只是**最常见的形状**，不是判据本身——mtime 会被
    `git checkout`、复制、跨盘搬运整体推后（`touch` 一下也会动），照 mtime 判会假红（内容没变却
    逼人重拼）也会假绿（mtime 没变而内容变了）。内容逐字相同就是「不需要重拼」那一档，
    `assemble_chapter.py` 对同一输入也是幂等不写。
    """
    problems = []
    groups = load_shard_groups(base_dir)
    if not groups:
        return problems
    for n in sorted(groups):
        shards = groups[n]
        # 章正文只认**拼章脚本写出来的那个名字**（零填充 `chapter-<NN>.md`）。
        # ⚠️ 我的枚举面比现实窄在哪里：① 手写的、不补零的 `chapter-1.md` 不被当成第 1 章的拼装件
        #   ——`assemble_chapter.py` 永远写 `chapter-01.md`，两者同时在场时合并会把它俩当两章收
        #   （那是合并输入面本来的歧义，不是本 guard 该替它选边的事）；② 片号重复时本 guard 不判
        #   「重号」，只按名字顺序拼出一份 `want` 去比 ⇒ 那一趟照样红，但点名的是「不一致」，要人
        #   跑 `assemble_chapter.py` 才会看到它自己那条「片号重复」的精确报错（重号归拼章脚本判）。
        chapter_rel = f"chapters/chapter-{n:02d}.md"
        chapter = Path(base_dir) / "chapters" / f"chapter-{n:02d}.md"
        shard_dir_rel = "/".join(SHARD_DIR_PARTS)
        pieces = []
        unreadable = False
        for shard in shards:
            try:
                text = shard["path"].read_bytes().decode("utf-8")
            except (UnicodeDecodeError, OSError):
                problems.append(
                    f"第 {n:02d} 章的分片读不出来（不是 UTF-8 或没有读权限？）："
                    f"{shard_dir_rel}/{shard['path'].name}"
                )
                unreadable = True
                continue
            # 与 `assemble_chapter.py` 的 render() 同一个**拼接口径**：只补「这一片没写尾换行」的
            # 那一个 \n，片间一个空行；不 trim、不归一空白。⛔ 两处口径分家时，guard 会对着一份拼不
            # 出来的章正文放行。⚠️ 这条「同口径」有判据兜着：test-skill-assemble-chapter 的 `⑦ 盲区③附`
            # 用**真脚本**拼出正文、再喂给本 guard，两侧 render 一旦漂移那一格当场红。
            if not text.endswith("\n"):
                text += "\n"
            pieces.append(text)
        if unreadable:
            continue
        want = "\n".join(pieces)
        if not chapter.is_file():
            problems.append(
                f"第 {n:02d} 章只有分片、没有章正文：{chapter_rel} 不在盘上 —— "
                f"先跑 python scripts/assemble_chapter.py .（或 --chapter {n}）把它拼出来，再重跑本脚本"
            )
            continue
        existing = chapter.read_bytes().decode("utf-8", errors="replace")
        if existing != want:
            problems.append(
                f"第 {n:02d} 章的章正文不是当前分片拼出来的：{chapter_rel} 与 {shard_dir_rel}/ 里那几片"
                f"重拼的结果不一致（改了分片但没重拼？）—— 先跑 python scripts/assemble_chapter.py ."
                f"（或 --chapter {n}）重拼章正文，再重跑本脚本；⛔ 别手改 {chapter_rel}"
            )
    return problems


def strip_frontmatter(content):
    """剥离 YAML frontmatter（--- ... ---）。"""
    return re.sub(r"^---\s*\n.*?\n---\n?", "", content, count=1, flags=re.DOTALL)


LOADER_TEMPLATE = """> **AI 老师使用说明**：本书是给人读的流畅教材。正文 prose 是素材库，用你自己的话重组教学；
> 每章末尾的思考题/练习区是提问路线图，请照那些问题的层次引导学生。

---

"""


HELP = """合并脚本：把 chapters/ 与 appendix/ 下所有 *.md 合并成 BOOK.md（按文件名字典序）。

用法：
    python merge_book.py [项目根目录] [--strip-frontmatter]

- 路线读 META.md 顶部 frontmatter 的 `format:`：`human`／`human-readable` 注入 loader 指令，
  `blueprint`／`pure-blueprint` 不注入（两套写法都认，见 ROUTE_ALIASES）。
- **合并前先核章正文是不是当前分片拼出来的**：`chapters/shards/` 里某章有分片、而章正文与「按分片
  重拼」的结果不一致（或章正文根本不在）⇒ 非零退出、点名第 N 章、**一个字节都不写**。它**不替你
  重拼**：先跑 `python scripts/assemble_chapter.py .` 重拼章正文，再重跑本脚本。
- 可重跑；⛔ 别手改 BOOK.md——改了下次合并就被覆盖。

⚠️ 它合并**章正文**（chapters/chapter-<NN>.md），不合并 chapters/shards/ 里的分片。
"""


def main():
    # `--help` 只印用法、一个字节都不写（票 `skill-release-ready/09` 走查实测：它原先落进
    # 下面那条「无参数 ⇒ 合并 0 章」的路，把盘上已有的 BOOK.md 清成 0 字节、退出码还是 0）。
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(HELP, end="")
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    base_dir = args[0] if args else DEFAULT_BASE_DIR
    do_strip = "--strip-frontmatter" in flags

    fmt = read_meta_format(base_dir)
    chapters = load_chapters(base_dir)
    appendices = load_appendices(base_dir)

    # ⚠️ **合并前先核输入是新的**（票 `skill-release-ready/14`）：改了分片但没重拼时，只再 merge
    # 一遍前后 md5 完全相同、书里还是旧正文。有错就**一个字节都不写**（这条判据的全部意义就是不让
    # 旧内容再被抄一遍）。
    outdated = outdated_chapter_problems(base_dir)
    if outdated:
        for problem in outdated:
            print(f"[error] {problem}", file=sys.stderr)
        print("（有错时一个字节都不写：没有替人重拼，也不把旧章正文再抄一遍——"
              "先跑 assemble_chapter.py 重拼，再重跑本脚本）", file=sys.stderr)
        return 1

    parts = []
    if fmt == "human-readable":
        parts.append(LOADER_TEMPLATE)

    for ch in chapters:
        content = ch.read_text(encoding="utf-8")
        if do_strip:
            content = strip_frontmatter(content)
        if not content.endswith("\n"):
            content += "\n"
        parts.append(content)
        parts.append("\n---\n\n")

    if appendices:
        parts.append("# 附录\n\n")
        for ap in appendices:
            content = ap.read_text(encoding="utf-8")
            if do_strip:
                content = strip_frontmatter(content)
            if not content.endswith("\n"):
                content += "\n"
            parts.append(content)
            parts.append("\n")

    output_path = Path(base_dir) / "BOOK.md"
    # 一章都没有时**不写盘**（票 `skill-release-ready/09` 走查实测：空目录跑一次 merge 会留下
    # 一个 0 字节 BOOK.md、exit 0，看起来像「合并成功」）。真正的空书只在全书确实没内容时成立，
    # 而那时用户要的是一个明确的错，不是一份 0 字节的成品。
    if not chapters and not appendices:
        print(f"[error] 没有可合并的章：{Path(base_dir) / 'chapters'} 下没有 chapter-<NN>.md，"
              f"{Path(base_dir) / 'appendix'} 下也没有 *.md —— 一个字节都不写", file=sys.stderr)
        return 1
    output_path.write_text("".join(parts), encoding="utf-8")

    size = output_path.stat().st_size
    lines = output_path.read_text(encoding="utf-8").count("\n")
    print(f"合并完成：{output_path}")
    print(f"路线：{fmt}")
    print(f"章数：{len(chapters)}，附录：{len(appendices)}")
    print(f"文件大小：{size:,} 字节 / {lines:,} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
