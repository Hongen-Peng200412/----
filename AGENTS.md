# 论文草稿工作约定

本目录的 Markdown↔Word 转换以 [转换工具说明](转换工具/README.md) 为准。新读者和 AI agent 应先阅读该说明，再修改转换脚本、图集引用或 Word 产物。

- `论文草稿.md` 是正文源稿。运行 `python md_to_word.py` 生成 Nature 投稿版 Word，运行 `python md_to_word_operation.py` 生成 Operation 阅读版 Word；运行 `python word_to_md.py` 将 Word 回转为 Markdown。输入、输出和文献库也可按 README 中的命令指定。
- 普通图片、三种表格、`[@key]` 文献引用和 `$...$`/`$$...$$` 公式的写法见 README 的“Markdown 写法”。
- PPT 图集采用一页一图，在 Markdown 中独立成行写 `{{pptfig:"画图/总览图.pptx"|fig-overview}}`。每处引用都写 PPT 路径和图名；相对路径以当前 Markdown 所在目录为基准，因此一篇文章可以引用多个 PPT。
- PPT 中只有内容为 `@@fig-overview` 这类形式的批注用于图名定位；同一篇文章涉及的所有 PPT 中图名必须互不重复，未引用的草稿页可留空。备注只写图注内容，不手写“图 X｜”或 `Fig. X |`；转换器按 Markdown 中插图出现顺序自动生成英文 `Fig. N |` 图注编号，其他批注保留作来源和绘图代码追溯，不进入正文。
- 正文用 `{{figref:fig-overview}}` 按图名引用，转换后显示 `Fig. 1`；面板用 `{{figref:图名|a,b}}` 或 `{{figref:图名|a–c}}`。多图用 `{{figref:图名1,图名2,图名3}}`，连续图号自动显示为 `Figs. 1–3`。调整插图位置后重新转换即可更新全部编号；不要在正文手写图号。
- 修改图集成品图及图注应回到 PPT。若直接在 Word 中改图，回转工具会保留修改后的图片，并记录原 PPT 路径和图名；不会静默恢复旧图。
- 运行和测试产生的临时文件统一放在 `temp/`，不要散放在正文、画图或转换工具目录。
