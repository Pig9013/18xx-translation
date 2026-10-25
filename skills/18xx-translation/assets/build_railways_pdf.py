#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把《Railways_规则中文翻译.md》按英文原书版式重排为中文 PDF（正文一字不改）。

流程：
  1. 解析 md → HTML：双栏杂志式版式（正文分段分栏；旁注盒 / 图注盒 / 公司色彩卡；
     三列以上的宽表通栏独立成块，避免多栏内跨栏的兼容性问题）
  2. Edge 无头模式 print-to-pdf（页面尺寸＝原书 285×214mm 横版）
  3. pymupdf 后处理：整页奶油底色（与原书纸色一致）、页脚（书名/版本 + 页码）、元数据
用法：python _tools/build_railways_pdf.py
产物：Railways_规则中文翻译（排版版）.pdf（项目根目录）
      中间产物：_work/railways_trans/railways_typeset.html、railways_typeset_raw.pdf
"""
import html as H
import re
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'Railways_规则中文翻译.md'
WORK = ROOT / '_work' / 'railways_trans'
WORK.mkdir(parents=True, exist_ok=True)
HTML_PATH = WORK / 'railways_typeset.html'
RAW_PDF = WORK / 'railways_typeset_raw.pdf'
OUT_PDF = ROOT / 'Railways_规则中文翻译（排版版）.pdf'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
FONT_SERIF_URI = Path('C:/Windows/Fonts/NotoSerifSC-VF.ttf').as_uri()
FONT_SANS_URI = Path('C:/Windows/Fonts/NotoSansSC-VF.ttf').as_uri()
FONT_FOOT = r'C:\Windows\Fonts\simhei.ttf'
CREAM = (1.0, 0.9725, 0.9294)          # ≈ #FFF8ED，与英文原书纸色一致（插图裁剪即此底色）
INK = (0.165, 0.141, 0.098)
FOOT_GRAY = (0.42, 0.38, 0.32)
FOOT_TEXT = '失落的阿特拉斯铁路 · 规则中文翻译 v1.2 ｜ 排版版 v1.1'

# 小公司标志色（供公司详情卡片与旁注盒描边；取自组件页实物照片）
COMPANY_COLORS = {
    '适应': '#7A5CA8', '夜行': '#2E2B28', '架桥': '#2E8C86', '宽敞': '#3E8E4E',
    '扩张': '#C75C8E', '郊区': '#DE93B4', '机智': '#B58E5E', '农业': '#35704A',
    '隧道': '#75716B', '东方矿业': '#8C5B3B', '北方港口': '#2B4C7E', '特快': '#A02F3C',
}
COLOR_WORDS = {
    '紫色': '#7A5CA8', '黑色': '#2E2B28', '青绿色': '#2E8C86', '绿色': '#3E8E4E',
    '品红色': '#C75C8E', '粉色': '#DE93B4', '浅褐色': '#B58E5E', '深绿色': '#35704A',
    '灰色': '#75716B', '褐色': '#8C5B3B', '深蓝色': '#2B4C7E', '深红色': '#A02F3C',
}
# 封面色带：6 大公司 + 12 小公司
COVER_STRIPES = ['#C0392B', '#D97B29', '#D9A62E', '#5B8DB8', '#6FA96F', '#8E6FB8'] + list(COMPANY_COLORS.values())

# 插图与徽记（由 _tools/clip_railways_art.py 从英文原书裁剪；HTML 与 art/ 同目录，用相对路径）
COMPANY_FILES = {
    '适应': 'ico_adaptive', '夜行': 'ico_overnight', '架桥': 'ico_bridging', '宽敞': 'ico_spacious',
    '扩张': 'ico_expansive', '郊区': 'ico_suburban', '机智': 'ico_resourceful', '农业': 'ico_agricultural',
    '隧道': 'ico_tunneling', '东方矿业': 'ico_eastern', '北方港口': 'ico_nport', '特快': 'ico_express',
}
COMP_FILES = {
    '小公司公司板': 'comp_minor', '大公司公司板': 'comp_major', '股份证书': 'comp_shares',
    '列车卡': 'comp_trains', '轨道板块': 'comp_tiles', '地图图例': 'comp_legend',
}


def img_tag(name, cls='fig'):
    c = f' class="{cls}"' if cls else ''
    return f'<img{c} src="art/{name}.png" alt="">'


# ---------------------------------------------------------------- inline
def inline(s: str) -> str:
    s = H.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'〔([^〕]+)〕', r'<span class="bk">〔\1〕</span>', s)
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
            rows = [r for r in rows
                    if not (r and all(c and set(c) <= set(':-') for c in r))]
            if rows:
                blocks.append({'t': 'table', 'rows': rows})
            continue
        if s.startswith('>'):
            paras = []
            while i < n and lines[i].strip().startswith('>'):
                paras.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({'t': 'note', 'paras': paras})
            continue
        m = re.match(r'^(\s*)[-*+] (.+)$', lines[i])
        if m:
            items = []
            while i < n:
                m2 = re.match(r'^(\s*)[-*+] (.+)$', lines[i])
                if not m2:
                    break
                items.append((len(m2.group(1)) // 2, m2.group(2).strip()))
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


def is_runhead(text):
    m = re.match(r'^\*\*(.+)\*\*$', text)
    if not m:
        return False
    inner = m.group(1)
    if inner.endswith(('。', '！', '？', '：', '，')):
        return False
    return bool(re.search(r'（[A-Za-z0-9 /／\-–—\'.]+）', inner))


def para_class(text):
    if re.match(r'^〔原书 p\.', text) and text.endswith('〕'):
        return 'pagemark'
    if text == '**或**':
        return 'or'
    if text.startswith('（见') and text.endswith('）'):
        return 'seeref'
    if re.match(r'^〔.+〕$', text):
        return 'caption'
    if is_runhead(text):
        return 'runhead'
    return ''


# ---------------------------------------------------------------- render
def render_list(items):
    """嵌套项目符号列表"""
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
    ncols = max(len(r) for r in rows)
    all_short = all(len(c) <= 10 for r in rows[1:] for c in r) if len(rows) > 1 else False
    cls = 'center ' if all_short else ''
    out = [f'<table class="{cls.strip()}">', '<thead><tr>']
    out += [f'<th>{inline(c)}</th>' for c in rows[0]]
    out.append('</tr></thead><tbody>')
    for r in rows[1:]:
        out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out), ncols


def heading_html(lvl, text, extra='', img=''):
    tag = f'h{min(lvl, 5)}'
    return f'<{tag} class="{extra}">{img}{inline(text)}</{tag}>'


def render(blocks):
    """把块列表渲染为 HTML 页面体（封面之外的全部正文）"""
    out, seg, stack = [], [], []      # stack: (kind, trig_lvl)
    cur_h2, cur_h1 = '', ''

    def flush_seg():
        nonlocal seg
        if seg:
            out.append('<div class="cols">' + ''.join(seg) + '</div>')
            seg = []

    def close_containers(to_lvl=None):
        while stack and (to_lvl is None or stack[-1][1] >= to_lvl):
            stack.pop()
            seg.append('</div>')

    skip = False
    for i, b in enumerate(blocks):
        if skip:
            skip = False
            continue
        t = b['t']
        if t == 'h':
            lvl, text = b['lvl'], b['text']
            # 标题紧跟宽表：两者一起通栏，避免标题与表格在分栏中被拆散
            if (lvl >= 3 and i + 1 < len(blocks)
                    and blocks[i + 1]['t'] == 'table' and blocks[i + 1].get('ncols', 0) >= 3):
                close_containers()
                flush_seg()
                extra = ''
                if lvl == 3 and '组件图解' in cur_h2:   # 组件图解的解剖图（如「地图图例」）
                    for k, f in COMP_FILES.items():
                        if k in text:
                            extra = img_tag(f)
                            break
                out.append('<div class="fullhead">' + heading_html(lvl, text) + extra + '</div>')
                out.append(render_table(blocks[i + 1])[0])
                skip = True
                continue
            if lvl == 1:
                close_containers()
                flush_seg()
                cls = 'sec pagebreak' if text.startswith('附录') else 'sec'
                seg.append(heading_html(2, text, cls))
                cur_h1 = text
                flush_seg()               # 附录大标题通栏独立
                continue
            if lvl == 2:
                close_containers()
                flush_seg()
                cls = 'sec'
                if text.startswith(('一、', '目录')):
                    cls += ' pagebreak'
                out.append(heading_html(2, text, cls))
                cur_h2, cur_h1 = text, text
                continue
            # h3+
            close_containers(lvl)
            kind, acc = None, ''
            if '旁注' in text:
                kind = 'sidebar'
                for name, col in COMPANY_COLORS.items():
                    if name in text:
                        acc = col
                        break
            elif text.startswith('图') and '说明' in text:
                kind = 'figbox'
            elif lvl == 3 and '公司详情' in cur_h2:
                kind = 'ccard'
                m = re.search(r'〔([^，〕]+)，', text)
                acc = COLOR_WORDS.get(m.group(1), '#2a2620') if m else '#2a2620'
            if kind:
                style = f' style="--acc:{acc}"' if acc else ''
                seg.append(f'<div class="{kind}"{style}>')
                stack.append((kind, lvl))
                if kind == 'figbox':          # 图 N 说明：说明文字上方嵌入原书插图
                    m = re.match(r'^图\s*(\d)\s*说明', text)
                    if m:
                        seg.append(img_tag('fig' + m.group(1)))
            imgtag = ''
            if kind == 'ccard':               # 公司详情卡片：标题内嵌公司徽记
                for k, f in COMPANY_FILES.items():
                    if k + '公司' in text:
                        imgtag = img_tag(f, 'ico')
                        break
            elif kind == 'sidebar':           # 公司旁注：标题内嵌徽记（联合旁注可有两枚）
                imgtag = ''.join(img_tag(f, 'icrow') for k, f in COMPANY_FILES.items() if k in text)
            seg.append(heading_html(lvl, text, img=imgtag))
            if kind is None and lvl == 3 and '组件图解' in cur_h2:
                for k, f in COMP_FILES.items():   # 组件图解：标题下嵌入对应解剖图
                    if k in text:
                        seg.append(img_tag(f))
                        break
            continue
        if t == 'table':
            html, ncols = render_table(b)
            if ncols >= 3:               # 宽表：通栏独立成块（切断分栏段）
                close_containers()
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
            if any('6 家大公司' in it for _, it in b['items']):
                seg.append(img_tag('majors_strip', 'strip'))   # 六家大公司徽记条
            continue
        if t == 'ol':
            lis = ''.join(f'<li>{inline(x)}</li>' for x in b['items'])
            seg.append(f'<ol>{lis}</ol>')
            continue
        # 段落
        text = b['text']
        if '两幅整页示意图' in text:          # 桌面布置：文字说明后接两幅整页示意图
            seg.append(f'<p>{inline(text)}</p>')
            flush_seg()
            out.append('<div class="artrow">' + img_tag('setup_a', '') + img_tag('setup_b', '') + '</div>')
            continue
        cls = para_class(text)
        if cls == 'runhead':
            seg.append(f'<p class="runhead">{inline(text[2:-2])}</p>')
        elif cls:
            seg.append(f'<p class="{cls}">{inline(text)}</p>')
        else:
            seg.append(f'<p>{inline(text)}</p>')

    close_containers()
    flush_seg()
    return ''.join(out)


# ---------------------------------------------------------------- 封面
def cover_html(front_title, front_sub, front_meta):
    meta = ''.join(f'<p>{inline(p)}</p>' for p in front_meta if '致谢' in p)
    stripes = ''.join(f'<i style="background:{c}"></i>' for c in COVER_STRIPES)
    return f'''<div class="cover">
<div class="top">ASTERISK GAMES · 2024 · SECOND EDITION</div>
<h1>失落的阿特拉斯铁路</h1>
<div class="sub">{inline(front_sub)}</div>
<div class="stripes">{stripes}</div>
<div class="colo">
<p><b>内容版本</b>：中译 v1.2（2026-09-29，逐段对照英文原书）</p>
<p><b>本排版版</b>：v1.1（2026-10-03）——依英文原书版式重排，<b>含原书插图与公司徽记</b>，正文一字未改</p>
<p><b>排版版沿革</b>：v1.0（2026-10-03）原版式重排 → v1.1（2026-10-03）嵌入原书插图（图 1–9、组件图解、桌面布置）与全部公司徽记</p>
<p><b>翻译人</b>：Pig9013 ｜ <b>使用模型</b>：Deepseek-flash ｜ <b>整理日期</b>：2026-09-29</p>
<p><b>底本</b>：Railways-EN-2nd-Rulebook.pdf（Asterisk Games 2024 年第 2 版，26 页＝印刷页 1–25）</p>
<p><b>姊妹文档</b>：Railways_单人模式规则中文翻译.md ｜ Railways_疑惑与答疑.md</p>
{meta}
</div>
</div>'''


def build_css():
    css = '''
@font-face { font-family:"RS"; src:url("__SERIF__"); }
@font-face { font-family:"RH"; src:url("__SANS__"); }
@page { size:285mm 214mm; margin:15mm 17mm 14mm; }
* { box-sizing:border-box; print-color-adjust:exact; -webkit-print-color-adjust:exact; }
html, body { margin:0; padding:0; background:#FFF8ED; }
body { font-family:"RS","Noto Serif SC",serif; font-size:9.9pt; line-height:1.74; color:#23201a; }
p { margin:0 0 1.8mm; }
b { font-weight:700; color:#14110d; }
a { color:#9c3b26; text-decoration:none; }
code { font-family:"RS",serif; background:#F0E7D2; border:0.5pt solid #DCCEAC; border-radius:1.5pt; padding:0 0.5mm; font-size:0.93em; color:#6f5a33; }
.bk { color:#94856a; font-size:0.9em; }
.cols { column-count:2; column-gap:10mm; }
h2.sec { font-family:"RH",sans-serif; font-weight:700; font-size:15.5pt; color:#1a1712;
  margin:6mm 0 3mm; padding-bottom:1.2mm; border-bottom:1.6pt solid #1a1712; }
h2.sec .bk { font-weight:400; font-size:8.6pt; }
h3 { font-family:"RH"; font-weight:700; font-size:11.6pt; color:#1a1712; margin:5mm 0 2mm; break-after:avoid; }
h4 { font-family:"RH"; font-weight:700; font-size:10.1pt; color:#2a251d; margin:4mm 0 1.6mm; break-after:avoid; }
h5 { font-family:"RH"; font-weight:700; font-size:9.6pt; color:#2a251d; margin:3mm 0 1.4mm; break-after:avoid; }
.runhead { font-family:"RH"; font-weight:700; font-size:9.9pt; color:#1a1712; margin:3mm 0 1.2mm; break-after:avoid; }
.runhead::before { content:"■ "; color:#A63B2A; font-size:7pt; vertical-align:2px; }
.or { text-align:center; font-family:"RH"; font-weight:700; margin:1.5mm 0; color:#6b5b3a; }
.seeref { text-align:center; color:#8a7b62; font-size:9pt; margin:1.5mm 0; }
.pagemark { text-align:center; color:#a3937a; font-size:8.2pt; letter-spacing:1px; margin:3mm 0 2mm; }
.pagemark::before { content:"—— "; color:#cfc3ab; }
.pagemark::after { content:" ——"; color:#cfc3ab; }
.caption { text-align:center; color:#7c6f58; font-size:8.8pt; margin:1.5mm 0; }
img.fig { width:100%; display:block; margin:1.2mm 0 2.2mm; border:0.7pt solid #D9CDB4; border-radius:1pt; }
img.ico { height:4.6mm; width:auto; vertical-align:-1.1mm; margin-right:1.6mm; }
img.icrow { height:4.6mm; width:auto; vertical-align:-1.1mm; margin-right:1.2mm; }
img.strip { width:100%; display:block; margin:0.5mm 0 2.5mm; border:0.7pt solid #D9CDB4; border-radius:1pt; }
.artrow { display:flex; gap:7mm; margin:1mm 0 3mm; break-inside:avoid; }
.artrow img { width:49.2%; border:0.7pt solid #D9CDB4; border-radius:1pt; }
ul { margin:0 0 2mm; padding-left:4mm; list-style:none; }
ul li { position:relative; padding-left:3mm; margin:0 0 1mm; }
ul li::before { content:"·"; position:absolute; left:0; color:#A63B2A; font-weight:700; }
ul ul { margin:1mm 0 0; }
ol { margin:0 0 2mm; padding-left:6mm; }
ol li { margin:0 0 1mm; }
li { break-inside:avoid; }
.note { background:#F4EEDE; border-left:2.6pt solid #C6B58C; padding:2.6mm 3mm 1.4mm; margin:2mm 0 2.5mm;
  font-size:9.4pt; color:#3c362b; break-inside:avoid; }
.note p:last-child { margin-bottom:0; }
.sidebar { background:#F4EBD8; border:1pt solid #2a2620; border-top:3pt solid var(--acc,#2a2620);
  padding:3mm 3.2mm 1.6mm; margin:2.5mm 0 3mm; font-size:9.4pt; break-inside:avoid; }
.sidebar h4, .sidebar h5 { margin-top:0; text-align:center; }
.figbox { border-top:0.8pt solid #B9AC8F; border-bottom:0.8pt solid #B9AC8F; padding:2.2mm 0 1.4mm;
  margin:2.5mm 0; font-size:9.3pt; color:#4a4237; break-inside:avoid; }
.figbox h4, .figbox h3 { margin-top:0; }
.ccard { border-left:3.6pt solid var(--acc,#2a2620); background:#F7F1E3; padding:2.4mm 3mm 1mm;
  margin:2.2mm 0; break-inside:avoid; }
.ccard h3 { margin-top:0; color:var(--acc,#1a1712); font-size:10.6pt; }
table { width:100%; border-collapse:collapse; font-size:8.8pt; margin:2mm 0 3mm; }
thead { display:table-header-group; }
th { font-family:"RH"; font-weight:700; font-size:8.6pt; background:#EBE1CB; color:#26221b;
  border:0.6pt solid #B9AC8F; padding:1.3mm 1.8mm; text-align:left; }
td { border:0.6pt solid #C9BCA0; padding:1.2mm 1.8mm; vertical-align:top; }
tr { break-inside:avoid; }
table.center td, table.center th { text-align:center; }
.pagebreak { break-before:page; }
.fullhead { margin:6mm 0 0; }
.fullhead h3, .fullhead h4, .fullhead h5 { margin:0 0 1.6mm; }
.cover { height:185mm; display:flex; flex-direction:column; break-after:page; }
.cover .top { font-family:"RH"; letter-spacing:3px; color:#8a7b62; font-size:9pt; }
.cover h1 { font-family:"RH"; font-weight:700; font-size:38pt; margin:7mm 0 3mm;
  letter-spacing:4mm; color:#181510; line-height:1.2; }
.cover .sub { font-family:"RH"; font-size:13pt; color:#5c5242; }
.cover .stripes { display:flex; gap:1.6mm; margin:10mm 0; }
.cover .stripes i { flex:1; height:2.6mm; border-radius:1.3mm; display:block; }
.cover .colo { margin-top:auto; border:1pt solid #2a2620; background:#F2E8D3; padding:4mm 5mm; font-size:9.2pt; }
.cover .colo p { margin:0 0 1.2mm; }
'''
    return css.replace('__SERIF__', FONT_SERIF_URI).replace('__SANS__', FONT_SANS_URI)


# ---------------------------------------------------------------- 构建
def main():
    md = SRC.read_text(encoding='utf-8')
    lines = md.splitlines()

    # 封面区（第一个 --- 之前）：标题 / 副标题 / 元信息引文
    idx = next(i for i, ln in enumerate(lines) if re.match(r'^-{3,}\s*$', ln))
    front = lines[:idx]
    body = lines[idx + 1:]
    title = next((re.sub(r'^#\s+', '', ln) for ln in front if re.match(r'^#\s+', ln)), '')
    sub = next((re.sub(r'^##\s+', '', ln) for ln in front if re.match(r'^##\s+', ln)), '')
    meta = [ln.strip()[1:].strip() for ln in front if ln.strip().startswith('>')]

    blocks = parse_blocks(body)
    for b in blocks:
        if b['t'] == 'table':
            b['ncols'] = max(len(r) for r in b['rows'])
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>{H.escape(title)}</title><style>{build_css()}</style></head><body>'
            + cover_html(title, sub, meta) + render(blocks) + '</body></html>')
    HTML_PATH.write_text(html, encoding='utf-8')
    print('HTML:', HTML_PATH)

    # Edge 无头渲染
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

    # pymupdf 后处理：整页底色 + 页脚 + 元数据
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
                       fontsize=7.2, color=FOOT_GRAY)
        num = str(i + 1)
        try:
            w = fitz.get_text_length(num, fontname='helv', fontsize=7.6)
        except Exception:
            w = 8
        pg.insert_text(fitz.Point(pg.rect.width - 48 - w, y), num, fontname='hei',
                       fontfile=FONT_FOOT, fontsize=7.6, color=INK)
    doc.set_metadata({
        'title': '失落的阿特拉斯铁路 · 规则中文翻译（排版版 v1.0）',
        'author': 'Pig9013（翻译）；Deepseek-flash（模型）',
        'subject': 'Railways of the Lost Atlas (2nd Edition) 规则中文翻译，依英文原书版式重排',
        'keywords': 'Railways of the Lost Atlas, 18xx, 规则, 中文翻译',
    })
    doc.save(OUT_PDF, garbage=3, deflate=True)
    doc.close()
    print('成品 PDF:', OUT_PDF, f'{n} 页')

    # 完整性核查：全部一二级标题都出现在 PDF 文本层中
    d2 = fitz.open(OUT_PDF)
    txt = re.sub(r'\s+', '', ''.join(p.get_text() for p in d2))
    missing = []
    for b in blocks:
        if b['t'] == 'h' and b['lvl'] in (1, 2):
            probe = re.sub(r'\s+', '', re.sub(r'〔[^〕]*〕', '', b['text']))[:10]
            if probe and probe not in txt:
                missing.append(b['text'])
    plain_md = re.sub(r'[\s#>*`|〔〕]', '', md)
    print(f'核查：缺标题 {len(missing)} 个；正文保真比 {len(txt) / len(plain_md):.3f}')
    for m in missing:
        print('  缺:', m)


if __name__ == '__main__':
    main()
