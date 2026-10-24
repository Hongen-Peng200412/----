"""在一个可见 ChimeraX 窗口中逐例建立全部材料, 执行官方 CXC 并保存会话与图片.

先运行 prepare_assets.py、prepare_views.py, 并在 ChimeraX 输入
remotecontrol rest start port 61113 json true log true。
本文件仅传递官方命令, 不调用图形、地图或分子操作 API. 日常编辑不用运行此文件.
命令日志、逐视图实际显隐和会话写入本例目录; 失败即停止, 不采用旧图替代.
"""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


def native(command, opener, port):
    """向本机官方 REST 服务传命令; 原生错误也包括 CXC 内部逐条执行产生的错误."""
    if "session" in globals():
        from chimerax.core.commands import run

        # 原生完整重建进程直接逐条执行同一份官方命令; 不调用地图或分子修改 API.
        if command.startswith('open "') and command.endswith('.cxc"'):
            for line in Path(command[6:-1]).read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.lstrip().startswith("#"):
                    run(session, line, log=True)
        else:
            run(session, command, log=True)
        return {}
    url = f"http://127.0.0.1:{port}/run?" + urllib.parse.urlencode({"command": command})
    with opener.open(url, timeout=900) as response:
        result = json.load(response)
    errors = result.get("log messages", {}).get("error", [])
    bugs = result.get("log messages", {}).get("bug", [])
    if result.get("error") or errors or bugs:
        raise RuntimeError(
            json.dumps(
                {"command": command, "error": result.get("error"), "messages": errors, "bugs": bugs},
                ensure_ascii=False,
            )
        )
    return result


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
parser.add_argument("--pdb", nargs="+")
parser.add_argument("--port", type=int, default=61113)
parser.add_argument("--width", type=int, default=1800)
parser.add_argument("--height", type=int, default=1400)
parser.add_argument("--supersample", type=int, default=2)
args = parser.parse_args()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
index = json.loads((args.data_root / "view_index.json").read_text(encoding="utf-8"))
pdbs = list(dict.fromkeys(r["pdb"] for r in index))
receipt = []
for pdb in pdbs:
    if args.pdb and pdb not in args.pdb:
        continue
    folder = (args.data_root / pdb).resolve()
    scene = json.loads((folder / "scene.json").read_text(encoding="utf-8"))
    print(pdb, "loading", len(scene["models"]), "materials", flush=True)
    native("log clear", opener, args.port)
    native(f'open "{(folder / "load.cxc").as_posix()}"', opener, args.port)
    native(
        f'ui tool hide "Volume Viewer"; log save "{(folder / "exports/load_commands.html").as_posix()}"',
        opener,
        args.port,
    )
    for row in (r for r in index if r["pdb"] == pdb):
        name = row["view"]
        cxc = folder / "views" / (name + ".cxc")
        image = folder / "exports" / (name + ".png")
        session_file = folder / "views" / (name + ".cxs")
        state = folder / "exports" / (name + ".status.json")
        native("log clear", opener, args.port)
        native(f'open "{cxc.as_posix()}"', opener, args.port)
        native(
            f'save "{image.as_posix()}" width {args.width} height {args.height} supersample {args.supersample}',
            opener,
            args.port,
        )
        native(
            f'ligwork status "{state.as_posix()}"; view matrix; log save "{(folder / "exports" / (name + ".commands.html")).as_posix()}"; log clear; ui tool hide "Volume Viewer"; save "{session_file.as_posix()}" includeMaps false',
            opener,
            args.port,
        )
        actual = json.loads(state.read_text(encoding="utf-8"))
        # 局部图只允许登记的完整流水线 top-1 构象, 没有合法构象时只显示参考与密度.
        if "occurrence_id" in row:
            pose_ids = [
                m["id"] for m in scene["models"] if m["kind"] == "pose" and m["key"] in actual["visible"]
            ]
            assert pose_ids == ([row["prediction_model"]] if row["prediction_model"] else []), (
                pdb,
                name,
                pose_ids,
            )
        else:
            assert actual["status"] == "与预设一致", (pdb, name, actual)
        assert image.stat().st_size > 10000 and session_file.stat().st_size > 10000
        receipt.append(
            {
                **row,
                "session": str(session_file),
                "actual_status": actual["status"],
                "width": args.width,
                "height": args.height,
                "supersample": args.supersample,
                "materials": len(scene["models"]),
            }
        )
        print(pdb, name, "saved", flush=True)
    native(f'open "{(folder / "views/CA2_find_match.cxc").as_posix()}"', opener, args.port)
    native(
        f'ligwork show; log clear; ui tool hide "Volume Viewer"; save "{(folder / "initial.cxs").as_posix()}" includeMaps false',
        opener,
        args.port,
    )
    (args.data_root / "render_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
print("NATIVE_RENDER_PASS", len(receipt), "views", flush=True)
