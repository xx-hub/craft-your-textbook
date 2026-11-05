# -*- coding: utf-8 -*-
"""
分片拼章脚本【示例模板】：把 chapters/shards/ 下按号落的分片拼成章正文。

★★ 本文件是示例模板。造书时复制进项目（<项目根>/scripts/）后直接用，通常不用改。

用法：
    python assemble_chapter.py [项目根目录] [--chapter NN]

- 读  chapters/shards/chapter-<NN>-<MM>.md（NN＝章号、MM＝这一路的号）
- 写  chapters/chapter-<NN>.md
- 按 MM 升序拼接，片间一个空行；**只拼不改**，正文一个字不动。

设计要点：
- 幂等：拼出来的内容与盘上 chapter-NN.md 逐字相同时**不重写**（mtime 不动，
  免得把下游「审的是旧稿」那种判据骗过去）。
- 三种情形**非零退出并点名**：该章一片没有／片号重复／片是空文件。有错时**一个字都不写**。
- 片号跳号（有 -01 有 -03）只 [warn] 不拦：主笔拆两路、第二路还没交是有意的。
- stdout 印三句可核对的话：片数、实际片号、字数合计。

⛔ **拼完不等于干净章**：本脚本**不删脚手架**（那是 strip_meta_sections.py 与交付前检查的活），
也**不做字数硬闸**（字数只印出来给主笔与审计读）。拼完还要走拆脚手架与交付前检查。
"""
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文 print 崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_BASE_DIR = "."
SHARD_DIR_PARTS = ("chapters", "shards")

# ⚠️ 分片号按「一位以上数字」认，不硬卡两位：写者少补一个零（chapter-1-1.md）照样认出来，
# 别把他的东西静默丢掉。代价是两份不同名的分片可能解出同一个号 ⇒ 那正是「片号重复」那一格，
# 由 collect() 当场点名，不静默拼两遍。
SHARD_RE = re.compile(r"^chapter-(\d+)-(\d+)\.md$")
HANZI_RE = re.compile(r"[\u4e00-\u9fff]")

HELP = """分片拼章脚本：把 chapters/shards/chapter-<NN>-<MM>.md 按 MM 升序拼成 chapters/chapter-<NN>.md。

用法：
    python assemble_chapter.py [项目根目录] [--chapter NN]

参数：
    项目根目录   含 chapters/ 的那一层，默认当前目录（造书项目根）。
    --chapter NN 只拼这一章（NN 可写 03 或 3）。省略时拼 chapters/shards/ 里出现过的每一章。
    -h, --help   印这段说明。

行为：
    - 片间一个空行；**只拼不改**，正文一个字不动。
    - 幂等：拼出来的内容与盘上 chapter-NN.md 逐字相同时**不重写**（mtime 不动）。
    - 三种情形非零退出并点名：该章一片没有／片号重复／片是空文件。有错时一个字都不写。
    - 片号跳号只 [warn] 不拦（主笔拆两路、第二路还没交是有意的）。
    - 分片号按「一位以上数字」认：规范写法是两位（chapter-01-02.md），写者少补一个零
      （chapter-1-2.md）也认得出、照样拼——宁可认下，也别把他的东西静默丢掉。
      代价：两个不同名却同号的分片（chapter-02-01.md 与 chapter-2-1.md）会按「片号重复」拦下。
    - stdout 印三句读数：片数、实际片号、字数合计；状态行与 [warn] 走 stderr。

⛔ **拼完不等于干净章**：
    - 不删脚手架（自检清单／版本记录／写作笔记这类元数据）——那是 strip_meta_sections.py
      与交付前检查的活；
    - 不做字数硬闸——字数只印出来给主笔与审计读，不达标不拦（也不逼人凑字数）。
    拼完整本仍走 merge_book.py（python scripts/merge_book.py .）——它会把 chapters/shards/
    当原料跳过、不重复收；别手改 BOOK.md。⚠️ 合并前它会先核「章正文＝当前分片的重拼结果」：
    改了分片没重拼时它会非零退出、点名第 N 章（票 `skill-release-ready/14`）——那一下就是在
    提醒你回来跑本脚本。
"""


def usage_error(message):
    """参数用错：退出码 2（与上面三种内容错区分开）。"""
    print(f"[error] {message}", file=sys.stderr)
    print("用法见：python assemble_chapter.py --help", file=sys.stderr)
    sys.exit(2)


def parse_positive_int(raw, flag):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        usage_error(f"{flag} 需要一个正整数，收到：{raw!r}")
    if value < 1:
        usage_error(f"{flag} 需要一个正整数，收到：{raw!r}")
    return value


def shard_dir_of(base_dir):
    return Path(base_dir).joinpath(*SHARD_DIR_PARTS)


def rel_shard(name):
    """报错用的可读路径：chapters/shards/xxx.md（跨平台都用正斜杠）。"""
    return f"{'/'.join(SHARD_DIR_PARTS)}/{name}"


def rel_chapter(n):
    return f"chapters/chapter-{n:02d}.md"


def collect(groups):
    """把「章号 → 分片列表」摊成 {n, shards}，同时收片号重复的问题。

    返回 (plans, problems)。problems 里的每一条都已带章号与文件路径。
    """
    plans = []
    problems = []
    for n in sorted(groups):
        shards = sorted(groups[n], key=lambda s: (s["m"], s["path"].name))
        seen = {}
        for shard in shards:
            m = shard["m"]
            if m in seen:
                problems.append(
                    f"第 {n:02d} 章片号重复：{rel_shard(seen[m])} 与 "
                    f"{rel_shard(shard['path'].name)} 都是第 {m:02d} 片 —— "
                    f"两片会拼成同一号（先并成一片，或把其中一份改号）"
                )
            else:
                seen[m] = shard["path"].name
        plans.append({"n": n, "shards": shards})
    return plans, problems


def read_shard(shard):
    """读一片；解码失败或读不动都算「读不出来」，不静默当空片。"""
    try:
        return shard["path"].read_bytes().decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def render(shards, texts):
    """按 MM 升序首尾相接，片间一个空行。

    ⚠️ 只补「这一片没写尾换行」的那一个 \\n（不补，两片会被粘成一行、正文里凭空多出一个错词）；
    除此之外不 trim、不归一空白、不碰正文一个字。
    """
    pieces = []
    for shard in shards:
        text = texts[shard["path"].name]
        if not text.endswith("\n"):
            text += "\n"
        pieces.append(text)
    return "\n".join(pieces)


def main():
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(HELP)
        return 0

    base_dir = DEFAULT_BASE_DIR
    chapter = None
    positional = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--chapter":
            index += 1
            if index >= len(argv):
                usage_error("--chapter 需要一个章号")
            chapter = parse_positive_int(argv[index], "--chapter")
        elif arg.startswith("--chapter="):
            chapter = parse_positive_int(arg.split("=", 1)[1], "--chapter")
        elif arg.startswith("-"):
            usage_error(f"不认识的参数：{arg}")
        else:
            positional.append(arg)
        index += 1

    if len(positional) > 1:
        usage_error(f"只接受一个项目根目录，收到：{' '.join(positional)}")
    if positional:
        base_dir = positional[0]

    shard_dir = shard_dir_of(base_dir)
    problems = []

    if not shard_dir.is_dir():
        target = f"第 {chapter:02d} 章" if chapter is not None else "任何一章"
        print(
            f"[error] 分片目录不存在：{'/'.join(SHARD_DIR_PARTS)} —— {target}一片分片都没有"
            f"（先让写作小助手把 chapter-<NN>-<MM>.md 落进这里）",
            file=sys.stderr,
        )
        return 1

    groups = {}
    skipped = []
    for entry in sorted(shard_dir.iterdir()):
        if not entry.is_file():
            continue
        matched = SHARD_RE.match(entry.name)
        if matched is None:
            skipped.append(entry.name)
            continue
        n = int(matched.group(1))
        m = int(matched.group(2))
        if n < 1 or m < 1:
            skipped.append(entry.name)
            continue
        groups.setdefault(n, []).append({"m": m, "path": entry})

    if chapter is not None and chapter not in groups:
        print(
            f"[error] 第 {chapter:02d} 章一片分片都没有：{'/'.join(SHARD_DIR_PARTS)} 里没有 "
            f"chapter-{chapter:02d}-<MM>.md —— 正文只能由分片拼出来（写作小助手只落分片）",
            file=sys.stderr,
        )
        return 1
    if chapter is None and not groups:
        print(
            f"[error] 没有找到任何分片：{'/'.join(SHARD_DIR_PARTS)} 里没有 "
            f"chapter-<NN>-<MM>.md —— 该章一片分片都没有",
            file=sys.stderr,
        )
        return 1

    selected = {chapter: groups[chapter]} if chapter is not None else groups
    plans, duplicate_problems = collect(selected)
    problems.extend(duplicate_problems)

    # ── 先把每一章都算完，有问题就整批不写（不留半成品） ─────────────────────
    # ⚠️ 每一章的问题先收在 `chapter_problems` 里、再并进总账：拿**总账**当这一章「能不能算」
    # 的条件，前面某一章的红会让后面每一章**连查都不查**——于是「三处坏、只报第一处」，
    # 人改完再跑又冒一处。这里要的是**一次报全**。⛔ 有错时一句读数也不印（那不是这一跑的目的）。
    for plan in plans:
        n = plan["n"]
        chapter_problems = []
        texts = {}
        for shard in plan["shards"]:
            text = read_shard(shard)
            if text is None:
                chapter_problems.append(
                    f"第 {n:02d} 章的分片读不出来（不是 UTF-8 或没有读权限？）："
                    f"{rel_shard(shard['path'].name)}"
                )
                continue
            texts[shard["path"].name] = text
            if text.strip() == "":
                chapter_problems.append(
                    f"第 {n:02d} 章的分片是空的：{rel_shard(shard['path'].name)} —— "
                    f"空片拼进正文等于少一段（先让它写满再交）"
                )
        if chapter_problems:
            problems.extend(chapter_problems)
            continue
        plan["text"] = render(plan["shards"], texts)
        plan["hanzi"] = len(HANZI_RE.findall(plan["text"]))
        plan["chars"] = len(plan["text"])
        plan["missing"] = sorted(
            set(range(1, max(s["m"] for s in plan["shards"]) + 1))
            - {s["m"] for s in plan["shards"]}
        )

    if problems:
        for problem in problems:
            print(f"[error] {problem}", file=sys.stderr)
        print("（有错时一个字都不写：修好上面点名的那几处再跑）", file=sys.stderr)
        return 1

    for plan in plans:
        n = plan["n"]
        target = Path(base_dir) / "chapters" / f"chapter-{n:02d}.md"
        wanted = plan["text"].encode("utf-8")
        existing = target.read_bytes() if target.exists() else None
        if existing == wanted:
            status = "内容相同，未重写"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(wanted)
            status = "已写入"
        # 状态行与下面的 [warn] 走 stderr：stdout 只留票面点名的那三句读数
        # （多一句状态行，「印三句」就成了四句；分开之后 `stdout | wc -l` 也对得上）。
        print(f"第 {n:02d} 章 → {rel_chapter(n)}（{status}）", file=sys.stderr)
        print(f"片数：{len(plan['shards'])}")
        numbers = "、".join(f"{shard['m']:02d}" for shard in plan["shards"])
        print(f"实际片号：{numbers}")
        print(f"字数合计：{plan['hanzi']:,} 汉字（共 {plan['chars']:,} 字符）")
        if plan["missing"]:
            missing = "、".join(f"{m:02d}" for m in plan["missing"])
            print(
                f"[warn] 第 {n:02d} 章片号跳号：缺 {missing}"
                f"（不拦——主笔拆两路、第二路还没交是有意的）",
                file=sys.stderr,
            )
            # ⚠️ 缺 01 与缺中间／末尾一号**后果不同**：缺 01 时拼出来的章从半截开始，
            # 而「有 -01 有 -03」那种正是票面点名的合法中间态（第二路还没交）。
            # 票面写的是「跳号只警告不拦」，所以这里仍不拦，但要把后果说出来——
            # dsh 侧同一形状是硬红（`shardShapeProblems` 从 01 起连续）；两边口径分叉记在票面 Answer。
            if 1 in plan["missing"]:
                print(
                    f"[warn] 第 {n:02d} 章缺的是第 01 片：这一章会**从半截开始**拼"
                    f"（前一半的正文不在这份章正文里）——确认这是有意的再往下走",
                    file=sys.stderr,
                )
    if skipped:
        print(f"[warn] {len(skipped)} 个文件名不像分片、已跳过：{'、'.join(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
