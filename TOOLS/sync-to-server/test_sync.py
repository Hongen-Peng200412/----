"""只在项目 temp/figure-centric 中验证同步契约; 不建立任何 SSH 连接.

使用隔离源 Git 与隔离服务器 Git, 验证首次孤儿历史、增改删、原字节恢复、
未发布失败、精确引用替换、完整历史覆盖查询、worktree 索引及链接边界.
实际 rsync 仅在本机临时目录间传输, 不访问正式部署根.
"""

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import uuid
from unittest.mock import patch
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


class FakeDocumentFile(io.BytesIO):
    """模拟既有SFTP文件句柄, 写入立即可见, 可在一次部分写入后报错."""
    def __init__(self, adapter, path, mode):
        super().__init__(adapter.files[path])
        self.adapter, self.path, self.mode = adapter, path, mode

    def write(self, content):
        assert self.mode == 'r+b'
        if self.adapter.fail_once == self.path:
            self.adapter.fail_once = None
            super().write(content[:max(1, len(content) // 2)])
            self.flush()
            raise OSError('fake SFTP partial write')
        if self.adapter.corrupt_once == self.path:
            self.adapter.corrupt_once = None
            content = bytes([content[0] ^ 1]) + content[1:]
        result = super().write(content)
        self.flush()
        return result

    def truncate(self, size):
        result = super().truncate(size)
        self.flush()
        return result

    def flush(self):
        if self.mode == 'r+b' and not self.closed:
            self.adapter.files[self.path] = self.getvalue()

    def close(self):
        self.flush()
        super().close()


class FakeSFTP:
    """只提供既有文件的lstat/open, 不支持mkdir、rename或新文件写入."""
    def __init__(self, files):
        self.files = dict(files)
        self.calls = []
        self.fail_once = None
        self.corrupt_once = None

    def lstat(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o644)

    def open(self, path, mode):
        assert path in self.files and mode in ('rb', 'r+b')
        self.calls.append((path, mode))
        return FakeDocumentFile(self, path, mode)


def git_at(directory, *arguments):
    """对本轮隔离夹具执行 Git, 不改变真实项目配置或引用."""
    return subprocess.check_output(['git', '-c', 'user.name=Sync contract test', '-c', 'user.email=sync@test', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *arguments], cwd=directory, stderr=subprocess.PIPE)


def reject(call):
    """必须拒绝一次违反契约的操作, 返回失败类型供本地测试使用."""
    try:
        call()
    except (RuntimeError, ValueError, OSError):
        return
    raise AssertionError('应拒绝的操作被接受')


def stage(client, server, source, base, syncid, operation, expected):
    """从真实临时源捕获并复制到隔离接收目录, 返回本次完整清单."""
    temporary = base / 'captures' / syncid
    temporary.mkdir(parents=True)
    generation = syncid if operation == 'reset-history' else server.state()['current']['generation']
    with redirect_stdout(io.StringIO()):
        manifest = client.capture(source, temporary, syncid, operation, generation, expected)
    manifest['document_index'] = 'docs/README.md'
    manifest['documents'] = server.parse_document_index(temporary / 'capture', manifest['document_index'])
    (temporary / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=True), encoding='utf-8')
    server.main({'action': 'begin', 'syncid': syncid, 'operation': operation, 'expected_current': expected, 'manifest_sha256': client.digest(temporary / 'manifest.json'), 'resume': False})
    destination = server.ROOT / 'runs' / syncid
    shutil.copytree(temporary / 'capture', destination / 'project', dirs_exist_ok=True)
    shutil.copyfile(temporary / 'manifest.json', destination / 'snapshot/manifest.json')
    return manifest


# ================================================================================================
def main():
    """运行全量本地隔离测试, 完成或失败后只清除本次创建的夹具目录."""
    modules = []
    for name, path in [('client', HERE / 'sync.py'), ('server', HERE / 'server.py')]:
        spec = importlib.util.spec_from_file_location('sync_contract_' + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    client, server = modules
    test_root = PROJECT / 'temp/figure-centric/sync-tests'
    base = test_root / ('local-' + uuid.uuid4().hex)
    base.mkdir(parents=True)
    results = []
    try:
        source = base / 'source'
        source.mkdir()
        git_at(source, 'init', '--quiet')
        document_index = '| 本地说明 | 服务器说明 |\n| --- | --- |\n| [甲](a.md) | `/fake-server/one/trace.md` |\n| b.md | /fake-server/two/trace.md |\n'
        initial = {'.gitignore': b'*.cxs\n.review/\n', '.gitattributes': b'* text eol=lf\n', '正文 空格.md': b'first\r\nsecond\r\n', 'binary.bin': bytes(range(256)), 'remove.txt': b'will remove', 'ignored.cxs': bytes(range(256)) * 2, '.review/comment.md': b'author', 'TOOLS/runtime/.manuscript_deps/pinned.bin': b'pinned', 'temp/omitted.txt': b'temporary', 'docs/README.md': document_index.encode(), 'docs/a.md': b'first document\r\nraw', 'docs/b.md': b'second document\n'}
        for name, content in initial.items():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        git_at(source, 'add', '--all')
        git_at(source, 'commit', '--quiet', '-m', 'initial fixture')
        initial_index = client.digest(source / '.git/index')
        external = base / 'external'
        external.mkdir()
        (external / 'sentinel.txt').write_bytes(b'outside source')
        link = source / 'external-link'
        if os.name == 'nt':
            executable = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            subprocess.run([str(executable), '-NoProfile', '-Command', 'New-Item -ItemType Junction -Path $env:SYNC_TEST_LINK -Target $env:SYNC_TEST_TARGET | Out-Null'], env={**os.environ, 'SYNC_TEST_LINK': str(link), 'SYNC_TEST_TARGET': str(external)}, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            link.symlink_to(external, target_is_directory=True)
        files, links = client.inventory(source, ('.git', 'temp'))
        assert {item['path'] for item in files} == set(initial) - {'temp/omitted.txt'}
        assert len(links) == 1 and links[0]['path'] == 'external-link'
        assert not any('sentinel.txt' in item['path'] for item in files)
        results.append('ignored_CXS_review_dependencies_included_links_not_followed')

        server.ROOT = (base / 'server').resolve()
        control = server.ROOT / 'control'
        control.mkdir(parents=True)
        repository = server.ROOT / 'history.git'
        git_at(base, 'init', '--bare', '--quiet', str(repository))
        legacy = server.ROOT / 'runs/legacy-existing'
        (legacy / 'project').mkdir(parents=True)
        (legacy / 'snapshot').mkdir()
        (legacy / 'project/legacy.txt').write_bytes(b'keep old run')
        (legacy / 'snapshot/manifest.json').write_text('{"version": 1}')
        environment = dict(os.environ, GIT_AUTHOR_NAME='Sync test', GIT_AUTHOR_EMAIL='sync@test', GIT_COMMITTER_NAME='Sync test', GIT_COMMITTER_EMAIL='sync@test')
        arguments = server.git_arguments(repository, legacy)
        server.run(arguments + ['add', '--force', '--all', '--', '.'], environment)
        tree = server.run(arguments + ['write-tree'], environment).decode().strip()
        legacy_commit = subprocess.check_output(arguments + ['commit-tree', tree], input=b'legacy fixture\n', env=environment, cwd=legacy).decode().strip()
        server.run(arguments + ['update-ref', server.FORMAL_REF, legacy_commit], environment)
        (control / 'current.json').write_text(json.dumps({'syncid': 'legacy-existing', 'commit': legacy_commit, 'source_head': '1' * 40, 'run': str(legacy), 'restored_verified': True}))
        (server.ROOT / 'original-git').mkdir()
        original_sentinel = server.ROOT / 'original-git/existing.txt'
        original_sentinel.write_bytes(b'preserve existing archive')
        server.RESET_FROM = legacy_commit
        document_files = {'/fake-server/one/trace.md': b'old first document', '/fake-server/two/trace.md': b'old second document', '/fake-server/unrelated.bin': b'keep unrelated', '/fake-server/unrelated.md': b'keep unrelated MD'}
        fake_sftp = FakeSFTP(document_files)
        server.DOCUMENT_IO = fake_sftp
        old_pointer = (control / 'current.json').read_bytes()
        reject(lambda: server.main({'action': 'begin', 'syncid': 'ordinary-before-reset', 'operation': 'snapshot', 'expected_current': legacy_commit, 'manifest_sha256': '0' * 64, 'resume': False}))
        reject(lambda: server.main({'action': 'begin', 'syncid': 'wrong-reset-expectation', 'operation': 'reset-history', 'expected_current': '0' * 40, 'manifest_sha256': '0' * 64, 'resume': False}))
        assert (control / 'current.json').read_bytes() == old_pointer
        assert server.main({'action': 'coverage'})['versions'] == []
        results.append('legacy_history_requires_explicit_exact_one_time_reset')

        first_id = 'test-reset-' + uuid.uuid4().hex[:8]
        first_manifest = stage(client, server, source, base, first_id, 'reset-history', legacy_commit)
        uploaded = server.ROOT / 'runs' / first_id / 'snapshot/manifest.json'
        original_manifest_bytes = uploaded.read_bytes()
        transaction_path = control / 'sync.lock/transaction.json'
        original_transaction_bytes = transaction_path.read_bytes()
        forged = json.loads(original_manifest_bytes)
        forged['documents'][0]['target'] = '/fake-server/unrelated.md'
        uploaded.write_text(json.dumps(forged), encoding='utf-8')
        forged_transaction = json.loads(original_transaction_bytes)
        forged_transaction['manifest_sha256'] = client.digest(uploaded)
        transaction_path.write_text(json.dumps(forged_transaction), encoding='utf-8')
        reject(lambda: server.main({'action': 'finalize', 'syncid': first_id}))
        assert fake_sftp.files == document_files
        uploaded.write_bytes(original_manifest_bytes)
        transaction_path.write_bytes(original_transaction_bytes)
        results.append('server_reparses_human_map_rejects_unlisted_MD_target')
        assert client.digest(source / '.git/index') == initial_index
        reject(lambda: server.main({'action': 'begin', 'syncid': 'foreign-test-writer', 'operation': 'reset-history', 'expected_current': legacy_commit, 'manifest_sha256': '0' * 64, 'resume': False}))
        reject(lambda: server.main({'action': 'abort', 'syncid': 'foreign-test-writer'}))
        extra = server.ROOT / 'runs' / first_id / 'project/unexpected.txt'
        extra.write_bytes(b'not in capture')
        reject(lambda: server.main({'action': 'finalize', 'syncid': first_id}))
        assert (control / 'current.json').read_bytes() == old_pointer
        assert server.state()['reference'] == legacy_commit
        extra.unlink()
        fake_sftp.fail_once = '/fake-server/two/trace.md'
        reject(lambda: server.main({'action': 'finalize', 'syncid': first_id}))
        assert fake_sftp.files == document_files
        assert (control / 'current.json').read_bytes() == old_pointer
        fake_sftp.corrupt_once = '/fake-server/two/trace.md'
        reject(lambda: server.main({'action': 'finalize', 'syncid': first_id}))
        assert fake_sftp.files == document_files
        results.append('fake_SFTP_partial_or_corrupt_MD_write_rolls_back_same_existing_files')
        original_check = server.check_tree
        def reject_restore(directory, manifest):
            if directory.is_relative_to(server.ROOT / 'restore'):
                raise ValueError('fixture rejects independent restore')
            return original_check(directory, manifest)
        with patch.object(server, 'check_tree', reject_restore):
            reject(lambda: server.main({'action': 'finalize', 'syncid': first_id}))
        assert (control / 'current.json').read_bytes() == old_pointer
        assert server.state()['reference'] == legacy_commit
        assert fake_sftp.files == document_files
        first = server.main({'action': 'finalize', 'syncid': first_id})
        assert first['documents']['mapped'] == 2 and first['documents']['live_verified']
        assert fake_sftp.files['/fake-server/one/trace.md'] == initial['docs/a.md'] and fake_sftp.files['/fake-server/two/trace.md'] == initial['docs/b.md']
        assert set(fake_sftp.files) == set(document_files) and fake_sftp.files['/fake-server/unrelated.bin'] == b'keep unrelated'
        assert not (control / 'document-stage' / first_id).exists()
        reject(lambda: server.write_document(fake_sftp, '/fake-server/unrelated.bin', b'forbidden'))
        reject(lambda: server.write_document(fake_sftp, '/fake-server/missing.md', b'forbidden'))
        results.append('MD_publish_matches_explicit_map_no_new_or_unrelated_science_files')
        parents = server.run(server.git_arguments(repository, server.ROOT) + ['rev-list', '--parents', '-n1', first['commit']], environment).decode().split()
        assert parents == [first['commit']]
        assert first['complete'] and first['restored_verified']
        assert first['history_root'] == first['commit']
        assert original_sentinel.read_bytes() == b'preserve existing archive'
        assert (legacy / 'project/legacy.txt').read_bytes() == b'keep old run'
        server.run(server.git_arguments(repository, server.ROOT) + ['cat-file', '-e', legacy_commit], environment)
        assert server.run(server.git_arguments(repository, server.ROOT) + ['for-each-ref', '--format=%(refname)', 'refs/heads'], environment).decode().split() == [server.FORMAL_REF]
        for item in first_manifest['files']:
            restored = server.run(server.git_arguments(repository, server.ROOT) + ['show', first['commit'] + ':project/' + item['path']], environment)
            assert hashlib.sha256(restored).hexdigest() == item['sha256']
        results.append('orphan_reset_keeps_legacy_objects_runs_archives_no_backup_branch')
        results.append('unexpected_file_and_restore_failure_leave_old_current_and_ref')
        results.append('raw_CRLF_binary_Chinese_ignore_attributes_restore_exactly')

        (source / 'remove.txt').unlink()
        (source / 'ignored.cxs').unlink()
        (source / '正文 空格.md').write_bytes(b'changed\r\nraw bytes\r\n')
        (source / 'added.bin').write_bytes(b'new\0file')
        (source / 'docs/a.md').write_bytes(b'updated second-version document\r\n')
        git_at(source, 'add', '--all')
        git_at(source, 'commit', '--quiet', '-m', 'second fixture')
        second_id = 'test-append-' + uuid.uuid4().hex[:8]
        stage(client, server, source, base, second_id, 'snapshot', first['commit'])
        prior_pointer = (control / 'current.json').read_bytes()
        prior_documents = dict(fake_sftp.files)
        real_replace = server.os.replace
        def fail_pointer(source_path, target_path):
            if Path(target_path) == control / 'current.json':
                raise OSError('fixture rejects pointer publication')
            return real_replace(source_path, target_path)
        with patch.object(server.os, 'replace', fail_pointer):
            reject(lambda: server.main({'action': 'finalize', 'syncid': second_id}))
        assert (control / 'current.json').read_bytes() == prior_pointer
        assert server.state()['reference'] == first['commit']
        assert fake_sftp.files == prior_documents
        second = server.main({'action': 'finalize', 'syncid': second_id})
        parents = server.run(server.git_arguments(repository, server.ROOT) + ['rev-list', '--parents', '-n1', second['commit']], environment).decode().split()
        assert parents == [second['commit'], first['commit']]
        paths = server.run(server.git_arguments(repository, server.ROOT) + ['ls-tree', '-r', '--name-only', second['commit']], environment).decode()
        assert 'project/remove.txt' not in paths and 'project/ignored.cxs' not in paths and 'project/added.bin' in paths
        assert server.main({'action': 'verify', 'syncid': 'test-verify-first', 'commit': first['commit']})['source_head'] == first['source_head']
        assert not server.main({'action': 'verify', 'syncid': 'test-verify-historical-docs', 'commit': first['commit']})['documents']['live_verified']
        reject(lambda: server.main({'action': 'verify', 'syncid': 'test-verify-legacy', 'commit': legacy_commit}))
        reject(lambda: server.main({'action': 'begin', 'syncid': 'test-reset-again', 'operation': 'reset-history', 'expected_current': legacy_commit, 'manifest_sha256': '0' * 64, 'resume': False}))
        results.append('append_parent_and_add_change_delete_are_exact')
        results.append('pointer_publication_failure_rolls_back_ref')
        results.append('old_formal_versions_verify_without_using_current_files')

        (source / '.review/comment.md').write_bytes(b'ignored edit at same HEAD')
        third_id = 'test-same-head-' + uuid.uuid4().hex[:8]
        stage(client, server, source, base, third_id, 'snapshot', second['commit'])
        third = server.main({'action': 'finalize', 'syncid': third_id})
        matching = server.main({'action': 'coverage', 'source_head': second['source_head']})
        assert third['source_head'] == second['source_head'] and len(matching['versions']) == 2
        assert not server.main({'action': 'coverage', 'source_head': 'f' * 40})['covered']
        assert len(server.main({'action': 'coverage'})['versions']) == 3
        results.append('coverage_reports_missing_HEAD_and_multiple_ignored_states_truthfully')

        worktree = base / 'worktree'
        git_at(source, 'worktree', 'add', '--detach', str(worktree), 'HEAD')
        work_capture = base / 'work-capture'
        work_capture.mkdir()
        with redirect_stdout(io.StringIO()):
            work_manifest = client.capture(worktree, work_capture, 'test-worktree-capture', 'snapshot', first_id, third['commit'])
        assert (worktree / '.git').is_file() and not any(item['path'] == '.git' for item in work_manifest['files'])
        work_index = Path(client.git(worktree, 'rev-parse', '--git-path', 'index').decode().strip())
        assert work_manifest['source_index_sha256'] == client.digest(work_index)
        results.append('worktree_git_pointer_excluded_actual_index_preserved')
        change_capture = base / 'change-capture'
        change_capture.mkdir()
        real_inventory = client.inventory
        calls = 0
        def changing_inventory(directory, exclusions):
            nonlocal calls
            if directory == source:
                calls += 1
                if calls == 2:
                    (source / 'added.bin').write_bytes(b'changed during capture')
            return real_inventory(directory, exclusions)
        with patch.object(client, 'inventory', changing_inventory), redirect_stdout(io.StringIO()):
            reject(lambda: client.capture(source, change_capture, 'test-changing-capture', 'snapshot', first_id, third['commit']))
        assert not (change_capture / 'manifest.json').exists()
        results.append('source_changes_do_not_get_complete_capture_manifest')

        # 模拟在正式ref已经替换而current尚未发布时的进程中断.
        fourth_id = 'test-resume-' + uuid.uuid4().hex[:8]
        (source / 'docs/a.md').write_bytes(b'new bytes for interrupted publication')
        stage(client, server, source, base, fourth_id, 'snapshot', third['commit'])
        before_resume = (control / 'current.json').read_bytes()
        before_resume_documents = dict(fake_sftp.files)
        def interrupt_pointer(source_path, target_path):
            if Path(target_path) == control / 'current.json':
                raise KeyboardInterrupt('fixture process interruption')
            return real_replace(source_path, target_path)
        try:
            with patch.object(server.os, 'replace', interrupt_pointer):
                server.main({'action': 'finalize', 'syncid': fourth_id})
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError('中断夹具没有触发')
        assert (control / 'current.json').read_bytes() == before_resume
        assert fake_sftp.files != before_resume_documents
        assert server.state()['pending_publication'] and server.state()['reference'] != third['commit']
        reject(lambda: server.main({'action': 'coverage'}))
        uploaded_manifest = server.ROOT / 'runs' / fourth_id / 'snapshot/manifest.json'
        resumed = server.main({'action': 'begin', 'syncid': fourth_id, 'operation': 'snapshot', 'expected_current': third['commit'], 'manifest_sha256': client.digest(uploaded_manifest), 'resume': True})
        assert resumed['previous']['commit'] == third['commit']
        assert fake_sftp.files == before_resume_documents
        assert server.state()['reference'] == third['commit'] and not server.state()['pending_publication']
        partial_restore = server.ROOT / 'restore' / fourth_id
        partial_restore.mkdir(parents=True)
        (partial_restore / 'incomplete.txt').write_bytes(b'not a valid restore')
        fourth = server.main({'action': 'finalize', 'syncid': fourth_id})
        assert not partial_restore.exists()
        accepted = server.main({'action': 'begin', 'syncid': fourth_id, 'operation': 'snapshot', 'expected_current': third['commit'], 'manifest_sha256': client.digest(uploaded_manifest), 'resume': True})
        assert accepted['published']['commit'] == fourth['commit'] and not server.state()['locked']
        results.append('interrupted_publication_and_partial_restore_resume_same_transaction')
        results.append('already_published_resume_is_idempotent')

        # 正式ref/current均已发布后, 收尾失败不能把现场说明回滚成旧字节.
        real_unlink = Path.unlink
        real_rmtree = server.shutil.rmtree
        for failure in ('publication', 'lock'):
            cleanup_id = 'test-cleanup-' + uuid.uuid4().hex[:8]
            previous = server.state()['current']['commit']
            (source / 'docs/a.md').write_bytes(('new document after ' + failure).encode())
            stage(client, server, source, base, cleanup_id, 'snapshot', previous)
            uploaded = server.ROOT / 'runs' / cleanup_id / 'snapshot/manifest.json'
            injected = []
            def reject_publication_cleanup(path, *args, **kwargs):
                if path == control / 'publication.json' and failure == 'publication' and not injected:
                    injected.append(failure)
                    raise OSError('fixture rejects published journal cleanup')
                return real_unlink(path, *args, **kwargs)
            def reject_lock_cleanup(path, *args, **kwargs):
                if Path(path) == control / 'sync.lock' and failure == 'lock' and not injected:
                    injected.append(failure)
                    raise OSError('fixture rejects published lock cleanup')
                return real_rmtree(path, *args, **kwargs)
            with patch.object(Path, 'unlink', reject_publication_cleanup), patch.object(server.shutil, 'rmtree', reject_lock_cleanup):
                reject(lambda: server.main({'action': 'finalize', 'syncid': cleanup_id}))
            assert injected == [failure]
            published = server.state()
            assert published['current']['syncid'] == cleanup_id and published['reference'] == published['current']['commit']
            assert fake_sftp.files['/fake-server/one/trace.md'] == (source / 'docs/a.md').read_bytes()
            assert fake_sftp.files['/fake-server/two/trace.md'] == (source / 'docs/b.md').read_bytes()
            resumed = server.main({'action': 'begin', 'syncid': cleanup_id, 'operation': 'snapshot', 'expected_current': previous, 'manifest_sha256': client.digest(uploaded), 'resume': True})
            assert resumed['published'] == published['current']
            assert not server.state()['locked'] and not server.state()['pending_publication'] and not server.state()['pending_documents']
            assert fake_sftp.files['/fake-server/one/trace.md'] == (source / 'docs/a.md').read_bytes()
            verified = server.main({'action': 'verify', 'syncid': 'test-cleanup-verify-' + failure, 'commit': published['current']['commit']})
            assert verified['restored_verified'] and not verified['documents']['live_verified']
            results.append('published_' + failure + '_cleanup_failure_keeps_new_documents_and_resumes')

        index_capture = base / 'index-change-capture'
        index_capture.mkdir()
        source_index = source / '.git/index'
        index_before_change = source_index.read_bytes()
        real_digest = client.digest
        index_reads = 0
        def changing_index(path):
            nonlocal index_reads
            if path.resolve() == source_index.resolve():
                index_reads += 1
                if index_reads == 2:
                    source_index.write_bytes(index_before_change + b'interrupted index')
            return real_digest(path)
        try:
            with patch.object(client, 'digest', changing_index), redirect_stdout(io.StringIO()):
                reject(lambda: client.capture(source, index_capture, 'test-index-capture', 'snapshot', first_id, fourth['commit']))
        finally:
            source_index.write_bytes(index_before_change)
        assert not (index_capture / 'manifest.json').exists()
        results.append('source_index_change_prevents_complete_capture')
        reject(lambda: client.clear_capture(source))
        assert source.exists()
        own_capture = client.TEMP_ROOT / ('test-clear-' + uuid.uuid4().hex)
        own_capture.mkdir(parents=True)
        (own_capture / 'own.txt').write_bytes(b'only this capture')
        client.clear_capture(own_capture)
        assert not own_capture.exists()
        if not any(client.TEMP_ROOT.iterdir()):
            client.TEMP_ROOT.rmdir()
        results.append('capture_cleanup_rejects_source_or_other_temp_roots')

        roots = [os.environ.get('PROJECT_MSYS_ROOT'), os.environ.get('MSYS2_ROOT'), 'C:/msys64', 'D:/msys64']
        msys = next(Path(root) / 'usr/bin' for root in roots if root and (Path(root) / 'usr/bin/rsync.exe').is_file())
        transfer_source = base / 'rsync-source'
        previous = base / 'rsync-previous'
        next_mirror = base / 'rsync-next'
        for folder in (transfer_source, previous, next_mirror):
            folder.mkdir()
        (transfer_source / 'keep.bin').write_bytes(b'keep')
        (transfer_source / 'change.bin').write_bytes(b'old!')
        (transfer_source / 'remove.bin').write_bytes(b'remove')
        (next_mirror / 'unexpected.bin').write_bytes(b'delete only here')
        sentinel = base / 'outside-mirror.txt'
        sentinel.write_bytes(b'keep outside')
        paths = [subprocess.check_output([str(msys / 'cygpath.exe'), '-u', str(folder)]).decode().strip() for folder in (transfer_source, previous, next_mirror)]
        command = [str(msys / 'rsync.exe'), '-rt', '--checksum', '--delete']
        subprocess.run(command + [paths[0] + '/', paths[1] + '/'], env={**os.environ, 'MSYS2_ARG_CONV_EXCL': '*'}, check=True)
        (transfer_source / 'change.bin').write_bytes(b'new!')
        (transfer_source / 'remove.bin').unlink()
        (transfer_source / 'new.bin').write_bytes(b'new')
        subprocess.run(command + ['--link-dest=' + paths[1], paths[0] + '/', paths[2] + '/'], env={**os.environ, 'MSYS2_ARG_CONV_EXCL': '*'}, check=True)
        assert {path.name for path in next_mirror.iterdir()} == {'keep.bin', 'change.bin', 'new.bin'}
        assert (previous / 'change.bin').read_bytes() == b'old!' and (previous / 'remove.bin').exists()
        assert sentinel.read_bytes() == b'keep outside'
        (transfer_source / 'keep.bin').write_bytes(b'edit')
        subprocess.run(command + ['--link-dest=' + paths[1], paths[0] + '/', paths[2] + '/'], env={**os.environ, 'MSYS2_ARG_CONV_EXCL': '*'}, check=True)
        assert (previous / 'keep.bin').read_bytes() == b'keep' and (next_mirror / 'keep.bin').read_bytes() == b'edit'
        results.append('actual_local_rsync_delete_bounded_previous_content_immutable')
        assert (external / 'sentinel.txt').read_bytes() == b'outside source'
    finally:
        if base.resolve().parent != test_root.resolve() or not base.resolve().is_relative_to(PROJECT.resolve() / 'temp/figure-centric'):
            raise RuntimeError('测试清理边界不符, 不递归删除')
        def clear_test_readonly(function, path, error):
            # Windows Git blob可带只读属性; 仅清除本轮已创建夹具内的属性.
            if not Path(path).resolve().is_relative_to(base.resolve()):
                raise RuntimeError('只读属性清理越出本次测试夹具')
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            function(path)
        shutil.rmtree(base, onerror=clear_test_readonly)
        if not any(test_root.iterdir()):
            test_root.rmdir()
    print(json.dumps({'LOCAL_CONTRACT_TESTS_OK': True, 'checks': results, 'remote_connections': 0, 'temporary_cleanup_complete': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
