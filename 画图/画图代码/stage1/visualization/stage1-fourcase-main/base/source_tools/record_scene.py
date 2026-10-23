"""只读记录当前 ChimeraX 相机、模型和定位投影; 不设置任何显示参数."""
from pathlib import Path
import json
import sys
import numpy as np

dest, label = Path(sys.argv[1]), sys.argv[2]
camera = session.main_view.camera
models = [m for m in session.models.list() if len(m.id) == 1]
ligand = next(m for m in models if m.id == (4,))
points = camera.position.inverse().transform_points(ligand.atoms.scene_coords)
row = dict(camera_matrix=camera.position.matrix.tolist(), field_width=camera.field_width,
           ligand_bounds_camera=[points.min(0).tolist(), points.max(0).tolist()],
           models=[dict(id=m.id_string, visible=bool(m.display), name=m.name, position=m.position.matrix.tolist()) for m in models])
path = dest / 'scene_checks.json'
data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
data[label] = row
path.write_text(json.dumps(data, indent=2), encoding='utf-8')
