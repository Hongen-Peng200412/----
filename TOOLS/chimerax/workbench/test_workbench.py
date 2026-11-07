"""在本次 temp 中测试中性工具的恢复、观察与输出边界, 不读取论文科学材料或启动软件."""

from pathlib import Path
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import types


def main():
    root = Path(__file__).resolve().parents[3]
    scope = root / "temp/figure-centric/workbench-contract"
    scope.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(dir=scope))
    commands, checks = [], []
    saved_modules = dict(sys.modules)

    def run(session, command, log):
        commands.append(command)
        if command.startswith("save "):
            target = Path(re.match(r'save "([^"]+)"', command).group(1))
            target.write_bytes(b"synthetic current display")

    class ToolInstance:
        def __init__(self, session, name):
            self.session = session
        def display(self, shown):
            self.shown = shown
        def delete(self):
            self.deleted = True

    class Handler:
        def remove(self):
            pass

    modules = {
        "chimerax": {}, "chimerax.core": {},
        "chimerax.core.commands": {"run": run},
        "chimerax.core.models": {"MODEL_DISPLAY_CHANGED": "display", "REMOVE_MODELS": "remove"},
        "chimerax.core.tools": {"ToolInstance": ToolInstance},
        "chimerax.core.errors": {"UserError": ValueError},
    }
    try:
        for name, fields in modules.items():
            module = types.ModuleType(name)
            module.__dict__.update(fields)
            module.__path__ = []
            sys.modules[name] = module
        package = types.ModuleType("chimerax.ligand_workbench")
        source = Path(__file__).with_name("bundle") / "src"
        package.__path__ = [str(source)]
        sys.modules[package.__name__] = package
        spec = importlib.util.spec_from_file_location(package.__name__ + ".tool", source / "tool.py")
        tool_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = tool_module
        spec.loader.exec_module(tool_module)
        adapter = types.SimpleNamespace(
            default_config={"choice": "a"}, managed_kinds={"object"},
            bind=lambda scene: {"title": "case", "focus": [], "output_name": "case"},
            report=lambda scene, config, overrides, actual: {"config": config, "actual": actual},
            plan=lambda scene, config, overrides, actual, keys, kinds: ({key: key == "first" for key in keys}, list(keys)),
        )
        paths = {"project_root": fixture, "output_root": fixture / "author", "temp_root": fixture / "temp"}
        paths["temp_root"].mkdir()
        tool_module.load_adapter = lambda: (adapter, paths)
        logger = types.SimpleNamespace(info=lambda text: None)
        session = types.SimpleNamespace(ui=types.SimpleNamespace(is_gui=False), triggers=types.SimpleNamespace(add_handler=lambda event, callback: Handler()), logger=logger)
        models = {"first": types.SimpleNamespace(visible=True, deleted=False, id=(1, 1), id_string="1.1"), "second": types.SimpleNamespace(visible=False, deleted=False, id=(2, 1), id_string="2.1")}
        frozen = {"version": 1, "scene": {"opaque": [1, 2, 3]}, "models": models, "config": {"choice": "saved"}, "overrides": {"first": False}, "shown": False}
        tool = tool_module.LigandWorkbench.restore_snapshot(session, frozen)
        assert not commands and tool.config == frozen["config"] and tool.overrides == frozen["overrides"]
        assert tool.take_snapshot(session, None) == frozen
        assert type(tool).__module__ == "chimerax.ligand_workbench.tool"
        checks.append("v1_restore_preserves_opaque_state_and_runs_no_display_commands")
        models["second"].visible = True
        tool._observe("display", models["second"])
        assert tool.overrides == {"first": False, "second": True} and not commands
        checks.append("manual_visibility_observation_has_no_graphics_side_effect")
        tool.apply()
        assert commands == ["hide #1|#2 models", "show #1.1 models"]
        checks.append("visibility_execution_uses_only_adapter_plan")
        io = sys.modules[package.__name__ + ".session_io"]
        first = io.save_output(tool, "save")
        second = io.save_output(tool, "save")
        image = io.save_output(tool, "export")
        assert first.name == "edit_001.cxs" and second.name == "edit_002.cxs" and image.name == "edit_001.png"
        assert "includeMaps true" in commands[-2] and "width 2400 height 1800 supersample 3" in commands[-1]
        assert first.read_bytes() == second.read_bytes() == b"synthetic current display"
        checks.append("session_and_image_save_do_not_overwrite_and_use_explicit_author_root")
        io.write_status(tool, str(paths["temp_root"] / "report.json"), {"opaque": [1, 2]})
        assert json.loads((paths["temp_root"] / "report.json").read_text(encoding="utf-8")) == {"opaque": [1, 2]}
        try:
            io.write_status(tool, str(paths["output_root"] / "report.json"), {})
        except ValueError:
            pass
        else:
            raise AssertionError("status escaped temp")
        assert not (paths["output_root"] / "report.json").exists()
        checks.append("diagnostic_json_is_bounded_to_temporary_root")
        tool.binding["output_name"] = "../../escape"
        try:
            io.save_output(tool, "save")
        except ValueError:
            pass
        else:
            raise AssertionError("save escaped author root")
        tool.delete()
        assert session._ligand_workbench is None and tool.deleted
        checks.append("output_escape_rejected_and_tool_deletion_only_unregisters_handlers")
    finally:
        for name in set(sys.modules) - set(saved_modules):
            if name.startswith(("chimerax", "manuscript_figure_workbench")):
                del sys.modules[name]
        for name in modules:
            if name in saved_modules:
                sys.modules[name] = saved_modules[name]
        assert fixture.resolve().parent == scope.resolve()
        shutil.rmtree(fixture)
        if not any(scope.iterdir()):
            scope.rmdir()
    print(json.dumps({"LOCAL_CONTRACT_TESTS_OK": True, "checks": checks, "scientific_inputs": 0, "native_processes": 0, "temporary_cleanup_complete": True}))


if __name__ == "__main__":
    main()
