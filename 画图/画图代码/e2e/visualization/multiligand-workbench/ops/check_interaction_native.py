"""在独立 --nogui ChimeraX 中检查显隐规则与 CXS 恢复; 全部改变通过官方命令完成.

由 ChimeraX runscript 注入 session. 本检查不替代解锁后的可见面板、字体与最终图片检查.
"""

import json
from pathlib import Path
from chimerax.core.commands import run

project = Path(r"C:/Users/15919/Desktop/论文草稿")
qa = project / "temp/multiligand-workbench/qa"
qa.mkdir(parents=True, exist_ok=True)
checks = []
for line in (
    Path("D:/AdaLigand_Visualization/9bjj/load.cxc").read_text(encoding="utf-8").splitlines()
):
    if not session.ui.is_gui and line.startswith(
        ("windowsize ", "label ", "camera ", "graphics ", "lighting ")
    ):
        continue
    run(session, line, log=False)
tool = session._ligand_workbench
initial_camera = session.main_view.camera.position.matrix.copy()
assert tool.report()["status"] == "与预设一致"
checks.append("initial_selection")
by_id = {m.id: m for m in session.models.list()}
for m in tool.scene["models"]:
    if m["kind"] in ["reference", "area"]:
        model = by_id[tuple(int(x) for x in m["id"].split("."))]
        assert model.name == m["display_name"]
        if m["kind"] == "area":
            assert not model.display
            assert model.surfaces and all(s.display and s.show_mesh for s in model.surfaces)
            assert all(
                s.level == 0.5 and tuple(s.color) == (230, 159, 0, 255) for s in model.surfaces
            )
assert not session.main_view.clip_planes.planes()
assert not session.main_view.lighting.depth_cue
run(session, "show #!4.1 models")
assert by_id[(4, 1)].visible and by_id[(4, 1, 1)].visible
run(session, "hide #!4.1 models; hide #!4 models")
checks.append("reference_names_orange_mesh_prepared_for_parent_only_checkbox")
for view in ["find_all", "find_small", "find_match", "find_build", "pipeline"]:
    run(session, "ligwork view " + view)
    assert all(by_id[(3, o["candidate_id"] + 1)].visible for o in tool.scene["occurrences"])
    if view in ["find_all", "find_small", "find_match"]:
        assert not any("_pose_" in key for key in tool.report()["visible"])
    if view == "find_build":
        assert {key for key in tool.report()["visible"] if "_blob_" in key} == {
            f"CA2_blob_{i}" for i in range(11)
        }
run(session, "ligwork home")
checks.append("five_modes_preserve_GT_references_and_budget_includes_false_positive")
run(session, "hide #10.1 models")
assert "CA2_blob_0" in tool.report()["hidden"]
run(session, "ligwork filter foreground")
assert "CA2_blob_10" not in tool.report()["visible"]
run(session, "ligwork filter all")
assert "CA2_blob_0" not in tool.report()["visible"]
assert "CA2_blob_10" in tool.report()["visible"]
checks.append("manual_A_hidden_filter_B_clear_A_stays_hidden_B_returns")
run(session, "color #10.1 blue; zoom 1.1")
assert tool.report()["status"] == "含手动显隐调整"
before_color = tool.models["CA2_blob_0"].surfaces[0].color.copy()
run(session, "ligwork reset")
assert tool.report()["status"] == "与预设一致"
assert (tool.models["CA2_blob_0"].surfaces[0].color == before_color).all()
checks.append("appearance_preserved_on_reset")
run(session, "hide #10 models")
assert tool.report()["status"] == "含手动显隐调整"
run(session, "show #10 models")
assert tool.report()["status"] == "与预设一致"
checks.append("parent_group_visibility")
run(session, "ligwork view pipeline; ligwork condition GT; ligwork budget 100")
assert sum("_pose_" in k for k in tool.report()["visible"]) == 10
run(session, "ligwork view find_build")
assert sum("_pose_" in k for k in tool.report()["visible"]) == 11
checks.append("given_identity_and_actual_pipeline_are_distinct")
run(session, "ligwork pose both")
assert sum("_pose_" in k for k in tool.report()["visible"]) == 22
run(session, "ligwork pose best")
assert sum("_pose_" in k for k in tool.report()["visible"]) == 11
checks.append("pose_selection")
run(session, "hide #11.1 models; show #21.1.1.1 models; ligwork pose best")
assert not any(k.endswith("_top1") for k in tool.report()["visible"])
assert "GT_blob_0" not in tool.report()["visible"]
checks.append("pose_switch_clears_pose_overrides_and_preserves_blob_hiding")
run(
    session,
    "ligwork view find_match; ligwork condition CA2; ligwork budget 100; ligwork labels identity on",
)
run(session, "hide #10.1 models")
run(session, "ligwork labels identity off; ligwork labels identity on")
assert "CA2_blob_0" not in tool.report()["visible"]
assert "CA2_identity_0" not in tool.report()["visible"]
checks.append("labels_never_reveal_manually_hidden_blob")
run(session, "ligwork pocket 16; color #3.17 blue; volume #2.1 level 0.0253; turn y 17; zoom 0.8")
assert not session.main_view.clip_planes.planes()
checks.append("pocket_does_not_add_clip_planes")
camera_before = session.main_view.camera.position.matrix.copy()
from chimerax.map import Volume

map_before = next(m for m in session.models.list() if m.id == (2, 1))
region_before = map_before.region
levels_before = [s.level for s in map_before.surfaces]
if session.ui.is_gui:
    run(session, f'save "{(qa/"gui_before.png").as_posix()}" width 900 height 700 supersample 1')
saved = tool.report()
if session.ui.is_gui:
    assert tool.tool_window.shown
snapshot = tool.take_snapshot(session, None)
snapshot["config"] = dict(snapshot["config"])
snapshot["overrides"] = dict(snapshot["overrides"])
model_ids = {k: m.id for k, m in tool.models.items()}
run(session, f'save "{(qa/"headless_edited.cxs").as_posix()}" includeMaps false')
run(session, "ligwork budget 200")
assert tool.report()["status"] == "与预设一致"
run(session, f'open "{(qa/"headless_edited.cxs").as_posix()}"')
if not session.ui.is_gui:
    # 官方会话加载器在 --nogui 中有意跳过所有 ToolInstance. 单独检查恢复处理器, GUI 自动恢复另验.
    from chimerax.ligand_workbench.tool import LigandWorkbench

    by_id = {m.id: m for m in session.models.list()}
    snapshot["models"] = {k: by_id[i] for k, i in model_ids.items()}
    LigandWorkbench.restore_snapshot(session, snapshot)
restored = session._ligand_workbench.report()
if session.ui.is_gui:
    assert session._ligand_workbench.tool_window.shown
for key in ["config", "visible", "status", "manual_overrides"]:
    assert saved[key] == restored[key], key
assert (session.main_view.camera.position.matrix == camera_before).all()
map_after = next(m for m in session.models.list() if m.id == (2, 1))
assert map_after.region == region_before
assert [s.level for s in map_after.surfaces] == levels_before
if session.ui.is_gui:
    run(session, f'save "{(qa/"gui_after.png").as_posix()}" width 900 height 700 supersample 1')
checks.append(
    "cxs_model_visibility_and_tool_snapshot_handler"
    if not session.ui.is_gui
    else "save_restore_configuration_actual_visibility_manual_overrides"
)
run(session, "ligwork pocket 16")
run(session, "ligwork unzone")
checks.append("pocket_and_unzone_commands")
run(session, "hide #3 models; ligwork home")
assert (
    tool is not session._ligand_workbench
    or session._ligand_workbench.config["view"] == "find_match"
)
current = session._ligand_workbench
assert current.report()["status"] == "与预设一致"
assert (
    current.config["view"] == "find_match"
    and current.config["condition"] == "CA2"
    and current.config["budget"] == "100"
)
assert (session.main_view.camera.position.matrix == initial_camera).all()
by_id = {m.id: m for m in session.models.list()}
assert by_id[(1, 2)].visible and not by_id[(1, 1)].visible
assert all(by_id[(3, o["candidate_id"] + 1)].visible for o in current.scene["occurrences"])
assert not by_id[(2, 1)].visible
assert [s.level for s in map_after.surfaces] == levels_before
checks.append(
    "home_restores_initial_camera_CA2_reference_and_prediction_visibility_preserving_map_threshold"
)
for action in ["focus 0", "pocket 16", "overview", "home"]:
    run(session, "ligwork " + action)
    assert not session.main_view.clip_planes.planes(), action
area_model = next(m for m in session.models.list() if m.id == (4, 1))
assert not area_model.display and all(s.display and s.show_mesh for s in area_model.surfaces)
run(session, "show #!4.1 models")
assert area_model.visible and all(s.visible for s in area_model.surfaces)
checks.append("home_keeps_region_ready_and_all_view_buttons_clear_clipping")
# 模拟旧会话的名称与两层关闭状态, 加上作者的配色、显隐、相机及局部密度修改.
run(
    session,
    'rename #3.1 "ref_0"; rename #4.1 "area_0"; hide #4 models; color #3 red; color #4 yellow; hide #10.1 models; hide #1 models; view #3.17; turn y 13; zoom 0.8; lighting depthCue true',
)
current = session._ligand_workbench
edited_report = current.report()
edited_camera = session.main_view.camera.position.matrix.copy()
edited_width = session.main_view.camera.field_width
edited_reference_colors = {
    m.id: m.atoms.colors.copy()
    for m in session.models.list()
    if m.id[0] == 3 and hasattr(m, "atoms")
}
edited_area_color = area_model.surfaces[0].color.copy()
run(session, "ligwork upgrade")
assert current.report() == edited_report
assert (session.main_view.camera.position.matrix == edited_camera).all()
assert session.main_view.camera.field_width == edited_width
assert (area_model.surfaces[0].color == edited_area_color).all()
assert not area_model.display and all(s.display for s in area_model.surfaces)
assert area_model.name == "area_0_ATP_A901"
assert not session.main_view.clip_planes.planes() and not session.main_view.lighting.depth_cue
for m in session.models.list():
    if m.id in edited_reference_colors:
        assert (m.atoms.colors == edited_reference_colors[m.id]).all()
checks.append(
    "upgrade_preserves_manual_colors_camera_config_visibility_and_prepares_hidden_surface"
)
run(session, f'save "{(qa/"upgraded_107.cxs").as_posix()}" includeMaps false')
if session.ui.is_gui:
    run(session, f'open "{(qa/"upgraded_107.cxs").as_posix()}"')
    assert session._ligand_workbench.report() == edited_report
    assert (session.main_view.camera.position.matrix == edited_camera).all()
    assert not session.main_view.clip_planes.planes() and not session.main_view.lighting.depth_cue
    checks.append("upgraded_cxs_restores_configuration_camera_and_no_fog_or_clip")
run(session, "ligwork home")
mode = "gui" if session.ui.is_gui else "headless"
(qa / f"interaction_{mode}.json").write_text(
    json.dumps(
        {
            "passed": True,
            "checks": checks,
            "restored": restored,
            "scope": "official commands, model state, camera, map region/threshold; pixel comparison is separate",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("WORKBENCH_" + mode.upper() + "_PASS", len(checks))
