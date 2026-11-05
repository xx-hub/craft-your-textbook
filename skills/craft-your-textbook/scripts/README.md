# scripts/ · 造书脚本模板

> 这些脚本是**示例模板**：造书时复制进你的项目（约定放 `<项目根>/scripts/`）再跑。
> 直接改 skill 目录里的原件会被插件更新覆盖。

## 用法一览

| 阶段 | 命令 | 干什么 |
| --- | --- | --- |
| Phase 1 | `python scripts/01_pdf_to_md.py <PDF路径> <输出目录>` | MinerU 在线 API 把 PDF 转 Markdown（需 `MINERU_TOKEN`） |
| Phase 5 · 分片拼章 | `python scripts/assemble_chapter.py .` | 把 `chapters/shards/chapter-<NN>-<MM>.md` 按 MM 升序拼成 `chapters/chapter-<NN>.md`（片间一个空行，只拼不改） |
| Phase 5.4 · 整本合并 | `python scripts/merge_book.py .` | 把 `chapters/` ＋ `appendix/` 合并成 `BOOK.md`（human-readable 路线注入 loader 指令）；`chapters/shards/` 是分片原料、**不当章收**。`META.md` 的 `format:` 两个**机器 id**（`blueprint`／`human`）与两个**路线名**（`pure-blueprint`／`human-readable`）都认。⚠️ **合并前先核「章正文＝当前分片的重拼结果」**：某章有分片而章正文与重拼结果不一致（或章正文不在）⇒ 非零退出、点名第 N 章、**一个字节都不写**，要你先跑 `assemble_chapter.py` 重拼（票 `skill-release-ready/14`） |
| Phase 6 · 拆脚手架 | `python scripts/strip_meta_sections.py chapters/ appendix/` | 按写作规范里的脚手架标题列表，拆掉**分片末尾**的过程元数据板块；拼好的章正文是派生件，有分片时跳过（见下）。⚠️ **必须先 `cd` 到项目根**——它把项目根钉死成 `.`（另两个脚本收项目根参数），从别处跑会读不到 `META.md`、0 删除、exit 0 |
| Phase 6 · 重拼 | `python scripts/assemble_chapter.py .` | 拆完脚手架把章正文重新拼一遍（分片变了，派生件要跟着变） |
| 任意 | `python <脚本> --help` | 只印用法、**一个字节都不写**（`merge_book.py --help` 原先会把已有的 `BOOK.md` 清成 0 字节、退出码还是 0） |

## 脚手架标题写在哪、怎么写（两处文档原先各说各的，票 09 走查实测）

- **载体**：`META.md`（只有它）。写到 `style-spec.md` 里**不生效**——脚本只读 `META.md`，
  读不到就 `[warn]` 并退回三个默认标题。
- **形状**：**bullet list**，一行一条：

  ```markdown
  ## 脚手架标题
  - ## 自检清单
  - ## 版本记录
  ```

  一行式（`脚手架标题：## 自检清单、## 版本记录`）**不认**——脚本按 `^[-*]\\s+` 收条目，
  收不到就 `[warn] '脚手架标题'后没有列表条目，用默认标题`，然后 0 删除、exit 0。
- 默认标题是 `## 📋 自检清单`／`## 📜 版本记录`／`## 写作笔记`（带 emoji）。你写的是自然标题时，
  **一定要显式声明**，否则一个都拆不掉而退出码照样 0。

## `strip_meta_sections.py` 拆哪一层（票 `skill-release-ready/09` 走查抓到的真丢稿）

- 脚手架是**每个写作单元**写在**它那一片的末尾**的，所以**拆的是分片** `chapters/shards/*.md`。
- **拼好的 `chapters/chapter-<NN>.md` 在那章有分片时会被跳过**：片 1 末尾的脚手架在拼好的正文里落在**中间**，
  按「标题到文件末尾」截断会把片 2 之后的正文一起删掉、且退出码照旧 0。没有分片的老书照旧拆章正文。
- 拆完**必须重拼**（`assemble_chapter.py`）再合并（`merge_book.py`）——跳过章正文之后它还是带脚手架的那一份。

## `merge_book.py` 的“分片比章正文新”红（票 `skill-release-ready/14`）

- **病**：交付检查第 ⑦ 项原来说「交付前重跑 `merge_book.py`，前后 `md5sum BOOK.md` 相同 ⇒ 过」。但 md5
  只证「merge 前后成品没变」——改一片分片、**不重拼**、只再 merge 一次，前后 md5 **完全相同**，而书里
  还是旧正文 ⇒ 判据恒绿、成品是旧的。
- **修法**：`merge_book.py` 在写 `BOOK.md` **之前**逐章核「章正文逐字等于当前那几片分片按拼章口径拼出来
  的结果」。不是 ⇒ 非零退出、点名第 N 章、**一个字节都不写**（⛔ 它不替你重拼：那是 `assemble_chapter.py`
  的活，也不把旧正文再抄一遍）。
- **为什么比内容不比 mtime**：「分片新于章正文」只是最常见的形状，不是判据本身——mtime 会被 `git
  checkout`、复制、跨盘搬运整体推后，照 mtime 判会假红（内容没变却逼人重拼）也会假绿（mtime 没变而内容变了）。
- **没有分片目录的老书不在面内**：那里章正文自己就是写作单元，没有「重拼」这一步，照旧直接合并。

## `assemble_chapter.py` 的三种红与一种黄

- **红（非零退出、点名，且一个字都不写）**：该章一片分片都没有／片号重复／片是空文件。
- **黄（只警告）**：片号跳号——例如有 `-01` 有 `-03`。这可能是**有意**的：主笔把一章拆两路，第二路还没交。
- **幂等**：拼出来的内容与盘上 `chapter-NN.md` 逐字相同时**不重写**，mtime 不动
  （下游有「正文比检查记录新 ⇒ 审的是旧稿」这类判据，重写会把它骗过去）。
- stdout 印三句可核对的话：**片数、实际片号、字数合计**（状态行与 `[warn]` 走 stderr，`stdout | wc -l` 正好对上三句）。
- 分片号按「一位以上数字」认：规范写法是两位（`chapter-01-02.md`），少补一个零（`chapter-1-2.md`）也认得出。
  代价：两个不同名却同号的分片会被按「片号重复」拦下，不会静默拼两遍。

> ⛔ **拼完不等于干净章**：本脚本**不删脚手架**（自检清单／版本记录／写作笔记这类元数据），
> 也**不做字数硬闸**（字数只印出来给主笔与审计读）。拆脚手架是 `strip_meta_sections.py`
> 与交付前检查的活（拆**分片**那一层，见上）；拼完整本仍走 `merge_book.py`，别手改 `BOOK.md`。

## 依赖

`pip install -r scripts/requirements.txt`（只有 `/01_pdf_to_md.py` 用到 `requests`；
拼章、合并、拆脚手架三件只用 Python 标准库）。
