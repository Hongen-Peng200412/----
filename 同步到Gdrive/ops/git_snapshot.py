"""构造独立浅 Git 快照, 不写源仓库.

Git.run 返回原始字节; capture 返回 head、branch、index、status、staged、unstaged 和 untracked.
prepare 在运行目录建立只读对象桥接, 在 cache 中增量抓取从 baseline 开始的历史及索引对象.
输出 snapshot.git 是不含 alternates、源 remote、hooks 或旧分支的独立 Git 目录.
"""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess


class Git:
    """隔离外部 Git 环境变量并执行命令; data 为 stdin 字节, file 为 stdout 二进制文件路径."""

    def __init__(self, root):
        self.root = Path(root)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")

    def run(self, *args, data=None, file=None, allowed=(0,)):
        command = ["git", "--no-optional-locks", "-c", "core.quotepath=false", "-c", "core.fsmonitor=false", *map(str, args)]
        if file is None:
            result = subprocess.run(command, cwd=self.root, env=self.env, input=data, capture_output=True)
        else:
            with Path(file).open("wb") as stream:
                result = subprocess.run(command, cwd=self.root, env=self.env, input=data, stdout=stream, stderr=subprocess.PIPE)
        if result.returncode not in allowed:
            raise RuntimeError(f"Git 失败 ({' '.join(map(str, args[:3]))}): {result.stderr.decode('utf-8', 'replace').strip()}")
        return result.stdout if file is None else b""


def capture(git):
    """读取三层逻辑状态; index 为索引文件摘要, status 使用 NUL 分隔保留特殊路径."""
    git_dir = Path(git.run("rev-parse", "--absolute-git-dir").decode().strip())
    if not (git_dir / "index").is_file():
        raise RuntimeError("源仓库没有索引文件, 请先建立正常 Git 工作区.")
    if git.run("rev-parse", "--shared-index-path").strip():
        raise RuntimeError("暂不支持 split index, 请先在母目录使用普通索引.")
    if any(git_dir.rglob("*.lock")):
        raise RuntimeError("源仓库有 Git 锁文件, 请等待 Git 操作完成后再同步.")
    diff_args = ("--no-ext-diff", "--no-textconv", "--no-color", "--no-renames", "--submodule=short")
    return {
        "head": git.run("rev-parse", "HEAD").decode().strip(),
        "branch": git.run("symbolic-ref", "-q", "--short", "HEAD", allowed=(0, 1)).decode().strip(),
        "index": hashlib.sha256((git_dir / "index").read_bytes()).hexdigest(),
        "status": git.run("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        "staged": git.run("diff", "--cached", *diff_args),
        "unstaged": git.run("diff", *diff_args),
        "untracked": git.run("ls-files", "--others", "--exclude-standard", "-z"),
    }


def prepare(source, cache, run_dir, baseline, captured):
    """增量抓取浅历史, 补齐索引 blob 并复制原索引, 返回完整独立 Git 目录.

    bridge 的 alternates 仅在 temp/ 内临时读取源对象; cache 和 snapshot.git 不保留该引用.
    HEAD 必须包含 baseline; 绕过基点的合并路径会拒绝, 防止旧历史意外进入副本.
    """
    git = Git(source)
    git.run("merge-base", "--is-ancestor", baseline, captured["head"])
    git_dir = Path(git.run("rev-parse", "--absolute-git-dir").decode().strip())
    bridge = run_dir / "bridge.git"
    git.run("init", "--bare", "--quiet", bridge)
    (bridge / "objects/info/alternates").write_text((git_dir / "objects").as_posix() + "\n", encoding="utf-8", newline="\n")
    (bridge / "shallow").write_text(baseline + "\n", encoding="ascii", newline="\n")
    bridge_git = Git(bridge)
    bridge_git.run("update-ref", "refs/heads/snapshot", captured["head"])
    bridge_git.run("symbolic-ref", "HEAD", "refs/heads/snapshot")
    visible = set(bridge_git.run("rev-list", "HEAD").splitlines())
    permitted = set(git.run("rev-list", captured["head"], "^" + baseline).splitlines()) | {baseline.encode()}
    if visible - permitted:
        raise RuntimeError("当前合并路径绕过浅历史起点, 会引入基点以前的历史; 请在包含基点的连续分支上同步.")
    if not cache.exists():
        git.run("init", "--bare", "--quiet", cache)
    cache_git = Git(cache)
    cache_git.run("fetch", "--quiet", "--no-tags", "--no-auto-maintenance", "--update-shallow", bridge, "+HEAD:refs/heads/snapshot")
    cache_git.run("symbolic-ref", "HEAD", "refs/heads/snapshot")
    object_ids = set()
    for entry in filter(None, git.run("ls-files", "--stage", "-z").split(b"\0")):
        mode, oid, stage = entry.split(b"\t", 1)[0].split()
        if mode in (b"160000", b"120000"):
            raise RuntimeError("暂不支持 Git 子模块或符号链接.")
        if oid.strip(b"0"):
            object_ids.add(oid)
    checks = cache_git.run("cat-file", "--batch-check=%(objectname) %(objecttype)", data=b"\n".join(sorted(object_ids)) + b"\n")
    missing = [line.split()[0] for line in checks.splitlines() if line.endswith(b" missing")]
    if missing:
        pack_path = run_dir / "index-objects.pack"
        git.run("pack-objects", "--stdout", data=b"\n".join(missing) + b"\n", file=pack_path)
        with pack_path.open("rb") as stream:
            result = subprocess.run(["git", "--no-optional-locks", "index-pack", "--stdin"], cwd=cache, env=cache_git.env, stdin=stream, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    shutil.copyfile(git_dir / "index", cache / "index")
    cache_git.run("repack", "-a", "-d", "--quiet")
    cache_git.run("prune", "--expire=now")
    snapshot = run_dir / "snapshot.git"
    shutil.copytree(cache, snapshot, ignore=shutil.ignore_patterns("FETCH_HEAD", "logs", "hooks", "index", "sync-owner.json"))
    target_git = Git(snapshot)
    (snapshot / "config").write_text("[core]\n\trepositoryformatversion = 0\n\tbare = true\n\tlogallrefupdates = false\n", encoding="ascii")
    for key in ("core.autocrlf", "core.filemode", "core.ignorecase", "core.symlinks", "core.safecrlf", "core.attributesfile", "core.excludesfile"):
        value = git.run("config", "--get", key, allowed=(0, 1)).decode().strip()
        if value:
            target_git.run("config", key, value)
    for name in ("exclude", "attributes"):
        original = git_dir / "info" / name
        if original.is_file():
            (snapshot / "info").mkdir(exist_ok=True)
            shutil.copyfile(original, snapshot / "info" / name)
    if captured["branch"]:
        target_git.run("update-ref", "refs/heads/" + captured["branch"], captured["head"])
        target_git.run("symbolic-ref", "HEAD", "refs/heads/" + captured["branch"])
        if captured["branch"] != "snapshot":
            target_git.run("update-ref", "-d", "refs/heads/snapshot")
    else:
        target_git.run("update-ref", "--no-deref", "HEAD", captured["head"])
        target_git.run("update-ref", "-d", "refs/heads/snapshot")
    shutil.copyfile(git_dir / "index", snapshot / "index")
    target_git.run("config", "core.bare", "false")
    if (snapshot / "objects/info/alternates").exists():
        raise RuntimeError("独立快照不能引用母目录对象.")
    return snapshot
