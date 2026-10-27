"""使用仓库教程地图验收显式 level Find 和 50 姿态 Build, 输出只写服务器 tmp."""

import json
import os
from pathlib import Path

import numpy as np
import torch
from hydra.utils import instantiate
from lightning.pytorch import Trainer

from build import run_one
from find import run_find
from emap2lig.data.io.writer import LigandWriter
from emap2lig.main import load_config
import emap2lig.main as main_module
import emap2lig.data.map as map_module


if __name__ == '__main__':
    # 本次冻结源码根, 其中 examples 是官方非测试教程资产, 不读取正式 179-PDB 地图.
    project_root = Path(__file__).resolve().parents[2]
    # 每次门控单独保留, 与正式 contour_level_20261026 产物隔离.
    gate_root = Path('/storage/penghongen/tmp/emap2lig_with_level_gate') / os.environ['TASK_RUN_STAMP']
    tutorial = {'pdb_id': 'tutorial', 'emdb_id': 'EMD-30556', 'input_map': str(project_root / 'examples/emd_30556.map.gz'), 'level': 0.025, 'contour_ratio': 0.5, 'effective_threshold': 0.0125, 'metadata_path': 'official tutorial', 'metadata_sha256': 'not_applicable', 'source': 'AUTHOR'}
    original_normalize = map_module.normalize_mrc
    observed_thresholds = []
    def observe_normalize(mrc_object, **kwargs):
        """记录实际送入官方归一化的阈值, 数值计算仍由原函数完成."""
        observed_thresholds.append(kwargs.get('contour_level', 0.0))
        return original_normalize(mrc_object, **kwargs)
    map_module.normalize_mrc = observe_normalize
    try:
        rows = run_find([tutorial], gate_root / 'find')
    finally:
        map_module.normalize_mrc = original_normalize
    assert observed_thresholds == [0.0125]
    # 用已知非零概率和全零二值掩码模拟零检出, 只验真实概率的保存, 不计为模型性能测试.
    class EmptyDetector:
        def sliding_window_inference(self, input_map, **kwargs):
            return torch.full((1, len(load_config(gpu=0).detection_labels), *input_map.shape[2:]), 0.1)

        def _binarize_output(self, predicted_map):
            return torch.zeros_like(predicted_map), {'ligand': 0.2}

    original_instantiate = main_module.instantiate
    main_module.instantiate = lambda config: EmptyDetector()
    try:
        empty_root = gate_root / 'scripted_empty_find'
        empty_status, _ = main_module.detect_ligand_objects(tutorial['input_map'], empty_root, load_config(gpu=0, contour_level=0.025), emdb_id='30556')
    finally:
        main_module.instantiate = original_instantiate
    saved_probability = main_module.parse_mrc(empty_root / 'find_maps/ligand.mrc').grid_data
    saved_mask = main_module.parse_mrc(empty_root / 'find_maps/ligand_mask.mrc').grid_data
    assert empty_status == 0 and np.allclose(saved_probability, 0.1) and not saved_mask.any()
    # 使用刚由新条件 Find 生成的原生 blob, 选择满足教程 C12 身份原比例筛选的第一个输入.
    blob_root = gate_root / 'find/held_out_test_0/raw_find_outputs/tutorial/find_blobs'
    eligible = []
    for path in sorted(blob_root.glob('blob_*.npz'), key=lambda item: int(item.stem.split('_')[1])):
        with np.load(path, allow_pickle=False) as blob:
            ratio = int(np.count_nonzero(blob['instance_grid'])) / 12
        if 5 <= ratio <= 25:
            eligible.append(path)
    assert eligible, 'Tutorial Find produced no blob compatible with the gate C12 ligand.'
    blob_path = eligible[0]
    record = {'pdb_id': 'tutorial', 'occurrence_id': 0, 'blob_id': int(blob_path.stem.split('_')[1]), 'status': 'ready', 'prepared_smiles': 'CCCCCCCCCCCC', 'blob_path': str(blob_path)}
    config = load_config(gpu=0)
    model = instantiate(config.model)
    # 教程 Build 的原始科学输出, 只放本次门控目录, 不混入正式结果.
    writer = LigandWriter(output_dir=gate_root / 'build', output_format='mmcif')
    trainer = Trainer(accelerator='gpu', devices=[0], callbacks=[writer], logger=False)
    torch.cuda.reset_peak_memory_stats()
    result = run_one(record, trainer, model, writer, os.environ['TASK_RUN_STAMP'], gate_root / 'build')
    report = {'find_status': rows[0]['status'], 'observed_thresholds': observed_thresholds, 'empty_find_preserves_real_probability': True, 'build': result, 'peak_gpu_bytes': torch.cuda.max_memory_allocated()}
    assert result['status'] == 'complete' and result['generated'] == 50
    (gate_root / 'gate_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)

