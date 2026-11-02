"""摘录9BJJ原Top-1 RMSD的范围, 不重新计算姿态或评价.

输入为author_9bjj/performance_source.json中原11个输出及冻结完成数.
首个命令参数指定本次摘要JSON输出位置. 背景构象的原RMSD为null,
不纳入有参考RMSD的十实例范围, 仍计入实际输出数.
"""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = json.loads((root / 'output/actual-small-molecule-cases/author_9bjj/performance_source.json').read_text(encoding='utf-8'))
values = [pose['rmsd_A'] for pose in source['poses'] if pose['rmsd_A'] is not None]
summary = {'original_success_count': source['expected']['success_count'], 'original_target_count': source['expected']['target_count'], 'attempt_budget': source['expected']['attempt_budget'], 'returned_pose_count': len(source['poses']), 'reference_pose_count': len(values), 'min_top1_rmsd_A': min(values), 'max_top1_rmsd_A': max(values), 'display_range_A': f'{min(values):.2f}–{max(values):.2f}'}
summary.update({'eligible_identity_counts': source['eligible_identity_counts'], 'recovered_identity_counts': source['recovered_identity_counts'], 'sub_angstrom_count': sum(value < 1.0 for value in values)})
output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
