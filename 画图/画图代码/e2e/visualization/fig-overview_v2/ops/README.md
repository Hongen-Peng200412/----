# 9HJX 总览背景密度的固定制备与核对

`prepare_density.py` 补全总览图真实背景从原 `exp.npy` 到绘图 MRC 的制备步骤。先读 `reproduce_density`，再读参数入口；默认只读核对冻结 MRC，不创建或修改科学来源。

输入为原 float32 `(1,Z,Y,X)` 实验密度和 `exp.npz` 的 XYZ 体素边界 `origin`、间距 `voxel_size`。固定 `gaussian_filter(sigma=1.5, mode="reflect", truncate=4.0)` 保留原四维形状；输出 MRC 首采样点为 `origin+0.5*voxel_size`，不裁切、不重采样。9HJX现有冻结MRC的全数组、间距及首采样点已与该步骤精确核对。

```powershell
python 画图/画图代码/e2e/visualization/fig-overview_v2/ops/prepare_density.py --report temp/figure-provenance/overview-density.json
```

报告包含来源路径与SHA-256、数组形状、dtype、固定平滑参数、全部采样值是否相等、最大绝对差、首采样点和间距的误差。只有显式传入 `--output temp/figure-provenance/recreated-9hjx.mrc` 才会写新的派生MRC；目标已存在时不覆盖。后续ChimeraX阈值／相机和PPT几何绘制仍由本图目录的原生入口承担。
