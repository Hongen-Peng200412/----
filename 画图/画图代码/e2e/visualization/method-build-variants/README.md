# 方法图 Build 四种内部设计

本目录从作者保存的独立Build页构造四个c候选。原5页不重绘、不经工具导入导出; 新页插在第2页后, 整体结构、密度机制、多pose、去噪示意分别为第3至6页, 原a/b为第7至9页。

```text
e2e/visualization/method-build-variants/
├─ render_native.py   # 从真实坐标及示意噪声坐标生成PyMOL素材
├─ build_deck.mjs     # Artifact Tool原生组件及对作者包的局部装配
├─ render_slides.ps1  # PowerPoint只读预览
├─ audit.py           # 原件、预览和相机核对
└─ finalize.mjs       # 9页PPT包、一方导入和字体验收
e2e/output/method-build-variants/
├─ source/author-20261028-ce373d2e.pptx # 作者冻结PPT输入
├─ source/author-output-9bjj.pse # 冻结的CA2口袋风格、相机与原子会话
├─ source/sources.json        # 作者PPT和会话的来源与散列
└─ regenerated/20261028-C1-C4/ # 已发布留档根目录
   ├─ Method总图.pptx        # 实际保存的9页正式文件副本
   ├─ render/                # 13组PNG与PSE
   ├─ render_manifest.json   # 输入、相机及逐图坐标
   ├─ variants.json          # 四种候选、页码和素材选择
   ├─ C1.png … C4.png        # 独立Build预览裁图
   ├─ Build-comparison.png   # 横向对比预览
   ├─ audit.json             # 装配候选的对象与像素核对
   ├─ receipt.json           # 禁止读取旧temp的完整重建回执
   └─ publication-check.json # 实际正式文件与候选的比较
```

## 本次重建产物

每次运行使用全新的 `FIGURE_BUILD_ROOT`, 不读旧temp。`render/`保存13幅透明PNG和同名`.pse`会话; `render_manifest.json`是对象, `images`以图名为键, 如`"denoise-2"`, 值含18项相机`view`、像素画幅`canvas_px`、输入说明`source`、单位Å的`ligand_xyz_A (31,3)`和`atom_count=31`。`denoising`保存`seed=20261028`、五个示意噪声标准差`sigma_A=[4.0,2.1,0.9,0.30,0.0]`及结构比例`structure_fraction=[0.0,0.45,0.75,0.95,1.0]`, 不表示真实采样步。各帧按中心加上结构比例乘以中心化最终坐标、再加高斯噪声构造; 初始化比例为0, 因而为中心附近的高斯点云。

`selected_candidate_indices=[21,13,35]`为同一个`e2e/output/e2e-flow/source/source/9bjj/poses.sdf`中的0基记录编号, 按顺序对应`pose-1`、`pose-2`、`pose-3`; 选择依据候选之间的坐标差异, 不用真实结构RMSD或修改模型排名。`inputs`为路径与SHA-256的列表, 如`path="画图/画图代码/e2e/output/e2e-flow/views/9bjj/assets/prediction.sdf"`, 固定所读原件。`case="9BJJ ATP B:901"`连接原auth身份; `candidate_count=50`为原SDF记录数。整体和局部结构采用GT; 其余三版采用对应CA2受体与预测坐标, 输入Pocket随之同步。

所有`ligand_xyz_A`均为原文件的世界XYZ坐标, 单位Å, 不另做平移、对齐或重新定义原点; 第一维保持相应SDF中的31个重原子顺序, 不含氢。`canvas_px=[1800,1300]`按宽、高排列。`view`按PyMOL原生18项格式保存: 0至8为旋转矩阵, 9至11为相机平移, 12至14为模型旋转中心, 15至16为前后裁剪面, 17为正交/视场信息; 直接交给`cmd.set_view`恢复。

示意去噪的中心为`prediction.sdf`中31个重原子的XYZ均值, 最终坐标为该文件的原预测坐标。`default_rng(20261028)`产生一次形状为`(31,3)`的标准高斯噪声, 所有帧复用同一噪声矩阵; 第i帧等于中心加上`structure_fraction[i]`倍中心化最终坐标, 再加上`sigma_A[i]`倍噪声。下面是`denoising`完整子对象; 逐图`images`和来源`inputs`在主JSON中独立保存。

```json
{"kind":"schematic_coordinate_perturbations","seed":20261028,"sigma_A":[4.0,2.1,0.9,0.3,0.0],"structure_fraction":[0.0,0.45,0.75,0.95,1.0],"meaning":"Illustrative noise levels, not measured model sampling timesteps; atom identities and count remain fixed."}
```

`variants.json`把`code="C1"`、`figure="fig-method-build-context"`、实际页码`page=3`和包内页号`part=6`连接。`label`为中文方案名, 如`"整体与局部结构"`; `pocket="reference-pocket"`连接`render_manifest.json.images["reference-pocket"]`及同名PNG; `cn`、`en`分别保存该方案的中文、英文图注说明。`editable_objects=40`计数该页的顶层原生图形、文本、图片和组, 不递归重复计数组内子形状。包内页号不等于显示顺序; `original_page_mapping`如`"3":7`表示原第3页显示为第7页。`candidate.pptx`为完整9页可编辑图集, `components.pptx`仅为本次新增原生组件。

`audit.json.passed`为核对结论, `failures=[]`表示无错误; `checks.original_parts.changed=[]`和`checks.original_pixels`全为true分别证明原页XML/资源与PowerPoint像素保留。`C1.png`至`C4.png`是预览裁图, `Build-comparison.png`仅用于横向审读, 不作为PPT素材。`published/Method总图.pptx`为通过一方验收的发布副本, `receipt.json`保存完整重建步骤。

`publication-check.json`针对实际保存的正式文件: `candidate_pixels`按新页码1至9比较候选, `original_pixels`按原页码1至5比较作者基底, `provenance`与`caption_language`分别按稳定图名检查来源批注及双语备注, 全为true时`passed=true`。`active_window_*`保留第一次活动窗口导出的比较, 单个字形的缓存差异不修改原对象; 实际判定使用重新打开保存副本后的导出。`final_manifest.json`连接最终散列、页码及源代码版本; `task-provenance-check.json`把本轮来源结果与其他图集的现有问题分开保存。

从仓库根运行 `D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-method-build-context --generated-captions`, 一次同时重建四版。稳定图名还包括`fig-method-build-conditioning`、`fig-method-build-poses`、`fig-method-build-denoising`, 共用相同入口。重建器自动创建新的`temp/figure_rebuild/<运行号>/<图名>/`并设置`FIGURE_BUILD_ROOT`, 无需用户手设。也可用`--build-root temp/自选的新目录`选择临时根目录, 仍由工具建立其下的图名子目录。上文未带完整前缀的`render/`、JSON、`slides/`和`published/`均位于这个单次构建根; 发布留档单独复制到目录树中的`regenerated/20261028-C1-C4/`, 不作为下次构建输入。

本机环境为`D:/Anaconda/python.exe`、`D:/Pymol/python.exe`、`C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`和已安装PowerPoint。Bundled Node位置可用Codex的`load_workspace_dependencies`重新查询; 重建器支持`FIGURE_NODE`和`FIGURE_PYMOL_PYTHON`覆盖已安装可执行程序。依赖包不安装在temp, 不训练、推理或重算实验指标。范围与实际留证见[方案与执行记录](../../../../../talk/method_build_20261028/映射索引.md)。
