"""对照服务器与本地原件的字节数/SHA-256, 核查 MRC 原值抽样, 写正式来源留证.

读取明确的 download_requests.json, 远端只读原件; 临时 SSH 输入写 repo/temp.
来源清单写 e2e/output/multiligand-workbench/source_receipt.json, 原文件及地图均不修改.
"""

import base64
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
import mrcfile

root = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
output = root / "画图/画图代码/e2e/output/multiligand-workbench"
data_root = Path("D:/AdaLigand_Visualization")
requests = json.loads((output / "download_requests.json").read_text(encoding="utf-8"))
scratch = root / "temp/multiligand-workbench/receipts"
scratch.mkdir(parents=True, exist_ok=True)
encoded = base64.b64encode(
    json.dumps(sorted({r["remote"] for r in requests}), ensure_ascii=False).encode()
).decode()
script = """/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python -B - <<'PY'
import base64,hashlib,json
from pathlib import Path
paths=json.loads(base64.b64decode('__PATHS__'))
rows=[]
for name in paths:
 p=Path(name);h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 rows.append({'source':name,'bytes':p.stat().st_size,'sha256':h.hexdigest()})
print(json.dumps(rows))
PY
""".replace(
    "__PATHS__", encoded
)
input_file = scratch / "remote_receipt.sh"
input_file.write_text(script, encoding="utf-8", newline="\n")
result = subprocess.run(
    [
        "powershell.exe",
        "-NoProfile",
        "-File",
        str(Path.home() / ".codex/tools/Invoke-ProjectSsh.ps1"),
        "-Command",
        "bash -s",
        "-InputFile",
        str(input_file),
        "-RetryCount",
        "2",
    ],
    capture_output=True,
    check=True,
)
remote = json.loads(result.stdout.decode("utf-8-sig").strip())
remote = {r["source"]: r for r in remote}
rows = []
for request in requests:
    path = data_root / request["local"]
    with path.open("rb") as f:
        sha = hashlib.file_digest(f, "sha256").hexdigest()
    item = {
        **request,
        "bytes": path.stat().st_size,
        "sha256": sha,
        "server_bytes": remote[request["remote"]]["bytes"],
        "server_sha256": remote[request["remote"]]["sha256"],
    }
    item["passed"] = item["bytes"] == item["server_bytes"] and sha == item["server_sha256"]
    rows.append(item)
catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
metadata = []
for name in catalog["evaluation_sources"]:
    p = Path(name)
    metadata.append(
        {
            "file": p.relative_to(root).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
    )
grids = []
for f in sorted(data_root.glob("*/scene.json")):
    scene = json.loads(f.read_text(encoding="utf-8"))
    folder = f.parent
    for model in scene["models"]:
        if model["kind"] != "density":
            continue
        source = np.load(folder / "source" / (model["key"] + ".npy"), mmap_mode="r").squeeze()
        with mrcfile.mmap(folder / model["file"], permissive=True) as target:
            assert tuple(target.data.shape) == source.shape
            assert np.array_equal(target.data[::7, ::9, ::11], source[::7, ::9, ::11])
            assert np.allclose(target.header.origin.tolist(), model["origin_xyz_A"], atol=2e-5)
        grids.append(
            {
                "pdb": scene["pdb_id"],
                "model": model["key"],
                "shape_zyx": list(source.shape),
                "sample_values_equal": True,
                "origin_matches": True,
            }
        )
receipt = {
    "passed": all(r["passed"] for r in rows),
    "files": rows,
    "evaluation_metadata": metadata,
    "map_checks": grids,
}
(output / "source_receipt.json").write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("source files", len(rows), "matched", sum(r["passed"] for r in rows), "map checks", len(grids))
assert receipt["passed"]
