"""读取明确指定的服务器科学原件, 为当前图表提供统一供应入口.

SourceStore.read_bytes/json/npz返回原件或内存解析结果. local_file为需要本地路径的原生程序供应逐字节相同的原件, 只在D:/AdaLigand_Visualization/server保留缓存. 下载中间文件写入调用者指定的本次temp构建目录. reads记录本次实际读取的服务器路径、SHA256和大小, 由调用者写入正式绘图说明或本次验收记录.
"""

from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import tarfile

from TOOLS.runtime.paths import configure_runtime

configure_runtime(Path(__file__).resolve().parents[2])

import numpy as np
import paramiko


class SourceStore:
    """通过本机已知主机密钥读取服务器, 不修改服务器科学文件.

    build: Path, 项目temp中的本次构建目录. cache: Path, 固定为D:/AdaLigand_Visualization/server. 连接使用本机统一SSH入口相同的主机、端口和账号; 密码从CODEX_SSH_PASSWORD或用户私有凭据文件读取, 不写入产物或日志.
    """

    def __init__(self, build: Path, cache: Path):
        self.build = Path(build).resolve()
        self.cache = Path(cache).resolve()
        if self.cache != Path("D:/AdaLigand_Visualization/server").resolve():
            raise ValueError("原样科学缓存仅使用D:/AdaLigand_Visualization/server")
        self.client = paramiko.SSHClient()
        self.client.load_host_keys(str(Path.home() / ".ssh/known_hosts"))
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        password = os.environ.get("CODEX_SSH_PASSWORD")
        if not password:
            password = (
                (Path.home() / ".ssh/pocket_plus_sshpass.txt")
                .read_text(encoding="utf-8-sig")
                .rstrip("\r\n")
            )
        self.client.connect(
            "10.102.33.220",
            port=10022,
            username="penghongen",
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=20,
            banner_timeout=30,
            auth_timeout=30,
        )
        self.client.get_transport().set_keepalive(20)
        self.sftp = self.client.open_sftp()
        self.sftp.get_channel().settimeout(120)
        self.reads = []
        self._batch = {}

    def read_bytes(self, remote: str, expected_sha256: str = "") -> bytes:
        """读取服务器绝对路径原件, 可比对指定实验版本的SHA256."""
        if remote in self._batch:
            raw = self._batch.pop(remote)
        elif self.sftp.stat(remote).st_size <= 1024 * 1024:
            # 小文件至多32个32KiB预取请求, 复用同一SFTP通道而不积压大文件请求.
            with self.sftp.open(remote, "rb") as handle:
                handle.prefetch()
                raw = b"".join(iter(lambda: handle.read(1024 * 1024), b""))
        else:
            # 大原件按SSH流顺序读取, 避免旧Paramiko的无界SFTP预取及平方级字节拼接.
            _, stdout, stderr = self.client.exec_command(
                "cat -- " + shlex.quote(remote), timeout=120
            )
            raw = b"".join(iter(lambda: stdout.read(1024 * 1024), b""))
            if stdout.channel.recv_exit_status() != 0:
                raise OSError(stderr.read().decode("utf-8", errors="replace"))
        digest = hashlib.sha256(raw).hexdigest()
        if expected_sha256 and digest != expected_sha256:
            raise ValueError(f"服务器原件与指定实验版本不符: {remote}")
        self.reads.append({"remote": remote, "sha256": digest, "bytes": len(raw)})
        return raw

    def read_many(self, remotes: list[str]) -> None:
        """批量读取明确文件列表到内存, 后续read_bytes/json消费原字节.

        一次只读tar网络流减少小文件往返. 不在服务器写tar、不在本地解包或持久保存, 不读取未列文件或目录; 成员必须是列表中同名普通文件. 后续解析时按原文件分别记录摘要.
        """
        paths = list(dict.fromkeys(remotes))
        for path in paths:
            source = PurePosixPath(path)
            if (
                not source.is_absolute()
                or ".." in source.parts
                or source.parts[1] not in ("storage", "home")
            ):
                raise ValueError("批量原件必须是明确服务器文件地址: " + path)
        command = "tar -cf - -C / -- " + " ".join(
            shlex.quote(path.lstrip("/")) for path in paths
        )
        _, stdout, stderr = self.client.exec_command(command, timeout=120)
        received = {}
        with tarfile.open(fileobj=stdout, mode="r|") as archive:
            for member in archive:
                remote = "/" + member.name.lstrip("/")
                if remote not in paths or not member.isfile():
                    raise ValueError("批量读取返回非指定原件: " + member.name)
                with archive.extractfile(member) as handle:
                    received[remote] = b"".join(
                        iter(lambda: handle.read(1024 * 1024), b"")
                    )
        if stdout.channel.recv_exit_status() != 0:
            raise OSError(stderr.read().decode("utf-8", errors="replace"))
        if set(received) != set(paths):
            raise ValueError("批量读取未返回完整指定原件列表")
        self._batch.update(received)

    def json(self, remote: str, expected_sha256: str = ""):
        """解析JSON或JSONL, 保留原字段、排序和缺失值."""
        content = self.read_bytes(remote, expected_sha256).decode("utf-8-sig")
        return (
            [json.loads(line) for line in content.splitlines() if line.strip()]
            if remote.endswith(".jsonl")
            else json.loads(content)
        )

    def npz(self, remote: str, expected_sha256: str = "") -> dict:
        """返回NPZ的具名原数组, 不改dtype、轴顺序、单位或缺失值."""
        with np.load(
            BytesIO(self.read_bytes(remote, expected_sha256)), allow_pickle=False
        ) as arrays:
            return {name: arrays[name] for name in arrays.files}

    def local_file(self, remote: str, expected_sha256: str = "") -> Path:
        """供应本地原样副本, 每次读取先与服务器当前完整SHA256核对.

        remote必须是/storage或/home下的绝对文件地址. cache内按服务器绝对路径展开目录; 例如/storage/a.npy对应server/storage/a.npy. 不在缓存中写日志、清单、会话或转换文件. 下载及跨卷复制后再次校验, 成功后删除本次下载临时文件.
        """
        source = PurePosixPath(remote)
        if (
            not source.is_absolute()
            or ".." in source.parts
            or source.parts[1] not in ("storage", "home")
        ):
            raise ValueError(f"原件必须使用明确的服务器绝对文件地址: {remote}")
        _, stdout, stderr = self.client.exec_command(
            "sha256sum -- " + shlex.quote(remote)
        )
        output = stdout.read().decode("utf-8")
        if stdout.channel.recv_exit_status() != 0:
            raise OSError(stderr.read().decode("utf-8", errors="replace"))
        digest = output.split()[0]
        if expected_sha256 and digest != expected_sha256:
            raise ValueError(f"服务器原件与指定实验版本不符: {remote}")
        target = self.cache.joinpath(*source.parts[1:])
        local_digest = ""
        if target.is_file():
            with target.open("rb") as handle:
                local_digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if local_digest != digest:
            self.build.mkdir(parents=True, exist_ok=True)
            incoming = self.build / ("download-" + digest)
            _, stdout, stderr = self.client.exec_command(
                "cat -- " + shlex.quote(remote), timeout=120
            )
            with incoming.open("wb") as handle:
                for block in iter(lambda: stdout.read(1024 * 1024), b""):
                    handle.write(block)
            if stdout.channel.recv_exit_status() != 0:
                raise OSError(stderr.read().decode("utf-8", errors="replace"))
            with incoming.open("rb") as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != digest:
                    raise ValueError(f"原样下载校验失败: {remote}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(incoming, target)
            with target.open("rb") as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != digest:
                    raise ValueError(f"D盘原样副本校验失败: {target}")
            incoming.unlink()
        self.reads.append(
            {
                "remote": remote,
                "sha256": digest,
                "bytes": target.stat().st_size,
                "local": str(target),
            }
        )
        return target

    def close(self):
        """关闭本次只读连接, 不删除原件或缓存."""
        self.sftp.close()
        self.client.close()
