import hashlib, json, os, subprocess, sys
from pathlib import Path
from uuid import uuid4
engine = Path(__file__).resolve().parents[1] / 'sync_snapshot.py'
root = Path(__file__).resolve().parents[3] / 'temp/git-snapshot-verification' / ('case-' + uuid4().hex[:8])
source, destination = root / '母目录 & 空格', root / '副本 & 空格'
source.mkdir(parents=True)
destination.mkdir()
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
def git(*args, allowed=(0,)):
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.quotepath=false', *args], cwd=source, env=env, capture_output=True)
    assert result.returncode in allowed, result.stderr.decode('utf-8', 'replace')
    return result.stdout

def write(name, data):
    path = source / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)

def sync(label, clean=1, expected=0, base=None):
    before_index = (source/'.git/index').read_bytes()
    result = subprocess.run([sys.executable, '-B', str(engine), '--source', str(source), '--destination', str(destination), '--baseline', base or baseline, '--clean-old-reports', str(clean)], env=env, capture_output=True)
    (root/(label+'.log')).write_bytes(result.stdout + result.stderr)
    print(result.stdout.decode('utf-8', 'replace'))
    assert result.returncode == expected, result.stderr.decode('utf-8', 'replace')
    assert (source/'.git/index').read_bytes() == before_index, 'source index modified'
    return result.stdout

git('init', '--quiet')
git('config', 'user.name', 'Snapshot test')
git('config', 'user.email', 'test@example.invalid')
write('obsolete.dat', os.urandom(65536))
git('add', '.')
git('commit', '-qm', 'old history')
old_head = git('rev-parse','HEAD').decode().strip()
old_blob = git('rev-parse','HEAD:obsolete.dat').decode().strip()
git('rm', '-q', 'obsolete.dat')
write('.gitignore', 'temp/\n*.secret\n')
write('部分暂存 [1] & ! 100%.md', 'A\n')
write('tracked.secret', 'tracked and now ignored')
write('delete.md', 'will disappear')
write('rename.md', 'will rename')
write('index-delete.md', 'keep disk, remove index')
git('add', '.')
git('add', '-f', 'tracked.secret')
git('commit','-qm','baseline')
baseline = git('rev-parse','HEAD').decode().strip()
(destination/'独立文件.txt').write_text('preserve', encoding='utf-8')
sync('01-initial')
assert (destination/'tracked.secret').is_file()
assert (destination/'独立文件.txt').read_text() == 'preserve'
assert subprocess.run(['git','cat-file','-e',old_head], cwd=destination, capture_output=True).returncode != 0
assert subprocess.run(['git','cat-file','-e',old_blob], cwd=destination, capture_output=True).returncode != 0
assert subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=destination).strip() == b'1'
print('PASS shallow boundary and tracked ignored copy')
(destination/'.tmp.driveupload').mkdir()
(destination/'.tmp.driveupload/internal').write_bytes(b'cloud internal')
write('部分暂存 [1] & ! 100%.md', 'B\n')
git('add','--','部分暂存 [1] & ! 100%.md')
write('部分暂存 [1] & ! 100%.md', 'C\n')
write('staged-binary.dat', b'\x00\x01\xff'*4000)
git('add','staged-binary.dat')
git('rm','--cached','-q','index-delete.md')
git('mv','rename.md','renamed.md')
(source/'delete.md').unlink()
write('untracked.md', 'new untracked text\n')
sync('02-partial-staging', clean=0)
expected_staged = git('diff','--cached','--no-ext-diff','--no-textconv','--no-renames')
actual_staged = subprocess.check_output(['git','-c','core.quotepath=false','diff','--cached','--no-ext-diff','--no-textconv','--no-renames'],cwd=destination)
assert expected_staged == actual_staged
assert subprocess.check_output(['git','show',':部分暂存 [1] & ! 100%.md'],cwd=destination) == b'B\n'
assert (destination/'部分暂存 [1] & ! 100%.md').read_bytes() == b'C\n'
assert not (destination/'delete.md').exists()
assert (destination/'index-delete.md').exists()
assert (destination/'temp/AI-Git/history').is_dir()
assert not (destination/'.git/objects/info/alternates').exists()
assert not subprocess.check_output(['git','remote'],cwd=destination).strip()
print('PASS staged B / unstaged C / staged blob / deletion / rename / untracked / archive off')
assert b'.tmp.driveupload' not in subprocess.check_output(['git','status','--porcelain=v1'],cwd=destination)
print('PASS Drive internal uploads do not pollute Git status')
out = sync('03-repeat-clean')
assert '更新 0'.encode() in out
assert not (destination/'temp/AI-Git/history').exists()
report = (destination/'temp/AI-Git/当前Git改动报告.md').read_text(encoding='utf-8')
assert 'Staged 改动' in report and 'Unstaged 改动' in report and '+B' in report and '+C' in report
assert (destination/'temp/AI-Git/当前Git改动报告.pdf').read_bytes().startswith(b'%PDF-')
print('PASS repeat no rewrite / clean history / fixed report paths / PDF')
git('add','-A')
git('commit','-qm','after baseline')
new_head=git('rev-parse','HEAD').strip()
sync('04-new-commit')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=destination).strip() == new_head
assert subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=destination).strip() == b'2'
assert subprocess.run(['git','cat-file','-e',old_head],cwd=destination,capture_output=True).returncode != 0
print('PASS subsequent commit kept with original SHA, old history still absent')
(source/'.git/index.lock').write_text('test lock')
sync('05-source-lock', expected=1)
(source/'.git/index.lock').unlink()
print('PASS source lock blocks synchronization')
print('ALL TESTS PASSED', root)
