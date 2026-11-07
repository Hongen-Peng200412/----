"""在指定部署根保存完整项目版本, 并从 Git 独立恢复后发布.

main 是 JSON 请求入口. status/coverage 只读; begin/finalize/abort 管理一次接收事务;
verify 只在部署根的 restore 中临时检出. 项目文件位于 runs/<syncid>/project,
snapshot/manifest.json 保存文件大小、SHA-256、链接描述及来源精选 HEAD.
本程序是文件历史运维工具, 不定义任何实验来源、评价规则或绘图条件.
"""

import hashlib
from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace


ROOT = Path('/home/penghongen/manuscript_full_history/LigandSeek')
RESET_FROM = '1e0f23ad9382692e7529ecb06f41d7b7677fd5bf'
FORMAL_REF = 'refs/heads/full-history'
SCOPE = 'project-excluding-root-git-and-temp'
DOCUMENT_IO = SimpleNamespace(lstat=os.lstat, open=open)


def digest(path):
    """流式计算普通文件原字节的 SHA-256; 只读文件内容."""
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def run(command, environment):
    """执行部署根内的 Git 操作, 返回 stdout 原字节并保留简短失败原因."""
    worktrees = [part.split('=', 1)[1] for part in command if part.startswith('--work-tree=')]
    result = subprocess.run(command, cwd=worktrees[0] if worktrees else None, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace')[-4000:])
    return result.stdout


def git_arguments(repository, worktree):
    """使用 Git 1.8.3 支持的参数, 关闭字节转换及自动对象清理."""
    return ['git', '--git-dir=' + str(repository), '--work-tree=' + str(worktree), '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', '-c', 'core.compression=1', '-c', 'core.looseCompression=1', '-c', 'gc.auto=0']


def state():
    """读取唯一有效回执及正式 Git 引用; 不建立目录或修复状态.

    返回字段:
        - current: dict 或 None, 已发布完整版本的回执, 包含 commit/source_head/syncid 等字段.
        - reference: str 或 None, 正式 full-history 分支当前 SHA.
        - normalized: bool, current 是否属于本轮新建且已经完整验收的正式历史.
        - pending_publication: bool, 是否存在尚待同一次 --resume 收口的发布事务.
        - locked: bool, 是否有接收事务持有同步锁.
    """
    current_path = ROOT / 'control/current.json'
    current = json.loads(current_path.read_text(encoding='utf-8')) if current_path.exists() else None
    repository = ROOT / 'history.git'
    reference = None
    if repository.exists():
        result = subprocess.run(['git', '--git-dir=' + str(repository), 'rev-parse', '--verify', FORMAL_REF], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            reference = result.stdout.decode().strip()
    return {'current': current, 'reference': reference, 'normalized': bool(current and current.get('history_format') == 2 and current.get('complete') is True and current.get('restored_verified') is True), 'pending_publication': (ROOT / 'control/publication.json').exists(), 'pending_documents': bool(current and (ROOT / 'control/document-stage' / current['syncid']).exists()), 'locked': (ROOT / 'control/sync.lock').exists()}


def check_tree(directory, manifest):
    """核对一次完整文件清单与实体目录, 不跟随文件或目录链接.

    manifest.files 的每项包含 path/bytes/mtime_ns/sha256; path 为项目相对路径.
    manifest.links 只描述原链接的 path/kind/target, 不在 project 中创建链接.
    mtime_ns 记录捕获时源时间, 恢复判定使用路径集合、大小和文件原字节摘要.
    """
    if manifest['version'] != 2 or manifest['complete'] is not True or manifest['scope'] != SCOPE:
        raise ValueError('清单不是已完整捕获的本轮项目版本')
    expected = {}
    for item in manifest['files']:
        parts = PurePosixPath(item['path']).parts
        if not parts or parts[0] in ('.git', 'temp') or '..' in parts or PurePosixPath(item['path']).is_absolute() or '\\' in item['path'] or item['path'] in expected:
            raise ValueError('文件清单越界或重复: ' + item['path'])
        if not re.fullmatch(r'[0-9a-f]{64}', item['sha256']) or item['bytes'] < 0:
            raise ValueError('文件大小或摘要格式错误: ' + item['path'])
        expected[item['path']] = item
    link_paths = set()
    for link in manifest['links']:
        parts = PurePosixPath(link['path']).parts
        if not parts or parts[0] in ('.git', 'temp') or '..' in parts or PurePosixPath(link['path']).is_absolute() or '\\' in link['path'] or link['path'] in expected or link['path'] in link_paths or link['kind'] not in ('file', 'directory') or not isinstance(link['target'], str):
            raise ValueError('链接描述越界、重复或格式错误')
        link_paths.add(link['path'])
    actual = set()
    for parent, directories, names in os.walk(directory, followlinks=False):
        for name in directories + names:
            path = Path(parent) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
                raise ValueError('接收目录只能包含实体文件: ' + str(path))
            if name in names and not stat.S_ISREG(info.st_mode):
                raise ValueError('接收目录含非普通文件: ' + str(path))
        actual.update((Path(parent) / name).relative_to(directory).as_posix() for name in names)
    if actual != set(expected):
        raise ValueError('文件集合不同: missing=%r extra=%r' % (sorted(set(expected) - actual)[:5], sorted(actual - set(expected))[:5]))
    for number, item in enumerate(manifest['files']):
        path = directory / item['path']
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('文件原字节不同: ' + item['path'])
        if number and number % 2000 == 0:
            print('已逐文件核对 %d/%d' % (number, len(expected)), flush=True)


def read_document(adapter, target):
    """只读取映射表明确列出的既有普通 MD; adapter 提供 SFTP 式 lstat/open 接口."""
    path = PurePosixPath(target)
    if not path.is_absolute() or '..' in path.parts or path.suffix.lower() != '.md' or not stat.S_ISREG(adapter.lstat(target).st_mode):
        raise ValueError('说明目标必须是明确既有的普通绝对路径 MD: ' + target)
    with adapter.open(target, 'rb') as handle:
        return handle.read()


def write_document(adapter, target, content):
    """在同一既有 MD 内写完整原字节并复读核对, 不创建目录、临时名或备份文件."""
    read_document(adapter, target)
    with adapter.open(target, 'r+b') as handle:
        handle.seek(0)
        handle.write(content)
        handle.truncate(len(content))
        handle.flush()
    if read_document(adapter, target) != content:
        raise ValueError('说明文件写入后的原字节不同: ' + target)


def parse_document_index(project, relative):
    """解析人读索引唯一的本地说明/服务器说明两列表, 返回逐字节同步的明确 MD 清单."""
    index = PurePosixPath(relative)
    if index.is_absolute() or '..' in index.parts or index.suffix.lower() != '.md':
        raise ValueError('说明索引必须是项目内相对 MD 路径')
    path = project / relative
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    starts = [number for number, line in enumerate(lines) if [part.strip() for part in line.strip().strip('|').split('|')] == ['本地说明', '服务器说明']]
    if len(starts) != 1:
        raise ValueError('需要唯一的 | 本地说明 | 服务器说明 | 显式表格')
    records, targets = [], set()
    for line in lines[starts[0] + 1:]:
        if not line.strip().startswith('|'):
            break
        cells = [part.strip() for part in line.strip().strip('|').split('|')]
        if len(cells) != 2:
            raise ValueError('说明映射只能有两列')
        if all(re.fullmatch(r':?-+:?', cell) for cell in cells):
            continue
        values = []
        for cell in cells:
            link = re.fullmatch(r'\[[^\]]+\]\(([^)]+)\)', cell)
            values.append((link.group(1) if link else cell).strip('`'))
        local, target = values
        source = (path.parent / local).resolve()
        remote = PurePosixPath(target)
        if Path(local).is_absolute() or not source.is_relative_to(project.resolve()) or not source.is_file() or source.suffix.lower() != '.md' or not remote.is_absolute() or '..' in remote.parts or remote.suffix.lower() != '.md' or target in targets:
            raise ValueError('说明映射需指向项目内既有MD和不重复的服务器绝对MD')
        records.append({'source': source.relative_to(project.resolve()).as_posix(), 'target': target, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        targets.add(target)
    if not records:
        raise ValueError('说明映射表没有文件')
    return records


def finish_documents(stage, keep_new):
    """收口本事务的短期旧字节: 保留已发布的新MD, 或回滚本事务实际触及的旧MD."""
    if not stage.exists():
        return
    expected = ROOT / 'control/document-stage'
    if stage.resolve() != stage or stage.parent != expected:
        raise ValueError('说明事务暂存目录越界')
    plan_path = stage / 'plan.json'
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        errors = []
        for item in plan:
            try:
                if keep_new:
                    if hashlib.sha256(read_document(DOCUMENT_IO, item['target'])).hexdigest() != item['sha256']:
                        raise ValueError('已发布说明与捕获字节不同')
                elif item['touched']:
                    if Path(item['old_file']).name != item['old_file']:
                        raise ValueError('回滚暂存文件路径错误')
                    old = (stage / item['old_file']).read_bytes()
                    if hashlib.sha256(old).hexdigest() != item['old_sha256']:
                        raise ValueError('回滚暂存原字节不完整')
                    if read_document(DOCUMENT_IO, item['target']) != old:
                        write_document(DOCUMENT_IO, item['target'], old)
            except Exception as error:
                errors.append(item['target'] + ': ' + str(error))
        if errors:
            raise RuntimeError('说明事务尚未完成, 保留短期回滚材料: ' + '; '.join(errors))
    shutil.rmtree(stage)


@contextmanager
def document_scope(project, documents, stage):
    """更新显式映射的说明文件; 正式发布前失败时恢复同一目标的旧原字节.

    documents 为 source/target/sha256 记录列表, 不解释 MD 的科学内容.
    old_file 仅暂存在论文部署 control 中, 成功或完成回滚后清除.
    若正式引用和有效回执均已发布本syncid, 收尾异常也保留新说明, 由同次resume清理锁和发布记录.
    """
    if stage.exists():
        raise RuntimeError('说明事务尚未收口, 使用同一次恢复')
    if stage.resolve() != stage or stage.parent.resolve() != stage.parent:
        raise ValueError('说明暂存目录不能经过链接')
    values = []
    targets = set()
    for item in documents:
        relative = PurePosixPath(item['source'])
        if relative.is_absolute() or '..' in relative.parts or relative.suffix.lower() != '.md' or '\\' in item['source'] or item['target'] in targets:
            raise ValueError('说明源路径或目标映射重复/越界')
        new = (project / item['source']).read_bytes()
        if hashlib.sha256(new).hexdigest() != item['sha256']:
            raise ValueError('说明源与捕获清单不同')
        values.append((item, new, read_document(DOCUMENT_IO, item['target'])))
        targets.add(item['target'])
    stage.mkdir(parents=True)
    plan = []
    for number, (item, new, old) in enumerate(values):
        old_file = str(number) + '.bin'
        (stage / old_file).write_bytes(old)
        plan.append({**item, 'old_file': old_file, 'old_sha256': hashlib.sha256(old).hexdigest(), 'touched': False})
    plan_path = stage / 'plan.json'
    plan_pending = stage / 'plan.pending.json'
    plan_pending.write_text(json.dumps(plan), encoding='utf-8')
    os.replace(plan_pending, plan_path)
    try:
        for item, (_, new, old) in zip(plan, values):
            if new != old:
                if read_document(DOCUMENT_IO, item['target']) != old:
                    raise ValueError('同步期间目标说明被其他编辑改变: ' + item['target'])
                item['touched'] = True
                plan_pending.write_text(json.dumps(plan), encoding='utf-8')
                os.replace(plan_pending, plan_path)
                write_document(DOCUMENT_IO, item['target'], new)
        yield {'verified': len(plan), 'changed': sum(item['touched'] for item in plan)}
    except Exception:
        published = state()
        keep_new = bool(published['normalized'] and published['current']['syncid'] == stage.name and published['reference'] == published['current']['commit'])
        finish_documents(stage, keep_new)
        raise
    else:
        finish_documents(stage, True)


# ================================================================================================
def main(request):
    """执行一个文件历史请求; 只有完整恢复验收后才发布新正式版本.

    reset-history 只接受 RESET_FROM, 只首次切换, 新提交没有旧父节点.
    snapshot 只能沿本轮正式历史追加. publication.json 是发布事务的短期元数据,
    不保存旧项目副本; 进程或网络中断后只允许同一次 resume 收口.
    """
    if ROOT.resolve() != ROOT:
        raise ValueError('部署根及其祖先必须是实体目录')
    for name in ('control', 'history.git', 'runs', 'restore'):
        path = ROOT / name
        if path.resolve() != path:
            raise ValueError('部署目录不能通过链接越出原位置: ' + str(path))
    action = request['action']
    control = ROOT / 'control'
    repository = ROOT / 'history.git'
    current_path = control / 'current.json'
    lock = control / 'sync.lock'
    publication = control / 'publication.json'
    if lock.resolve() != lock:
        raise ValueError('同步锁目录不能是链接')
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_AUTHOR_NAME='Manuscript full history', GIT_AUTHOR_EMAIL='history@localhost', GIT_COMMITTER_NAME='Manuscript full history', GIT_COMMITTER_EMAIL='history@localhost')
    before = state()
    if action == 'status':
        return before
    if action == 'coverage':
        versions = []
        if before['normalized']:
            if before['reference'] != before['current']['commit'] or before['pending_publication']:
                raise RuntimeError('正式引用与有效回执尚未收口, 请恢复原同步事务')
            arguments = git_arguments(repository, ROOT)
            for commit in run(arguments + ['rev-list', '--reverse', FORMAL_REF], environment).decode().split():
                manifest = json.loads(run(arguments + ['show', commit + ':snapshot/manifest.json'], environment))
                if manifest['version'] != 2 or manifest['complete'] is not True or manifest['generation'] != before['current']['generation']:
                    raise RuntimeError('正式历史混入未完整验收的旧版本')
                versions.append({'commit': commit, 'source_head': manifest['head'], 'source_branch': manifest['branch'], 'source_dirty': manifest['dirty'], 'captured_utc': manifest['captured_utc'], 'files': len(manifest['files']), 'bytes': sum(item['bytes'] for item in manifest['files']), 'documents': len(manifest['documents']), 'complete': True})
        target = request.get('source_head')
        matching = [version for version in versions if version['source_head'] == target] if target else versions
        return {'normalized': before['normalized'], 'scope': SCOPE, 'versions': matching, 'source_head': target, 'covered': bool(matching), 'meaning': '只列实际捕获并验收的完整版本; 未列出的精选提交没有对应全面快照'}
    syncid = request['syncid']
    if not re.fullmatch(r'[A-Za-z0-9-]{8,100}', syncid):
        raise ValueError('同步编号格式错误')
    directory = ROOT / 'runs' / syncid
    document_stage = control / 'document-stage' / syncid
    if action == 'begin':
        if before['pending_documents'] and before['current']['syncid'] != syncid:
            raise RuntimeError('已发布事务尚有说明暂存, 先恢复原事务收口')
        control.mkdir(parents=True, exist_ok=True)
        created = False
        if lock.exists():
            if not request['resume'] or (lock / 'owner').read_text() != syncid:
                raise RuntimeError('另一事务持有同步锁')
        else:
            lock.mkdir()
            (lock / 'owner').write_text(syncid)
            created = True
        try:
            if publication.exists():
                transaction = json.loads(publication.read_text(encoding='utf-8'))
                if transaction['syncid'] != syncid:
                    raise RuntimeError('另一事务存在待收口的发布记录')
                if before['current']['commit'] == transaction['new'] and before['reference'] == transaction['new']:
                    publication.unlink()
                elif before['current']['commit'] == transaction['old'] and before['reference'] == transaction['new']:
                    run(git_arguments(repository, ROOT) + ['update-ref', FORMAL_REF, transaction['old'], transaction['new']], environment)
                    publication.unlink()
                elif before['current']['commit'] == transaction['old'] and before['reference'] == transaction['old']:
                    publication.unlink()
                else:
                    raise RuntimeError('发布记录与引用不符, 不自动覆盖')
                before = state()
            if document_stage.exists():
                if not request['resume']:
                    raise RuntimeError('说明暂存需由原事务恢复, 不另起覆盖')
                finish_documents(document_stage, bool(before['current'] and before['current']['syncid'] == syncid and before['reference'] == before['current']['commit']))
            if before['current'] and before['current']['syncid'] == syncid:
                shutil.rmtree(lock)
                return {'published': before['current']}
            operation = request['operation']
            expected = request['expected_current']
            if operation == 'reset-history':
                if before['normalized'] or expected != RESET_FROM or before['reference'] != RESET_FROM or not before['current'] or before['current']['commit'] != RESET_FROM:
                    raise RuntimeError('首次正式历史切换条件不符; 不覆盖其他版本')
            elif operation != 'snapshot' or not before['normalized'] or before['reference'] != expected or before['current']['commit'] != expected:
                raise RuntimeError('普通同步只能沿已规范化且引用一致的正式历史追加')
            if directory.exists() and not request['resume']:
                raise FileExistsError('同步编号已存在, 不复用其他接收目录')
            if directory.resolve() != directory:
                raise ValueError('本次接收目录不能是链接')
            (directory / 'project').mkdir(parents=True, exist_ok=True)
            (directory / 'snapshot').mkdir(exist_ok=True)
            transaction = {'operation': operation, 'expected_current': expected, 'manifest_sha256': request['manifest_sha256'], 'generation': syncid if operation == 'reset-history' else before['current']['generation']}
            (lock / 'transaction.json').write_text(json.dumps(transaction), encoding='utf-8')
            return {'previous': before['current'], 'generation': transaction['generation']}
        except Exception:
            if created and not publication.exists():
                shutil.rmtree(lock)
            raise
    if action == 'abort':
        if not lock.exists() or (lock / 'owner').read_text() != syncid:
            raise RuntimeError('当前调用者不持有同步锁')
        if publication.exists():
            raise RuntimeError('发布尚待收口, 保留锁并使用同一次 --resume')
        finish_documents(document_stage, bool(before['current'] and before['current']['syncid'] == syncid))
        shutil.rmtree(lock)
        return {'aborted': syncid, 'current_unchanged': state()['current']}
    arguments = git_arguments(repository, ROOT if action == 'verify' else directory)
    index = control / ('index-' + syncid)
    environment['GIT_INDEX_FILE'] = str(index)
    if action == 'finalize':
        if not lock.exists() or (lock / 'owner').read_text() != syncid:
            raise RuntimeError('当前调用者不持有同步锁')
        transaction = json.loads((lock / 'transaction.json').read_text(encoding='utf-8'))
        manifest_path = directory / 'snapshot/manifest.json'
        if digest(manifest_path) != transaction['manifest_sha256']:
            raise ValueError('上传清单与完整捕获清单摘要不同')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['syncid'] != syncid or manifest['generation'] != transaction['generation'] or manifest['operation'] != transaction['operation']:
            raise ValueError('清单不属于当前同步事务')
        check_tree(directory / 'project', manifest)
        if parse_document_index(directory / 'project', manifest['document_index']) != manifest['documents']:
            raise ValueError('说明映射与捕获的人读索引不一致')
        before = state()
        expected = transaction['expected_current']
        if before['reference'] != expected or before['current']['commit'] != expected:
            raise RuntimeError('正式引用在接收期间改变, 不发布')
    elif action == 'verify':
        commit = request['commit']
        if not re.fullmatch(r'[0-9a-f]{40}', commit) or not before['normalized'] or before['reference'] != before['current']['commit']:
            raise ValueError('需要本轮正式历史中的完整提交 SHA')
        formal = run(arguments + ['rev-list', FORMAL_REF], environment).decode().split()
        if commit not in formal:
            raise ValueError('该提交不在本轮正式历史中; 旧对象未被删除')
        manifest = json.loads(run(arguments + ['show', commit + ':snapshot/manifest.json'], environment))
    else:
        raise ValueError('未知操作')
    scope = document_scope(directory / 'project', manifest['documents'], document_stage) if action == 'finalize' else nullcontext(None)
    with scope as document_result:
        if action == 'finalize':
            (repository / 'info/attributes').write_text('* -text -filter -ident -working-tree-encoding\n', encoding='ascii')
            run(arguments + ['read-tree', expected] if transaction['operation'] == 'snapshot' else arguments + ['read-tree', '--empty'], environment)
            run(arguments + ['add', '--force', '--all', '--', 'project', 'snapshot'], environment)
            tree = run(arguments + ['write-tree'], environment).decode().strip()
            command = arguments + ['commit-tree', tree]
            if transaction['operation'] == 'snapshot':
                command += ['-p', expected]
            message = ('Complete project version %s\n\nsource-head: %s\nsource-branch: %s\nsource-dirty: %s\ngeneration: %s\nscope: %s\n' % (syncid, manifest['head'], manifest['branch'], manifest['dirty'], manifest['generation'], SCOPE)).encode()
            process = subprocess.run(command, env=environment, input=message, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode:
                raise RuntimeError(process.stderr.decode('utf-8', 'replace')[-4000:])
            commit = process.stdout.decode().strip()
        restore = ROOT / 'restore' / syncid
        if restore.exists() and action == 'finalize':
            if restore.resolve() != restore:
                raise ValueError('恢复临时目录不能是链接')
            shutil.rmtree(restore)
        restore.mkdir(parents=True)
        try:
            restored_arguments = git_arguments(repository, restore)
            run(restored_arguments + ['read-tree', commit], environment)
            run(restored_arguments + ['checkout-index', '--all', '--force'], environment)
            restored_manifest = json.loads((restore / 'snapshot/manifest.json').read_text(encoding='utf-8'))
            if restored_manifest != manifest:
                raise ValueError('恢复的清单与捕获清单不同')
            check_tree(restore / 'project', restored_manifest)
            if parse_document_index(restore / 'project', manifest['document_index']) != manifest['documents']:
                raise ValueError('恢复的说明映射与源MD原字节不符')
        finally:
            shutil.rmtree(restore)
            if index.exists():
                index.unlink()
        history_root = commit if manifest['operation'] == 'reset-history' else before['current']['history_root']
        if action == 'verify':
            history_root = before['current']['history_root']
        result = {'history_format': 2, 'generation': manifest['generation'], 'history_root': history_root, 'syncid': manifest['syncid'], 'commit': commit, 'source_head': manifest['head'], 'source_branch': manifest['branch'], 'source_dirty': manifest['dirty'], 'captured_utc': manifest['captured_utc'], 'files': len(manifest['files']), 'bytes': sum(item['bytes'] for item in manifest['files']), 'links': len(manifest['links']), 'run': str(ROOT / 'runs' / manifest['syncid']), 'complete': True, 'restored_verified': True, 'documents': {'mapped': len(manifest['documents']), 'live_verified': action == 'finalize', 'changed': document_result['changed'] if document_result else None}}
        if action == 'finalize':
            for item in manifest['documents']:
                if hashlib.sha256(read_document(DOCUMENT_IO, item['target'])).hexdigest() != item['sha256']:
                    raise ValueError('正式发布前说明文件字节发生变化: ' + item['target'])
            pending = control / ('current-' + syncid + '.pending.json')
            pending.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            journal = control / ('publication-' + syncid + '.pending.json')
            journal.write_text(json.dumps({'syncid': syncid, 'old': expected, 'new': commit}), encoding='utf-8')
            os.replace(journal, publication)
            try:
                run(arguments + ['update-ref', FORMAL_REF, commit, expected], environment)
                os.replace(pending, current_path)
            except Exception:
                after = state()
                if after['current']['commit'] == expected and after['reference'] == commit:
                    run(arguments + ['update-ref', FORMAL_REF, expected, commit], environment)
                if state()['reference'] == expected:
                    publication.unlink()
                raise
            publication.unlink()
            shutil.rmtree(lock)
    return result


if __name__ == '__main__':
    try:
        print(json.dumps(main(json.load(sys.stdin)), ensure_ascii=False), flush=True)
    except Exception as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr, flush=True)
        raise
