"""由 ChimeraX runscript 执行：加载固定编号模型，生成命名视角、预览与初始化会话。

命令：runscript "本脚本" "prepared目录" 9bjj "本次输出目录"。
必须在独立 ChimeraX 进程运行，因为该脚本初始化新场景；不在作者活动会话内执行。
全部绘图均使用下面逐条保存的原生命令。结果通过 report.json 确认，不能只看进程退出码。
"""

from pathlib import Path
import json
import os
import runpy
import sys
import traceback

from chimerax.core.commands import run


guard_active = False
if os.environ.get("FIGURE_VERIFY_ROOT"):
    # ChimeraX 的内置解释器不保证读取外部 sitecustomize，显式启用同一个文件审计。
    guard = runpy.run_path(str(Path(os.environ["FIGURE_VERIFY_ROOT"]) / "转换工具/ops/rebuild_support/sitecustomize.py"))
    guard_active = "workspace" in guard
prepared, pdb, destination = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
destination.mkdir(parents=True, exist_ok=True)
evidence = json.loads((prepared / pdb / "evidence.json").read_text(encoding="utf-8"))
selection = evidence["selection"]
assets = prepared / pdb / "assets"
models = [
    ("density.mrc", "Experimental_density_full_map"),
    ("reference_receptor.cif", "Deposited_receptor_reference"),
    ("ca2_receptor.cif", "CA2_input_receptor_optional"),
    ("ligands_all.cif", "All_deposited_ligands"),
    ("truth_all.mrc", "All_ground_truth_ligand_regions"),
    ("cryo_all.mrc", "CA2_all_retained_predictions"),
    ("emap_all.mrc", "Emap2lig_all_retained_predictions"),
    ("real_all.mrc", "GT_all_retained_predictions_optional"),
    ("ligand_target.cif", f'Target_ligand_occurrence_{selection["occurrence_id"]}'),
    ("truth_local.mrc", "Target_ground_truth_region"),
    ("cryo_local.mrc", f'CA2_local_blob_{selection["local_blobs"]["cryo"]}'),
    ("emap_local.mrc", f'Emap2lig_local_blob_{selection["local_blobs"]["emap"]}'),
    ("real_local.mrc", f'GT_local_blob_{selection["local_blobs"]["real"]}_optional'),
    ("emap_receptor_fp.mrc", f'Emap2lig_on_receptor_FP_blob_{selection["receptor_fp_blob"]}'),
    ("emap_remote_fp.mrc", f'Emap2lig_remote_FP_blob_{selection["remote_fp_blob"]}'),
    ("receptor_pocket.cif", "Deposited_receptor_pocket_atoms"),
    ("receptor_fp_neighbours.cif", "Deposited_receptor_atoms_near_FP"),
    ("emap_local_near_receptor.mrc", "Emap_local_voxel_centres_within_1p5A_of_receptor"),
]
commands = ["close all", "set bgColor white", "camera ortho", "lighting soft", "material dull",
            "graphics silhouettes false", "windowsize 1000 800"]
for index, (filename, name) in enumerate(models, start=1):
    commands.append(f'open "{(assets / filename).as_posix()}" id #{index} name "{name}"')
commands += [
    "hide models", "hide #2-4,9,16,17 atoms", "cartoon #2,3",
    "color #2,3 #9ca3ad target c", "transparency #2,3 20 target c",
    "style #4,9,16,17 stick", "color #4,9 byelement",
    "color #4,9 & C #374151", "size #4,9 stickRadius 0.17",
    "color #16,17 #7c8797", "size #16,17 stickRadius 0.13", "hide #16,17 pseudobonds", "hide #16,17 cartoons",
    f'volume #1 style mesh step 1 level {evidence["contour"]:.10g} color #b4b9bf transparency 0.75 surfaceSmoothing false',
    "volume #5-8,10-15,18 style surface level 0.5 step 1 surfaceSmoothing false",
    "volume #5,10 color #009E73 transparency 0.45",
    "volume #6,11 color #5975bd transparency 0.40",
    "volume #7,12,14,15 color #D55E00 transparency 0.40",
    "volume #8,13 color #139b9b transparency 0.40",
    "volume #18 color #b51f4b transparency 0.15",
    "show #2,5-8 models", "view #2,5-8 orient",
]
commands += [f"turn {axis} {angle}" for axis, angle in selection["global_turns"]]
commands += ["view #2,5-8 pad 0.08", "clip off", "view name global"]

# 全局三种条件严格复用同一相机与受体，不单独 fit 各种候选。
for tag, prediction in (("truth", 5), ("ca2", 6), ("emap", 7), ("gt_optional", 8)):
    commands += ["hide models", f"show #2,4,{prediction} models", "cartoon #2", "show #4 atoms", "view global",
                 "wait 2", f'save "{(destination / ("global_" + tag + ".png")).as_posix()}" width 1600 height 1280 supersample 2']
commands += ["hide models", "show #2,4,7,14,15 models", "volume #14 color #b51f4b transparency 0.1", "volume #15 color #b51f4b transparency 0.1", "wait 2",
             f'save "{(destination / "global_emap_highlights.png").as_posix()}" width 1600 height 1280 supersample 2',
             "volume #14,15 color #D55E00 transparency 0.40"]
for tag, prediction in (("ca2", 6), ("emap", 7)):
    commands += ["hide models", f"show #1,2,4,{prediction} models", "view global", "wait 2",
                 f'save "{(destination / ("global_density_" + tag + ".png")).as_posix()}" width 1600 height 1280 supersample 2']

# 局部相机包含真实区域与三种局部候选的完整范围，避免裁掉较大的 Emap blob。
commands += ["hide models", "show #9-13 models", "show #9 atoms", "view #9-13 orient"]
commands += [f"turn {axis} {angle}" for axis, angle in selection["local_turns"]]
commands += ["view #9-13 pad 0.15", "clip off", "view name local",
             "hide #2,3 cartoons"]
for tag, prediction in (("truth", 10), ("ca2", 11), ("emap", 12), ("gt_optional", 13)):
    commands += ["hide models", f"show #2,9,16,{prediction} models", "show #9,16 atoms", "view local", "wait 2",
                 f'save "{(destination / ("local_" + tag + ".png")).as_posix()}" width 1600 height 1280 supersample 2']
commands += ["hide models", "show #2,9,12,16,18 models", "wait 2",
             f'save "{(destination / "local_emap_receptor_overlap.png").as_posix()}" width 1600 height 1280 supersample 2']
commands += ["volume zone #1 nearAtoms #9 range 6 newMap false minimalBounds true"]
for tag, prediction in (("ca2", 11), ("emap", 12)):
    commands += ["hide models", f"show #1,9,16,{prediction} models", "view local", "wait 2",
                 f'save "{(destination / ("local_density_" + tag + ".png")).as_posix()}" width 1600 height 1280 supersample 2']
commands += ["volume unzone #1", "volume #1 region all"]

# 受体上误报的独立放大，两方法仍共用相机。#17 只显示误报附近的参考原子。
commands += ["hide models", "show #14,17 models", "show #17 atoms", "view #14 orient", "turn y 35", "turn x -25",
             "view #14 pad 0.30", "clip off", "view name receptor_fp"]
for tag, prediction in (("ca2", 6), ("emap", 14)):
    commands += ["hide models", f"show #17,{prediction} models", "view receptor_fp", "wait 2",
                 f'save "{(destination / ("receptor_fp_" + tag + ".png")).as_posix()}" width 1600 height 1280 supersample 2']

# 初始打开时为 CA2 全局图，其他模型和三个命名视角均留在会话中。
commands += ["hide models", "show #2,4,6 models", "cartoon #2", "view global", "clip off",
             f'save "{(destination / "initial.cxs").as_posix()}" includeMaps true']
(destination / "all_native_commands.cxc").write_text("\n".join(commands) + "\n", encoding="utf-8")
executed, views = [], {}
try:
    for command in commands:
        run(session, command)
        executed.append(command)
        if command.startswith("view name "):
            views[command.split()[-1]] = {"camera_matrix":session.main_view.camera.position.matrix.tolist(),
                                         "window_size":list(session.main_view.window_size),
                                         "pixel_size_A":float(session.main_view.pixel_size())}
    model_state = [{"id": m.id_string, "name":m.name, "display":bool(m.display)} for m in session.models.list() if len(m.id) == 1]
    report = {"success":True, "pdb":pdb, "commands":len(executed), "models":model_state, "views":views, "old_temp_read_guard":guard_active,
              "chimerax_version":__import__("chimerax.core", fromlist=["__version__"]).__version__}
except Exception:
    report = {"success":False, "pdb":pdb, "completed_commands":len(executed),
              "failed_command":commands[len(executed)], "traceback":traceback.format_exc()}
finally:
    (destination / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    run(session, f'log save "{(destination / "chimerax.html").as_posix()}"')
if not report["success"]:
    raise RuntimeError(report["traceback"])
