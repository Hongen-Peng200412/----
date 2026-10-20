"""一键同步运维入口: 文件单向镜像、浅 Git 快照及固定 AI 报告.

main 解析路径和清理开关; execute 完成准备、源状态复核、发布、副本核对和报告更新.
temp/gdrive-sync/<目标摘要>/state.json 记录托管文件清单; cache.git 增量保存浅历史.
副本 temp/AI-Git/ 固定保存 PDF、Markdown、Git状态.json 和 Gemini提示词.md.
"""

import argparse
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import json
import msvcrt
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import uuid

from git_snapshot import Git, capture, prepare
from ai_report import build


def plain_path(path):
    """拒绝链接、联接和云端占位重解析点, 在路径尚未存在时检查最近的已有祖先."""
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.exists() and part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f"请使用普通本地路径, 不支持重解析点: {part}")
    return path


def child(root, relative):
    """将正斜线相对路径约束在 root 内; 清单和源路径都经过此边界检查."""
    parsed = PurePosixPath(relative)
    if not relative or parsed.is_absolute() or ":" in relative or "\\" in relative or any(p in (".", "..") for p in relative.split("/")):
        raise RuntimeError(f"无效相对路径: {relative}")
    path = plain_path(root / parsed)
    if not path.is_relative_to(root):
        raise RuntimeError(f"路径越界: {path}")
    return path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def remove_tree(path, owner_root):
    """仅清除已验证位于指定运行根内的运维目录, 不跟随链接."""
    path, owner_root = plain_path(path), plain_path(owner_root)
    if path == owner_root or not path.is_relative_to(owner_root):
        raise RuntimeError(f"拒绝递归清除边界外目录: {path}")
    for walk_root, directories, files in os.walk(path):
        for name in directories + files:
            plain_path(Path(walk_root) / name)
    def writable_delete(function, filename, error):
        os.chmod(filename, stat.S_IWRITE)
        function(filename)
    if path.exists():
        shutil.rmtree(path, onerror=writable_delete)


def put(source, target, run_dir, backup_relative):
    """按内容增量替换目标, 用独立暂存文件拆开潜在硬链接; 可选备份旧目标."""
    plain_path(target)
    if target.is_file() and digest(source) == digest(target):
        return False
    if target.exists() and not target.is_file():
        raise RuntimeError(f"同名目标不是普通文件: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = run_dir / ("publish-" + uuid.uuid4().hex)
    shutil.copyfile(source, pending)
    if backup_relative and target.exists():
        backup = child(run_dir / "replaced", backup_relative)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, backup)
    os.replace(pending, target)
    return True


def ignore_literal(name):
    return "/" + "".join("\\" + c if c in "\\!#[]*? " else c for c in name)


def execute(source, destination, baseline, clean, dry_run, state_dir, run_dir):
    """先准备完整快照并复核源状态, 再更新副本并验证, 最后发布同一 snapshot_id 的报告."""
    git = Git(source)
    if Path(git.run("rev-parse", "--show-toplevel").decode().strip()) != source:
        raise RuntimeError("源路径必须是 Git 工作区根目录.")
    initial = capture(git)
    # 提交起点和路径先验证, 避免在错误分支上修改副本.
    git.run("merge-base", "--is-ancestor", baseline, initial["head"])
    reserved = {".git", ".tmp.driveupload", ".tmp.drivedownload"}
    tracked = {raw.decode("utf-8") for raw in git.run("ls-files", "--cached", "-z").split(b"\0") if raw}
    untracked = {raw.decode("utf-8") for raw in initial["untracked"].split(b"\0") if raw}
    files, hashes, updates = [], {}, []
    for name in sorted(tracked | untracked):
        parts = PurePosixPath(name).parts
        if parts[0] == "temp" or reserved.intersection(parts):
            if name in tracked:
                raise RuntimeError(f"Git 已跟踪保留路径, 无法保持隔离: {name}")
            raise RuntimeError(f"源状态含运行或 Drive 内部文件, 请先在 .gitignore 排除: {name}")
        origin, target = child(source, name), child(destination, name)
        if origin.is_dir():
            raise RuntimeError(f"不支持子模块或目录索引项: {name}")
        if not origin.exists():
            continue
        files.append(name)
        hashes[name] = digest(origin)
        if not target.is_file() or digest(target) != hashes[name]:
            updates.append(name)
            print(f"[更新] {name}")
            if not dry_run:
                staged = child(run_dir / "staged", name)
                staged.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin, staged)
                if digest(staged) != hashes[name]:
                    raise RuntimeError(f"复制时源文件发生变化: {name}")
    state_path = state_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8-sig")) if state_path.exists() else {"source": str(source), "destination": str(destination), "files": []}
    if state["source"].lower() != str(source).lower() or state["destination"].lower() != str(destination).lower():
        raise RuntimeError("状态清单路径不匹配.")
    if state.get("baseline", baseline) != baseline:
        raise RuntimeError("不能自动更换已有副本的浅历史起点.")
    removed = sorted(set(state["files"]) - set(files))
    for name in removed:
        if PurePosixPath(name).parts[0] in (".git", "temp"):
            raise RuntimeError("旧状态含保留目录.")
        child(destination, name)
        print(f"[移出副本] {name}")
    print(f"文件 {len(files)}, 更新 {len(updates)}, 无变化 {len(files) - len(updates)}, 移出清单 {len(removed)}.")
    if dry_run:
        print("预览完成, 副本、Git 缓存和报告未修改.")
        return

    metadata = destination / ".git"
    owner_path = metadata / "sync-owner.json"
    if metadata.exists():
        plain_path(metadata)
        if not owner_path.is_file():
            raise RuntimeError("副本已有未经本工具管理的 .git, 不会覆盖.")
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        if owner != {"source": str(source), "baseline": baseline}:
            raise RuntimeError("副本 Git 所属源目录或起点不匹配.")
    report_root = child(destination, "temp/AI-Git")
    marker = report_root / ".sync-report-owner.json"
    if report_root.exists() and any(report_root.iterdir()):
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8"))["source"] != str(source):
            raise RuntimeError("报告固定目录已有非本工具文件, 不会接管或清除.")

    print("准备独立浅 Git 快照 (首次需要复制当前提交的对象)...", flush=True)
    snapshot = prepare(source, state_dir / "cache.git", run_dir, baseline, initial)
    # 先检查 snapshot 对源工作区的解释, 确认缺失 staged 对象、行尾配置等不会改变三层含义.
    check = Git(source)
    for key, args in (("staged", ("diff", "--cached")), ("unstaged", ("diff",))):
        actual = check.run("--git-dir=" + str(snapshot), "--work-tree=" + str(source), *args, "--no-ext-diff", "--no-textconv", "--no-color", "--no-renames", "--submodule=short")
        if actual != initial[key]:
            raise RuntimeError(f"准备的浅快照未保留 {key} 状态.")
    if capture(git) != initial or any(digest(child(source, name)) != value for name, value in hashes.items()):
        raise RuntimeError("准备期间母目录状态发生变化, 请保存并暂停 Git 操作后重新同步.")
    snapshot_id = run_dir.name
    reports = build(source, run_dir, baseline, initial, snapshot_id, Path(__file__).parents[1] / "Gemini提示词.md")
    if capture(git) != initial or any(digest(child(source, name)) != value for name, value in hashes.items()):
        raise RuntimeError("生成报告期间母目录状态发生变化, 请重新同步.")

    destination.mkdir(parents=True, exist_ok=True)
    for name in updates:
        put(child(run_dir / "staged", name), child(destination, name), run_dir, name)
    for name in removed:
        target = child(destination, name)
        if target.exists():
            if not target.is_file():
                raise RuntimeError(f"待移出路径已变为目录: {target}")
            backup = child(run_dir / "removed", name)
            backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(target, backup)

    metadata.mkdir(exist_ok=True)
    pending_owner = run_dir / "sync-owner.json"
    pending_owner.write_text(json.dumps({"source": str(source), "baseline": baseline}, ensure_ascii=False), encoding="utf-8")
    put(pending_owner, owner_path, run_dir, None)
    exclude_path = snapshot / "info/exclude"
    exclude_path.parent.mkdir(exist_ok=True)
    excludes = exclude_path.read_bytes() if exclude_path.exists() else b""
    excludes += b"\n/temp/AI-Git/\n.tmp.driveupload/\n.tmp.drivedownload/\n"
    # 保留副本额外文件, 但让其不污染与母目录对齐的 untracked 状态.
    for walk_root, directories, names in os.walk(destination):
        directories[:] = [name for name in directories if name not in reserved and not (Path(walk_root) == destination and name == "temp")]
        for name in names:
            target = plain_path(Path(walk_root) / name)
            relative = target.relative_to(destination).as_posix()
            if relative not in files and relative not in tracked:
                excludes += (ignore_literal(relative) + "\n").encode("utf-8")
    exclude_path.write_bytes(excludes)
    expected = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file()}
    for name in sorted(expected):
        put(child(snapshot, name), child(metadata, name), run_dir, None)
    for path in list(metadata.rglob("*")):
        if path.is_file() and path.name != "sync-owner.json" and path.relative_to(metadata).as_posix() not in expected:
            plain_path(path).unlink()
    result = capture(Git(destination))
    if result != initial:
        differences = [key for key in initial if result[key] != initial[key]]
        raise RuntimeError(f"副本 Git 状态与母目录不一致: {differences}. 本轮不发布新报告.")
    if capture(git) != initial or any(digest(child(destination, name)) != value for name, value in hashes.items()):
        raise RuntimeError("发布期间源状态或副本内容变化, 请重新同步.")

    report_root.mkdir(parents=True, exist_ok=True)
    report_names = [p.name for p in reports.iterdir()]
    history = report_root / "history"
    if not clean and marker.exists():
        old_metadata = json.loads((report_root / "Git状态.json").read_text(encoding="utf-8"))
        archive = child(history, old_metadata["snapshot_id"])
        archive.mkdir(parents=True, exist_ok=True)
        for name in report_names:
            existing = child(report_root, name)
            if existing.exists():
                put(existing, child(archive, name), run_dir, None)
    for name in report_names:
        put(child(reports, name), child(report_root, name), run_dir, None)
    pending_marker = run_dir / "report-owner.json"
    pending_marker.write_text(json.dumps({"source": str(source), "files": report_names}, ensure_ascii=False), encoding="utf-8")
    put(pending_marker, marker, run_dir, None)
    if clean and history.exists():
        remove_tree(history, report_root)
    new_state = {"version": 2, "source": str(source), "destination": str(destination), "baseline": baseline, "files": files, "snapshot_id": snapshot_id}
    pending = run_dir / "state.json"
    pending.write_text(json.dumps(new_state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(pending, state_path)
    # 不累积运行副本、桥接仓库、PDF 或 pack; 日志与用户文件备份仍保留.
    for path in run_dir.iterdir():
        if path.is_dir() and path.name not in ("replaced", "removed"):
            remove_tree(path, state_dir)
        elif path.is_file() and path.suffix == ".pack":
            path.unlink()
    if clean:
        for old_run in state_dir.glob("run-*"):
            if old_run != run_dir and old_run.is_dir():
                for name in ("reports", "snapshot.git", "bridge.git", "staged"):
                    remove_tree(old_run / name, state_dir)
                old_pack = old_run / "index-objects.pack"
                if old_pack.exists():
                    plain_path(old_pack).unlink()
    print(f"同步成功: HEAD {initial['head']}, Git 三层状态一致.")
    print(f"固定报告: {report_root / '当前Git改动报告.pdf'}")
    print("云端上传进度请查看 Google Drive 桌面版.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--clean-old-reports", type=int, choices=(0, 1), default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    source, destination = plain_path(args.source), plain_path(args.destination)
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        parser.error("源目录和副本目录必须分离, 不能互相包含.")
    if source.drive.lower() != destination.drive.lower():
        parser.error("源目录和副本必须同盘.")
    state_key = hashlib.sha256(str(destination).lower().encode()).hexdigest()[:16].upper()
    state_dir = plain_path(source / "temp/gdrive-sync" / state_key)
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "sync.lock"
    with lock_path.open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print("同一副本已有同步进程运行, 请等待.")
            return 1
        run_dir = state_dir / (datetime.now().strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        run_dir.mkdir()
        with (run_dir / "sync.log").open("w", encoding="utf-8") as log:
            class Tee:
                def write(self, text):
                    sys.__stdout__.write(text)
                    log.write(text)
                def flush(self):
                    sys.__stdout__.flush()
                    log.flush()
            with redirect_stdout(Tee()):
                print(f"源目录: {source}\n副本目录: {destination}\n运行日志: {run_dir / 'sync.log'}")
                try:
                    execute(source, destination, args.baseline, bool(args.clean_old_reports), args.dry_run, state_dir, run_dir)
                except Exception as error:
                    print(f"同步失败: {error}\n本轮不视为成功; 请处理问题后重试. 母目录 Git 未被回写.")
                    return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
