"""复用旧实跑的官方 Build 构造与采样, 消费本轮显式 level 的原生 blob.

先读 run_one, 再读 run_build. 每个有效请求联合生成 50 个 100 步姿态; result_root 指定独立条件根, build_status.jsonl 保存每次尝试, build/<pdb>/<occurrence>/<run_id>/ 保存化学输入、CIF、掩码及原 consistency_iou 评分. 真值坐标不进入本模块.
"""

import csv
import json
import os
import random
from pathlib import Path

import numpy as np
import torch
from hydra.utils import instantiate
from lightning.pytorch import Trainer
from torch.utils.data import DataLoader

from emap2lig.data.dataset import LigandModelingDataset, collate_fn
from emap2lig.data.io.writer import LigandWriter
from emap2lig.data.types import LigandRecord
from emap2lig.main import create_blob_csv_tables, load_config, prepare_ligand_dataset
from emap2lig.model.model import Emap2lig

from paths import RESULT_ROOT


# ================================================================================================
def run_one(record: dict, trainer: Trainer, model: Emap2lig,
            writer: LigandWriter, run_id: str, result_root: Path) -> dict:
    """一个 Dataset 输入一次产生 50 个姿态, 保留原 Build 过滤与评分.

    输入参数:
        - record: dict, 一个新 Find 命中实例的请求, 实际读取下面六个字段.
            - pdb_id: str, 小写 PDB 标识, 如 9llg.
            - occurrence_id: int, 冻结测试实例编号, 不是 blob 编号, 如 0.
            - blob_id: int, 原生 Find 文件 blob_N.npz 中的 N, 如 1.
            - blob_path: str, 新条件原生 blob 的绝对路径, 包含连续密度与局部实例掩码.
            - prepared_smiles: str, 冻结精确身份, 如 CCO; 不含参考坐标.
            - status: str, ready 才运行模型, 其他状态直接保留失败.
        - trainer: Trainer, 使用同一官方权重的 Lightning 推理器.
        - model: Emap2lig, 官方 Build 模型; 本函数设定 multiplicity=50 和 num_sampling_steps=100.
        - writer: LigandWriter, 函数将 writer.output_dir 改为当前实例目录, 写出 CIF、预测掩码和 consistency_iou 评分 CSV.
        - run_id: str, 本次任务启动编号, 如 with_level_job423330_20261026T200000_a2, 使尝试目录互不覆盖.
        - result_root: Path, 新显式 level 条件的 Build 根; 不指向旧 stage3_find_hit_build.

    返回字段:
        pdb_id、occurrence_id: 字符串结构编号与整数冻结实例编号.
        status: ready 输入可完成时为 complete; 未通过原筛选为 build_filter_failed; 配对失败为 build_input_failed; CIF 不足 50 为 sampling_failed; 原始评分不足 50 为 scoring_failed.
        generated: 已写出的 CIF 姿态数, 整数.
        result_dir: build/<pdb_id>/<occurrence_id>/<run_id>/; complete 时内含 preprocess/ligands/LIG.npz、build_struct/blob_<blob_id>/ 的 CIF、掩码和评分 CSV. 筛选失败时目录可不存在, 配对失败时可能只含 preprocess/ligands/LIG.npz.
        seed: 仅 complete 时存在的整数随机种子.
    """
    pdb_id = record["pdb_id"]
    occurrence_id = record["occurrence_id"]
    # 新条件内某个测试实例的一次独立启动目录, 保存化学输入与 50 个姿态, 不指向旧结果.
    result_dir = result_root / "build" / pdb_id / str(occurrence_id) / run_id
    if record["status"] != "ready":
        return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
                "status": record["status"], "generated": 0, "result_dir": str(result_dir)}

    result_dir.mkdir(parents=True, exist_ok=True)
    # LIG 名称仅在本实例的独立目录内使用; blobs 使 Dataset 只配对此次命中的 blob.
    ligand = LigandRecord(type="SMILES", name="LIG", blobs=[record["blob_id"]],
                          smiles=record["prepared_smiles"])
    # 由精确 SMILES 生成的官方参考构象与图特征, 不是沉积真值坐标.
    ligand_dir = result_dir / "preprocess/ligands"
    if not (ligand_dir / "LIG.npz").exists():
        _, ligand_dir = prepare_ligand_dataset([ligand], result_dir)
    dataset = LigandModelingDataset(
        density_object_list=[Path(record["blob_path"])],
        ref_mol_dir=ligand_dir,
        multiplicity=50,
    )
    if len(dataset) != 1:
        return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
                "status": "build_input_failed", "generated": 0, "result_dir": str(result_dir)}

    # 一个 batch 是一个 blob-配体配对; prompt_points 为以预测 blob 中心为原点的 (50, 3) XYZ 坐标, 单位 Å; 拼批为 (1, 50, 3), writer 加回中心后写世界坐标.
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0,
                            collate_fn=collate_fn)
    writer.output_dir = result_dir / "build_struct"
    writer.output_dir.mkdir(exist_ok=True)
    # 原写出器把一次联合采样的 50 个 CIF 和 consistency_iou 写到同一目录.
    blob_dir = writer.output_dir / f"blob_{record['blob_id']}"  # 当前原生 blob 的 CIF、预测掩码和评分目录.
    csv_path = blob_dir / f"blob_{record['blob_id']}_results.csv"  # 原 writer 逐姿态生成的 consistency_iou, 不含真值 RMSD.
    # 同一实例的参考构象、50 个 prompt 和扩散随机数来自同一次 Dataset 读取.
    seed = 20260928 + sum(ord(char) for char in pdb_id) * 100 + occurrence_id
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    model.predict_args.multiplicity = 50
    model.predict_args.num_sampling_steps = 100
    trainer.predict(model, dataloaders=dataloader, return_predictions=False)
    cif_names = {path.stem for path in blob_dir.glob(f"blob_{record['blob_id']}_LIG_*.cif")}
    generated = len(cif_names)
    if generated != 50:
        return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
                "status": "sampling_failed", "generated": generated,
                "result_dir": str(result_dir)}
    # 官方汇总会为缺评分的 CIF 补 0 分; 在调用前核对原始 50 个评分与 CIF 一一对应.
    if not csv_path.exists():
        return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
                "status": "scoring_failed", "generated": generated,
                "result_dir": str(result_dir)}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        scores = list(csv.DictReader(handle))
    if (len(scores) != 50 or
            {row["conformer_name"] for row in scores} != cif_names or
            not all(np.isfinite(float(row["consistency_iou"])) for row in scores)):
        return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
                "status": "scoring_failed", "generated": generated,
                "result_dir": str(result_dir)}
    # 原函数将 50 个 consistency_iou 统一排序, 并复制评分第一名到 best/.
    create_blob_csv_tables(writer.output_dir)
    return {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
            "status": "complete", "generated": 50, "result_dir": str(result_dir),
            "seed": seed}


def run_build(records: list[dict], result_root: Path) -> None:
    """单次装载官方权重, 按冻结顺序生成姿态并追加 build_status.jsonl.

    输入参数:
        - records: list[dict], run_one 接受的命中请求, 包含原生 blob 和精确 SMILES.
        - result_root: Path, 本条件化学输入、姿态和状态的共同根, 如 contour_level_20261026/build.

    每行必含 pdb_id、occurrence_id、status. 正常返回还含 generated 和 result_dir, 成功时含 seed; 未捕获异常写 status=runtime_failed 和 error 后终止本次任务, 该异常记录没有 generated/result_dir. 中断重启时跳过已 complete 的实例, 新尝试使用新的 TASK_RUN_STAMP 目录.
    """
    # 同一任务只装载一次官方 Build 权重, 有效输入数由新 Find 与原比例筛选共同决定.
    result_root.mkdir(parents=True, exist_ok=True)
    cfg = load_config(gpu=0)
    model = instantiate(cfg.model)
    model.predict_args.multiplicity = 50
    model.predict_args.num_sampling_steps = 100
    # 官方写出器的初始目标, 每个 run_one 会再切换到对应实例的独立目录.
    writer = LigandWriter(output_dir=result_root / "build", output_format="mmcif")
    trainer = Trainer(accelerator="gpu", devices=[0], callbacks=[writer], logger=False)
    status_path = result_root / "build_status.jsonl"  # 本条件所有实例尝试的追加记录, 不覆盖中断前的尝试.
    completed = {}
    if status_path.exists():
        for line in status_path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            completed[(item["pdb_id"], item["occurrence_id"])] = item
    run_id = os.environ["TASK_RUN_STAMP"]
    with status_path.open("a", encoding="utf-8") as status_file:
        for record in records:
            key = (record["pdb_id"], record["occurrence_id"])
            if completed.get(key, {}).get("status") in ("complete", "build_filter_failed"):
                continue
            try:
                result = run_one(record, trainer, model, writer, run_id, result_root)
            except Exception as error:
                result = {"pdb_id": record["pdb_id"],
                          "occurrence_id": record["occurrence_id"],
                          "status": "runtime_failed",
                          "error": f"{type(error).__name__}: {error}"}
                status_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                status_file.flush()
                raise
            status_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            status_file.flush()
            print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    # 本轮命中请求清单, 包括原 Build 比例筛选失败, 不读取旧条件请求.
    subset_path = RESULT_ROOT / "find_hit_subset.jsonl"
    run_build([json.loads(line) for line in subset_path.read_text(encoding="utf-8").splitlines()], RESULT_ROOT)
