"""按冻结顺序运行显式推荐 level 的官方 Find.

主要入口 run_find 接收逐图输入和本条件的输出根. 每个 PDB 写出官方 preprocess、find_maps、find_blobs, 以及 status.json; held_out_test_0/reports/find_run_summary.json 保存按 PDB 顺序的状态列表. 官方模型、Li 阈值、连通域和 blob 裁剪直接来自 emap2lig.main.
"""

import json
import shutil
from pathlib import Path

from lightning import seed_everything

from emap2lig.main import detect_ligand_objects, load_config
from paths import FIND_ROOT, FROZEN_TEST, INPUT_ROOT, SOURCE_INPUTS


def run_find(map_records: list[dict], output_root: Path) -> list[dict]:
    """逐图显式传入原推荐值, 保存官方结果和本条件的输入记录.

    输入参数:
        - map_records: list[dict], 按正式清单排序的地图输入, 如 pdb_id=9ter、emdb_id=EMD-55834、level=0.011.
            - pdb_id: str, 小写 PDB 标识, 如 9ter.
            - emdb_id: str, 该原图的 EMDB 标识, 如 EMD-55834.
            - input_map: str, 原始压缩密度图的绝对路径, 不是 AdaLigand 的归一化密度.
            - level: float, 与原图同尺度的推荐 contour, 函数内部由官方代码乘 0.5.
            - contour_ratio: float, 冻结为 0.5, 用于明确本次输入条件.
            - effective_threshold: float, level * 0.5, 即归一化前实际清零阈值.
            - metadata_path: str, 原主图 EMDB 元数据的只读位置.
            - metadata_sha256: str, 核查阶段已冻结的元数据身份, 本函数不计算散列.
            - source: str, 推荐值的记录来源, 如 AUTHOR 或 EMDB.
        - output_root: Path, 本条件 Find 的父目录, 如新实验根的 find 子目录.

    返回及落盘:
        - rows: list[dict], 与已完成 PDB 顺序一致; 每个字典保留全部 map_records 字段, 并增加下面的状态字段.
            - normalization_mode: str, 固定 explicit_emdb_level, 区分旧无 level 条件.
            - output_dir: str, 当前 PDB 的官方产物目录, 包含 preprocess/unified.mrc、find_maps 和 find_blobs.
            - blobs_dir: str 或 None, 官方返回的原生 blob 目录; 失败时可为 None.
            - blob_count: int, mask_N.mrc 的实际文件数, 与保留实例一一对应.
            - status_code: int, 官方返回码, 0 表示完成.
            - status: str, ok 或 failed; 新失败写盘后停止, 不删除测试 PDB.
        - <output_root>/held_out_test_0/raw_find_outputs/<pdb>/status.json: object, 保存该 PDB 的上述字典.
        - <output_root>/held_out_test_0/reports/find_run_summary.json: list[dict], 保存本次已完成状态.
    """
    # 当前条件的 179-PDB 产物根, 不指向旧 official_find_li 目录.
    split_root = output_root / 'held_out_test_0'
    # 逐 PDB 原生地图和 blob 的写出目录.
    raw_root = split_root / 'raw_find_outputs'
    # 每完成一个 PDB 后刷新的有序状态列表.
    report_path = split_root / 'reports/find_run_summary.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    seed_everything(42)
    rows = []
    for record in map_records:
        # 当前 PDB 的独立官方输出, 可在相同冻结输入下续跑.
        sample_root = raw_root / record['pdb_id']
        # 当前 PDB 的状态文件, 只读取新条件目录内的状态.
        status_path = sample_root / 'status.json'
        if status_path.exists():
            previous = json.loads(status_path.read_text(encoding='utf-8'))
            assert previous['level'] == record['level']
            assert previous['normalization_mode'] == 'explicit_emdb_level'
            if previous['status'] == 'ok':
                rows.append(previous)
                continue
        # 显式传入原推荐值 L, 官方 get_unified_mrc 内部应用 L/2, 不在这里先除以二.
        config = load_config(gpu=0, detection_batch_size=16, contour_level=record['level'])
        status_code, blobs_dir = detect_ligand_objects(
            record['input_map'], sample_root, config,
            emdb_id=record['emdb_id'].removeprefix('EMD-'),
        )
        row = {
            **record, 'normalization_mode': 'explicit_emdb_level',
            'output_dir': str(sample_root),
            'blobs_dir': str(blobs_dir) if blobs_dir is not None else None,
            'blob_count': len(list((sample_root / 'find_blobs').glob('mask_*.mrc'))),
            'status_code': status_code, 'status': 'ok' if status_code == 0 else 'failed',
        }
        sample_root.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        rows.append(row)
        report_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if status_code != 0:
            raise RuntimeError(f"{record['pdb_id']}: official Find status={status_code}")
    report_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    return rows


if __name__ == '__main__':
    # 本次实际输入的字节副本, 供后续追溯, 不修改原测试清单或原化学资产.
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ('maps.json', 'test_0.json', 'test_1.json'):
        shutil.copyfile(SOURCE_INPUTS / name, INPUT_ROOT / name)
    shutil.copyfile(FROZEN_TEST, INPUT_ROOT / 'test.jsonl')
    run_find(json.loads((INPUT_ROOT / 'maps.json').read_text(encoding='utf-8')), FIND_ROOT)

