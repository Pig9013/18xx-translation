#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把《1880China_规则中文翻译.md》按英文原书版式重排为中文 PDF（正文一字不改）。

按 skill `18xx-analysis` §8 的标准流程；样板为 Railways 版（build_railways_pdf.py）。
本作特点：A4 竖版、原书黑色横幅章节头、纸色 #EDE8E0；插图 26 张由 clip 脚本裁剪，
经 HOOKS 表挂到对应章节。
用法：python _tools/build_1880china_pdf.py
产物：1880China_规则中文翻译（排版版）.pdf（项目根目录）
"""
import html as H
import re
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / '1880China_规则中文翻译.md'
WORK = ROOT / '_work' / '1880_trans'
WORK.mkdir(parents=True, exist_ok=True)
HTML_PATH = WORK / 'typeset.html'
RAW_PDF = WORK / 'typeset_raw.pdf'
OUT_PDF = ROOT / '1880China_规则中文翻译（排版版）.pdf'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
FONT_SERIF_URI = Path('C:/Windows/Fonts/NotoSerifSC-VF.ttf').as_uri()
FONT_SANS_URI = Path('C:/Windows/Fonts/NotoSansSC-VF.ttf').as_uri()
FONT_FOOT = r'C:\Windows\Fonts\simhei.ttf'
CREAM = (0.9294, 0.9098, 0.8784)          # #EDE8E0，与英文原书纸色一致（插图同底色）
INK = (0.10, 0.09, 0.08)
FOOT_GRAY = (0.42, 0.38, 0.32)
FOOT_TEXT = '1880：中国 · 规则中文翻译 v1.1 ｜ 排版版 v1.0'

# 插图挂载钩子：(h2 关键串 或 None, h3 关键串 或 None, [图], 版式)
# 版式：'fig'=栏内竖排；'grid2'=两列网格；'wide'=通栏大图
HOOKS = [
    ('III. 组件', None, ['comp_map', 'comp_tiles', 'comp_cards'], 'fig'),
    ('IV. 游戏准备', None, ['setup_money'], 'fig'),
    ('VIII. 主要公司', '董事长（Director）', ['dir_cert'], 'fig'),
    (None, '建筑许可（Building Permits）', ['permit_card'], 'fig'),
    ('IX. 运营轮次', '运营轮次内的回合顺序', ['or_photo'], 'fig'),
    ('X. 运营轮次中一家公司的行动顺序', '列车（Trains）', ['train_card_a', 'train_card_b', 'train_pic'], 'grid2'),
    ('X. 运营轮次中一家公司的行动顺序', '购买列车（Purchase of Trains）', ['train_stack'], 'fig'),
    ('X. 运营轮次中一家公司的行动顺序', '运行列车（Operating Trains）', ['icr_map'], 'wide'),
    ('X. 运营轮次中一家公司的行动顺序', '计算收入（Calculating Income）', ['operation_map'], 'wide'),
    ('X. 运营轮次中一家公司的行动顺序', '股价表奖励（Bonus from the Share Price Chart）', ['chart_p17'], 'fig'),
    ('X. 运营轮次中一家公司的行动顺序', '西伯利亚大铁路线路奖励（Bonus for the Trans-Siberian Line）', ['transsib'], 'wide'),
    ('XIII. 股价变动', None, ['comp_pricechart', 'comp_incometable'], 'fig'),
    ('板块清单（Tile Manifest）', None, ['manifest'], 'wide'),
    ('升级图（Upgrade Chart）', None, ['upgrade'], 'wide'),
    ('1880 China 游戏阶段', None, ['gamephase'], 'wide'),
]


def fig_img(name):
    return f'<img class="fig" src="art/{name}.png" alt="">'


def hook_html(imgs, layout):
    if layout == 'grid2':
        return '<div class="artgrid">' + ''.join(fig_img(n) for n in imgs) + '</div>'
    if layout == 'wide':
        return ''.join(f'<img class="figwide" src="art/{n}.png" alt="">' for n in imgs)
    return ''.join(fig_img(n) for n in imgs)


# ---------------------------------------------------------------- inline
def inline(s: str) -> str:
    s = H.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'〔([^〕]+)〕', r'<span class="bk">〔\1〕</span>', s)
    s = s.replace('\\*', '＊')
    return s


# ---------------------------------------------------------------- parse
def parse_blocks(lines):
    blocks, i = [], 0
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if re.match(r'^-{3,}$', s):
            i += 1
            continue
        m = re.match(r'^(#{1,6}) (.+)$', s)
        if m:
            blocks.append({'t': 'h', 'lvl': len(m.group(1)), 'text': m.group(2).strip()})
            i += 1
            continue
        if s.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells)
                i += 1
            rows = [r for r in rows if not (r and all(c and set(c) <= set(':-') for c in r))]
            if rows:
                blocks.append({'t': 'table', 'rows': rows, 'ncols': max(len(r) for r in rows)})
            continue
        if s.startswith('>'):
            paras = []
            while i < n and lines[i].strip().startswith('>'):
                paras.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({'t': 'note', 'paras': paras})
            continue
        m = re.match(r'^(\s*)([-*+]|\\\*) (.+)$', lines[i])
        if m:
            items = []
            while i < n:
                m2 = re.match(r'^(\s*)([-*+]|\\\*) (.+)$', lines[i])
                if not m2:
                    break
                items.append((len(m2.group(1)) // 2, m2.group(3).strip()))
                i += 1
            blocks.append({'t': 'ul', 'items': items})
            continue
        m = re.match(r'^(\s*)(\d+)[.、] (.+)$', lines[i])
        if m:
            items = []
            while i < n:
                m2 = re.match(r'^(\s*)(\d+)[.、] (.+)$', lines[i])
                if not m2:
                    break
                items.append(m2.group(3).strip())
                i += 1
            blocks.append({'t': 'ol', 'items': items})
            continue
        blocks.append({'t': 'p', 'text': s})
        i += 1
    return blocks


def para_class(text):
    if text == '**或**':
        return 'or'
    if text.startswith('（见') and text.endswith('）'):
        return 'seeref'
    return ''


def render_list(items):
    out, stack = [], []
    for depth, text in items:
        while len(stack) > depth:
            out.append('</li></ul>')
            stack.pop()
        while len(stack) < depth:
            out.append('<ul>')
            stack.append(1)
            out.append('<li>')
        if stack:
            out.append('</li><li>')
        else:
            out.append('<ul><li>')
            stack.append(1)
        out.append(inline(text))
    while stack:
        out.append('</li></ul>')
        stack.pop()
    return ''.join(out)


def render_table(b):
    rows = b['rows']
    ncols = b['ncols']
    all_short = all(len(c) <= 10 for r in rows[1:] for c in r) if len(rows) > 1 else False
    cls = 'center' if all_short else ''
    out = [f'<table class="{cls}">', '<thead><tr>']
    out += [f'<th>{inline(c)}</th>' for c in rows[0]]
    out.append('</tr></thead><tbody>')
    for r in rows[1:]:
        out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out), ncols


def heading_html(lvl, text, extra=''):
    tag = f'h{min(lvl, 5)}'
    return f'<{tag} class="{extra}">{inline(text)}</{tag}>'


def render_pc_table(rows):
    """私营公司表：每行末尾附加该公司卡牌图（P0–P7 一一对应）。"""
    out = ['<table class="pc">', '<thead><tr>']
    out += [f'<th>{inline(c)}</th>' for c in rows[0]]
    out.append('<th class="cardcell"></th>')
    out.append('</tr></thead><tbody>')
    for r in rows[1:]:
        code = re.sub(r'\*+', '', r[0]).strip() if r else ''
        img = f'<img class="pcard" src="art/pc_{code}.png" alt="">' if re.match(r'^P[0-7]$', code) else ''
        out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r)
                   + f'<td class="cardcell">{img}</td></tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def render(blocks):
    out, seg = [], []
    cur_h2 = ''

    def flush_seg():
        nonlocal seg
        if seg:
            out.append('<div class="cols">' + ''.join(seg) + '</div>')
            seg = []

    def fire_hooks(text, lvl):
        nonlocal seg
        for k2, k3, imgs, layout in HOOKS:
            if k3 is None:
                if lvl == 2 and k2 in text:
                    h = hook_html(imgs, layout)
                    if layout == 'wide':
                        flush_seg()
                        out.append(h)
                    else:
                        seg.append(h)
                    return
            elif k3 in text and (k2 is None or k2 in cur_h2):
                seg.append(hook_html(imgs, layout))
                return

    for b in blocks:
        t = b['t']
        if t == 'h':
            lvl, text = b['lvl'], b['text']
            if lvl == 2:
                flush_seg()
                cls = 'sec'
                if text.startswith(('目录', 'I.', '附录')):
                    cls += ' pagebreak'
                out.append(heading_html(2, text, cls))
                cur_h2 = text
                fire_hooks(text, 2)
                continue
            if lvl == 1:
                seg.append(heading_html(2, text, 'sec'))
                continue
            seg.append(heading_html(lvl, text))
            fire_hooks(text, lvl)
            continue
        if t == 'table':
            rows = b['rows']
            first = re.sub(r'\*+', '', (rows[1][0] or '')).strip() if len(rows) > 1 else ''
            if (rows and any('特殊能力' in c for c in rows[0])
                    and len(rows) >= 9 and re.match(r'^P[0-7]$', first)):
                flush_seg()
                out.append(render_pc_table(rows))
                continue
            html, ncols = render_table(b)
            if ncols >= 3:
                flush_seg()
                out.append(html)
            else:
                seg.append(html)
            continue
        if t == 'note':
            paras = ''.join(f'<p>{inline(p)}</p>' for p in b['paras'] if p)
            seg.append(f'<div class="note">{paras}</div>')
            continue
        if t == 'ul':
            seg.append(render_list(b['items']))
            continue
        if t == 'ol':
            seg.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in b['items']) + '</ol>')
            continue
        text = b['text']
        cls = para_class(text)
        seg.append(f'<p class="{cls}">{inline(text)}</p>' if cls else f'<p>{inline(text)}</p>')

    flush_seg()
    return ''.join(out)


# ---------------------------------------------------------------- 封面
def cover_html(title, meta):
    metas = ''.join(f'<p>{inline(p)}</p>' for p in meta if '致谢' in p)
    return f'''<div class="cover">
<img class="clogo" src="art/cover_logo.png" alt="">
<h1>{inline(title)}</h1>
<img class="cart" src="art/cover_art.png" alt="">
<div class="colo">
<p><b>内容版本</b>：中译 v1.1（2026-09-22，逐段对照英文原书）</p>
<p><b>本排版版</b>：v1.0（2026-10-03）——依英文原书（A4 竖版）版式重排，<b>含原书插图</b>，正文一字未改</p>
<p><b>翻译人</b>：Pig9013 ｜ <b>使用模型</b>：Deepseek-flash ｜ <b>整理日期</b>：2026-09-22</p>
<p><b>底本</b>：英规1880chinaRules.pdf（Lookout GmbH 2022 英文规则书，24 页）</p>
<p><b>姊妹文档</b>：1880China_规则中文翻译.md ｜ 1880China疑惑与答疑.md</p>
{metas}
</div>
</div>'''


def build_css():
    css = '''
@font-face { font-family:"RS"; src:url("__SERIF__"); }
@font-face { font-family:"RH"; src:url("__SANS__"); }
@page { size:210mm 297mm; margin:14mm 15mm 13mm; }
* { box-sizing:border-box; print-color-adjust:exact; -webkit-print-color-adjust:exact; }
html, body { margin:0; padding:0; background:#EDE8E0; }
body { font-family:"RS","Noto Serif SC",serif; font-size:9.4pt; line-height:1.74; color:#201d19; }
p { margin:0 0 1.8mm; }
b { font-weight:700; color:#12100d; }
a { color:#9c3b26; text-decoration:none; }
code { font-family:"RS",serif; background:#E2DACB; border:0.5pt solid #CBBFA8; border-radius:1.5pt; padding:0 0.5mm; font-size:0.93em; color:#5f4c2e; }
.bk { color:#8d7f68; font-size:0.9em; }
.cols { column-count:2; column-gap:7mm; }
h2.sec { font-family:"RH"; font-weight:700; font-size:13.4pt; color:#F3EFE6; background:#1A1815;
  padding:1.2mm 3.5mm; margin:6mm 0 3mm; break-after:avoid; }
h3 { font-family:"RH"; font-weight:700; font-size:10.8pt; color:#1a1712; margin:4.5mm 0 1.8mm;
  padding-bottom:0.8mm; border-bottom:0.8pt solid #1a1712; break-after:avoid; }
h4 { font-family:"RH"; font-weight:700; font-size:9.8pt; color:#2a251d; margin:3.5mm 0 1.4mm; break-after:avoid; }
h5 { font-family:"RH"; font-weight:700; font-size:9.3pt; color:#2a251d; margin:3mm 0 1.2mm; break-after:avoid; }
.or { text-align:center; font-family:"RH"; font-weight:700; margin:1.5mm 0; color:#6b5b3a; }
.seeref { text-align:center; color:#8a7b62; font-size:9pt; margin:1.5mm 0; }
ul { margin:0 0 2mm; padding-left:4mm; list-style:none; }
ul li { position:relative; padding-left:3mm; margin:0 0 1mm; }
ul li::before { content:"·"; position:absolute; left:0; color:#A6322B; font-weight:700; }
ul ul { margin:1mm 0 0; }
ol { margin:0 0 2mm; padding-left:6mm; }
ol li { margin:0 0 1mm; }
li { break-inside:avoid; }
.note { background:#E6DECF; border:0.8pt solid #1A1815; border-left:2.6pt solid #A6322B;
  padding:2.4mm 3mm 1.2mm; margin:2mm 0 2.6mm; font-size:9pt; color:#3a342a; break-inside:avoid; }
.note p:last-child { margin-bottom:0; }
table { width:100%; border-collapse:collapse; font-size:8.5pt; margin:2mm 0 3mm; }
thead { display:table-header-group; }
th { font-family:"RH"; font-weight:700; font-size:8.3pt; background:#DCD2C0; color:#26221b;
  border:0.6pt solid #9c8f76; padding:1.2mm 1.7mm; text-align:left; }
td { border:0.6pt solid #B4A78C; padding:1.1mm 1.7mm; vertical-align:top; }
tr { break-inside:avoid; }
table.center td, table.center th { text-align:center; }
.pagebreak { break-before:page; }
img.fig { width:100%; display:block; margin:1.4mm 0 2.6mm; border:0.8pt solid #23201a;
  border-radius:1pt; break-inside:avoid; }
img.figwide { width:100%; display:block; margin:2mm 0 3mm; border:0.8pt solid #23201a;
  border-radius:1pt; break-inside:avoid; }
.artgrid { display:grid; grid-template-columns:1fr 1fr; gap:2.4mm; margin:1.4mm 0 2.6mm; break-inside:avoid; }
.artgrid img { width:100%; display:block; border:0.8pt solid #23201a; border-radius:1pt; }
table.pc td, table.pc th { vertical-align:middle; }
table.pc .cardcell { width:33mm; padding:0.9mm 1.2mm; text-align:center; }
img.pcard { width:100%; display:block; border:0.6pt solid #23201a; border-radius:1pt; }
.cover { height:266mm; display:flex; flex-direction:column; break-after:page; }
.cover .clogo { width:104mm; margin:2mm auto 5mm; display:block; }
.cover h1 { font-family:"RH"; font-weight:700; font-size:26pt; text-align:center; color:#181510;
  margin:0 0 4mm; letter-spacing:1.5mm; }
.cover .cart { width:100%; display:block; margin:2mm 0 0; }
.cover .colo { margin-top:auto; border:1pt solid #1A1815; background:#E5DDCD; padding:3.6mm 4.6mm; font-size:8.9pt; }
.cover .colo p { margin:0 0 1.1mm; }
'''
    return css.replace('__SERIF__', FONT_SERIF_URI).replace('__SANS__', FONT_SANS_URI)


def main():
    md = SRC.read_text(encoding='utf-8')
    lines = md.splitlines()
    idx = next(i for i, ln in enumerate(lines) if re.match(r'^-{3,}\s*$', ln))
    front, body = lines[:idx], lines[idx + 1:]
    title = next((re.sub(r'^#\s+', '', ln) for ln in front if re.match(r'^#\s+', ln)), '')
    meta = [ln.strip()[1:].strip() for ln in front if ln.strip().startswith('>')]

    blocks = parse_blocks(body)
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>{H.escape(title)}</title><style>{build_css()}</style></head><body>'
            + cover_html(title, meta) + render(blocks) + '</body></html>')
    HTML_PATH.write_text(html, encoding='utf-8')
    print('HTML:', HTML_PATH)

    RAW_PDF.unlink(missing_ok=True)
    r = subprocess.run(
        [EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--no-pdf-header-footer',
         '--user-data-dir=C:/Users/Windows/AppData/Local/Temp/edgepdf',
         f'--print-to-pdf={RAW_PDF}', HTML_PATH.as_uri()],
        capture_output=True, text=True, errors='replace', timeout=300)
    if not RAW_PDF.exists():
        print('Edge 渲染失败 rc=%s\n%s' % (r.returncode, (r.stderr or '')[-800:]))
        sys.exit(1)
    print('原始 PDF:', RAW_PDF, f'({RAW_PDF.stat().st_size / 1024:.0f} KB)')

    doc = fitz.open(RAW_PDF)
    n = len(doc)
    for i, pg in enumerate(doc):
        sh = pg.new_shape()
        sh.draw_rect(pg.rect)
        sh.finish(color=None, fill=CREAM)
        sh.commit(overlay=False)
        if i == 0:
            continue
        y = pg.rect.height - 15
        pg.insert_text(fitz.Point(48, y), FOOT_TEXT, fontname='hei', fontfile=FONT_FOOT,
                       fontsize=6.8, color=FOOT_GRAY)
        num = str(i + 1)
        try:
            w = fitz.get_text_length(num, fontname='helv', fontsize=7.4)
        except Exception:
            w = 8
        pg.insert_text(fitz.Point(pg.rect.width - 48 - w, y), num, fontname='hei',
                       fontfile=FONT_FOOT, fontsize=7.4, color=INK)
    doc.set_metadata({
        'title': '1880：中国 · 规则中文翻译（排版版 v1.0）',
        'author': 'Pig9013（翻译）；Deepseek-flash（模型）',
        'subject': '1880 China（Lookout 2022）规则中文翻译，依英文原书版式重排并嵌入原书插图',
        'keywords': '1880 China, 18xx, 规则, 中文翻译',
    })
    doc.save(OUT_PDF, garbage=3, deflate=True)
    doc.close()
    print('成品 PDF:', OUT_PDF, f'{n} 页')

    d2 = fitz.open(OUT_PDF)
    txt = re.sub(r'\s+', '', ''.join(p.get_text() for p in d2))
    missing = []
    for b in blocks:
        if b['t'] == 'h' and b['lvl'] in (2, 3):
            probe = re.sub(r'[\s*]+', '', re.sub(r'〔[^〕]*〕', '', b['text']))[:10]
            if probe and probe not in txt:
                missing.append(b['text'])
    plain_md = re.sub(r'[\s#>*`|〔〕\\]', '', md)
    print(f'核查：缺标题 {len(missing)} 个；正文保真比 {len(txt) / len(plain_md):.3f}')
    for m in missing:
        print('  缺:', m)


if __name__ == '__main__':
    main()
