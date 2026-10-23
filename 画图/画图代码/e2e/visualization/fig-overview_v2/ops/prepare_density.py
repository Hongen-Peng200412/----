"""复原并核对总览图9HJX绘图密度的固定平滑步骤.

从原 float32 exp.npy 以 scipy.ndimage.gaussian_filter(sigma=1.5, mode='reflect', truncate=4.0) 生成派生数组, 保留 (1,Z,Y,X) 形状. 默认只读比较冻结MRC, 不覆盖它.
显式 --output 指定新路径时写一个绘图MRC; XYZ体素间距来自exp.npz, 第一采样点为边界origin+0.5*voxel_size. --report 将核对报告写入调用者指定的临时目录.
运行例子: python 画图/画图代码/e2e/visualization/fig-overview_v2/ops/prepare_density.py --report temp/figure-provenance/overview-density.json
"""

import argparse
import hashlib
import json
from pathlib import Path

import mrcfile
import numpy as np
from scipy.ndimage import gaussian_filter


def reproduce_density(source_path, metadata_path, reference_path, output_path):
    """核对平滑数值和世界坐标, 可向独立新路径写同源MRC.

    输入参数:
        - source_path: Path, 原float32数组(1,Z,Y,X), 不挤压单例轴.
        - metadata_path: Path, exp.npz内origin和voxel_size均为(3,)XYZ Å, origin是边界角点.
        - reference_path: Path, 已冻结9hjx_drawing.mrc, 只读比较全部数组值及首体素中心.
        - output_path: Path或None, 独立输出MRC位置; None表示不创建MRC, 已存在路径不覆盖.
    返回值:
        - report: dict, 数组形状、数值完全相等判定、最大绝对差、坐标误差、原文件SHA256和passed.
    """
    source = np.load(source_path, allow_pickle=False)
    with np.load(metadata_path, allow_pickle=False) as metadata:
        spacing = metadata["voxel_size"].copy()
        first_center = metadata["origin"] + spacing * 0.5
    smoothed = gaussian_filter(source, sigma=1.5, mode="reflect", truncate=4.0)
    with mrcfile.open(reference_path, permissive=True) as reference:
        exact = np.array_equal(smoothed, reference.data)
        shape = list(reference.data.shape)
        difference = float(np.max(np.abs(smoothed - reference.data)))
        center_difference = float(np.max(np.abs(np.array(reference.header.origin.tolist()) - first_center)))
        spacing_difference = float(np.max(np.abs(np.array(reference.voxel_size.tolist()) - spacing)))
    passed = exact and center_difference < 2e-5 and spacing_difference < 2e-6
    if not passed:
        raise ValueError("固定平滑参数与冻结9HJX绘图密度不一致, 停止导出.")
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with mrcfile.new(output_path, overwrite=False) as output:
            output.set_data(smoothed)
            output.voxel_size = tuple(spacing)
            output.header.origin = tuple(first_center)
    return {"passed": passed, "source": str(source_path), "reference": str(reference_path), "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(), "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(), "shape": shape, "dtype": str(smoothed.dtype), "sigma_voxels": 1.5, "mode": "reflect", "truncate": 4.0, "array_equal": exact, "max_abs_difference": difference, "first_center_max_abs_A": center_difference, "spacing_max_abs_A": spacing_difference, "output": str(output_path) if output_path is not None else None}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[6]
    assets = root / "画图/画图代码/e2e/output/fig-overview_v2/素材"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=assets / "density/9hjx/exp.npy")
    parser.add_argument("--metadata", type=Path, default=assets / "density/9hjx/exp.npz")
    parser.add_argument("--reference", type=Path, default=assets / "9hjx_drawing.mrc")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()
    report = reproduce_density(arguments.source, arguments.metadata, arguments.reference, arguments.output)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.report is not None:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(text + "\n", encoding="utf-8")
    print(text)
