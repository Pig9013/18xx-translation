#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前静态自检：README 链接、PDF 元数据、单文件大小、缓存/临时文件、版本号一致。

用法：python tools/verify_repo.py
退出码 0 = 全部通过（可有警告）；1 = 有错误。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []
warns = []


def walk_files():
    for r, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in fs:
            yield os.path.join(r, f)


def main():
    # 1. 文件大小 / 缓存
    for p in walk_files():
        rel = os.path.relpath(p, ROOT)
        mb = os.path.getsize(p) / 1048576
        if mb > 100:
            errors.append("[size] %s: %.1f MB > 100 MB" % (rel, mb))
        if "__pycache__" in rel or p.endswith(".pyc"):
            errors.append("[cache] %s 不应入库" % rel)

    # 2. README 相对链接
    readme = os.path.join(ROOT, "README.md")
    if not os.path.exists(readme):
        errors.append("[readme] 缺少 README.md")
    else:
        text = open(readme, encoding="utf-8").read()
        targets = re.findall(r"\]\(<([^>]+)>\)", text) + re.findall(r"\]\(([^)<\s]+)\)", text)
        for target in targets:
            target = target.strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#")[0].strip()
            if not target:
                continue
            if not os.path.exists(os.path.join(ROOT, target)):
                errors.append("[link] README -> %s 不存在" % target)

    # 3. PDF 可读性 / 页数 / 标题
    try:
        import fitz
    except ImportError:
        fitz = None
        warns.append("[pdf] 未安装 PyMuPDF，跳过 PDF 检查")
    if fitz:
        pdfs = [p for p in walk_files() if p.lower().endswith(".pdf")]
        for p in sorted(pdfs):
            rel = os.path.relpath(p, ROOT)
            try:
                d = fitz.open(p)
                title = (d.metadata or {}).get("title") or ""
                if d.page_count < 1:
                    errors.append("[pdf] %s: 0 页" % rel)
                if not title:
                    warns.append("[pdf] %s: 无标题元数据" % rel)
                print("  PDF %-55s %3dp | %s" % (rel, d.page_count, title[:40]))
                d.close()
            except Exception as e:
                errors.append("[pdf] %s: 打不开（%s）" % (rel, e))

    # 4. README 当前版本 vs CHANGELOG 首条
    cl = os.path.join(ROOT, "CHANGELOG.md")
    if os.path.exists(cl) and os.path.exists(readme):
        head = "\n".join(open(readme, encoding="utf-8").read().splitlines()[:25])
        m = re.search(r"仓库版本[：:]\s*v(\d+\.\d+\.\d+)", head) or re.search(r"v(\d+\.\d+\.\d+)", head)
        c = re.search(r"^##\s*v(\d+\.\d+\.\d+)", open(cl, encoding="utf-8").read(), re.M)
        if m and c and m.group(1) != c.group(1):
            warns.append("[ver] README 当前版本 v%s 与 CHANGELOG 首条 v%s 不一致" % (m.group(1), c.group(1)))

    # 5. 汇总
    print()
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print("=" * 60)
    print("检查完成：%d 个错误，%d 个警告" % (len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
