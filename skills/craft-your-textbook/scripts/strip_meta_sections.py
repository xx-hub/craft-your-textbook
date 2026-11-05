# -*- coding: utf-8 -*-
"""
拆脚手架脚本【示例模板】（造书 Phase 6）：
删除章文件末尾的"脚手架"板块（自检清单/版本记录/写作笔记等写作过程元数据）。

★★ 本文件是示例模板。复制进项目后运行。脚手架标题列表从 META.md 读（META #10）。

用法：
    python strip_meta_sections.py [目录1] [目录2] ...
    # 默认递归扫描 chapters/ 和 appendix/

⛔ **拼好的章正文（`chapters/chapter-<NN>.md`）在有分片时不拆**（票 `skill-release-ready/09`
走查抓到的真丢稿）：脚手架是**每个写作单元**写在**它那一片的末尾**的，所以拼好之后片 1 的脚手架
落在章正文的**中间**——本脚本按「标题到文件末尾」截断，一截就把片 2 之后的全部正文**静默删掉**。
正确的落点是**分片**（每一片的脚手架都在它自己的末尾，截断不会伤到别人的正文），拆完重跑
`assemble_chapter.py` 重拼即可。没有分片的老书（直接写 `chapters/chapter-<NN>.md`）不受影响：
那时章正文自己就是写作单元，照旧截断。

★ 删完后必须重跑 assemble_chapter.py 重拼章正文，再跑 merge_book.py 重新合并 BOOK.md。
"""
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_DIRS = ["chapters", "appendix"]

# ⚠️ 分片是**写作单元**，章节正文是从它拼出来的**派生件**（票 `skill-release-ready/09`）：
# 脚手架写在每片末尾 ⇒ 拼好之后它落在章正文中间，截断章正文会丢掉后半章。所以有分片时只拆分片。
SHARD_DIR_PARTS = ("chapters", "shards")


def is_shard(path):
    """`chapters/shards/` 下的任何 `.md` 都算分片（与 `assemble_chapter.py` 同一个判定口径）。"""
    parts = path.parts
    for index in range(len(parts) - len(SHARD_DIR_PARTS) + 1):
        if parts[index:index + len(SHARD_DIR_PARTS)] == SHARD_DIR_PARTS:
            return True
    return False


def assembled_chapters_with_shards(base_dir, dirs):
    """有分片的那几章：它们的章正文是派生件，不许在这里截断。返回章正文路径的集合。

    ⚠️ 返回的键与主循环里 `rglob` 吐出来的**同一个基准**（票 09 收口 review 抓到的第二个漏网：
    原先这里用 `Path(".") / dirname`，而主循环用 `Path(base_dir) / dirname`——`dirs=('.')`
    时两边拼出来的字符串不同，`f in derived` 恒假、guard 静默失效，照旧截断派生件）。
    所以两边都走 `resolved()`，并且**只收直属层的章正文**（`chapters/chapter-<NN>.md`）。
    """
    derived = set()
    for dirname in dirs:
        d = (Path(base_dir) / dirname).resolve()
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            if not is_shard(f):
                continue
            m = re.match(r"^chapter-(\d+)-\d+\.md$", f.name)
            if m:
                # ⚠️ 章号**零填充成两位**再拼：`assemble_chapter.py` 认一位数字的分片号，
                # 但写出来的章正文永远是 `chapter-01.md`。分片在 `<章目录>/shards/` 下，
                # 章正文在它的**上一层**（`f.parent.parent`），两边都 resolve 到同一基准。
                derived.add((f.parent.parent / f"chapter-{int(m.group(1)):02d}.md").resolve())
    return derived


def read_scaffold_titles(base_dir):
    """从 META.md 读脚手架标题列表（META #10）。
    找到含"脚手架标题"的那一行，把其后所有 `- item` 列表条目收为标题（容忍缩进）。
    找不到或没条目 → 返回默认值并打警告（不静默）。
    """
    meta_path = Path(base_dir) / "META.md"
    defaults = ["## 📋 自检清单", "## 📜 版本记录", "## 写作笔记"]
    if not meta_path.exists():
        print("[warn] 没找到 META.md，用默认脚手架标题", file=sys.stderr)
        return defaults
    content = meta_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    start = next((i for i, ln in enumerate(lines) if "脚手架标题" in ln), None)
    if start is None:
        print("[warn] META 里没找到'脚手架标题'小节，用默认标题（可能漏拆自定义标题）", file=sys.stderr)
        return defaults
    titles = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        m = re.match(r"^[-*]\s+(.+)$", s)
        if m:
            titles.append(m.group(1).strip().strip("`"))
        elif titles:
            break  # 已开始收集列表，遇到非列表行 = 列表结束
        # 未开始收集时跳过空行/说明行，继续找第一条列表项
    if not titles:
        print("[warn] '脚手架标题'后没有列表条目，用默认标题", file=sys.stderr)
        return defaults
    return titles


def process_file(path, markers):
    """从找到第一个 marker 行处截断文件到末尾。返回删除的字符数。"""
    content = path.read_text(encoding="utf-8")
    cut_idx = len(content)
    for marker in markers:
        idx = content.find(marker)
        if idx != -1 and idx < cut_idx:
            cut_idx = idx
    if cut_idx == len(content):
        return 0
    removed = content[cut_idx:]
    new_content = content[:cut_idx].rstrip() + "\n"
    path.write_text(new_content, encoding="utf-8")
    return len(removed)


HELP = """拆脚手架脚本：删掉每个写作单元末尾的「脚手架」板块（自检清单/版本记录/写作笔记等）。

用法：
    python strip_meta_sections.py [目录1] [目录2] ...
    # 默认递归扫描 chapters/ 和 appendix/

- 拆**分片**（chapters/shards/chapter-<NN>-<MM>.md）那一层：脚手架写在每片末尾，截断它不伤别人的正文。
- 有分片时**跳过**拼好的 chapters/chapter-<NN>.md（派生件）——在它上面按标题截断会把后面几片删掉。
- 拆完重跑 assemble_chapter.py 重拼，再跑 merge_book.py 重新合并。

⛔ `--help` 只印这份用法，不动盘上任何文件。
"""


def main():
    # `--help` 只印用法、一个字节都不写（票 `skill-release-ready/09` 走查实测：它原先把 `--help`
    # 当成一个目录名，印完「目录不存在」就退出 0——退出码看着没事，用法一个字没有）。
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(HELP, end="")
        return
    args = sys.argv[1:]
    dirs = args if args else DEFAULT_DIRS
    base_dir = "."

    markers = read_scaffold_titles(base_dir)
    print(f"脚手架标题：{markers}")

    total_removed = 0
    files_changed = 0
    derived = assembled_chapters_with_shards(base_dir, dirs)

    for dirname in dirs:
        d = Path(base_dir) / dirname
        if not d.exists():
            print(f"[skip] 目录不存在：{d}")
            continue
        for f in sorted(d.rglob("*.md")):
            # `META.md` 是**声明面**、`BOOK.md` 是**合并成品**，都不是章也不是片
            # （票 09 收口 review 实测：`dirs=('.')` 时两个都会被当普通 md 截断——声明面截了
            # 之后这趟跑完就读不到脚手架标题，成品书截了等于交一本被砍掉尾部的书）。
            if f.name in ("META.md", "BOOK.md"):
                print(f"[skip] {f}: 声明面/合并成品，不是章也不是分片（见文件头）")
                continue
            if f.resolve() in derived:
                print(f"[skip] {f}: 这一章有分片，章正文是派生件——拆它的分片、重拼（见文件头）")
                continue
            removed = process_file(f, markers)
            if removed > 0:
                lines = f.read_text(encoding="utf-8").count("\n")
                print(f"[ok]   {f}: 删除 {removed:,} 字符")
                total_removed += removed
                files_changed += 1
            else:
                print(f"[skip] {f}: 未找到脚手架标题")

    print("-" * 60)
    print(f"完成：{files_changed} 个文件，共删除 {total_removed:,} 字符")
    print("★ 记得重跑 assemble_chapter.py 重拼章正文，再跑 merge_book.py 重新合并 BOOK.md")


if __name__ == "__main__":
    main()
