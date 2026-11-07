# Fig5: Match准确率、Build共同实例与9WUP构象

本目录只重建正文Fig5, 对应正式图名`stage2-stage3-results(v1)`。完整入口读取服务器原始评价, 重新计算a–f的统计图元, 再从9WUP原构象和实验密度生成g–i的可编辑分子视图。作者的面板位置、配色、图例和文字由本目录`author_layout.json`提供; 双语图注复制自`画图/PPT/stage2-stage3结果.pptx`的当前备注。

## 运行与产物

在论文项目根运行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/正文/Fig5-result-Match&Build/run.py"
```

入口自动新建根`temp/figure-build/`下的本次目录。也可用`--build temp/<新目录>`指定空目录。成功产物为一页`candidate.pptx`; 不修改正式PPT。其余文件都是本次可清空材料:

| 产物 | 内容 |
| --- | --- |
| `data/data.json`、`summary.json` | Match计数和235共同实例的原序列、描述统计 |
| `source_reads.json` | 本次实际读取的绝对服务器路径、完整SHA256和大小 |
| `case-source/assets/9wup_2/arrays.npz`、`metadata.json` | 本次原构象、原子轴、局部密度及身份/原排名记录 |
| `case-source/case_metrics.json`、`geometry.json` | 真实三维指标与单独用于显示的二维投影 |
| 图名对应的SVG/PDF/PNG、`scenes.json` | 本次重画的科学图元; 单页最终显示以candidate为准 |
| `*.alignment.json`、`*.alignment.svg` | 本次面板几何核对 |

`arrays.npz` 的数组直接服务本次 9WUP 视图，主要字段为：

| 字段 | 形状与含义 |
| --- | --- |
| `gt/official/tuned/build` | 各为 `(53,3)` 世界 XYZ/Å，分别是真实、官方、DG、Emap2lig 的同轴重原子坐标 |
| `element`、`bonds` | `(53,)` 原子序数；`(B,3)` 的前两列是该配体原子轴下标，第三列为键阶 |
| `receptor_xyz` | `(R_local,3)`，按原世界 XYZ/Å 保留的局部受体原子 |
| `receptor_element/receptor_res_index/receptor_atom_name` | 各为 `(R_local,)`，与局部坐标同轴的原属性；残基编号不改写为沉积 auth 编号 |
| `receptor_bonds` | `(B_local,2)`，两端已经映射为局部受体原子下标 |
| `density` | `(Z_local,Y_local,X_local)` 原密度裁片，不重新采样或按显示阈值改像素 |
| `origin/voxel_size/contour` | 前两项为 `(3,)` XYZ/Å 的裁后网格边界与步长；体素中心加半步长。contour 是原等值面标量 |

`metadata.json::density_slice_xyz` 是 `[low,high]` 两个 XYZ 网格下标向量，低端含、高端不含；切数组时才反转为 ZYX。代码中的 `mapping` 将完整受体原子轴映射为局部轴，`-1` 表示未保留，只有两端均保留的原键进入 `receptor_bonds`。metadata 另保存原实例、原 Top-1 的采样编号/RMSD及本次实际来源，不从投影图片反推科学坐标。

## 阅读顺序

1. 读[trace.md](trace.md), 先分清Match的blob支持数、主比较的235实例和标准消融的446实例。
2. 读`run.py → build.py → science.py`。`read_match(...,'main')`读取最强模型及身份分组; `read_main_build`读取三方共同实例。服务器读取旁的注释给出绝对路径、字段语义和现存生产README。
3. 读`plot.py`, 对照a–f的类别、身份数分层、严格RMSD成功率和配对散点。
4. 读`visual/arrays.py → geometry.py → compose.py → inject.py`。前三步分别提取原数组、计算三维指标与PCA显示、组合9WUP三列; 最后一步把本次原生对象放入g–i。
5. 读`visual/axis.py`和`author_layout.json`, 理解b/c的0–105%轴与当前作者显示如何结合。科学计数不会从旧PPT对象反读。

## 跨图共用的科学代码

本目录是标准Build科学读取和分布规则的唯一代码所有者。正文Fig9显式复用`science.py::read_standard_build(...,'C0')`及`build_panels.py::boxes`; 补充Fig3复用同函数的`'E'`协议。Fig9还复用`read_match(...,'ablation')`获取四模型雷达。两个消融入口均不运行本图235交集、身份数分组或9WUP。

这些函数包含实验路径、模型身份、446分母、百分位与KDE定义, 因而属于Fig5科学代码。`TOOLS`只承担SSH原字节供应、SVG解析、原生PPT装配、二维矩形裁切和OOXML显示运输。

## 保持的科学与显示约定

Match分组按同一PDB不同精确SMILES身份数, 不是采样构象数。Build的Top-1/Top-5/best-of-50沿用原排序, 不按真实RMSD重新排名。成功条件是严格小于阈值; 235共同实例与446标准消融不能互换。9WUP的密度索引`-0.5`、碰撞半径和阈值、受体邻域、原子连接、PCA取景和网格近邻选择均保留在本图, 未移入通用工具。
