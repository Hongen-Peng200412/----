"""在独立 GUI ChimeraX 中逐例打开九份 initial.cxs, 只读检查参考材料和显示初值.

用官方 runscript 执行; 会替换当前窗口模型, 因而只用于独立检查窗口.
报告写仓库 temp/multiligand-workbench/qa/initial_107.json, 不覆盖个人会话或生成图片.
"""

import json
from pathlib import Path

from chimerax.core.commands import run
from chimerax.ligand_workbench.selection import DEFAULT

root = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
qa = root / "temp/multiligand-workbench/qa"
qa.mkdir(parents=True, exist_ok=True)
results = []
(qa / "initial_107.json").write_text(json.dumps({"passed": False, "cases": []}), encoding="utf-8")
for path in sorted(Path("D:/AdaLigand_Visualization").glob("*/scene.json")):
    scene = json.loads(path.read_text(encoding="utf-8"))
    run(session, "log clear")
    run(session, f'open "{(path.parent/"initial.cxs").as_posix()}"')
    tool = session._ligand_workbench
    by_id = {m.id_string: m for m in session.models.list()}
    assert tool.scene["pdb_id"] == scene["pdb_id"]
    assert tool.config == DEFAULT and tool.report()["status"] == "与预设一致"
    assert not session.main_view.clip_planes.planes()
    assert not session.main_view.lighting.depth_cue
    counts = {"reference": 0, "area": 0}
    for m in scene["models"]:
        if m["kind"] not in counts:
            continue
        model = by_id[m["id"]]
        assert model.name == m["display_name"], (scene["pdb_id"], m["key"], model.name)
        counts[m["kind"]] += 1
        if m["kind"] == "reference":
            assert model.visible
        else:
            assert not model.display
            assert model.surfaces and all(s.display and s.show_mesh for s in model.surfaces)
            assert all(
                s.level == 0.5 and tuple(s.color) == (230, 159, 0, 255) for s in model.surfaces
            )
    assert counts["area"] == counts["reference"] == scene["counts"]["all"]
    results.append({"pdb": scene["pdb_id"], **counts, "passed": True})
    (qa / "initial_107.json").write_text(
        json.dumps({"passed": len(results) == 9, "cases": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
print("INITIAL_107_PASS", len(results), sum(r["reference"] for r in results))
