"""通过官方 localhost REST 向可见 ChimeraX 发送原生命令; 命令及错误留在应用 Log.

本工具只负责传递命令, 不调用分子或图形 API. 使用 --command 传一条命令或 --file 打开 CXC.
连接仅限 127.0.0.1, 不经系统代理. --receipt 将官方返回 JSON 保存到明确指定的运行证据位置.
"""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--command")
parser.add_argument("--file", type=Path)
parser.add_argument("--port", type=int, default=61113)
parser.add_argument("--receipt", type=Path)
args = parser.parse_args()
command = args.command if args.command is not None else f'open "{args.file.resolve().as_posix()}"'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
url = f"http://127.0.0.1:{args.port}/run?" + urllib.parse.urlencode({"command": command})
with opener.open(url, timeout=300) as response:
    data = json.load(response)
if args.receipt:
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "error": data.get("error"),
            "messages": data.get("log messages", {}),
            "values": data.get("json values"),
        },
        ensure_ascii=False,
    )[:3000]
)
assert not data.get("error"), data.get("error")
assert not data.get("log messages", {}).get("error"), data.get("log messages", {}).get("error")
assert not data.get("log messages", {}).get("bug"), data.get("log messages", {}).get("bug")
