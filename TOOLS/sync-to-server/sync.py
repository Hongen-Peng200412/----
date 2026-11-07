"""捕获项目原字节并同步到服务器正式全面 Git, 不保存项目 .git 的副本.

main 提供 snapshot/reset-history/coverage/verify 四个运维命令. capture 将本地
项目的实体文件复制到独立 temp 副本, 返回含完整 SHA-256 与来源 Git 状态的清单;
链接只保存描述. 只有源路径集合、文件摘要、HEAD、分支和索引都复核后才允许上传.
服务器端从提交独立恢复全量文件并核对后, 才发布唯一有效回执.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import uuid
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*(?:TripleDES|Blowfish).*')
import paramiko
from server import parse_document_index


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REMOTE_ROOT = '/home/penghongen/manuscript_full_history/LigandSeek'
TEMP_ROOT = PROJECT_ROOT / 'temp/figure-centric/sync-to-server'
SCOPE = 'project-excluding-root-git-and-temp'


def digest(path):
    """计算文件原字节 SHA-256, 不应用 Git 的换行、过滤器或文本转换."""
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def inventory(root, excluded_root_names):
    """不跟随链接地枚举实体文件与链接描述.

    excluded_root_names 为根层排除名称, 项目捕获固定使用 .git/temp; 捕获副本复核使用空元组.
    返回 files/list[dict] 与 links/list[dict], 都按项目相对 path 排序.
    files 每项含 path/bytes/mtime_ns; links 每项含 path/kind/target, 不读取 target 内容.
    """
    files, links = [], []
    for parent, directories, names in os.walk(root, followlinks=False):
        for name in directories[:]:
            path = Path(parent) / name
            if Path(parent) == root and name in excluded_root_names:
                directories.remove(name)
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
                links.append({'path': path.relative_to(root).as_posix(), 'kind': 'directory', 'target': os.readlink(path)})
                directories.remove(name)
        for name in names:
            path = Path(parent) / name
            if Path(parent) == root and name in excluded_root_names:
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
                links.append({'path': path.relative_to(root).as_posix(), 'kind': 'file', 'target': os.readlink(path)})
            elif stat.S_ISREG(info.st_mode):
                files.append({'path': path.relative_to(root).as_posix(), 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns})
            else:
                raise ValueError('不捕获设备或管道等特殊文件: ' + str(path))
    return sorted(files, key=lambda item: item['path']), sorted(links, key=lambda item: item['path'])


def git(source, *arguments):
    """只读取得源 Git 状态, 关闭可选索引刷新和文件系统监视器."""
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *arguments], cwd=source, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def capture(source, temporary, syncid, operation, generation, expected_current):
    """取得可独立上传的完整文件副本, 成功后返回文件清单并打印 CAPTURE_COMPLETE.

    source 为项目 Git 工作树根, 同时支持 .git 目录及 worktree 的 .git 指针文件.
    temporary 由调用者创建在本项目 temp/figure-centric 下; capture/ 不与源共享硬链接.
    返回的 manifest 含来源 head/branch/dirty/status_hex/index 摘要、捕获时间、实体文件摘要及链接描述.
    任一源文件、路径集合、Git HEAD/分支/索引在捕获期间变化时, 不生成 complete 清单.
    """
    source = source.resolve()
    if Path(git(source, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != source:
        raise ValueError('source 必须指向项目工作树根')
    head = git(source, 'rev-parse', 'HEAD')
    branch = git(source, 'rev-parse', '--abbrev-ref', 'HEAD')
    raw_index = Path(git(source, 'rev-parse', '--git-path', 'index').decode().strip())
    index = raw_index if raw_index.is_absolute() else source / raw_index
    index_hash = digest(index)
    status = git(source, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    files, links = inventory(source, ('.git', 'temp'))
    if shutil.disk_usage(temporary).free < sum(item['bytes'] for item in files) + 1024 ** 3:
        raise RuntimeError('独立捕获副本空间不足, 需要文件总量另加 1 GiB')
    destination = temporary / 'capture'
    destination.mkdir()
    print('开始完整捕获; CAPTURE_COMPLETE 前请暂停保存源文件和 Git 写操作.', flush=True)
    for number, item in enumerate(files):
        target = destination / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        value = hashlib.sha256()
        with (source / item['path']).open('rb') as incoming, target.open('xb') as outgoing:
            for block in iter(lambda: incoming.read(8 * 1024 * 1024), b''):
                outgoing.write(block)
                value.update(block)
        os.utime(target, ns=(item['mtime_ns'], item['mtime_ns']))
        item['sha256'] = value.hexdigest()
        if number and number % 2000 == 0:
            print('已独立复制 %d/%d 文件' % (number, len(files)), flush=True)
    before = [{key: item[key] for key in ('path', 'bytes', 'mtime_ns')} for item in files]
    if inventory(source, ('.git', 'temp')) != (before, links):
        raise RuntimeError('捕获期间源路径集合、类型、大小或时间改变')
    for item in files:
        if digest(source / item['path']) != item['sha256']:
            raise RuntimeError('捕获期间源文件原字节改变: ' + item['path'])
    if git(source, 'rev-parse', 'HEAD') != head or git(source, 'rev-parse', '--abbrev-ref', 'HEAD') != branch or digest(index) != index_hash or git(source, 'status', '--porcelain=v1', '-z', '--untracked-files=all') != status:
        raise RuntimeError('捕获期间源 Git 状态改变')
    manifest = {'version': 2, 'scope': SCOPE, 'complete': True, 'syncid': syncid, 'operation': operation, 'generation': generation, 'expected_current': expected_current, 'source': str(source), 'head': head.decode().strip(), 'branch': branch.decode().strip(), 'dirty': bool(status), 'status_hex': status.hex(), 'source_index_sha256': index_hash, 'captured_utc': datetime.now(timezone.utc).isoformat(), 'files': files, 'links': links}
    (temporary / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=True), encoding='utf-8')
    print('CAPTURE_COMPLETE: 源文件与 Git 状态已完整复核; 后续只读独立副本, 可以恢复编辑.', flush=True)
    return manifest


def request(client, program, payload):
    """通过严格 SSH 执行本工具服务器程序并发送 JSON; 不在服务器常驻安装程序."""
    stdin, stdout, stderr = client.exec_command('python3 -B -c ' + shlex.quote(program))
    stdin.write(json.dumps(payload, ensure_ascii=True))
    stdin.channel.shutdown_write()
    lines = []
    for line in stdout:
        lines.append(line)
        if not line.startswith('{'):
            print(line.rstrip(), flush=True)
    error = stderr.read().decode('utf-8', 'replace')
    if stdout.channel.recv_exit_status():
        raise RuntimeError(error[-6000:])
    return json.loads(lines[-1])


def transfer(source, target, password, previous):
    """只把实体捕获副本传入部署根内的本次接收目录, 不使用原地覆盖."""
    if not target.startswith(REMOTE_ROOT + '/runs/') or '..' in target.split('/'):
        raise ValueError('接收目录超出本次项目版本根')
    if previous and (not previous.startswith(REMOTE_ROOT + '/runs/') or '..' in previous.split('/')):
        raise ValueError('增量参照目录超出项目版本根')
    roots = [os.environ.get('PROJECT_MSYS_ROOT'), os.environ.get('MSYS2_ROOT'), 'C:/msys64', 'D:/msys64']
    msys = next(Path(root) / 'usr/bin' for root in roots if root and (Path(root) / 'usr/bin/rsync.exe').is_file())
    local = subprocess.check_output([str(msys / 'cygpath.exe'), '-u', str(source.resolve())]).decode().strip()
    known = subprocess.check_output([str(msys / 'cygpath.exe'), '-u', str(Path.home() / '.ssh/known_hosts')]).decode().strip()
    shell = '/usr/bin/sshpass -e /usr/bin/ssh -p 10022 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=' + shlex.quote(known) + ' -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ConnectTimeout=20 -o ServerAliveInterval=30'
    command = [str(msys / 'rsync.exe'), '-rtz', '--compress-level=1', '--checksum', '--delete', '--protect-args', '--partial', '--partial-dir=.rsync-partial', '--info=progress2', '-e', shell]
    if previous:
        command.append('--link-dest=' + previous)
    command += [local.rstrip('/') + '/', 'penghongen@10.102.33.220:' + target.rstrip('/') + '/']
    subprocess.run(command, env={**os.environ, 'SSHPASS': password, 'MSYS2_ARG_CONV_EXCL': '*', 'LANG': 'C.UTF-8'}, check=True)


def clear_capture(temporary):
    """只清除本项目固定临时根内的一个独立捕获副本, 不跟随目录链接."""
    expected = PROJECT_ROOT / 'temp/figure-centric/sync-to-server'
    if TEMP_ROOT.resolve() != expected or temporary.resolve() != temporary or temporary.parent != expected:
        raise ValueError('捕获副本清理边界不符, 不递归删除')
    shutil.rmtree(temporary)


# ================================================================================================
def main():
    """解析运维命令并装配捕获、SSH 和服务器事务; 不替作者 commit 或 push."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'reset-history', 'coverage', 'verify'])
    parser.add_argument('--source', type=Path, default=PROJECT_ROOT)
    parser.add_argument('--expect-current', help='仅首次 reset-history 使用的已核对服务器旧正式 SHA')
    parser.add_argument('--source-head', help='coverage 查询实际捕获过的一个精选提交')
    parser.add_argument('--commit', help='verify 独立恢复一个正式全面提交')
    parser.add_argument('--resume', type=Path, help='恢复同一次已经完整捕获的本地副本')
    parser.add_argument('--document-index', type=Path, help='项目人读说明的本地说明/服务器说明两列表')
    options = parser.parse_args()
    if options.action == 'reset-history' and not options.expect_current:
        parser.error('reset-history 必须显式提供 --expect-current')
    if options.action == 'verify' and not options.commit:
        parser.error('verify 必须显式提供 --commit')
    if options.action in ('snapshot', 'reset-history') and not options.resume and not options.document_index:
        parser.error('完整发布必须显式提供 --document-index')
    source = options.source.resolve()
    program = Path(__file__).with_name('server.py').read_text(encoding='utf-8')
    password = os.environ.get('CODEX_SSH_PASSWORD') or (Path.home() / '.ssh/pocket_plus_sshpass.txt').read_text().rstrip('\r\n')
    client = paramiko.SSHClient()
    client.load_host_keys(str(Path.home() / '.ssh/known_hosts'))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect('10.102.33.220', port=10022, username='penghongen', password=password, look_for_keys=False, allow_agent=False, timeout=20)
    client.get_transport().set_keepalive(20)
    locked = False
    sftp = None
    syncid = ''
    try:
        if options.action == 'coverage':
            print(json.dumps(request(client, program, {'action': 'coverage', 'source_head': options.source_head}), ensure_ascii=False), flush=True)
            return
        syncid = datetime.now(timezone.utc).strftime('sync-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
        if options.action == 'verify':
            print(json.dumps(request(client, program, {'action': 'verify', 'syncid': syncid, 'commit': options.commit}), ensure_ascii=False), flush=True)
            return
        previous = request(client, program, {'action': 'status'})
        if options.resume:
            temporary = options.resume.resolve()
            if temporary.parent != TEMP_ROOT.resolve():
                raise ValueError('resume 只读取本项目 temp/figure-centric/sync-to-server 下的独立副本')
            manifest = json.loads((temporary / 'manifest.json').read_text(encoding='utf-8'))
            if manifest['complete'] is not True or manifest['version'] != 2 or manifest['source'] != str(source) or manifest['operation'] != options.action:
                raise ValueError('resume 的来源或操作与完整捕获记录不符')
            syncid = manifest['syncid']
            actual, links = inventory(temporary / 'capture', ())
            expected = [{key: item[key] for key in ('path', 'bytes', 'mtime_ns')} for item in manifest['files']]
            if actual != expected or links:
                raise ValueError('resume 独立副本的文件集合或元数据改变')
            for item in manifest['files']:
                if digest(temporary / 'capture' / item['path']) != item['sha256']:
                    raise ValueError('resume 独立副本的原字节改变: ' + item['path'])
            if previous['current'] and previous['current']['syncid'] == syncid and not previous['pending_publication'] and not previous['pending_documents'] and not previous['locked']:
                print('SNAPSHOT_SUCCESS ' + json.dumps(previous['current'], ensure_ascii=False), flush=True)
                clear_capture(temporary)
                return
        else:
            if previous['pending_publication'] or previous['pending_documents'] or previous['locked']:
                raise RuntimeError('上一同步事务尚未结束, 请恢复原事务而非开始新捕获')
            if options.action == 'snapshot' and not previous['normalized']:
                raise RuntimeError('尚未开始本轮正式历史; 普通 snapshot 不会自动重置旧历史')
            if options.action == 'reset-history' and (previous['normalized'] or previous['reference'] != options.expect_current):
                raise RuntimeError('reset-history 条件已变化, 不自动替换预期旧 SHA')
            temporary = TEMP_ROOT / syncid
            temporary.mkdir(parents=True)
            expected_current = options.expect_current if options.action == 'reset-history' else previous['current']['commit']
            generation = syncid if options.action == 'reset-history' else previous['current']['generation']
            manifest = capture(source, temporary, syncid, options.action, generation, expected_current)
            index_relative = options.document_index.resolve().relative_to(source).as_posix()
            manifest['document_index'] = index_relative
            manifest['documents'] = parse_document_index(temporary / 'capture', index_relative)
            (temporary / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=True), encoding='utf-8')
        accepted = request(client, program, {'action': 'begin', 'syncid': syncid, 'operation': manifest['operation'], 'expected_current': manifest['expected_current'], 'manifest_sha256': digest(temporary / 'manifest.json'), 'resume': bool(options.resume)})
        if 'published' in accepted:
            print('SNAPSHOT_SUCCESS ' + json.dumps(accepted['published'], ensure_ascii=False), flush=True)
            clear_capture(temporary)
            return
        locked = True
        previous_project = accepted['previous']['run'] + '/project' if accepted['previous'] else None
        transfer(temporary / 'capture', REMOTE_ROOT + '/runs/' + syncid + '/project', password, previous_project)
        sftp = client.open_sftp()
        sftp.put(str(temporary / 'manifest.json'), REMOTE_ROOT + '/runs/' + syncid + '/snapshot/manifest.json')
        result = request(client, program, {'action': 'finalize', 'syncid': syncid})
        locked = False
        print('SNAPSHOT_SUCCESS ' + json.dumps(result, ensure_ascii=False), flush=True)
        clear_capture(temporary)
    finally:
        if locked:
            try:
                request(client, program, {'action': 'abort', 'syncid': syncid})
            except Exception as error:
                print('本次事务可能需要同一次 --resume 收口: ' + str(error), file=sys.stderr)
        if sftp is not None:
            sftp.close()
        client.close()


if __name__ == '__main__':
    main()
