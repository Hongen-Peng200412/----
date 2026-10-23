"""用独立夹具验证旧temp屏蔽、冻结输入写保护与实际跨目录导入登记。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'转换工具/ops'))
from rebuild_support.source_dependencies import code_dependencies


class RebuildTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(dir=ROOT/'temp',prefix='rebuild-test-')
        self.root=Path(self.work.name)
        self.build=self.root/'temp/current';self.build.mkdir(parents=True)
        self.old=self.root/'temp/old/input.json';self.old.parent.mkdir();self.old.write_text('{"value":42}',encoding='utf-8')
        self.frozen=self.root/'output/input.json';self.frozen.parent.mkdir();self.frozen.write_text('{"value":42}',encoding='utf-8')
        self.env=dict(os.environ,FIGURE_VERIFY_ROOT=str(self.root),FIGURE_BUILD_ROOT=str(self.build),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'转换工具/ops/rebuild_support'))

    def tearDown(self):self.work.cleanup()

    def test_python_blocks_old_temp_and_frozen_writes(self):
        code='from pathlib import Path\nimport shutil\n'+f'old=Path({str(self.old)!r});frozen=Path({str(self.frozen)!r});build=Path({str(self.build)!r})\n'+'''assert frozen.read_text()=='{"value":42}'
try:old.read_text()
except FileNotFoundError:pass
else:raise AssertionError('old temp was readable')
try:frozen.write_text('changed')
except PermissionError:pass
else:raise AssertionError('frozen input was writable')
try:shutil.copyfile(old,build/'copied.json')
except FileNotFoundError:pass
else:raise AssertionError('old temp copy was permitted')
try:(build/'..'/'old'/'input.json').read_text()
except FileNotFoundError:pass
else:raise AssertionError('parent traversal reached old temp')
'''
        result=subprocess.run([sys.executable,'-B','-c',code],env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.frozen.read_text(),'{"value":42}')

    def test_node_blocks_read_and_copy_from_old_temp(self):
        node=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
        script='const fs=require("node:fs");'+f'const old={json.dumps(str(self.old))},frozen={json.dumps(str(self.frozen))},target={json.dumps(str(self.build/"copy.json"))};'+'''fs.readFileSync(frozen);for(const action of [()=>fs.readFileSync(old),()=>fs.copyFileSync(old,target),()=>fs.writeFileSync(frozen,'changed')]){let blocked=false;try{action()}catch(error){blocked=true}if(!blocked)throw Error('guard did not block')}'''
        result=subprocess.run([str(node),'--require',str(ROOT/'转换工具/ops/rebuild_support/node_guard.cjs'),'-e',script],env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.build/'copy.json').exists())

    def test_cross_directory_alias_is_discovered_without_importing(self):
        directory=self.root/'画图/画图代码/e2e/calculate'
        source=directory/'one/draw.py';source.parent.mkdir(parents=True)
        shared=directory/'shared/draw_core.py';shared.parent.mkdir()
        shared.write_text('raise RuntimeError("must not execute")\n',encoding='utf-8')
        source.write_text('from pathlib import Path\nimport sys\nSHARED=Path(__file__).resolve().parents[1]/"shared"\nsys.path.insert(0,str(SHARED))\nimport draw_core\n',encoding='utf-8')
        paths,temporary=code_dependencies(self.root,[{'path':source.relative_to(self.root).as_posix()}])
        self.assertIn(shared,paths);self.assertFalse(temporary)


if __name__=='__main__':unittest.main()
