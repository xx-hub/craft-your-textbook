#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill 侧交付前检查器：只读、可执行、判据全部从盘上读。

用法：
    python3 scripts/check_book.py [<书目录>] [--json]

默认书目录＝当前目录。输出一行一项；`--json` 给机器读。任何红项 → 退出码 1；
**有「未查」（not-checked）项也 → 1**——没查不等于查过干净；主笔确认这些项确实不适用时
用 `--allow-unchecked` 显式放行（读数里会印出放行了哪几项，不留静默）；
缺 `BOOK.md` 等必需输入 → 2，并说清缺什么。

## 判据从哪来

本脚本对齐交付检查（判据来源：`runQualityChecks`）与交付清单
（`references/delivery-checklist.md`）里 skill 侧能自己判的那几项：

    encode／chapters-count／chapter-title-unique／heading-duplicate／required-blocks／
    banned-words／scaffold／word-budget／cross-ref／progress-ledger

判据**一律从盘上读**，本文件里没有这本书的任何内容：

    style-spec.md（没有则回退 META.md）  必含板块／禁用词／脚手架标题
    OUTLINE.md                          章数／章名／每章 targetWords
    BOOK.md                             成品书（没有它就不做交付检查）
    chapters/chapter-<NN>.md            逐章汉字数
    progress.md                         进度账（只验在不在，不解析正文）

## 只提示不拦的措辞类

「②新增内容措辞」与「⑥造书者口吻」按同一口径只记 `warn`、给行号，不计入红项。
交付清单里「AI」单独命中也要人工确认，所以裸 `AI`（不带「老师／教师／助手」等后缀）
同样只提示、不判红。

## 我的枚举面比现实窄在哪里

- **章界只认行首 1–3 级标题里的「第 N 章」**（半角数字与常用的中文数字）。正文里不带
  `#` 的「第 3 章开始了」、4 级及更深的标题、以及 `## 第3章与第4章` 这种并列写法都分不出章界。
- **章内标题只看 H2/H3**（与票面口径一致）；H4 及更深的标题不参与同章去重。
- **章名唯一性同时读章节骨架与成品书的章级标题**：两份里不同章号用了同一个归一化章名才算重复；
  只读骨架会漏「成品书标题写错」这一形状（交付检查只读骨架，skill 侧不收窄到那一半）。
- **必含板块与禁用词只认写作规范里声明得出来的写法**：`必含板块…：A、B` 或其后紧跟的
  编号／列表项；`禁用词…：A、B` 或其后紧跟的列表项。写成散文、表格或别的符号的声明读不出来，
  这时该项记 `not-checked`，**不猜、也不回落硬编码词表**。
- **禁用词是子串命中**：只查声明里写出来的词，声明里没有的词查不到；不判语境。
- **字数只数 CJK 统一汉字**（`\\u4e00-\\u9fff`），数字／字母／标点／空白都不计；只读
  `chapters/chapter-<NN>.md`，不拿成品书回推。低于兜底只报数、不判红，达到或超过一律放行。
- **跨章引用只认「第 N 章」**；「见附录 A」「见卡 X.Y」与「概念／知识点真实存在」不在扫面内。
- **⑤ 源教材引用收哪些形状**：①括注出处（`（出处：S1 第一章）`／`（资料来源：…）`）②源简码＋章号
  （`S3 第 18 章`／`SE1 第六章`）③旧四个短语（`教师用书说` 等）。两类白区：**附录区**（附录/参考文献/
  参考书目/源材料/术语表/索引/书目 标题起，到下一个同级或更高级标题止）两类都豁免；
  **「说法不一」节**（标题含 说法不一／两说／各家说法／不同说法／歧见）只豁免简码——本书规范明确
  允许那一节点名双方，但不允许在那里写括注。裸 `出处：`／`资料来源：`（不在括号里）**不设判据**：
  实测 8 条误报里 7 条出自裸冒号（「偏差也分两个来源：」）。形状外的同义写法（以原书为主语、
  只说书名不带简码）**抓不到**，归 ⑥ 措辞类提示与人判。
- **脚手架声明标题**同时读 `style-spec.md` 与 `META.md`（skill 侧拆脚手架脚本只读 `META.md`，
  所以两处都认；这不是合并两份写作规范）；通用 7 个标记与「拆脚手架八类」里按形状能认的
  6 类按同一口径硬查，②⑥ 只提示。
- 本脚本**只读不写、不删任何文件**。拆脚手架仍由 `strip_meta_sections.py` 做，顺序仍是
  「拆 → 重拼 → 合并」；本脚本只看不给改。

## 依赖

默认**只用 Python 标准库**。真需要第三方库时，按 `skill/SKILL-APPENDIX.md` 的「依赖」一节
由使用本 skill 的 agent 自己安装，并在这里给一句可行动的报错；本脚本今天没有第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文/emoji 打印崩溃。
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_INPUT = 2

STATE_LABELS = {
    "pass": "PASS",
    "fail": "FAIL",
    "warn": "WARN",
    "not-checked": "SKIP",
}

# 章界：行首 1–3 级标题 ＋「第 N 章」。半角数字与常用中文数字都收。
CHAPTER_HEADING_RE = re.compile(
    r"^(#{1,3})[ \t]+第[ \t]*([0-9]+|[一二三四五六七八九十百零两]+)[ \t]*章[ \t]*(.*)$"
)
# 跨章引用：只认「第 N 章」（允许中间空格）。
CHAPTER_REF_RE = re.compile(r"第[ \t]*([0-9]+|[一二三四五六七八九十百零两]+)[ \t]*章")
# 7 个通用脚手架标记（与 `runQualityChecks` 同一份）。
SCAFFOLD_MARKERS_RE = re.compile(r"\b(META|TODO|FIXME|HACK)\b|审计批注|未决问题|loader 指令")
# 八类过程元数据；hard 命中即红，soft 只提示（与 `runQualityChecks` 同一份）。
SCAFFOLD_CATEGORIES = (
    ("①", "版本标记注释", "hard", re.compile(r"<!--[^>\n]*\bv[ \t]?\d")),
    ("②", "“新增内容”措辞", "soft", re.compile(r"新增|追加|新加")),
    ("③", "自检清单", "hard", re.compile(r"^[ \t]*[-*+][ \t]*\[[xX]\][ \t]*[^\n]*")),
    (
        "④",
        "版本记录",
        "hard",
        re.compile(
            r"(?:^|[^0-9A-Za-z])v[ \t]?\d+(?:\.\d+)*[ \t]*[（(：:]?[ \t]*"
            r"(?:初稿|定稿|修订|改版|版本|版次)|(?:版本记录|修订记录|修订日志)[ \t]*[：:]"
        ),
    ),
    ("⑤", "源教材引用", "hard", re.compile(r"教师用书说|教材原文指出|学生用书说|原文指出")),
    ("⑥", "造书者口吻", "soft", re.compile(r"给人类教师|可追溯|造书者|人类教师")),
    (
        "⑦",
        "增量描述",
        "hard",
        re.compile(
            r"v[ \t]?\d+(?:\.\d+)?[ \t]*(?:增量|基础)|在[ \t]*v[ \t]?\d|"
            r"基础上追加|基础上补充"
        ),
    ),
    ("⑧", "过程勾选项", "hard", re.compile(r"^[ \t]*[-*+][ \t]*\[[xX]\][ \t]*[^\n]*")),
)

# ⑤ 源教材引用：除了上面那 4 个短语，另按**形状**判两类真实泄漏（2026-11-12 起）。
# 每条：(标签, 正则, 是否也豁免「说法不一」节)。
#   括注出处——本书规范允许「说法不一」节点名双方，但那一节也不许写括注，所以不豁免。
#   源简码＋章号——那一节本来就是比两本书，点名 S 简码是设计，豁免。
SOURCE_LEAK_PATTERNS = (
    (
        "出处括注",
        re.compile(r"[（(][ \t]*(?:出处|资料来源)[ \t]*[：:][^）)\n]{0,120}[）)]"),
        False,
    ),
    (
        "源简码＋章号",
        re.compile(
            r"(?<![A-Za-z0-9])S[Ee]?\d{1,2}(?![0-9])[^\n]{0,8}?第[ \t]*"
            r"[0-9一二三四五六七八九十百零两]+[ \t]*[章节]"
        ),
        True,
    ),
    # 简码＋行号括注：`（S7 296）`／`（S7 2286–2296）`／`（SE1 3.2 节）`。
    # 这一形最毒——读者手里没有那几份材料，行号对谁都解不开（2026-11-12 实测一本 393 处）。
    (
        "简码＋行号括注",
        re.compile(r"[（(][ \t]*S[Ee]?[ \t]?\d{1,2}[ \t]*[：:]?[ \t]*\d"),
        True,
    ),
)
# 白区一：附录/参考文献一类标题起算（目录里的列表项不算，只认行首 # 标题）。
APPENDIX_HEAD_RE = re.compile(
    r"^(#{1,6})[ \t]*(?:附录|本章出处|章末出处|参考资料|参考文献|参考书目|源材料|引用书目|术语表|索引|书目)"
)
# 白区二：「说法不一」类节——本书写作规范明确允许那一节点名双方。
ARBITRATION_HEAD_RE = re.compile(
    r"^(#{1,6})[ \t]*[^\n]*(?:说法不一|两说|各家说法|不同说法|歧见)"
)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]*")


def heading_zone_lines(lines: list[str], head_re: re.Pattern) -> set[int]:
    """标题命中起，到下一个同级或更高级标题止（0-based 行号集合）。

    只认行首 `#` 标题：目录里的「- 附录 A · 术语表」是列表项，不会误把全书划进白区。
    """
    zone: set[int] = set()
    level = 0
    inside = False
    for index, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if heading is not None:
            if head_re.match(line) is not None:
                inside, level = True, len(heading.group(1))
            elif inside and len(heading.group(1)) <= level:
                inside = False
        if inside:
            zone.add(index)
    return zone

CN_NUMERALS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


class InputError(Exception):
    """缺必需输入或输入读不出来；主程序转成退出码 2。"""


def read_text(path: Path, label: str) -> str:
    """读一份文本；读不出来时给可行动的报错，不甩 traceback。"""
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise InputError(f"找不到{label}：{path}") from error
    except IsADirectoryError as error:
        raise InputError(f"{label}是一个目录，不是文件：{path}") from error
    except PermissionError as error:
        raise InputError(f"没有权限读{label}：{path}（检查文件权限后重跑）") from error
    except UnicodeDecodeError as error:
        raise InputError(f"{label}不是 UTF-8 文本：{path}（{error.reason}）") from error
    except OSError as error:
        raise InputError(f"读不了{label}：{path}（{error.strerror or error}）") from error


def normalize_text(text: str) -> str:
    """CRLF 一律归一成 LF（比对与行号都以归一后的文本为准）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_chapter_number(raw: str) -> int | None:
    """把半角数字或常用中文数字解析成正整数；解析不出返回 None。"""
    raw = raw.strip()
    if raw.isdigit():
        number = int(raw)
        return number if number > 0 else None
    if raw == "十":
        return 10
    if raw == "百":
        return 100
    if "十" in raw:
        head, _, tail = raw.partition("十")
        tens = CN_NUMERALS.get(head, 1) if head else 1
        ones = CN_NUMERALS.get(tail, 0) if tail else 0
        number = tens * 10 + ones
        return number if number > 0 else None
    if all(ch in CN_NUMERALS for ch in raw):
        number = 0
        for ch in raw:
            number = number * 10 + CN_NUMERALS[ch]
        return number if number > 0 else None
    return None


def normalize_title(text: str) -> str:
    """标题归一化：只留文字与数字（剥掉 emoji、符号、标点、空白），与交付检查的标题归一化同口径。"""
    return "".join(ch for ch in text if ch.isalnum()).lower()


def strip_markdown_item(text: str) -> str:
    """剥掉列表项/标题/粗体/反引号外壳，留下名字本身。"""
    item = text.strip()
    item = re.sub(r"^[#>*+\-\s]+", "", item)
    item = re.sub(r"^\d+[.、)]\s*", "", item)
    item = item.replace("**", "").replace("`", "")
    item = item.strip()
    item = re.sub(r"[（(][^）)]*[）)]", "", item).strip()
    item = item.rstrip("：:，,。.；;、 ")
    return item.strip()


def split_declared_values(text: str) -> list[str]:
    """把一行声明按常见分隔符拆成条目（保留顺序、去重）。"""
    parts = re.split(r"[、,，;；|/]+", text)
    items: list[str] = []
    for part in parts:
        item = strip_markdown_item(part)
        if item and item not in items:
            items.append(item)
    return items


def _list_item_text(line: str) -> str | None:
    match = re.match(r"^[ \t]*(?:[-*+]|\d+[.、)])\s+(.+)$", line)
    if match is None:
        return None
    return strip_markdown_item(match.group(1))


def collect_items_after(lines: list[str], start: int, limit: int = 30) -> list[str]:
    """从声明行之后收列表项；遇到下一个标题/粗体小标题/连续空行就停。"""
    items: list[str] = []
    blanks = 0
    for line in lines[start + 1 : start + 1 + limit]:
        stripped = line.strip()
        if stripped == "":
            blanks += 1
            if blanks >= 2 or items:
                break
            continue
        blanks = 0
        if re.match(r"^#{1,6}\s+", stripped):
            break
        item = _list_item_text(line)
        if item is not None:
            if item and item not in items:
                items.append(item)
            continue
        # 粗体小标题（**本节无额外标题** 这种）到了就停，别把下一节当成声明。
        if re.match(r"^\*\*[^*]+\*\*\s*[：:]?\s*$", stripped):
            break
        if items:
            break
    return items


def section_text(text: str, keyword: str) -> str | None:
    """取含 keyword 的那个标题节（到同级或更高级标题为止）；找不到返回 None。"""
    lines = text.split("\n")
    start = None
    level = None
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match is not None and keyword in match.group(2):
            start = index
            level = len(match.group(1))
            break
    if start is None:
        return None
    body = [lines[start]]
    for line in lines[start + 1 :]:
        match = re.match(r"^(#{1,6})\s+", line)
        if match is not None and len(match.group(1)) <= level:
            break
        body.append(line)
    return "\n".join(body)


def declaration_from_section(section: str | None, label: str) -> dict:
    """从一节里读「label：值」或「label」标题后紧跟的列表项。

    返回 `{state: declared|declared-none|undeclared, items: [...]}`：
    - `declared`      真读到条目；
    - `declared-none` 明写「无／不需要」；
    - `undeclared`    这一份写作规范里没有可读的声明。
    """
    if section is None:
        return {"state": "undeclared", "items": []}
    lines = section.split("\n")
    for index, line in enumerate(lines):
        plain = re.sub(r"^[#>*+\-\s]+", "", line.strip()).replace("**", "")
        if not re.match(rf"^{re.escape(label)}(?:[（(]|[：:]|\s|$)", plain):
            continue
        # 先看冒号后面的同行值。
        match = re.search(r"[:：]\s*(.*)$", plain)
        if match is not None:
            value = match.group(1).strip()
            if value:
                items = split_declared_values(value)
                if items and items[0] in ("无", "没有", "不需要", "不适用", "无额外标题"):
                    return {"state": "declared-none", "items": []}
                if items:
                    return {"state": "declared", "items": items}
        # 再看紧随其后的列表项（`## 脚手架标题` 后跟 `- ## 自检清单` 就是这一支）。
        items = collect_items_after(lines, index)
        if items and items[0] in ("无", "没有", "不需要", "不适用", "无额外标题"):
            return {"state": "declared-none", "items": []}
        if items:
            return {"state": "declared", "items": items}
    return {"state": "undeclared", "items": []}


def parse_outline(text: str) -> tuple[list[dict] | None, str]:
    """读章节骨架：JSON／markdown 表格／`## 第N章 标题` 三种写法。

    返回 `(chapters, source_note)`；读不出来时 `chapters` 为 None，`source_note` 说原因。
    chapters 每项形如 `{n, title, targetWords}`（targetWords 读不出为 None）。
    """
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as error:
            return None, f"OUTLINE.md 看起来像 JSON 但解析失败（第 {error.lineno} 行：{error.msg}）"
        rows = data.get("chapters") if isinstance(data, dict) else data
        if not isinstance(rows, list) or not rows:
            return None, "OUTLINE.md 的 JSON 里没有非空 chapters 数组"
        chapters: list[dict] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            number = row.get("章号", row.get("number", row.get("n", index)))
            try:
                number = int(number)
            except (TypeError, ValueError):
                number = index
            title = str(row.get("title", row.get("标题", row.get("章名", "")))).strip()
            target = row.get("targetWords", row.get("target_words", row.get("目标字数", row.get("字数"))))
            target_words = None
            if isinstance(target, (int, float)):
                target_words = int(target)
            elif isinstance(target, str):
                match = re.search(r"\d+", target)
                if match is not None:
                    target_words = int(match.group(0))
            chapters.append({"n": number, "title": title, "targetWords": target_words})
        return (chapters, "OUTLINE.md（JSON）") if chapters else (None, "OUTLINE.md 的 chapters 里没有可读条目")

    lines = text.split("\n")
    table_rows: list[dict] = []
    header: list[str] | None = None
    for line in lines:
        if not line.strip().startswith("|"):
            if header is not None and table_rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.match(r"^:?-{2,}:?$", cell) for cell in cells):
            continue
        lowered = [cell.lower() for cell in cells]
        has_title = any("标题" in cell or "章名" in cell or "title" in cell for cell in lowered)
        has_number = any(
            re.search(r"章号|^章$|^#|number|序号", cell, re.IGNORECASE) for cell in cells
        )
        if has_title and has_number:
            header = cells
            table_rows = []
            continue
        if header is None:
            continue
        table_rows.append({"cells": cells, "header": header})
    if table_rows:
        chapters = []
        for index, row in enumerate(table_rows, start=1):
            cells, header_cells = row["cells"], row["header"]
            title_index = next(
                (i for i, cell in enumerate(header_cells) if "标题" in cell or "章名" in cell or "title" in cell.lower()),
                None,
            )
            number_index = next(
                (
                    i
                    for i, cell in enumerate(header_cells)
                    if re.search(r"章号|^章$|number|^n$|^#", cell, re.IGNORECASE)
                ),
                None,
            )
            target_index = next(
                (
                    i
                    for i, cell in enumerate(header_cells)
                    if "targetwords" in cell.lower() or "目标字数" in cell or "字数" in cell
                ),
                None,
            )
            if title_index is None or title_index >= len(cells):
                continue
            title = strip_markdown_item(cells[title_index])
            number = index
            if number_index is not None and number_index < len(cells):
                parsed = parse_chapter_number(cells[number_index])
                if parsed is not None:
                    number = parsed
            target_words = None
            if target_index is not None and target_index < len(cells):
                match = re.search(r"\d+", cells[target_index])
                if match is not None:
                    target_words = int(match.group(0))
            if title:
                chapters.append({"n": number, "title": title, "targetWords": target_words})
        if chapters:
            return chapters, "OUTLINE.md（表格）"

    # 标题式：`## 第1章 标题`；targetWords 可写在同一行或紧跟的几行里。
    chapters = []
    current = None
    for offset, line in enumerate(lines):
        match = CHAPTER_HEADING_RE.match(line)
        if match is not None:
            number = parse_chapter_number(match.group(2))
            if number is None:
                continue
            title = strip_markdown_item(match.group(3))
            current = {"n": number, "title": title, "targetWords": None}
            chapters.append(current)
            target = re.search(r"(?:targetWords|目标字数|字数)\s*[:：]\s*(\d+)", line, re.IGNORECASE)
            if target is not None:
                current["targetWords"] = int(target.group(1))
            continue
        if current is not None and current["targetWords"] is None:
            target = re.search(r"(?:targetWords|目标字数|字数)\s*[:：]\s*(\d+)", line, re.IGNORECASE)
            if target is not None:
                current["targetWords"] = int(target.group(1))
    if chapters:
        return chapters, "OUTLINE.md（标题式）"

    # 列表式：`- 第1章 标题`。
    chapters = []
    for line in lines:
        match = re.match(r"^[ \t]*[-*+]\s+第[ \t]*([0-9]+|[一二三四五六七八九十百零两]+)[ \t]*章[ \t]*(.*)$", line)
        if match is None:
            continue
        number = parse_chapter_number(match.group(1))
        if number is None:
            continue
        rest = match.group(2)
        target = re.search(r"(?:targetWords|目标字数|字数)\s*[:：]\s*(\d+)", rest, re.IGNORECASE)
        title = re.sub(r"(?:targetWords|目标字数|字数)\s*[:：]\s*\d+", "", rest, flags=re.IGNORECASE)
        chapters.append(
            {
                "n": number,
                "title": strip_markdown_item(title),
                "targetWords": int(target.group(1)) if target is not None else None,
            }
        )
    if chapters:
        return chapters, "OUTLINE.md（列表式）"

    return None, "OUTLINE.md 里读不出逐章骨架（试过 JSON、表格、`## 第N章 标题`、`- 第N章 标题` 四种写法）"


def split_book(text: str) -> list[dict]:
    """按「第 N 章」把成品书切成章段；章标题行本身不进正文。"""
    chapters: list[dict] = []
    current: dict | None = None
    for line_no, line in enumerate(text.split("\n"), start=1):
        match = CHAPTER_HEADING_RE.match(line)
        if match is not None:
            number = parse_chapter_number(match.group(2))
            current = {
                "n": number,
                "line": line_no,
                "title": strip_markdown_item(match.group(3)),
                "lines": [],
            }
            chapters.append(current)
            continue
        if current is not None:
            current["lines"].append((line_no, line))
    return chapters


def chapter_lines(chapter: dict) -> str:
    return "\n".join(line for _, line in chapter["lines"])


def chapter_of_line(chapters: list[dict], line_no: int) -> int | None:
    """某一行落在哪一章；章标题之前返回 None。"""
    found = None
    for chapter in chapters:
        if chapter["line"] <= line_no:
            found = chapter["n"]
        else:
            break
    return found


def hit(chapter: int | None, line: int | None, text: str) -> dict:
    return {"chapter": chapter, "line": line, "text": text}


def where(chapter: int | None, line: int | None) -> str:
    """人话位置：第 N 章第 M 行／第 N 章／书首第 M 行／全书。"""
    if chapter is None and line is None:
        return "全书"
    if chapter is None:
        return f"书首第 {line} 行"
    if line is None:
        return f"第 {chapter} 章"
    return f"第 {chapter} 章第 {line} 行"


def excerpt(text: str, limit: int = 60) -> str:
    cleaned = text.strip().replace("\t", " ")
    return cleaned[:limit] + ("…" if len(cleaned) > limit else "")


def check_encode(book_text: str, chapters: list[dict]) -> dict:
    hits = []
    count = 0
    for line_no, line in enumerate(book_text.split("\n"), start=1):
        if "\ufffd" not in line:
            continue
        count += line.count("\ufffd")
        hits.append(hit(chapter_of_line(chapters, line_no), line_no, f"乱码 U+FFFD：{excerpt(line)}"))
    if count == 0:
        return {"name": "encode", "state": "pass", "readings": "0 处乱码", "hits": []}
    return {
        "name": "encode",
        "state": "fail",
        "readings": f"{count} 处乱码（U+FFFD）",
        "hits": hits,
    }


def check_chapters_count(book_dir: Path, chapters: list[dict], outline: list[dict] | None) -> dict:
    if outline is None:
        return {
            "name": "chapters-count",
            "state": "not-checked",
            "readings": "缺 OUTLINE.md，这一项没得查",
            "hits": [],
        }
    expected = len(outline)
    actual = len(chapters)
    expected_numbers = [chapter["n"] for chapter in outline]
    actual_numbers = [chapter["n"] for chapter in chapters]
    missing_files = []
    for chapter in outline:
        number = chapter["n"]
        path = book_dir / "chapters" / f"chapter-{number:02d}.md"
        try:
            size = path.stat().st_size if path.is_file() else 0
        except OSError:
            size = 0
        if size == 0:
            missing_files.append((number, path))
    hits = []
    for number in expected_numbers:
        if number not in actual_numbers:
            hits.append(hit(number, None, f"成品书里缺第 {number} 章（章节骨架声明了它）"))
    seen_numbers: set[int] = set()
    for chapter in chapters:
        number = chapter["n"]
        if number in seen_numbers:
            hits.append(hit(number, chapter["line"], f"成品书里的第 {number} 章出现了不止一次"))
        seen_numbers.add(number)
        if number not in expected_numbers:
            hits.append(hit(number, chapter["line"], f"成品书里的第 {number} 章不在章节骨架声明里"))
    for number, path in missing_files:
        hits.append(hit(number, None, f"缺章正文：{path.relative_to(book_dir)}"))
    readings = f"章标题 {actual}/{expected}；章正文 {expected - len(missing_files)}/{expected}"
    if hits:
        return {"name": "chapters-count", "state": "fail", "readings": readings, "hits": hits}
    return {"name": "chapters-count", "state": "pass", "readings": readings, "hits": []}


def check_chapter_title_unique(chapters: list[dict], outline: list[dict] | None) -> dict:
    if outline is None:
        return {
            "name": "chapter-title-unique",
            "state": "not-checked",
            "readings": "缺 OUTLINE.md，这一项没得查",
            "hits": [],
        }
    # 两份来源都收：章节骨架的章名（交付检查口径）＋成品书的章级标题（交付清单 skill 侧的
    # 「抽全部章标题逐对比较」口径）。同一章在两份里各出现一次不算两章同名；只有**不同章号**
    # 用了同一个归一化章名才是真重复。落点优先用 BOOK 的行号（能点得过去）。
    titles: list[dict] = []
    for chapter in outline:
        if chapter["title"]:
            titles.append({"n": chapter["n"], "title": chapter["title"], "line": None, "source": "OUTLINE.md"})
    for chapter in chapters:
        if chapter["title"]:
            titles.append(
                {
                    "n": chapter["n"],
                    "title": chapter["title"],
                    "line": chapter["line"],
                    "source": "BOOK.md",
                }
            )
    groups: dict[str, list[dict]] = {}
    for item in titles:
        key = normalize_title(item["title"])
        if not key:
            continue
        groups.setdefault(key, []).append(item)
    hits = []
    for items in groups.values():
        distinct = sorted({item["n"] for item in items})
        if len(distinct) < 2:
            continue
        numbers = "、".join(f"第 {number} 章" for number in distinct)
        first = next((item for item in items if item["line"] is not None), items[0])
        hits.append(
            hit(
                first["n"],
                first["line"],
                f"{numbers}章名相同：「{first['title']}」（归一化后比较）",
            )
        )
    chapter_count = len({item["n"] for item in titles})
    readings = f"{chapter_count} 章共 {len(titles)} 个章名，{len(hits)} 组重复"
    if hits:
        return {"name": "chapter-title-unique", "state": "fail", "readings": readings, "hits": hits}
    return {"name": "chapter-title-unique", "state": "pass", "readings": readings, "hits": []}


def check_heading_duplicate(chapters: list[dict]) -> dict:
    if not chapters:
        return {
            "name": "heading-duplicate",
            "state": "not-checked",
            "readings": "成品书里没识别出章标题，这一项没得查",
            "hits": [],
        }
    # 第一遍：逐章收 H2/H3 标题；同章内重复直接进红项。
    hard_hits = []
    hard_keys: set[str] = set()
    across: dict[str, dict] = {}
    for chapter in chapters:
        seen: dict[str, dict] = {}
        for line_no, line in chapter["lines"]:
            match = re.match(r"^(#{2,3})[ \t]+(.*)$", line)
            if match is None:
                continue
            title = match.group(2).strip()
            key = normalize_title(title)
            if not key:
                continue
            if key in seen:
                hard_keys.add(key)
                hard_hits.append(
                    hit(
                        chapter["n"],
                        line_no,
                        f"同章重复标题「{title}」（首次在第 {seen[key]['line']} 行）",
                    )
                )
                continue
            seen[key] = {"line": line_no, "title": title}
        for key, item in seen.items():
            slot = across.setdefault(key, {"title": item["title"], "chapters": {}})
            slot["chapters"][chapter["n"]] = item["line"]
    # 第二遍：跨章同名只提示；同章重复过的标题不再重复提示。
    warn_hits = []
    for key, slot in across.items():
        if key in hard_keys:
            continue
        numbers = sorted(slot["chapters"])
        if len(numbers) < 2:
            continue
        first = numbers[0]
        names = "、".join(f"第 {number} 章" for number in numbers)
        warn_hits.append(
            hit(
                first,
                slot["chapters"][first],
                f"{names}同名「{slot['title']}」（跨章同名，不拦）",
            )
        )
    readings = f"同章重复 {len(hard_hits)} 处；跨章同名 {len(warn_hits)} 组（只提示）"
    if hard_hits:
        return {
            "name": "heading-duplicate",
            "state": "fail",
            "readings": readings,
            "hits": hard_hits + warn_hits,
        }
    if warn_hits:
        return {
            "name": "heading-duplicate",
            "state": "warn",
            "readings": readings,
            "hits": warn_hits,
        }
    return {"name": "heading-duplicate", "state": "pass", "readings": readings, "hits": []}


def check_required_blocks(
    chapters: list[dict], declared: dict, source: str | None, spec_names: str = ""
) -> dict:
    if declared["state"] == "undeclared":
        if spec_names:
            where_text = f"（读了 {spec_names}，没读到「必含板块」声明）"
        elif source:
            where_text = f"（读了 {source}，没读到「必含板块」声明）"
        else:
            where_text = "（缺 style-spec.md/META.md）"
        return {
            "name": "required-blocks",
            "state": "not-checked",
            "readings": f"没有可读的必含板块声明{where_text}，这一项没得查",
            "hits": [],
        }
    boards = declared["items"]
    if not boards:
        return {
            "name": "required-blocks",
            "state": "not-checked",
            "readings": "写作规范明写「无必含板块」，这一项没得查",
            "hits": [],
        }
    if not chapters:
        return {
            "name": "required-blocks",
            "state": "not-checked",
            "readings": "成品书里没识别出章标题，这一项没得查",
            "hits": [],
        }
    hits = []
    found = 0
    for chapter in chapters:
        body = chapter_lines(chapter)
        missing = [board for board in boards if board not in body]
        found += len(boards) - len(missing)
        for board in missing:
            hits.append(hit(chapter["n"], chapter["line"], f"缺必含板块「{board}」"))
    total = len(chapters) * len(boards)
    readings = f"按章计数 {found}/{total}（{len(chapters)} 章 × {len(boards)} 块；来源：{source}）"
    if hits:
        return {"name": "required-blocks", "state": "fail", "readings": readings, "hits": hits}
    return {"name": "required-blocks", "state": "pass", "readings": readings, "hits": []}


def check_banned_words(
    book_text: str,
    chapters: list[dict],
    declared: dict,
    source: str | None,
    spec_names: str = "",
) -> dict:
    if declared["state"] == "undeclared":
        if spec_names:
            where_text = f"（读了 {spec_names}，没读到「禁用词」声明）"
        elif source:
            where_text = f"（读了 {source}，没读到「禁用词」声明）"
        else:
            where_text = "（缺 style-spec.md/META.md）"
        return {
            "name": "banned-words",
            "state": "not-checked",
            "readings": f"没有可读的禁用词声明{where_text}，这一项没得查",
            "hits": [],
        }
    words = declared["items"]
    if not words:
        return {
            "name": "banned-words",
            "state": "not-checked",
            "readings": "写作规范明写「无禁用词」，这一项没得查",
            "hits": [],
        }
    hard_hits = []
    ai_hits = []
    lines = book_text.split("\n")
    for word in words:
        if word == "AI":
            # 交付清单：裸 AI 归人工确认，带「老师／教师／助手」等后缀的合法。
            pattern = re.compile(r"AI(?!\s*(?:老师|教师|助手|助教))")
            for line_no, line in enumerate(lines, start=1):
                if pattern.search(line) is None:
                    continue
                ai_hits.append(
                    hit(chapter_of_line(chapters, line_no), line_no, f"裸「AI」命中（归人工确认）：{excerpt(line)}")
                )
            continue
        for line_no, line in enumerate(lines, start=1):
            count = line.count(word)
            if count == 0:
                continue
            for _ in range(count):
                hard_hits.append(
                    hit(
                        chapter_of_line(chapters, line_no),
                        line_no,
                        f"命中「{word}」（禁用词表：{source} §正文语言风格）：{excerpt(line)}",
                    )
                )
    readings = f"{len(hard_hits)} 处命中（词表：{source} §正文语言风格，{len(words)} 个词）"
    if ai_hits:
        readings += f"；裸「AI」提示 {len(ai_hits)} 处（归人工确认）"
    if hard_hits:
        return {"name": "banned-words", "state": "fail", "readings": readings, "hits": hard_hits + ai_hits}
    if ai_hits:
        return {"name": "banned-words", "state": "warn", "readings": readings, "hits": ai_hits}
    return {"name": "banned-words", "state": "pass", "readings": readings, "hits": []}


def check_scaffold(
    book_text: str,
    chapters: list[dict],
    declared: dict,
    declared_missing: bool,
) -> dict:
    lines = book_text.split("\n")
    appendix_zone = heading_zone_lines(lines, APPENDIX_HEAD_RE)
    arbitration_zone = heading_zone_lines(lines, ARBITRATION_HEAD_RE)
    hard_hits = []
    soft_hits = []
    for line_no, line in enumerate(lines, start=1):
        index0 = line_no - 1
        chapter = chapter_of_line(chapters, line_no)
        marker = SCAFFOLD_MARKERS_RE.search(line)
        if marker is not None:
            hard_hits.append(hit(chapter, line_no, f"通用脚手架标记「{marker.group(0)}」：{excerpt(line)}"))
            continue
        # ⑤ 源教材引用：按形状判；附录区两类都豁免，「说法不一」节只豁免简码那一类。
        leak_label = ""
        if index0 not in appendix_zone:
            for label, pattern, skip_arbitration in SOURCE_LEAK_PATTERNS:
                if skip_arbitration and index0 in arbitration_zone:
                    continue
                if pattern.search(line) is not None:
                    leak_label = label
                    break
        if leak_label:
            hard_hits.append(
                hit(chapter, line_no, f"拆脚手架硬类命中：⑤ 源教材引用（{leak_label}）：{excerpt(line)}")
            )
            continue
        hard_categories = []
        soft_categories = []
        for category_id, label, tier, pattern in SCAFFOLD_CATEGORIES:
            if pattern.search(line) is None:
                continue
            if tier == "hard":
                hard_categories.append(f"{category_id} {label}")
            else:
                soft_categories.append(f"{category_id} {label}")
        if hard_categories:
            hard_hits.append(hit(chapter, line_no, f"拆脚手架硬类命中：{hard_categories[0]}：{excerpt(line)}"))
            continue
        if soft_categories:
            soft_hits.append(hit(chapter, line_no, f"措辞类提示：{soft_categories[0]}：{excerpt(line)}"))
    for title in declared["items"]:
        for line_no, line in enumerate(lines, start=1):
            if title not in line:
                continue
            hard_hits.append(
                hit(
                    chapter_of_line(chapters, line_no),
                    line_no,
                    f"本书声明的脚手架标题「{title}」还留着：{excerpt(line)}",
                )
            )
    readings = (
        f"硬类命中 {len(hard_hits)} 处；措辞类提示 {len(soft_hits)} 处；"
        f"扫面 {len(lines)} 行（附录区豁免 {len(appendix_zone)} 行、「说法不一」节豁免 {len(arbitration_zone)} 行）"
    )
    if declared["state"] == "declared":
        readings += f"；声明标题 {len(declared['items'])} 个"
    elif declared["state"] == "declared-none":
        readings += "；写作规范明写「本书无额外脚手架标题」（不是查过没查到）"
    readings += "；⑤ 认的形状＝括注出处／源简码＋章号／简码＋行号括注／旧四短语；形状外（以原书为主语、裸书名）不命中，归 ⑥ 与人判"
    if hard_hits:
        return {
            "name": "scaffold",
            "state": "fail",
            "readings": readings,
            "hits": hard_hits + soft_hits,
        }
    if declared_missing or declared["state"] == "undeclared":
        readings += "；写作规范里没读到「脚手架标题」声明，这一半没得查"
        return {
            "name": "scaffold",
            "state": "not-checked",
            "readings": readings,
            "hits": soft_hits,
        }
    if soft_hits:
        return {"name": "scaffold", "state": "warn", "readings": readings, "hits": soft_hits}
    return {"name": "scaffold", "state": "pass", "readings": readings, "hits": []}


def count_hanzi(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def check_word_budget(book_dir: Path, outline: list[dict] | None) -> dict:
    if outline is None:
        return {
            "name": "word-budget",
            "state": "not-checked",
            "readings": "缺 OUTLINE.md，这一项没得查",
            "hits": [],
        }
    rows = [chapter for chapter in outline if chapter.get("targetWords") is not None]
    missing_targets = len(outline) - len(rows)
    if not rows:
        return {
            "name": "word-budget",
            "state": "not-checked",
            "readings": "章节骨架没声明 targetWords，这一项没得查",
            "hits": [],
        }
    hits = []
    floor_total = 0
    actual_total = 0
    below = []
    for chapter in rows:
        number = chapter["n"]
        floor = int(chapter["targetWords"])
        floor_total += floor
        path = book_dir / "chapters" / f"chapter-{number:02d}.md"
        if not path.is_file():
            hits.append(hit(number, None, f"读不到章正文 {path.relative_to(book_dir)}，这一章的字数没得数"))
            below.append(f"第{number}章正文读不到")
            continue
        try:
            actual = count_hanzi(normalize_text(read_text(path, f"第 {number} 章正文")))
        except InputError as error:
            hits.append(hit(number, None, str(error)))
            below.append(f"第{number}章正文读不到")
            continue
        actual_total += actual
        if actual < floor:
            hits.append(
                hit(number, None, f"低于兜底：兜底 {floor} 汉字 / 实际 {actual} 汉字（差 {floor - actual} 字）")
            )
            below.append(f"第{number}章兜底 {floor} / 实际 {actual}（差 {floor - actual} 字）")
    readings = f"兜底 {floor_total} 汉字 / 实际 {actual_total} 汉字"
    if missing_targets > 0:
        readings += f"；{missing_targets} 章没声明 targetWords（不判）"
    if below:
        readings += f"；低于兜底：{'；'.join(below[:3])}"
    # 只报数：低于兜底也只提示，不判红（交付检查同一口径，不设上限）。
    return {
        "name": "word-budget",
        "state": "warn" if hits else "pass",
        "readings": readings,
        "hits": hits,
    }


def check_cross_ref(book_text: str, chapters: list[dict]) -> dict:
    if not chapters:
        return {
            "name": "cross-ref",
            "state": "not-checked",
            "readings": "成品书里没识别出章标题，这一项没得查",
            "hits": [],
        }
    valid = {chapter["n"] for chapter in chapters}
    total = max(valid)
    hits = []
    scanned = 0
    chapter_heading_lines = {chapter["line"] for chapter in chapters}
    for line_no, line in enumerate(book_text.split("\n"), start=1):
        if line_no in chapter_heading_lines:
            continue
        for match in CHAPTER_REF_RE.finditer(line):
            scanned += 1
            number = parse_chapter_number(match.group(1))
            if number is not None and number in valid and number <= total:
                continue
            hits.append(
                hit(
                    chapter_of_line(chapters, line_no),
                    line_no,
                    f"「{match.group(0)}」指向不存在的章（全书 {len(chapters)} 章）：{excerpt(line)}",
                )
            )
    if not hits:
        readings = f"{scanned} 处「第 N 章」引用，0 处空指（全书 {len(chapters)} 章）"
        return {"name": "cross-ref", "state": "pass", "readings": readings, "hits": []}
    readings = f"{scanned} 处「第 N 章」引用，{len(hits)} 处空指（全书 {len(chapters)} 章）"
    return {"name": "cross-ref", "state": "fail", "readings": readings, "hits": hits}


def check_progress(book_dir: Path) -> dict:
    path = book_dir / "progress.md"
    if not path.is_file():
        return {
            "name": "progress-ledger",
            "state": "fail",
            "readings": "缺 progress.md",
            "hits": [hit(None, None, "缺 progress.md：每章一行（章号 → 完成 → 审计结论），同口径不豁免")],
        }
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return {
        "name": "progress-ledger",
        "state": "pass",
        "readings": f"progress.md 在（{size} 字节；本检查只验在不在，不解析正文）",
        "hits": [],
    }


def resolve_declaration(specs: list[tuple[str, str]], section_keyword: str, label: str) -> tuple[dict, str | None]:
    """先看 style-spec，没有再回退 META；同族声明只取第一份读到的。

    先在这一节里读，读不到再看全文——交付检查的声明读取也是「这一节优先、
    声明行在别处也认」，两处口径保持一致；⛔ 仍不回落硬编码词表。
    """
    for name, text in specs:
        section = section_text(text, section_keyword)
        if section is not None:
            declared = declaration_from_section(section, label)
            if declared["state"] != "undeclared":
                return declared, name
        declared = declaration_from_section(text, label)
        if declared["state"] != "undeclared":
            return declared, name
    return {"state": "undeclared", "items": []}, None


def resolve_scaffold_titles(specs: list[tuple[str, str]]) -> dict:
    """脚手架标题**两份写作规范都读**：skill 侧拆脚手架脚本只读 META.md，所以两处都认。"""
    items: list[str] = []
    declared_seen = False
    for _name, text in specs:
        # 先按「脚手架标题」那一节读（标题式/列表式），再退回全文中带冒号的行。
        declared = declaration_from_section(section_text(text, "脚手架标题"), "脚手架标题")
        if declared["state"] == "undeclared":
            declared = declaration_from_section(text, "脚手架标题")
        if declared["state"] == "undeclared":
            continue
        declared_seen = True
        for item in declared["items"]:
            if item and item not in items:
                items.append(item)
    if items:
        return {"state": "declared", "items": items}
    if declared_seen:
        return {"state": "declared-none", "items": []}
    return {"state": "undeclared", "items": []}


def gather_specs(book_dir: Path) -> list[tuple[str, str]]:
    """读写作规范：style-spec.md 先，META.md 回退；两份都在时都提供给各自的族。"""
    specs: list[tuple[str, str]] = []
    for name in ("style-spec.md", "META.md"):
        path = book_dir / name
        if path.is_file():
            specs.append((name, normalize_text(read_text(path, f"写作规范 {name}"))))
    return specs


def run_checks(book_dir: Path) -> tuple[list[dict], str | None]:
    """跑全部检查；返回 `(checks, fatal_error)`。缺 BOOK.md 时 fatal_error 非空。

    ⚠️ 十个检查项里**没有**「成品＝各章拼装件」（交付检查第 ⑦ 项）：那一格由装配脚本
    `merge_book.py` 在合并前逐字核「章正文＝当前分片的重拼结果」，本脚本不重复判、也不冒充
    自己能判。别把「10 项全绿」读成「12 项交付自查全过」——⑥ 文件大小与 ⑧ 已划知识点也归人。
    """
    book_path = book_dir / "BOOK.md"
    if not book_path.is_file():
        return [], f"缺 BOOK.md：{book_path}（没有成品就没有交付检查）"
    book_text = normalize_text(read_text(book_path, "成品书 BOOK.md"))

    specs = gather_specs(book_dir)
    spec_names = "、".join(name for name, _ in specs) if specs else ""

    outline_path = book_dir / "OUTLINE.md"
    outline = None
    outline_note = ""
    if outline_path.is_file():
        outline, outline_note = parse_outline(normalize_text(read_text(outline_path, "章节骨架 OUTLINE.md")))
        if outline is None:
            # 读不出来时不让依赖它的三项静默判绿：下面各 check 按 outline is None 记 not-checked。
            outline = None
    else:
        outline_note = "缺 OUTLINE.md"

    chapters = split_book(book_text)

    required, required_source = resolve_declaration(specs, "章内板块语法", "必含板块")
    banned, banned_source = resolve_declaration(specs, "正文语言风格", "禁用词")
    scaffold = resolve_scaffold_titles(specs)

    checks = [
        check_encode(book_text, chapters),
        check_chapters_count(book_dir, chapters, outline),
        check_chapter_title_unique(chapters, outline),
        check_heading_duplicate(chapters),
        check_required_blocks(chapters, required, required_source, spec_names),
        check_banned_words(book_text, chapters, banned, banned_source, spec_names),
        check_scaffold(
            book_text,
            chapters,
            scaffold,
            declared_missing=not specs or scaffold["state"] == "undeclared",
        ),
        check_word_budget(book_dir, outline),
        check_cross_ref(book_text, chapters),
        check_progress(book_dir),
    ]

    # 写作规范缺失／OUTLINE 读不出时，把「没得查」的原因如实写进读数（不是判绿）。
    if not specs:
        for check in checks:
            if check["name"] in ("required-blocks", "banned-words") and "缺 style-spec.md/META.md" not in check["readings"]:
                check["readings"] = f"缺 style-spec.md/META.md：{check['readings']}"
    elif outline is None:
        note = outline_note or "OUTLINE.md 读不出"
        for check in checks:
            if check["name"] not in ("chapters-count", "chapter-title-unique", "word-budget"):
                continue
            # 文件在、但骨架读不出来时，别把原因说成「缺 OUTLINE.md」——那两句会互相打架。
            if "缺 OUTLINE.md，这一项没得查" in check["readings"] and note != "缺 OUTLINE.md":
                check["readings"] = f"{note}，这一项没得查"
            elif note not in check["readings"]:
                check["readings"] = f"{note}：{check['readings']}"
    return checks, None


def summarize(checks: list[dict], exit_code: int) -> dict:
    return {
        "red": sum(1 for check in checks if check["state"] == "fail"),
        "warn": sum(1 for check in checks if check["state"] == "warn"),
        "notChecked": sum(1 for check in checks if check["state"] == "not-checked"),
        "total": len(checks),
        "exitCode": exit_code,
    }


def print_human(checks: list[dict], summary: dict) -> None:
    for check in checks:
        label = f"[{STATE_LABELS.get(check['state'], check['state'].upper())}]"
        print(f"{label:<7} {check['name']:<20} {check['readings']}")
        for item in check["hits"]:
            location = where(item.get("chapter"), item.get("line"))
            print(f"  - {location}：{item['text']}")
    print(
        f"红 {summary['red']} 项 / 提示 {summary['warn']} 项 / 未查 {summary['notChecked']} 项"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_book.py",
        description="skill 侧交付前检查器：只读、判据从盘上读（对齐交付检查里 skill 侧能判的那几项）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""检查项（--json 的 name 字段就是这些名字）：
  encode               乱码 U+FFFD 计数
  chapters-count       章数＝章节骨架声明的章数；章正文逐章点名缺哪几章
  chapter-title-unique 章名全书唯一（归一化后比较）
  heading-duplicate    同一章内 H2/H3 标题不重名；跨章同名只提示
  required-blocks      每章含写作规范声明的必含板块
  banned-words         写作规范声明的禁用词命中数
  scaffold             通用标记＋写作规范声明的脚手架标题＋八类里按形状能认的 6 类
                       （⑤ 另认两种形状：括注出处、源简码＋章号；附录区与「说法不一」节有白区）
  word-budget          逐章汉字数 vs OUTLINE 的 targetWords（只报数，低于兜底不判红）
  cross-ref            「第 N 章」引用指向真实存在的章
  progress-ledger      progress.md 在不在（同口径，不豁免）

⚠️ 交付检查第 ⑦ 项（成品＝各章拼装件）不在这里：由装配脚本 merge_book.py 在合并前核。
⚠️ ⑥ 文件大小与 ⑧ 已划知识点仍归人；②⑥ 措辞类只提示。

输入（全部从盘上读，没有就记 not-checked 并点名缺哪份，⛔ 不静默判绿）：
  style-spec.md / META.md  必含板块、禁用词、脚手架标题；先看 style-spec.md，没有再回退 META.md
  OUTLINE.md               章数、章名、每章 targetWords
  BOOK.md                  成品书（缺它 → 退出码 2）
  chapters/chapter-<NN>.md 逐章汉字数
  progress.md              进度账

退出码：0 无红项且无未查项（只提示不算红）；1 有红项、**或有未查项**；2 缺必需输入或输入读不出来。
⚠️ 未查项（not-checked）不再当绿——「没得查」不是「查过干净」。确认确实不适用时用
   --allow-unchecked 显式放行，读数与 JSON 会印出放行了哪几项。

只读：本脚本不写盘、不删文件。拆脚手架仍由 strip_meta_sections.py 做，顺序仍是「拆 → 重拼 → 合并」。
依赖：只用 Python 标准库（今天没有第三方依赖）。
""",
    )
    parser.add_argument("book_dir", nargs="?", default=".", help="书目录（默认当前目录）")
    parser.add_argument("--json", action="store_true", help="输出机器可读的 JSON")
    parser.add_argument(
        "--allow-unchecked",
        action="store_true",
        help="未查项放行：有 not-checked 项时仍退出 0（读数与 JSON 里会印出放行了哪几项）",
    )
    return parser


def emit_fatal(message: str, as_json: bool) -> int:
    """缺必需输入的统一出口：JSON 走 stdout，人话走 stderr，退出码 2。"""
    if as_json:
        print(
            json.dumps(
                {"checks": [], "summary": summarize([], EXIT_INPUT), "error": message},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"[ERROR] {message}", file=sys.stderr)
    return EXIT_INPUT


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    book_dir = Path(args.book_dir)
    if not book_dir.exists() or not book_dir.is_dir():
        return emit_fatal(f"书目录不存在或不是目录：{book_dir}", args.json)

    try:
        checks, fatal = run_checks(book_dir)
    except InputError as error:
        return emit_fatal(str(error), args.json)

    if fatal is not None:
        return emit_fatal(fatal, args.json)

    has_fail = any(check["state"] == "fail" for check in checks)
    unchecked = [check["name"] for check in checks if check["state"] == "not-checked"]
    if has_fail:
        exit_code = EXIT_FAIL
    elif unchecked and not args.allow_unchecked:
        exit_code = EXIT_FAIL
    else:
        exit_code = EXIT_OK
    summary = summarize(checks, exit_code)
    summary["uncheckedNames"] = unchecked
    if unchecked and args.allow_unchecked and not has_fail:
        summary["uncheckedAllowed"] = True
    if args.json:
        print(json.dumps({"checks": checks, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        print_human(checks, summary)
    if unchecked and args.allow_unchecked and not has_fail:
        print(
            f"[WARN] --allow-unchecked 生效：放行未查 {len(unchecked)} 项"
            f"（{'、'.join(unchecked)}）——放行不等于查过",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
