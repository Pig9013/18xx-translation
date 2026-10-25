# 规则书中译 → 原版式排版版 PDF（工作流细则）

> **2026-10-25 归属**：本手册是 skill **`18xx-translation`** 的操作手册（18xx 作品原版式排版）。兵棋规则书排版用 skill `wargame-rulebook-layout`（GBII Ds 版，Letter 竖版双栏）；2026-10 之前的 SCS/TCS/GTS 旧批次模板只作历史参考，**新兵棋书不要从这里起手**。
>
> 2026-10-03 定稿，**Railways（失落的阿特拉斯铁路 2nd Ed.）样板**。
> 样板脚本：`D:\兵棋\18xx\_tools\build_railways_pdf.py`（构建）、`clip_railways_art.py`（插图裁剪）；
> 成品：`Railways_规则中文翻译（排版版）.pdf`（44 页，排版版 v1.1；原书 285×214mm 横版 1:1 复刻）。
> 做新作品前：把两个脚本 fork 成 `<作品>` 版本，本文件当操作手册对照执行。
>
> **2026-10-03 增补（SCS/TCS 批次）**：信纸竖版三栏的配置驱动模板＝`D:\兵棋\SCS大全\_tools\_legacy\build_scs_pdf.py`（BOOKS 字典，SCS 全系列 + TMEE 通用）与 `D:\兵棋\TCS\_tools\_legacy\build_gd42_pdf.py`（TCS fork）；裁图 `_legacy\clip_scs_art.py`（含旋转参数）。**§9 部分横幅与侧边色签**（合订本专用，TMEE 样板）。

---

## 0. 两步交付（用户 2026-10-03 明确为标准流程）

1. **`<作品>_规则中文翻译.md`**——逐段对照英文原规的全篇中译（正文不缩写、不扩写、不杜撰；术语裁决、底本勘误、核对记录进附录 A/B/C）。**这是唯一内容源。**
2. **`<作品>_规则中文翻译（排版版）.pdf`**——以 md 为唯一内容源（**正文一字不改**），按**英文原书版式**排成印刷级 PDF，并**按对应位置嵌入原书插图与公司徽记**。

## 1. 管线总览

```
md ──解析──▶ HTML+CSS（仿原书版式）
   ──Edge 无头 --print-to-pdf──▶ 原始 PDF
   ──pymupdf 后处理（整页纸色/页脚/页码/元数据）──▶ 成品 PDF
   ──完整性核查（标题零缺失 + 字符保真比）──▶ 交付
```

本机（Windows）**没有** weasyprint / reportlab / wkhtmltopdf / pandoc / LaTeX——**Edge 无头是唯一高保真路径**。
Edge：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`，参数
`--headless=new --disable-gpu --no-first-run --no-pdf-header-footer --print-to-pdf=...`；
**经 python subprocess 调用**（git-bash 直传中文路径有编码风险）；读取输出用 `text=True, errors='replace'`（stderr 非 UTF-8）。

## 2. 开工前：冒烟测试（必做，半小时内）

拿一个最小 HTML 把渲染链四件事各验一次，**全过了再动真格**：

1. `@page { size: <原书开本> }` 是否精确生效（Railways 实测输出 285.1×214.1mm，原书 285.0×214.0）；
2. 中文字体：`C:/Windows/Fonts/NotoSerifSC-VF.ttf`、`NotoSansSC-VF.ttf`（可变字重，Edge 正常加载；@font-face 的 file:// 路径用 `Path.as_uri()` 生成）；
3. 整页底色（见 §5——Chromium 不会自动把底色画进页边距）；
4. 中文页脚/页码盖章（见 §5）。

## 3. md → HTML 解析（本文件专用，不引 markdown 库）

按 md 的实际构造写行级解析器（标题 h1–h5 / `|` 表格 / `>` 引用 / 列表（含嵌套）/ 加粗斜体行内代码 / `〔…〕` 括注），再按**结构化钩子**映射成仿原书版式：

| md 构造 | HTML 钩子 | 版式 |
|:--|:--|:--|
| `#### 图 N 说明` | `figbox` | 图注框：**插图（顶部）＋ 标题 ＋ 说明文**，上下细线 |
| `#### 旁注：X公司` | `sidebar` | 旁注盒：**公司色顶边**（`--acc` 变量）＋ **标题内嵌公司徽记**；联合旁注（如「东方矿业与北方港口」）嵌两枚 |
| `### X公司（…）〔颜色…〕`（公司详情节） | `ccard` | 色卡：左粗边=公司色，**标题内嵌徽记** |
| `> **注**：` | `note` | 注框：浅底＋左粗线 |
| 3 列及以上宽表 | 通栏块 | **结构化拆成通栏独立块**（把该表前后的内容各起一个 `.cols` 分栏段）——多栏内不要依赖 `column-span`，兼容性差 |
| 标题紧跟宽表 | 两件一起通栏 | 避免标题与表在分栏中被拆散（注意：此分支要单独写插图钩子，容易漏——地图图例就漏过一次） |
| 表格 | `thead` ＋ `display: table-header-group` | **跨页自动重复表头** |

其它版式要点：正文双栏（每个 `##` 节一个 `.cols` 容器，`column-count:2`）；h2 章节头通栏＋下缘粗线；旁注盒／图注盒／色卡／行／注框一律 `break-inside: avoid`；三类盒的标题 `break-after: avoid`。

**易漏钩子清单**（Railways 实际踩过）：
- 走「标题＋宽表通栏」分支时忘了嵌图（`地图图例` 漏图）；
- 公司徽记的匹配键要用「公司名前两字」（适应/夜行/架桥/…），旁注标题里可能一次命中两家；
- 组件解剖图的嵌图钩子要加**小节限定**（`cur_h2` 含「组件图解」），否则「轨道板块／股份证书」这类标题在别的节再次出现会误嵌。

## 4. 插图裁剪（`clip_<作品>_art.py`）

**前提认知：原书的图不是独立文件。** 排版软件把插图导出成了几百张小碎片位图互相叠放（一页可达 300–500 张），`extract_image` 出来的只是碎片——**唯一可靠方法是按坐标区域整页高分渲染再裁**。

```python
pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=fitz.Rect(x0, y0, x1, y1))
im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
# 自动裁边：以角落像素为底色，差异蒙版阈值 16，getbbox 收紧，再留 8px（图标 1–2px）白边
bg = im.getpixel((2, 2))
mask = ImageChops.difference(im, Image.new('RGB', im.size, bg)).convert('L').point(lambda p: 255 if p > 16 else 0)
im = im.crop(mask.getbbox() 外扩 pad)
```

**找坐标的三种锚**：

1. **图注文字**：`search_for('Diagram N')` → 原书图注在插图**下方**（图表编号小字）；每图通常命中 2 处（正文交叉引用 + 真图注），真图注与图同栏；
2. **碎片聚类**：`get_image_info(xrefs=True)` 逐图取 bbox，排除整页背景图（大图），按间隙 24pt 聚类 → 候选框（注意：部分碎片的 transform 异常，会出现负坐标的假框，需目视排除）；
3. **网格叠图**：把 50pt 网格直接画到页图上渲染成图，肉眼读坐标——最可靠，定稿坐标前建议都过一遍。

**小图标（公司徽记等矢量图）**：用**文字锚点**——`search_for('Adaptive Company')` 拿到名称行位置，徽记在该行**上方约 28pt**、左对齐同栏；矢量内容用 `zoom=8`（576dpi）渲染，成品 ~200px 方，嵌入后任意放大都清晰。

**逐张过目 QC——边界三坑（都是真实踩过的）**：

| 坑 | 案例 | 对策 |
|:--|:--|:--|
| **邻栏正文条带** | 图8 左缘、图9 右缘混入旁边正文栏的文字尾巴 | 先 `search_for` 量出邻栏文字的边界 x（如 p19 正文栏起点 x=288.2），裁剪框收在边界内侧 4–8pt |
| **原书页码** | 地图图例图右下带进了原书的「5」 | 先搜页码位置（如 (750.7,563.5)），右/下边界收在页码内侧 |
| **页头装饰** | 图7 顶部带进页头图标/装饰线 | 对比渲染图标位置，上边界下移 |

另外两条经验：**完整页示意图**（桌面布置等）直接整页裁（留页边距内侧一点），比抠图稳；**插图与排版版纸色同源**——所有页面底色用采样原书纸色（Railways＝#FFF8ED），插图带 0.7pt 细边框后与页面无缝。

**质检拼图**：裁完后把所有成品拼成 1–2 张带标签的联系表过目一遍（`--sheet`），比逐个打开快得多；发现问题的逐个调坐标重裁。

## 5. pymupdf 后处理

```python
CREAM = (1.0, 0.9725, 0.9294)   # 采样原书纸色 #FFF8ED
for i, pg in enumerate(doc):
    sh = pg.new_shape(); sh.draw_rect(pg.rect); sh.finish(color=None, fill=CREAM)
    sh.commit(overlay=False)     # 垫底：Chromium 不把背景画进 @page 页边距
    if i == 0: continue          # 封面不盖章
    y = pg.rect.height - 15
    pg.insert_text((48, y), FOOT_TEXT, fontname='hei',
                   fontfile=r'C:\Windows\Fonts\NotoSansSC-VF.ttf',   # 见下方字体坑
                   fontsize=7.2, color=(0.42,0.38,0.32))         # 页脚：书名·版本
    pg.insert_text((pg.rect.width-48-w, y), str(i+1), ...)       # 页码（右对齐，w 用 get_text_length 估）
doc.set_metadata({'title': ..., 'author': 'Pig9013（翻译）；Deepseek-flash（模型）', ...})
doc.save(OUT, garbage=3, deflate=True)
```

要点：命令行 `--print-to-pdf` **没有页眉页脚模板**，页码/页脚只能后处理盖；中文页脚用 `insert_text(fontfile=...)` 直接带字体文件，无需预注册。

**盖章字体坑（2026-10-03，实际踩过）**：`simhei.ttf` **没有 © 字形**——版权页脚会渲染成"□2014 …"（一整批 6 本书中招）。页眉/页脚/色签盖章一律用 `C:\Windows\Fonts\NotoSansSC-VF.ttf`（含 ©、·、｜ 等符号；`fitz.Font(fontfile=...).has_glyph(0xA9)` 可先自测）。

## 6. 完整性核查（构建脚本自带，必看两条）

1. **全部一二级标题出现在 PDF 文本层**（用 `page.get_text()` 归一化后逐标题查）——缺一个都要查原因；
2. **字符保真比** = PDF 提取字符数 ÷ md 去标记字符数，应 ≈ 1.0x（Railways 实测 1.04–1.05，多出的部分是页脚与封面元信息；**明显低于 1.0 说明丢内容**）。

## 7. 版本与快照

- **双轨版本**：内容版（中译 vX.Y）与排版版（vX.Y）各自记录；PDF 封面写明两份版本＋**排版版沿革**（如 v1.0 原版式重排 → v1.1 嵌入原书插图与公司徽记）；页脚也带「排版版 vX.Y」。
- **排版版每次改动都升版本**；改了 md 就要重生成排版版并同步升版沿革。
- 快照：`_tools/_snapshot/YYYYMMDD/` 里放两个脚本（`build_*_pdf.py`、`clip_*_art.py`）＋成品 PDF。

## 8. 「对应位置」插图规则（速查）

| 原书元素 | 嵌入位置 |
|:--|:--|
| 图 1、2… 编号插图 | md 里对应的「图 N 说明」框内（说明文字上方） |
| 组件解剖图 | 「组件图解」各小节标题下（节限定钩子） |
| 小公司徽记 | 公司详情卡片标题内 ＋ 各家旁注盒标题内 |
| 大公司徽记 | 「组件」条目下（徽记条） |
| 桌面布置等整页示意图 | 对应小节（flex 双图并排） |

**边界情况**：原书图形自带的英文小标签（徽记条上方的说明行、桌布图内的区域标签）属于图形组成部分，**保留不动**（与「不剔除英文括注」一致）；如用户要求纯中文化再另行处理。

---

## 9. 部分横幅与侧边色签（大部头 / 合订本专用；2026-10-03 TMEE 样板，用户明确表扬）

> **场景**：一本书含两个及以上"部分"——典型是**基础规则 + 扩展规则合订本**（TMEE 样板），或规则书＋剧本书。查规的人需要"翻两下就到位"。两层做法：**部分首页整幅横幅**（颜色区分）＋**该部分每一页右缘竖直色签**（拇指索引）。

### 9.1 部分横幅（HTML/CSS）

```css
h2.part { font-family:"RH"; font-weight:900; font-size:16.5pt; color:#fff; background:#231f20;
  padding:3.2mm 2mm 3.6mm; margin:3mm 0 4mm; text-align:center; letter-spacing:1.4mm; break-after:avoid; }
h2.part.accent { background:#8c2f1b; }   /* 后一部（扩展）用书内强调色，与第一部拉开 */
```

- 部分标题（md 里的 lvl1 `# 第一部分…`／`# 第二部分…`）单独判定 → `part` 类 **＋ pagebreak 独立成页**（成为"部分扉页"，扉页上接该部「出版信息」）；后续 `##` 节照常。
- **配色约定**：第一部分＝黑（#fafafa 反白，与封面横带同源）；**第二部分/扩展＝书内强调色**（TMEE 用暗红 #8c2f1b）。用户原话："扩展规则那一页醒目一点，这样找扩展规则容易一些。"
- 解析器加两组配置：`parts`（黑横幅）与 `part_accent`（强调色横幅）——lvl1 标题命中关键词即套类，**对单部书零影响**（不配置就不触发）。

### 9.2 侧边色签（pymupdf 后处理，拇指索引）

在**页边距内**（本例右缘 11mm＝31.2pt）画一条竖直色签：宽 ~16pt、高 ~66pt、垂直居中；色与横幅同源、白字竖排（**逐字 `insert_text`**，回避文字旋转的兼容问题）。

```python
pages_text = [p.get_text() for p in doc]          # 每部分页范围：动态按文本探测，不写死页码
def find(key, start=0):
    for k in range(start, len(pages_text)):
        if key and key in pages_text[k]: return k
marks = [  # 顺序＝书内顺序；用【完整标题】探测，避免命中卷首"翻译说明"里的提及
    ('第一部分：基础规则', '第二部分：扩展规则', '基础规则', (0.137, 0.122, 0.125)),
    ('第二部分：扩展规则', 'SCS/TME 专业名词对应库', '扩展规则', (0.549, 0.184, 0.106)),
]
for i, pg in enumerate(doc):
    for s, e, label, col in marks:               # e=None 表示直到书末
        if s is None or i < s or (e is not None and i >= e): continue
        x1 = pg.rect.width - 14; x0 = x1 - 16
        y0 = (pg.rect.height - 66) / 2
        sh = pg.new_shape(); sh.draw_rect(fitz.Rect(x0, y0, x1, y0 + 66))
        sh.finish(color=None, fill=col); sh.commit()
        for k, ch in enumerate(label):           # 竖排逐字，9pt、行距 12.6pt
            pg.insert_text(fitz.Point(x0 + 3.4, y0 + 15 + k * 12.6), ch,
                           fontname='hei', fontfile=FONT_HEI, fontsize=9, color=(1, 1, 1))
        break
```

三条纪律：① 签只画在**页边距内**（先量 `@page` margin，再定 x）——绝不压正文；② 尾部共享附录（术语库等）**不挂签**，签只标"内容部"；③ 重排后页码会漂移——范围**每次动态探测**（探测键＝部分标题的完整文本，如 `第二部分：扩展规则`）。

### 9.3 合订本（基础＋扩展合并）的配套体例

TMEE 样板（`D:\兵棋\SCS大全\_tools\_legacy\merge_tmee.py` 生成合并 md → `_legacy\build_scs_pdf.py` 排版）：

1. 合并 md ＝ 卷首「**翻译说明**」（翻译人／标准／底本／勘误沿革）＋ `# 第一部分…` ＋ `# 第二部分…` ＋ 共享附录（术语库）；
2. 各部的原封面块（The Gamers／版权／设计名单）整理为每部开头的「**出版信息**」小节——**不重复**（基础规则的测试名单等只出现一次）；
3. 扩展部分若只有纯文本抽取稿，合并时做**版式性结构整理**：`N.N 标题`→`##`；`格/单位`、`回合/区域` 列表→md 表；`•`→列表；整理后**逐字符校验**（去空白后字符多重集比对——只允许表头/项目符号等版式字符有差），防"整理"时丢内容；
4. 合并时**顺手复核**：本次即查出 CRT 行列错位、增援表错行、整段漏译等实错——合并是复核的好时机；
5. 排版版完整性核查照旧（缺标题 0、保真比 ≈1.0x）。
