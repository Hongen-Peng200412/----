# Method 方法图 v4：图注与正文中英对照

正文引用 [Method方法图_v4.pptx](Method方法图_v4.pptx) 的第 3 页，图名为 `fig-method-v4`。正式中文图注保存在该页备注中。以下英文与本次新增或微调的中文逐项对应，未翻译或改写其余 Methods 内容。

## 图注

### 中文

图 6｜Find–Match–Build 的网络结构与信息流。

a，共享输入表示。四个基础密度场分别为实验密度 $M_{\mathrm{exp}}$、模拟受体密度 $M_{\mathrm{sim}}$、差密度 $M_{\mathrm{diff}}$ 和正差密度 $M_{\mathrm{diff}}^{+}$。每个密度场采用两种归一化方式和七种空间视图，组成 56 个密度通道；受体原子由 50 维特征表示。

b，Find 的体素–点云网络。3D voxel U-Net 与 Point Transformer V3 通过多尺度体素到点的特征融合协同定位配体区域，并分别输出配体区域概率与原子结合概率。回收连接用于迭代更新点云表示；候选区域（blob）和伪原子为 Match 提供局部线索。

c，Match 的候选–身份匹配。候选区域的密度与原子特征经 U-Net 编码为基础摘要，口袋、blob 和伪原子特征通过池化、交叉注意力与 FiLM 调制候选表示。身份编码器以 SMI-TED 语言表示为查询，分别对自身分子图特征和同一 PDB 中其他身份的语言表示执行图注意力（graph attention）和背景注意力（context attention），再融合为身份表示。候选与身份表示经可学习投影和余弦相似度计算形成 $J\times K$ 匹配分数矩阵，独立前景头输出候选的前景概率。$J$ 为候选数，$K$ 为有效身份数；Q、K、V 分别表示注意力中的查询、键和值。

d，Build 的下游构象重建。候选位点、匹配得到的 SMILES 身份和口袋环境输入密度条件微调的 PocketXMol，或满足适用条件的其他对接工具，得到全原子配体构象。blob 内的深蓝点表示几何中心及对接起始位点。密度、原子和配体构象均为示意。

### English

**Fig. 6 | Architecture and information flow of Find–Match–Build.**

**a,** Shared input representation. Four base fields comprise experimental density $M_{\mathrm{exp}}$, simulated receptor density $M_{\mathrm{sim}}$, difference density $M_{\mathrm{diff}}$ and positive difference density $M_{\mathrm{diff}}^{+}$. Two normalization schemes and seven spatial views yield 56 density channels. Each receptor atom is represented by 50 features.

**b,** The Find point–voxel network. A 3D voxel U-Net and Point Transformer V3 exchange information through multiscale voxel-to-point feature fusion to locate ligand regions, producing ligand-area and atom binding probabilities, respectively. Recycling iteratively updates point representations. Candidate regions (blobs) and pseudo atoms provide local cues for Match.

**c,** Candidate-to-identity assignment in Match. A U-Net encodes candidate density and atom features into a base summary, which is modulated by pocket, blob and pseudo-atom features through pooling, cross-attention and FiLM. The identity encoder uses SMI-TED language representations as queries for graph attention over the identity’s own molecular graph features and context attention over language representations of other identities in the same PDB. These outputs are fused into an identity representation. Learned projections and cosine similarity produce a $J\times K$ candidate–identity score matrix; a separate foreground head predicts candidate foreground probabilities. $J$ and $K$ denote the numbers of candidates and valid identities. Q, K and V denote attention queries, keys and values.

**d,** Downstream pose reconstruction in Build. Candidate sites, matched SMILES identities and pocket environments are supplied to density-conditioned, fine-tuned PocketXMol or other applicable docking tools to reconstruct all-atom ligand poses. The dark-blue point marks the blob’s geometric centre and docking start site. Densities, atoms and ligand poses are schematic.

## 正文的局部改动

### Methods 开头新增图文衔接

中文：Find–Match–Build 的网络结构与信息流见图 6。三个阶段共享密度与受体原子的输入表示（图 6a），依次完成配体区域定位（图 6b）、候选区域与配体身份匹配（图 6c）以及全原子配体构象重建（图 6d）。

English: The architecture and information flow of Find–Match–Build are shown in Fig. 6. The three stages share a density and receptor-atom input representation (Fig. 6a) and sequentially locate ligand regions (Fig. 6b), assign ligand identities to candidate regions (Fig. 6c) and reconstruct all-atom ligand poses (Fig. 6d).

### 配体身份编码中的注意力名称

原句：对于PDB中的某个SMILES $S_i\in\{S_k\}_{k=1}^{K}$，使用它的向量表示分别与它自身的图表示以及其他 SMILES 的向量表示进行注意力运算：

修改后：对于PDB中的某个SMILES $S_i\in\{S_k\}_{k=1}^{K}$，使用它的向量表示作为查询，分别对它自身的图表示进行图注意力（graph attention）运算，对同一 PDB 中其他 SMILES 的向量表示进行背景注意力（context attention）运算（图 6c）：

English: For a SMILES identity $S_i\in\{S_k\}_{k=1}^{K}$ in a PDB, its vector representation serves as the query for graph attention over its own graph representation and for context attention over the vector representations of other SMILES identities in the same PDB (Fig. 6c):

该句之后的两个注意力公式原样保留。这里的“图注意力”指以语言向量为查询、对自身图特征进行的注意力运算；图中的 GNN 是它之前的图特征编码模块。

### 身份表示的符号对应

中文：$S_k^{\mathrm{repr}}=(S_k^{\mathrm{language}},\hat S_k,\tilde S_k)$ 将作为第k个配体身份的最终表示（图 6c 中记为 $g_k$）。

English: $S_k^{\mathrm{repr}}=(S_k^{\mathrm{language}},\hat S_k,\tilde S_k)$ is used as the final representation of ligand identity $k$ (denoted by $g_k$ in Fig. 6c).

本句只增加图中符号的对应说明，原有表示式不变。

### 术语对应与拼写

| 中文或符号 | 英文 | 本次处理 |
|:--|:--|:--|
| 图注意力 | graph attention | 自身分子图特征上的注意力 |
| 背景注意力 | context attention | 同一 PDB 中其他身份语言表示上的注意力 |
| 交叉注意力 | cross-attention | 候选摘要作为查询，读取辅助特征；图中名称与原正文一致 |
| 最终身份表示 $S_k^{\mathrm{repr}}$ | final identity representation | 图中对应 $g_k$ |
| RDKit | RDKit | 将正文中的 RDKID 更正为 RDKit |

正文图集引用：

```text
{{pptfig:"画图/Method方法图_v4.pptx"|fig-method-v4}}
```
