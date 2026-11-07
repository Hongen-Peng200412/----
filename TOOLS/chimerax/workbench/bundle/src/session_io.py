"""另存会话/图片和临时状态报告, 输出目录只取显式部署配置.

save_output 在 output_root/<适配器给定名称>/ 建立不覆盖的 edit_NNN.cxs 或 png; CXS includeMaps true, PNG 保持原 2400×1800、supersample 3.
write_status 只允许将诊断 JSON 写入本次 temp_root; 正式显示资产与临时报告不混放.
"""

import json
from pathlib import Path
from chimerax.core.commands import run
from chimerax.core.errors import UserError


def save_output(tool, action):
    """将当前真实显示另存到部署时限定的正式输出根, 保留所有原件与已存在编号."""
    root = tool.paths["output_root"]
    folder = (root / tool.binding["output_name"]).resolve()
    if not folder.is_relative_to(root):
        raise UserError("保存子目录超出工作台正式输出根")
    folder.mkdir(parents=True, exist_ok=True)
    suffix = "cxs" if action == "save" else "png"
    index = 1
    while (folder / f"edit_{index:03}.{suffix}").exists():
        index += 1
    target = folder / f"edit_{index:03}.{suffix}"
    run(tool.session, f'save "{target.as_posix()}"' + (" includeMaps true" if action == "save" else " width 2400 height 1800 supersample 3"), log=True)
    tool.session.logger.info("已另存：" + str(target))
    return target


def write_status(tool, argument, report):
    """可选地写一个临时 JSON, 内容保持适配器给出的字段, 同时记录到 ChimeraX Log."""
    if argument:
        target = Path(argument).resolve()
        if not target.is_relative_to(tool.paths["temp_root"]):
            raise UserError("状态 JSON 只允许写入本次项目 temp 目录")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    tool.session.logger.info(json.dumps(report, ensure_ascii=False))
    return report
