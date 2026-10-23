"""只从冻结逐 PDB 指标生成两代 LigandSeek 比较图的绘图统计.

入口 prepare_plot_data() 不导入模型或评估模块, 不读取体素掩码, 不计算交集、匹配、PRAUC 或成员资格.
output_root 决定三个文件的位置: plot_data.json 保存配对指标、均值区间和小提琴密度, source_data.csv 保存逐 PDB 指标, bar_statistics.csv 保存柱图均值与区间.
全部成员直接读取正式评估的 input_manifest; source_data.csv 和 JSON 中的 PDB 顺序保持该清单顺序.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde


METHODS = ("L2_GT", "L2_CA2", "L1_GT", "L1_CA2")  # 四种固定模型/受体条件; GT 是沉积受体, CA2 是 CryoAtom2 重建受体.
METRICS = ("dice", "prauc_0p3", "prauc_0p5", "precision", "recall")  # 每个 PDB 的五个已评估指标; 实例指标均为一对一, P/R 的双向覆盖阈值为 0.3.
BOOTSTRAP_REPLICATES = 10_000  # PDB 等权重采样次数; 不是模型运行次数.
BOOTSTRAP_SEED = 20260922  # 与论文原六图相同的绘图统计随机种子.
KDE_BANDWIDTH = 0.045  # 无量纲 bw_method 带宽因子; 核标准差为反射样本标准差乘 0.045, 核协方差乘 0.045**2.


def prepare_plot_data(ligandseek2_source: Path, ligandseek1_root: Path, input_manifest: Path, output_root: Path) -> None:
    """对齐冻结 PDB 指标, 再生成均值区间、分布和配对描述, 不重新评估模型.

    输入参数:
        - ligandseek2_source: Path, 已冻结 JSON; models.GT/Cryo 分别保存沉积/重建受体条件, resolution 是 PDB 到分辨率 Å 的映射.
        - ligandseek1_root: Path, 正式结果的只读本地镜像根; deposited/inferred 分别对应沉积/重建受体条件, 如 data/ligandseek1.
        - input_manifest: Path, 正式评估冻结 JSON; test_0_pdb_ids 是完整集合, small_pdb_ids 是既定小分子阳性集合, 本函数不筛选或修改成员.
        - output_root: Path, 三个绘图数据文件的输出根; 必须尚无同名文件, 不覆盖既有结果.

    读取的指标字段:
        - LigandSeek2 models.GT/Cryo.full_rows: list[dict], 每个 PDB 一项, 读取 pdb_id 和 semantic_macro_f1、one_to_one_macro_prauc_0p3/0p5、one_to_one_macro_precision/recall_0p3.
        - LigandSeek2 models.GT/Cryo.small_rows: list[dict], 冻结小分子 PDB 指标, 读取 pdb_id 和 semantic_dice、one_to_one_prauc_0p3/0p5、one_to_one_precision/recall_0p3.
        - LigandSeek1 <mode>/held_out_test_0/evaluation/official_pv.jsonl: JSONL, 逐 PDB 完整指标, 五个数值字段与 LigandSeek2 full_rows 的字段相同.
        - LigandSeek1 <mode>/held_out_test_0/small_molecule_only/official_pv.jsonl: JSONL, 正式小分子评估指标, 五个数值字段与完整 JSONL 相同; 不从匹配计数推导 P/R.

    落盘文件:
        - plot_data.json: JSON 对象, 供六图读取; 数值均不舍入, 全部成员按 input_manifest 顺序排列.
            - bootstrap_replicates: int, 固定 10000, 每个集合内四方法/三个柱图指标共享重采样索引.
            - bootstrap_seed: int, 固定 20260922; full/small 分别重置同一随机种子, 不把二者作为独立统计样本.
            - kde_bandwidth: float, 固定 0.045, gaussian_kde 的无量纲带宽因子; 核标准差为反射样本标准差乘 0.045, 核协方差乘 0.045**2.
            - sources: dict[str, str], 三个已读取路径, 不计算哈希.
                - ligandseek2_source: str, 冻结 LigandSeek2 的指标 JSON 路径, 如 data/server_metrics_and_pr.json.
                - ligandseek1_root: str, LigandSeek1 已验收指标的只读本地镜像根, 如 data/ligandseek1.
                - input_manifest: str, 固定 PDB 成员的正式评估 JSON 路径, 如 Ligandseek/实验记录/held_out/inputs.json.
            - cohorts: dict, full/small 分别保存完整/既定小分子集合的绘图统计.
                - ids: list[str], N 个 PDB 的有序标识, 如 [9ter, 30yu]; N 是本集合 PDB 数.
                - n: int, 等于 len(ids), 正式 full/small 分别为 179/94.
                - resolution: list[float], (N,), 与 ids 对齐的实验分辨率, 单位 Å.
                - models: dict, L2_GT/L2_CA2/L1_GT/L1_CA2 四方法, 每种方法拥有以下三个字段.
                    - values: dict[str, list[float]], 五个长度 N 的无量纲指标, 均直接读取冻结事实.
                        - dice: list[float], (N,), 逐 PDB 语义 F1/Dice, 与 ids 对齐, 不从平均 P/R 推导.
                        - prauc_0p3: list[float], (N,), 逐 PDB 一对一 PRAUC, 双向覆盖阈值为 0.3.
                        - prauc_0p5: list[float], (N,), 逐 PDB 一对一 PRAUC, 双向覆盖阈值为 0.5.
                        - precision: list[float], (N,), 逐 PDB 一对一精确率, 双向覆盖阈值为 0.3.
                        - recall: list[float], (N,), 逐 PDB 一对一召回率, 双向覆盖阈值为 0.3.
                    - bars: dict, dice/prauc_0p3/prauc_0p5 三种柱图指标, 每个指标保存以下三个 float 字段.
                        - mean: float, 当前指标的 N 个 PDB 等权算术均值.
                        - lower: float, 10000 次 PDB 重采样均值的第 2.5 百分位数.
                        - upper: float, 10000 次 PDB 重采样均值的第 97.5 百分位数.
                    - distribution: dict, precision/recall 分别保存小提琴曲线和分位数, 不移除等于 0 或 1 的 PDB.
                        - grid: list[float], (161,), 从 0 到 1 的等距指标取值, 两端都包含.
                        - density: list[float], (161,), 在 [v, -v, 2-v] 上计算的 KDE 除以其最大值, 与 grid 对齐, 只表示相对展示宽度.
                        - quartiles: list[float], (3,), 原始 N 个指标的第 25/50/75 百分位数, 中间一项为中位数.
                - paired_counts: dict[str, int], CA2 条件下 PRAUC_0p3 的同 PDB 两代差值方向计数.
                    - l2_higher: int, LigandSeek2 减 LigandSeek1 的差值大于 1e-12 的 PDB 数.
                    - equal: int, 两代差值绝对值不超过 1e-12 的 PDB 数.
                    - l1_higher: int, LigandSeek2 减 LigandSeek1 的差值小于 -1e-12 的 PDB 数.
        - source_data.csv: UTF-8 BOM 的 CSV, 每个集合/方法/PDB 一行; full 与 small 分别按冻结成员顺序展开, 小分子成员也出现在完整集合中.
            - cohort: str, full 或 small, 如 full.
            - method: str, 固定四方法之一, 如 L1_CA2.
            - pdb_id: str, 该行的 PDB, 如 9ter.
            - resolution_angstrom: float, 实验分辨率 Å, 与该行 PDB 对应.
            - dice: float, 该行 PDB 的语义 F1/Dice, 对应 plot_data.json 的 values.dice.
            - prauc_0p3: float, 该行 PDB 的一对一 PRAUC_0p3, 对应 values.prauc_0p3.
            - prauc_0p5: float, 该行 PDB 的一对一 PRAUC_0p5, 对应 values.prauc_0p5.
            - precision: float, 该行 PDB 的一对一_0p3 精确率, 对应 values.precision.
            - recall: float, 该行 PDB 的一对一_0p3 召回率, 对应 values.recall.
        - bar_statistics.csv: UTF-8 BOM 的 CSV, 每个集合/方法/三个柱图指标一行, 正式共 24 行.
            - cohort: str, 冻结集合名称, 如 full.
            - method: str, 固定模型/受体条件, 如 L1_GT.
            - metric: str, 三种柱图指标之一, 如 dice.
            - n: int, 该集合 PDB 数, 与 plot_data.json 的 n 一致.
            - mean: float, PDB 等权算术均值, 对应 bars 的 mean.
            - ci95_lower: float, 重采样均值的第 2.5 百分位数, 对应 bars 的 lower.
            - ci95_upper: float, 重采样均值的第 97.5 百分位数, 对应 bars 的 upper.

    只读取现成指标, 未完成、成员不同或顺序不同的输入会报错, 不补零、不重定资格、不发布占位性能图.
    """
    source = json.loads(ligandseek2_source.read_text(encoding="utf-8-sig"))  # 冻结的两种 LigandSeek2 受体条件指标和 PDB 分辨率映射.
    manifest = json.loads(input_manifest.read_text(encoding="utf-8-sig"))  # 固定 test_0 与 small 的成员列表; 不是重新判定小分子类别的输入.
    result = {
        "bootstrap_replicates": BOOTSTRAP_REPLICATES, "bootstrap_seed": BOOTSTRAP_SEED, "kde_bandwidth": KDE_BANDWIDTH,
        "sources": {"ligandseek2_source": str(ligandseek2_source), "ligandseek1_root": str(ligandseek1_root), "input_manifest": str(input_manifest)}, "cohorts": {},
    }  # JSON 的全局统计条件与两个集合; 子字段由本函数 Docstring 定义.
    long_rows, bar_rows = [], []  # 两种 CSV 的待发布记录; 每行按下方固定表头的字段顺序排列.
    for cohort, member_field in (("full", "test_0_pdb_ids"), ("small", "small_pdb_ids")):
        ids = manifest[member_field]  # list[str], N 个冻结成员, 不按性能或标签重新筛选.
        n = len(ids)
        block = {"ids": ids, "n": n, "resolution": [float(source["resolution"][pdb]) for pdb in ids], "models": {}}  # 四方法的相同 PDB 轴和实验分辨率 Å.
        regular_fields = ("semantic_macro_f1", "one_to_one_macro_prauc_0p3", "one_to_one_macro_prauc_0p5", "one_to_one_macro_precision_0p3", "one_to_one_macro_recall_0p3")
        l2_fields = regular_fields if cohort == "full" else ("semantic_dice", "one_to_one_prauc_0p3", "one_to_one_prauc_0p5", "one_to_one_precision_0p3", "one_to_one_recall_0p3")  # 旧小分子视图的指标字段名不同, 数值直接读取, 不重算.
        for method in METHODS:
            if method.startswith("L2_"):
                receptor_key = "GT" if method == "L2_GT" else "Cryo"
                rows = source["models"][receptor_key][f"{cohort}_rows"]  # list[dict], 冻结逐 PDB 指标, 不使用原 Emap2lig 数据.
                fields = l2_fields
            else:
                mode = "deposited" if method == "L1_GT" else "inferred"
                folder = "evaluation" if cohort == "full" else "small_molecule_only"
                path = ligandseek1_root / mode / "held_out_test_0" / folder / "official_pv.jsonl"
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]  # 正式评估生成的逐 PDB 数值, 不读取或重新处理模型原生输出.
                fields = regular_fields
            assert [row["pdb_id"] for row in rows] == ids, (cohort, method, "PDB membership/order mismatch")
            values = {metric: [float(row[field]) for row in rows] for metric, field in zip(METRICS, fields)}  # 五个长度 N 的指标, 同一位置始终是 ids 中相同的 PDB.
            metric_matrix = np.asarray(list(values.values()), dtype=np.float64)  # (5, N), 第一轴按 METRICS 排列, 第二轴按冻结成员排列.
            assert np.isfinite(metric_matrix).all() and np.min(metric_matrix) >= 0 and np.max(metric_matrix) <= 1, (cohort, method, "invalid frozen metric")
            distribution = {}  # precision/recall 的展示分布; 候选资格和指标值不在此处改变.
            for metric in ("precision", "recall"):
                v = np.asarray(values[metric], dtype=np.float64)  # (N,), 已评估的一对一 P/R, 包含所有 0/1 端点.
                grid = np.linspace(0.0, 1.0, 161)  # (161,), 只供小提琴横向宽度计算的指标轴.
                reflected = np.concatenate((v, -v, 2.0 - v))  # [N] -> [3*N], 在 0/1 两端反射, 沿用原图的边界 KDE 规则.
                density = gaussian_kde(reflected, bw_method=KDE_BANDWIDTH)(grid)  # (161,), 在相同指标轴计算平滑密度, 不是性能指标或概率图.
                distribution[metric] = {"grid": grid.tolist(), "density": (density / density.max()).tolist(), "quartiles": np.quantile(v, [0.25, 0.5, 0.75]).tolist()}
            block["models"][method] = {"values": values, "distribution": distribution, "bars": {}}
            for index, pdb in enumerate(ids):
                long_rows.append([cohort, method, pdb, block["resolution"][index]] + [values[metric][index] for metric in METRICS])  # 一行对应当前集合/方法/PDB, 同一行五指标共用同一 PDB 身份.
        columns = [(method, metric) for method in METHODS for metric in METRICS[:3]]  # 12 个柱图指标列, 四方法均使用同一 PDB 轴.
        matrix = np.column_stack([block["models"][method]["values"][metric] for method, metric in columns])  # [12, N] -> [N, 12], 每行同一个 PDB 的四方法/三指标.
        rng = np.random.default_rng(BOOTSTRAP_SEED)  # full/small 分别使用原图同一种子; 每次在该集合内部进行 PDB 重采样.
        boot = np.concatenate([matrix[rng.integers(0, n, size=(250, n))].mean(axis=1) for _ in range(BOOTSTRAP_REPLICATES // 250)])  # [250, N, 12] -> [250, 12] -> [10000, 12], 四方法/三指标共用同批整数 PDB 索引.
        bounds = np.quantile(boot, [0.025, 0.975], axis=0)  # [10000, 12] -> [2, 12], 两行依次为 95% 均值区间下界和上界.
        for index, (method, metric) in enumerate(columns):
            stats = {"mean": float(matrix[:, index].mean()), "lower": float(bounds[0, index]), "upper": float(bounds[1, index])}
            block["models"][method]["bars"][metric] = stats  # 三个 float 分别为该方法/指标的 PDB 等权均值、下界和上界.
            bar_rows.append([cohort, method, metric, n, stats["mean"], stats["lower"], stats["upper"]])
        delta = np.asarray(block["models"]["L2_CA2"]["values"]["prauc_0p3"]) - np.asarray(block["models"]["L1_CA2"]["values"]["prauc_0p3"])  # (N,), 同 PDB 重建受体条件的两代 PRAUC 差值, 正值为 L2 较高.
        block["paired_counts"] = {"l2_higher": int((delta > 1e-12).sum()), "equal": int((np.abs(delta) <= 1e-12).sum()), "l1_higher": int((delta < -1e-12).sum())}
        result["cohorts"][cohort] = block
    output_root.mkdir(parents=True, exist_ok=True)
    for name in ("plot_data.json", "source_data.csv", "bar_statistics.csv"):
        assert not (output_root / name).exists(), f"Refusing to overwrite {output_root / name}"
    for name, header, rows in (
        ("source_data.csv", ["cohort", "method", "pdb_id", "resolution_angstrom", *METRICS], long_rows),
        ("bar_statistics.csv", ["cohort", "method", "metric", "n", "mean", "ci95_lower", "ci95_upper"], bar_rows),
    ):
        with (output_root / name).open("x", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)
    with (output_root / "plot_data.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, allow_nan=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ligandseek2-source", type=Path, required=True)
    parser.add_argument("--ligandseek1-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    prepare_plot_data(args.ligandseek2_source, args.ligandseek1_root, args.input_manifest, args.output_root)
