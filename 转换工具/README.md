# 论文草稿与 Word 双向转换

这组工具提供两种 Markdown → Word 版式：Nature 主刊 Article 初次投稿版，以及参照 `D:/OneDrive/Operation.docx` 的阅读版。两者都能用同一个 `word_to_md.py` 转回 Markdown，并保留图表、公式与引用。运行入口位于仓库根目录；首次运行会将 Pandoc、Word、PPT 和 XLSX 处理依赖安装到脚本旁的 `.manuscript_deps/`。PPT 图集导图需要本机安装 Microsoft PowerPoint。

## 文件与产物

```text
论文草稿/
├─ 论文草稿.md                 # 默认 Markdown 输入，仍由作者维护
├─ md_to_word.py              # Markdown → Nature Word
├─ md_to_word_operation.py    # Markdown → Operation 阅读版 Word
├─ word_to_md.py              # Word → Markdown 命令入口
├─ manuscript_conversion.py   # 双向转换实现
├─ nature_article.csl         # Word 参考文献的数字编号格式
├─ 画图/总图集.pptx             # 可引用的成品图片图集之一
├─ 转换工具/ppt_figures.py      # 读取图名批注、备注并裁边导图
├─ 转换工具/export_slide.ps1    # 调用本机 PowerPoint 导出指定页
├─ 转换工具/test_roundtrip.py   # 可再生的往返测试
├─ references.bib             # 可选；出现 [@key] 引用时需要
├─ 论文草稿.nature.docx        # 默认 Word 输出
├─ 论文草稿.operation.docx     # 阅读版 Word 输出
├─ 论文草稿.from_word.md       # 默认回转输出，不覆盖原草稿
├─ manuscript_assets/images/  # Word 中的图片回转时导出的原始文件
└─ temp/                     # 所有测试与渲染中间文件
```

默认命令：

```powershell
python md_to_word.py
python md_to_word_operation.py
python word_to_md.py
```

处理其他文件时可指定输入和输出，例如：

```powershell
python md_to_word.py 文章.md --output 文章.nature.docx --bib references.bib
python md_to_word_operation.py 文章.md --output 文章.operation.docx --reference D:/OneDrive/Operation.docx
python word_to_md.py 文章.nature.docx --output 文章.from_word.md
python word_to_md.py 文章.operation.docx --output 文章.operation.from_word.md
```

三个命令都不覆盖输入文件。Word 转回 Markdown 时，图片保存到输出 Markdown 所在目录的 `manuscript_assets/images/`；内容相同的图片复用已有文件，Word 中新增或替换的图片写入新文件。

阅读代码可先看三个命令入口，再看 `manuscript_conversion.py` 的双向主流程；`ppt_figures.py` 只负责 PPT 图名、备注和导图。

## Markdown 写法

### 图片与 PPT 图集

普通图片可用 Markdown 图片语法，也可用 `&&"绝对路径"` 标记图片文件：

```markdown
![图 1：方法概览](&&"C:/Users/15919/Desktop/figures/overview.png")
```

PPT 图集采用一页一图。将引用独立写在一行，双引号内是 PPT 路径，竖线后是该 PPT 中的图名：

```markdown
{{pptfig:"画图/总图集.pptx"|fig-overview}}
{{pptfig:"C:/Users/15919/Desktop/other_figures.pptx"|fig-model}}
```

同一篇 Markdown 可引用多个 PPT。相对路径以这篇 Markdown 所在目录为基准，绝对路径直接使用。每张图在所属 PPT 的一条批注中写 `@@fig-overview` 这样的图名；去掉首尾空白后整条批注必须是 `@@` 加图名。同一 PPT 内图名不得重复，不同 PPT 可使用相同图名。该页备注是 Word 图片下方的图注；其他批注只保存数据来源、服务器路径与绘图代码等追溯信息，不进入正文。未引用的空白草稿页不要求填写图名或备注。被引用页的备注为空时，转换器会提示，并只插入图片。

转换器按图名找到幻灯片，以清晰 PNG 导出并裁掉页面大块留白。生成的 Word 图片保留 PPT 路径和图名标记；未修改的图片转回 Markdown 后仍是原来的 `{{pptfig:"路径"|图名}}`。如果在 Word 里直接调整或替换图集图片，回转时会保存 Word 中的图片为普通图片，并在它上方写入 `pptfig-edited` 来源注释，保留原 PPT 路径和图名；之后要把修改重新纳入图集，需要在 PPT 中更新成品图。

### 表格

普通表格使用 Markdown 管道表格：

```markdown
| 指标 | 方法 A | 方法 B |
|:-----|-------:|-------:|
| 成功率 | 0.81 | 0.84 |
```

合并单元格使用内嵌 HTML 表格。`rowspan` 是跨行数，`colspan` 是跨列数；`caption` 是表题：

```html
<table>
<caption>表 1：实验分组</caption>
<tr><th colspan="2">分组信息</th><th>结果</th></tr>
<tr><td rowspan="2">A</td><td>甲</td><td>0.81</td></tr>
<tr><td>乙</td><td>0.84</td></tr>
</table>
```

XLSX 作为另一种表格输入来源，在 Markdown 中写一条导入指令。`path` 指向工作簿，`sheet` 指向工作表，`range` 是 Excel 单元格区域；省略后两项时分别使用首张工作表和已使用区域。默认将区域首行作为表头，设 `"header":false` 可关闭。

```markdown
<!-- xlsx-table {"path":"C:/Users/15919/Desktop/results.xlsx","sheet":"Sheet1","range":"A1:D8","caption":"表 2：主要结果"} -->
```

XLSX 中的合并关系会进入可编辑的 Word 表格。回转时以 Word 中的实际单元格内容为准：无合并的表格写成管道表格，有合并的表格写成 HTML 表格；不会改写原 XLSX 文件。PDF 表格不在输入范围内。

### 文献引用

文献使用同目录的 `references.bib` 和正文中的 `[@key]`：

```markdown
这一结果与已有研究一致 [@smith2020]。
```

Word 中显示按首次出现顺序编号的上标引用，并生成参考文献列表。引用键附着在 Word 字符样式中，回转后恢复为 `[@key]`。可用 `--bib` 指定其他 `.bib` 文件；Word 中的参考文献列表不反写到 `.bib`。

### 公式

```markdown
行内公式为 $E=mc^2$。

$$
L = L_1 + L_2
$$
```

行内 `$...$` 和块级 `$$...$$` 公式转换为 Word 可编辑公式。多行公式保留明确的换行和对齐点；下括号使用 Word 可伸展的原生公式结构。极长的独立公式才缩小字号，其余公式沿用正文大小。Markdown 中相邻的正文行各自成为 Word 段落，段间留白，正文首行缩进两个汉字宽度。

Nature 版采用 A4、12 磅正文、双倍行距、连续行号和 6 磅段后间距；表格另起一页，表题与表体同页。这些版式依据 [Nature 的格式指南](https://www.nature.com/nature/for-authors/formatting-guide)。Operation 版沿用参考文件的 A4 页面、页边距与标题层级，正文为 10.5 磅、1.5 倍行距和 6 磅段后间距，一级至六级标题均有明确样式。两种版式仅改变 Word 的排版，不改写原稿内容。

## 往返检查

先运行 Word 转 Markdown，再把回转的 Markdown 转成第二份 Word，最后再次转回 Markdown：

```powershell
python md_to_word.py 论文草稿.from_word.md --output second.docx
python word_to_md.py second.docx --output second.md
```

在当前草稿以及覆盖三种表格来源、公式、普通图片、PPT 图集和文献引用的测试稿中，第一次与第二次回转的 Markdown 内容完全一致。PPT 测试还覆盖同名图片来自两个不同 PPT、图注、Word 内改图、缺失图名和重复图名。测试记录见 [执行记录](执行记录.md)。

也可随时运行自动检查：

```powershell
python 转换工具/test_roundtrip.py
```

测试、媒体提取与版面检查产生的临时文件统一放在 `temp/` 中；稳定输出和 Word 回转所引用的图片仍放在文稿所在目录。
