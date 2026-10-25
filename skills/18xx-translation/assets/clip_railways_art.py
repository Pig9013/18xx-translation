#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Railways 英文原书 PDF 裁剪插图与公司徽记（供排版版 PDF 嵌入）。

- 原书的图是被切成大量小碎片的内嵌位图，无法单张提取——统一用「按坐标区域高分渲染 + 自动裁边」。
- 坐标（PDF pt，左上原点）经多轮目视核对确定；改坐标后重跑本脚本即可。
- 产物：_work/railways_trans/art/*.png
用法：python _tools/clip_railways_art.py [--sheet]   （--sheet 额外生成质检拼图）
"""
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / 'Railways-EN-2nd-Rulebook.pdf'
OUT = ROOT / '_work' / 'railways_trans' / 'art'
OUT.mkdir(parents=True, exist_ok=True)

# name: (PDF页, (x0,y0,x1,y1) pt, 渲染倍率)
ARTS = {
    # ── 组件图解（原书 p.5）─────────────── 对应 md「五、组件图解与地图图例」
    'comp_minor':  (6, (36, 64, 368, 252), 4),
    'comp_major':  (6, (368, 64, 726, 222), 4),
    'comp_shares': (6, (40, 275, 318, 436), 4),
    'comp_trains': (6, (320, 275, 504, 436), 4),
    'comp_tiles':  (6, (506, 286, 775, 450), 4),
    'comp_legend': (6, (50, 446, 744, 592), 3),
    # ── 图 1–9 ─────────────────────────── 对应 md「图 N 说明」
    'fig1': (7,  (108, 206, 258, 458), 4),
    'fig2': (8,  (52, 290, 285, 468), 4),
    'fig3': (11, (48, 84, 272, 236), 4),
    'fig4': (13, (36, 90, 246, 248), 4),
    'fig5': (13, (12, 312, 214, 490), 4),
    'fig6': (14, (355, 345, 505, 472), 4),
    'fig7': (15, (80, 72, 285, 240), 4),
    'fig8': (16, (508, 12, 755, 212), 4),
    'fig9': (19, (42, 198, 285, 381), 4),
    # ── 桌面布置（原书 p.8–9 两幅整页示意）── 对应 md「七、桌面布置」
    'setup_a': (9,  (40, 30, 788, 585), 2.2),
    'setup_b': (10, (40, 30, 788, 585), 2.2),
    # ── 六家大公司徽记条（组件页照片）──── 对应 md「二、组件」大公司条目
    'majors_strip': (4, (46, 78, 774, 122), 3),
    # ── 12 家小公司徽记（原书 p.24 公司详情页，矢量）─ 对应 md「十五、公司详情」与各家旁注
    # 名称行锚点：第一排 y=130、第二排 y=388；徽记圆位于名称上方（约 26pt 直径）
    'ico_adaptive':    (25, (47, 96, 81, 129), 8),
    'ico_overnight':   (25, (162, 96, 196, 129), 8),
    'ico_bridging':    (25, (278, 96, 312, 129), 8),
    'ico_spacious':    (25, (393, 96, 427, 129), 8),
    'ico_expansive':   (25, (508, 96, 542, 129), 8),
    'ico_suburban':    (25, (623, 96, 657, 129), 8),
    'ico_resourceful': (25, (47, 354, 81, 387), 8),
    'ico_agricultural': (25, (162, 354, 196, 387), 8),
    'ico_tunneling':   (25, (278, 354, 312, 387), 8),
    'ico_eastern':     (25, (393, 354, 427, 387), 8),
    'ico_nport':       (25, (508, 354, 542, 387), 8),
    'ico_express':     (25, (623, 354, 657, 387), 8),
}
ICON_PAD = 1   # 徽记裁边后留白（px）


def crop(page, box, zoom, thresh=16, pad=8):
    pg = PDF_DOC[page - 1]
    r = fitz.Rect(*box) & pg.rect
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=r)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    bg = im.getpixel((2, 2))
    mask = (ImageChops.difference(im, Image.new('RGB', im.size, bg))
            .convert('L').point(lambda p: 255 if p > thresh else 0))
    b = mask.getbbox()
    if b:
        x0, y0, x1, y1 = b
        im = im.crop((max(0, x0 - pad), max(0, y0 - pad),
                      min(im.width, x1 + pad), min(im.height, y1 + pad)))
    return im, bg


def main():
    global PDF_DOC
    PDF_DOC = fitz.open(PDF)
    made = {}
    for name, (page, box, zoom) in ARTS.items():
        im, bg = crop(page, box, zoom, pad=ICON_PAD if name.startswith('ico_') else 8)
        im.save(OUT / f'{name}.png')
        made[name] = im
    # 报告原书纸色（供排版版页面底色对齐）
    sample = PDF_DOC[5].get_pixmap(matrix=fitz.Matrix(2, 2), clip=fitz.Rect(2, 2, 12, 12))
    px = sample.pixel(5, 5)
    print('原书纸色 RGB:', px, '= #%02X%02X%02X' % px)
    for n, im in made.items():
        print(f'  {n:16s} {im.width}x{im.height}px')

    if '--sheet' in sys.argv:
        from PIL import ImageDraw
        names = list(made)
        cw, ch, cols = 330, 240, 5
        rows = (len(names) + cols - 1) // cols
        s = Image.new('RGB', (cols * cw + 8 * (cols - 1), rows * (ch + 20)), (255, 255, 255))
        dr = ImageDraw.Draw(s)
        for i, n in enumerate(names):
            im = made[n]
            k = min(cw / im.width, ch / im.height, 2)
            im2 = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
            r, c = divmod(i, cols)
            x, y = c * (cw + 8), r * (ch + 20)
            dr.text((x + 4, y + 3), f'{n} {im.width}x{im.height}', fill=(160, 30, 30))
            s.paste(im2, (x + (cw - im2.width) // 2, y + 17))
        qc = OUT.parent / 'qc' / 'art_final.png'
        s.save(qc)
        print('质检拼图:', qc)


if __name__ == '__main__':
    main()
