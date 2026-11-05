# 复合物层面的端到端top-k成功率

本入口沿用作者确认的四面板模板第一页：a为全配体检出与身份匹配，b为合格小分子检出与身份匹配，c、d分别为CA2和沉积受体条件下的小分子完整构象重建。纵轴保留30%起点；只对末端文字标签避让，不改变曲线或点的纵坐标。

先读本说明及所属[计算追溯](../图表追溯.md)，再读plot.py中的颜色和双语图注、标签避让、main绘图过程。PPT运输复用[e2e-top5-revision/build_pptx.py](../e2e-top5-revision/build_pptx.py)，只转换SVG几何和文字；不复制该目录的科学统计。

唯一科学输入为`e2e/output/find-build-shared/explicit_emdb_level/topk_data.json`。full为179个PDB、2,502个实例；small_find、small_match和build为77个PDB、446个合格小分子。每条数组依次给出K=1…10内至少成功一个目标实例的PDB数，纵坐标严格为成功PDB数／固定PDB分母×100。build仅选local_cov-C原模型排名Top-1／best-of-50及严格RMSD <2／<3 Å。Emap2lig为显式推荐level条件。零成功、无候选条目保留分母；该指标不按配体实例加权。

完整重建命令：`D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure e2e-topk-success`。统一入口在隔离的FIGURE_BUILD_ROOT中读取冻结计数、重新绘图、检查面板对齐并生成单页可编辑PPT；不写正式图集。

构建输出包括`data/topk_data.json`输入快照、`data/plotted_series.json`实际绘图点、`figures/e2e-topk-success.{svg,pdf,png}`、对齐报告、`manifest.json`双语图注及尺寸、`candidate.pptx`和带来源批注的`rebuilt.pptx`。作者模板原件及最终验收留档于`e2e/output/e2e-topk-success/`，长期入口不读取旧temp。
