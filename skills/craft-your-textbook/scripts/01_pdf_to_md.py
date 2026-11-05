# -*- coding: utf-8 -*-
"""
造书 Phase 1：PDF → Markdown（MinerU 在线 API 方案）

★★ 本文件是**示例模板**。请复制进你的造书项目（约定放 <项目根>/scripts/）后，
    按需改顶部「转换参数」常量再跑——不要直接改 skill 目录里的原件（会被插件更新覆盖）。
    依赖：pip install -r requirements.txt（就一个 requests）。

★ 运行前必须先申请 API Token：
    1. 打开 https://mineru.net 注册/登录
    2. 进入「API」/「个人中心」页面申请 API Token（免费额度足够造书用）
    3. 把 Token 设为环境变量（不要硬编码进代码，避免泄漏）：
         Windows (Git Bash):  export MINERU_TOKEN="你的token"
         Windows (PowerShell): $env:MINERU_TOKEN="你的token"
         Linux/Mac:            export MINERU_TOKEN="你的token"

用法：
    export MINERU_TOKEN="..."
    python 01_pdf_to_md.py <输入PDF路径> <输出目录>
    # 例：python 01_pdf_to_md.py "教材.pdf" sources-md/

流程（MinerU v4 API）：
    1. 申请批量上传链接（POST /api/v4/file-urls/batch）
    2. PUT 上传 PDF
    3. 轮询任务状态（GET /api/v4/extract-results/batch/{batch_id}）
    4. 下载 zip 结果并解压到输出目录（内含 full.md + 图片）
"""

import io
import os
import sys
import time
import zipfile
from pathlib import Path

# ⚠️ 依赖检查**推迟到真跑的时候**（票 `skill-release-ready/09` 收口 review 抓到的）：
# 原先它在模块顶层就 `import requests`、缺库直接 `sys.exit(1)`，于是**没装依赖的机器上
# `--help` 也退出 1**——而 `--help` 恰好是这些人最需要的那条命令。缺库的提示改在
# `require_requests()` 里，`--help` 走不到它。

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

API_BASE = "https://mineru.net"

# ── 转换参数（按教材类型调整）──────────────────────────────────
MODEL_VERSION = "vlm"     # vlm 对扫描版教材版面识别更准
ENABLE_FORMULA = False    # 理科教材（大量公式）设 True
ENABLE_TABLE = True       # 保留表格识别
LANGUAGE = "ch"           # 主语言：ch=中文, en=英文 ...


def get_headers():
    token = os.environ.get("MINERU_TOKEN")
    if not token:
        sys.exit(
            "✗ 未找到 MINERU_TOKEN 环境变量。\n"
            "  请先去 https://mineru.net 申请 API Token，然后：\n"
            '    export MINERU_TOKEN="你的token"'
        )
    return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}


def step1_apply_upload_url(pdf_path, headers):
    print("\n[Step 1] 申请上传链接 ...")
    url = f"{API_BASE}/api/v4/file-urls/batch"
    data = {
        "files": [{"name": os.path.basename(pdf_path), "data_id": "book-src"}],
        "model_version": MODEL_VERSION,
        "enable_formula": ENABLE_FORMULA,
        "enable_table": ENABLE_TABLE,
        "language": LANGUAGE,
    }
    res = requests.post(url, headers=headers, json=data, timeout=60)
    result = res.json()
    print(f"  HTTP {res.status_code} | code={result.get('code')} msg={result.get('msg')}")
    if result.get("code") != 0:
        raise RuntimeError(f"申请上传链接失败: {result}")
    batch_id = result["data"]["batch_id"]
    file_urls = result["data"]["file_urls"]
    print(f"  batch_id = {batch_id}")
    return batch_id, file_urls


def step2_upload_file(pdf_path, file_urls):
    print("\n[Step 2] 上传 PDF ...")
    size_mb = os.path.getsize(pdf_path) / 1024 / 1024
    print(f"  文件: {pdf_path} ({size_mb:.2f} MB)")
    with open(pdf_path, "rb") as f:
        res = requests.put(file_urls[0], data=f, timeout=300)
    if res.status_code != 200:
        raise RuntimeError(f"上传失败: {res.text}")
    print("  上传成功")


def step3_poll_batch_result(batch_id, headers, max_wait_seconds=3600):
    print(f"\n[Step 3] 轮询任务结果（batch_id={batch_id}）...")
    url = f"{API_BASE}/api/v4/extract-results/batch/{batch_id}"
    start = time.time()
    last = None
    while time.time() - start < max_wait_seconds:
        res = requests.get(url, headers=headers, timeout=60)
        result = res.json()
        if result.get("code") != 0:
            time.sleep(15)
            continue
        data_list = result.get("data", {}).get("extract_result", [])
        if not data_list:
            time.sleep(15)
            continue
        item = data_list[0]
        state = item.get("state", "unknown")
        prog = item.get("extract_progress", {})
        cur = f"{state}:{prog.get('extracted_pages', 0)}/{prog.get('total_pages', 0)}"
        if cur != last:
            print(f"  [{int(time.time()-start)}s] 状态 {state} | 进度 {prog.get('extracted_pages',0)}/{prog.get('total_pages',0)} 页")
            last = cur
        if state == "done":
            print("  ✅ 解析完成")
            return item
        if state == "failed":
            raise RuntimeError(f"解析失败: {item.get('err_msg', '')}")
        time.sleep(15)
    raise TimeoutError("等待超时")


def step4_download_and_unzip(zip_url, output_dir):
    print("\n[Step 4] 下载并解压 ...")
    output_dir.mkdir(parents=True, exist_ok=True)
    res = requests.get(zip_url, timeout=300)
    if res.status_code != 200:
        raise RuntimeError("下载 zip 失败")
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        names = zf.namelist()
        zf.extractall(output_dir)
        print(f"  已解压 {len(names)} 个文件到: {output_dir}")


HELP = """PDF → Markdown（MinerU 在线 API）。

用法:
    export MINERU_TOKEN="..."
    python 01_pdf_to_md.py <输入PDF路径> <输出目录>

- 需要环境变量 MINERU_TOKEN（缺了会明确报错并退出，不是静默失败）。
- 只依赖 requests（pip install -r requirements.txt）。
- 已有 MD 的源可跳过本步（SKILL.md「Phase 1 前置」）。
- 理科材料把顶部 ENABLE_FORMULA 改成 True。

⛔ `--help` 只印这份用法、一个字节都不写、退出码 0。
"""


def require_requests():
    """真跑之前才要 requests：缺库时给一条能照做的提示，⛔ 不是裸 ImportError。"""
    try:
        import requests
    except ImportError:
        sys.exit(
            "✗ 缺少 requests 库。请先安装：\n"
            "    pip install requests\n"
            "  （或 pip install -r scripts/requirements.txt）"
        )
    globals()["requests"] = requests


def main():
    # `--help` 单独处理（票 `skill-release-ready/09` 走查实测：它原先落进下面那条 usage 分支、
    # 以退出码 1 打印——而 `scripts/README.md` 承诺「任意脚本 --help 只印用法」。用法是印出来了，
    # 但一个「我想看看怎么用」的请求不该带非零退出码）。
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(HELP, end="")
        return 0
    if len(sys.argv) < 3:
        sys.exit("用法: python 01_pdf_to_md.py <输入PDF路径> <输出目录>")
    require_requests()
    pdf_path = sys.argv[1]
    output_dir = Path(sys.argv[2])
    if not os.path.isfile(pdf_path):
        sys.exit(f"✗ PDF 不存在: {pdf_path}")

    headers = get_headers()
    print("=" * 60)
    print(f"MinerU PDF → Markdown | 源: {pdf_path} | 输出: {output_dir}")
    print("=" * 60)

    batch_id, file_urls = step1_apply_upload_url(pdf_path, headers)
    step2_upload_file(pdf_path, file_urls)
    result = step3_poll_batch_result(batch_id, headers)
    zip_url = result.get("full_zip_url")
    if not zip_url:
        raise RuntimeError(f"未找到 full_zip_url，返回: {result}")
    step4_download_and_unzip(zip_url, output_dir)
    print("\n✅ 全部完成，输出目录:", output_dir)


if __name__ == "__main__":
    sys.exit(main())
