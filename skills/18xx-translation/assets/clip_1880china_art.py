#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 1880 China 英文原书 PDF 裁剪插图（供排版版 PDF 嵌入）。

坐标（PDF pt，左上原点）经网格叠图 + 程序化探测 + 逐张目视 QC 确定；
改坐标后重跑本脚本即可。注意三坑已处理：邻栏正文条带、原书页码、页头装饰。
产物：_work/1880_trans/art/*.png（26 张）
用法：python _tools/clip_1880china_art.py [--sheet]
"""
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / '英规1880chinaRules.pdf'
OUT = ROOT / '_work' / '1880_trans' / 'art'
OUT.mkdir(parents=True, exist_ok=True)

# name: (PDF页, (x0,y0,x1,y1) pt, 渲染倍率)
ARTS = {
    # 封面
    'cover_logo':  (1, (60, 10, 560, 150), 2.5),
    'cover_art':   (1, (18, 198, 578, 536), 2),
    # 组件（原书 p.3）
    'comp_map':        (3, (26, 50, 280, 418), 2.2),
    'comp_tiles':      (3, (293, 48, 470, 174), 2.5),
    'comp_cards':      (3, (26, 466, 592, 712), 2.2),
    'comp_incometable': (3, (296, 189, 469, 321), 3),
    'comp_pricechart': (3, (294, 331, 470, 458), 2.2),
    # 游戏准备（p.4）
    'setup_money': (4, (300, 240, 512, 348), 3),
    # 私营公司卡 ×8（p.6，一列八张与 P0–P7 行一一对应；pitch 85pt）
    'pc_P0': (6, (143, 116, 271, 202), 3.5),
    'pc_P1': (6, (143, 201, 271, 287), 3.5),
    'pc_P2': (6, (143, 286, 271, 372), 3.5),
    'pc_P3': (6, (143, 371, 271, 457), 3.5),
    'pc_P4': (6, (143, 456, 271, 542), 3.5),
    'pc_P5': (6, (143, 541, 271, 627), 3.5),
    'pc_P6': (6, (143, 626, 271, 712), 3.5),
    'pc_P7': (6, (143, 711, 271, 797), 3.5),
    # 主要公司（p.10）
    'dir_cert':    (10, (428, 32, 575, 142), 3),
    'permit_card': (10, (458, 410, 552, 548), 3),
    # 运营轮次（p.11）
    'or_photo': (11, (476, 33, 578, 197), 3),
    # 路线示例（p.12）
    'icr_map': (12, (103, 333, 494, 598), 2.5),
    # 列车（p.14）
    'train_card_a':  (14, (450, 44, 564, 124), 3),
    'train_card_b':  (14, (450, 188, 564, 270), 3),
    'operation_map': (14, (106, 376, 490, 660), 2.2),
    'train_pic':     (14, (400, 738, 537, 828), 3),
    # 购买列车示例（p.15）
    'train_stack': (15, (58, 472, 208, 708), 2.5),
    # 收入/奖励（p.17）
    'chart_p17': (17, (52, 316, 298, 466), 3),
    'transsib':  (17, (56, 518, 565, 700), 2),
    # 板块清单 / 升级图（p.23）
    'manifest': (23, (28, 40, 594, 500), 2),
    'upgrade':  (23, (28, 502, 568, 816), 2),
    # 游戏阶段速查表（p.24）
    'gamephase': (24, (26, 62, 592, 618), 2),
}


def crop(page, box, zoom, thresh=16, pad=1):
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
    return im


def main():
    global PDF_DOC
    PDF_DOC = fitz.open(PDF)
    made = {}
    for name, (page, box, zoom) in ARTS.items():
        im = crop(page, box, zoom)
        im.save(OUT / f'{name}.png')
        made[name] = im
    px = PDF_DOC[5].get_pixmap(matrix=fitz.Matrix(2, 2), clip=fitz.Rect(2, 2, 12, 12)).pixel(5, 5)
    print('原书纸色 RGB:', px, '= #%02X%02X%02X' % px)
    for n, im in made.items():
        print(f'  {n:18s} {im.width}x{im.height}px')

    if '--sheet' in sys.argv:
        from PIL import ImageDraw
        names = list(made)
        cols, cw, ch = 5, 300, 230
        rows = (len(names) + cols - 1) // cols
        s = Image.new('RGB', (cols * cw + 6 * (cols - 1), rows * (ch + 20)), (255, 255, 255))
        dr = ImageDraw.Draw(s)
        for i, n in enumerate(names):
            im = made[n]
            k = min(cw / im.width, ch / im.height, 1.6)
            im2 = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
            r, c = divmod(i, cols)
            x, y = c * (cw + 6), r * (ch + 20)
            dr.text((x + 3, y + 2), n, fill=(170, 30, 30))
            s.paste(im2, (x + (cw - im2.width) // 2, y + 17))
        s.save(OUT.parent / 'qc_art_final.png')
        print('质检拼图:', OUT.parent / 'qc_art_final.png')


if __name__ == '__main__':
    main()
