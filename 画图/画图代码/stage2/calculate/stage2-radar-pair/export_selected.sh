python3 - <<'PY'
import hashlib
import json
from pathlib import Path

result = {}
for model in ['strongest-1', 'density_only-106', 'density_only-0', 'pocket_only-0']:
    path = Path('/storage/penghongen/Matcher/evaluation/final_smiles') / model / 'frozen_test.json'
    raw = path.read_bytes()
    obj = json.loads(raw)
    item = {'source': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
            'threshold_source': obj['foreground_threshold_source'], 'conditions': {}}
    for condition in ['real_receptor', 'cryoatom2_receptor']:
        rows = []
        for pdb_id, candidates in obj['predictions'][condition].items():
            for candidate in candidates:
                if not candidate['candidate_selected']:
                    continue
                row = {key: candidate[key] for key in ['centered_box_index', 'source_blob_index',
                       'foreground_probability', 'foreground_target', 'identity_supported',
                       'matched_occurrence_id', 'target_category']}
                row['pdb_id'] = pdb_id
                row['identity_correct'] = candidate['predicted_smiles'] == candidate['target_smiles']
                rows.append(row)
        item['conditions'][condition] = {'metrics': obj['metrics'][condition], 'rows': rows}
    result[model] = item
print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
PY
