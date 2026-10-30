"""在 temp 内合成最小图集, 验证来源批注同步不会修改论文内容或作者身份."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("figure_provenance", ROOT / "转换工具/ops/figure_provenance.py")
provenance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = provenance
SPEC.loader.exec_module(provenance)
XML = provenance.XML


def make_deck(path: Path, modern: bool) -> None:
    """slide7 位于第二页, 名字与顺序故意不一致, 以验证关系定位."""
    p, a, m, r, pr = provenance.P, provenance.A, provenance.M, provenance.R, provenance.PACKAGE_R
    namespace = m if modern else p
    prefix = "m" if modern else "p"
    comments = f'<{prefix}:cmLst xmlns:{prefix}="{namespace}" xmlns:a="{a}">'
    for index, text in enumerate(("@@test-modern" if modern else "@@test-legacy", "作者原有批注: 保留 &amp; 保留"), 1):
        if modern:
            comments += f'<m:cm id="{{comment-{index}}}" authorId="author-local" created="2026-01-01T00:00:00Z"><m:pos x="0" y="0"/><m:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{text}</a:t></a:r></a:p></m:txBody></m:cm>'
        else:
            comments += f'<p:cm authorId="0" dt="2026-01-01T00:00:00Z" idx="{index}"><p:pos x="0" y="0"/><p:text>{text}</p:text></p:cm>'
    comments += f'</{prefix}:cmLst>'
    author_part = "ppt/authors.xml" if modern else "ppt/commentAuthors.xml"
    author_type = "http://schemas.microsoft.com/office/2018/10/relationships/authors" if modern else r + "/commentAuthors"
    author = f'<m:authorLst xmlns:m="{m}"><m:author id="author-local" name="Original author" userId="original-account" providerId="existing"/></m:authorLst>' if modern else f'<p:cmAuthorLst xmlns:p="{p}"><p:cmAuthor id="0" name="Original author" initials="OA" lastIdx="2" clrIdx="0"/></p:cmAuthorLst>'
    files = {
        "ppt/presentation.xml": f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId7"/></p:sldIdLst></p:presentation>',
        "ppt/_rels/presentation.xml.rels": f'<Relationships xmlns="{pr}"><Relationship Id="rId2" Type="{r}/slide" Target="slides/slide2.xml"/><Relationship Id="rId7" Type="{r}/slide" Target="slides/slide7.xml"/><Relationship Id="rIdAuthor" Type="{author_type}" Target="{Path(author_part).name}"/></Relationships>',
        "ppt/slides/slide2.xml": f'<p:sld xmlns:p="{p}"/>',
        "ppt/slides/slide7.xml": f'<p:sld xmlns:p="{p}"><p:cSld name="手工图形"/></p:sld>',
        "ppt/slides/_rels/slide7.xml.rels": f'<Relationships xmlns="{pr}"><Relationship Id="rId9" Type="{r}/comments" Target="../comments/comment7.xml"/></Relationships>',
        "ppt/comments/comment7.xml": comments,
        author_part: author,
        "ppt/notesSlides/notesSlide7.xml": "<notes>手工双语备注</notes>",
        "unknown/future-extension.bin": b"\x00\xff\x80unknown-extension\r\n",
        "[Content_Types].xml": "<Types/>",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as package:
        package.comment = b"preserve archive comment"
        for name, text in files.items():
            package.writestr(name, text if isinstance(text, bytes) else text.encode("utf-8"))


def record(identifier: str, kind: str, **extra) -> str:
    metadata = {"id": identifier, "kind": kind, "entries": [{"path": "画图/画图代码/stage1/calculate/figure/draw.py", "symbol": "Renderer.draw"}], "inputs": ["画图/画图代码/stage1/output/raw.json"], "status": "已核验", **extra}
    if kind=='figure':metadata.update(sharing=[],rebuild={'script':'转换工具/ops/rebuild_figures.py','figure':metadata['figure']})
    return f'<!-- provenance:begin {identifier} -->\n<!-- provenance-meta {json.dumps(metadata, ensure_ascii=False)} -->\n## {identifier}\n\n完整的科学来源.\n第二行含 <xml> & 符号.\n<!-- provenance:end {identifier} -->\n'


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "temp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="figure_provenance_test_", dir=ROOT / "temp")
        self.root = Path(self.temporary.name)
        rebuild=self.root/'转换工具/ops/rebuild_figures.py'
        rebuild.parent.mkdir(parents=True)
        rebuild.write_text('# isolated test entry\n',encoding='utf-8')
        for stage in (*provenance.STAGES, "archive"):
            for category in ("calculate", "visualization", "output"):
                (self.root / "画图/画图代码" / stage / category).mkdir(parents=True)
        self.document = self.root / "画图/画图代码/stage1/calculate/图表追溯.md"
        for stage in provenance.STAGES:
            for category in provenance.CATEGORIES:
                (self.root / "画图/画图代码" / stage / category / "图表追溯.md").write_text("# 来源\n", encoding="utf-8")
        script = self.document.parent / "figure/draw.py"
        script.parent.mkdir()
        script.write_text("class Renderer:\n    def draw(self):\n        return 42\n", encoding="utf-8")
        (self.root / "画图/画图代码/stage1/output/raw.json").write_text('{"value":42}', encoding="utf-8")
        self.document.write_text(record("modern", "figure", pptx="画图/modern.pptx", figure="test-modern") + record("legacy", "figure", pptx="画图/legacy.pptx", figure="test-legacy") + "".join(record(f"table-{number}", "table", table=number) for number in range(1, 5)) + record("claim-speed", "claim"), encoding="utf-8")
        for name in provenance.MANUSCRIPTS:
            (self.root / name).write_text('{{pptfig:"画图/modern.pptx"|test-modern}}\n{{pptfig:"画图/legacy.pptx"|test-legacy}}\n' + "\n".join(f"<caption>Table {number} | Results</caption>" for number in range(1, 5)), encoding="utf-8")
        make_deck(self.root / "画图/modern.pptx", True)
        make_deck(self.root / "画图/legacy.pptx", False)

    def tearDown(self):
        self.temporary.cleanup()

    def test_sync_check_idempotence_and_preservation(self):
        before = {}
        for name in ("modern", "legacy"):
            with ZipFile(self.root / f"画图/{name}.pptx") as package:
                before[name] = {part: package.read(part) for part in package.namelist()}
        self.assertTrue(provenance.run(self.root)["errors"])
        report = provenance.run(self.root, True)
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["updated"]), 2)
        self.assertEqual(provenance.run(self.root)["errors"], [])
        after = {}
        for name in ("modern", "legacy"):
            path = self.root / f"画图/{name}.pptx"
            after[name] = path.read_bytes()
            with ZipFile(path) as package:
                self.assertEqual(package.comment, b"preserve archive comment")
                for part, payload in before[name].items():
                    if part == "ppt/comments/comment7.xml" or (name == "legacy" and part == "ppt/commentAuthors.xml"):
                        continue
                    self.assertEqual(package.read(part), payload, part)
            deck = provenance.Deck(path)
            self.assertEqual(deck.figures[f"test-{name}"].page, 2)
            comments = deck.comments("ppt/comments/comment7.xml")
            self.assertEqual(provenance.comment_text(comments[1]), "作者原有批注: 保留 & 保留")
            self.assertEqual(len(comments), 3)
            old_root = XML.fromstring(before[name]["ppt/comments/comment7.xml"])
            self.assertEqual(XML.tostring(old_root[0]), XML.tostring(comments[0]))
            self.assertEqual(XML.tostring(old_root[1]), XML.tostring(comments[1]))
        self.assertEqual(provenance.run(self.root, True)["updated"], [])
        for name in after:
            self.assertEqual((self.root / f"画图/{name}.pptx").read_bytes(), after[name])

    def test_existing_source_updates_without_touching_author_comments(self):
        self.assertEqual(provenance.run(self.root, True)["errors"], [])
        self.document.write_text(self.document.read_text(encoding="utf-8").replace("完整的科学来源", "更新的完整科学来源"), encoding="utf-8")
        self.assertTrue(any("不一致" in error for error in provenance.run(self.root)["errors"]))
        self.assertEqual(provenance.run(self.root, True)["errors"], [])
        deck = provenance.Deck(self.root / "画图/modern.pptx")
        self.assertEqual(len(deck.comments("ppt/comments/comment7.xml")), 3)
        self.assertIn("更新的完整科学来源", provenance.comment_text(deck.managed()["modern"][0][2]))

    def test_reordered_slide_is_found_by_relationship(self):
        self.assertEqual(provenance.run(self.root, True)["errors"], [])
        path = self.root / "画图/modern.pptx"
        with ZipFile(path) as package:
            payloads = {part: package.read(part) for part in package.namelist()}
        presentation = XML.fromstring(payloads["ppt/presentation.xml"])
        slides = presentation.find(f"{{{provenance.P}}}sldIdLst")
        slides.insert(0, slides[-1])
        payloads["ppt/presentation.xml"] = provenance.xml_bytes(presentation)
        with ZipFile(path, "w") as package:
            for part, payload in payloads.items():
                package.writestr(part, payload)
        self.assertEqual(provenance.Deck(path).figures["test-modern"].page, 1)
        self.assertEqual(provenance.run(self.root)["errors"], [])

    def test_missing_function_and_unregistered_reference_fail_without_writes(self):
        original = (self.root / "画图/modern.pptx").read_bytes()
        self.document.write_text(self.document.read_text(encoding="utf-8").replace("Renderer.draw", "Renderer.missing"), encoding="utf-8")
        manuscript = self.root / "论文草稿.md"
        manuscript.write_text(manuscript.read_text(encoding="utf-8") + '\n{{pptfig:"画图/modern.pptx"|unregistered}}', encoding="utf-8")
        report = provenance.run(self.root, True)
        self.assertTrue(any("符号不存在" in error for error in report["errors"]))
        self.assertTrue(any("论文插图未登记" in error for error in report["errors"]))
        self.assertEqual((self.root / "画图/modern.pptx").read_bytes(), original)

    def test_missing_comments_relationship_and_unknown_marker_fail_explicitly(self):
        self.document.write_text(self.document.read_text(encoding="utf-8").replace('"figure": "test-modern"', '"figure": "missing-marker"'), encoding="utf-8")
        report = provenance.run(self.root, True)
        self.assertTrue(any("无 comments 关系" in error for error in report["errors"]))

    def test_missing_input_table_document_and_bad_layout_fail(self):
        (self.root / "画图/画图代码/stage1/output/raw.json").unlink()
        self.document.write_text(self.document.read_text(encoding="utf-8").replace('"table": 4', '"table": 3'), encoding="utf-8")
        (self.root / "画图/画图代码/stage3/visualization/图表追溯.md").unlink()
        (self.root / "画图/画图代码/extra").mkdir()
        errors = provenance.run(self.root)["errors"]
        self.assertTrue(any("冻结输入不存在" in error for error in errors))
        self.assertTrue(any("表 4" in error for error in errors))
        self.assertTrue(any("追溯文档缺失" in error for error in errors))
        self.assertTrue(any("顶层须恰为" in error for error in errors))

    def test_missing_author_aborts_all_ppt_writes(self):
        modern_path = self.root / "画图/modern.pptx"
        original = modern_path.read_bytes()
        legacy_path = self.root / "画图/legacy.pptx"
        with ZipFile(legacy_path) as package:
            payloads = {part: package.read(part) for part in package.namelist()}
        payloads["ppt/commentAuthors.xml"] = payloads["ppt/commentAuthors.xml"].replace(b'id="0"', b'id="999"')
        with ZipFile(legacy_path, "w") as package:
            for part, payload in payloads.items():
                package.writestr(part, payload)
        report = provenance.run(self.root, True)
        self.assertTrue(any("不创建账户" in error for error in report["errors"]))
        self.assertEqual(report["updated"], [])
        self.assertEqual(modern_path.read_bytes(), original)

    def test_saved_author_changes_are_never_overwritten(self):
        path = self.root / "画图/modern.pptx"
        deck = provenance.Deck(path)
        deck.append(deck.figures["test-modern"], "PROVENANCE v1\nid: conflict\nsource: test\n\n来源")
        authored = path.read_bytes() + b"author save"
        path.write_bytes(authored)
        with self.assertRaisesRegex(ValueError, "外部修改"):
            deck.save(self.root, self.root / "temp/backup")
        self.assertEqual(path.read_bytes(), authored)

    def test_cross_directory_import_needs_explicit_shared_relationship(self):
        draw=self.root/'画图/画图代码/stage1/calculate/figure/draw.py'
        shared=draw.parent.parent/'shared/core.py'
        shared.parent.mkdir();shared.write_text('raise RuntimeError("must not execute")\n',encoding='utf-8')
        with draw.open('a',encoding='utf-8') as handle:
            handle.write('from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"shared"))\nimport core\n')
        records=provenance.load_records(self.root,[]);errors=[]
        provenance.check_sources(self.root,records,errors)
        self.assertTrue(any('未登记跨目录代码依赖' in error for error in errors))
        fixed=[]
        for item in records:
            metadata=dict(item.metadata)
            if metadata['kind']=='figure':metadata['sharing']=[{'path':shared.parent.relative_to(self.root).as_posix(),'figures':['test-modern','test-legacy'],'purpose':'共享同一测试绘图核心'}]
            fixed.append(provenance.Record(item.identifier,item.document,metadata,item.body+'\n共享 @@test-modern 和 @@test-legacy'))
        errors=[];provenance.check_sources(self.root,fixed,errors)
        self.assertEqual(errors,[])

    def test_transitive_old_temp_search_path_is_rejected(self):
        draw=self.root/'画图/画图代码/stage1/calculate/figure/draw.py'
        with draw.open('a',encoding='utf-8') as handle:
            handle.write('from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[5]/"temp/pkg"))\n')
        errors=[];provenance.check_sources(self.root,provenance.load_records(self.root,[]),errors)
        self.assertTrue(any('旧temp搜索路径' in error for error in errors))

    def test_author_version_inherits_source_and_copied_comment_is_renamed(self):
        self.assertEqual(provenance.run(self.root, True)['errors'], [])
        path=self.root/'画图/modern.pptx'
        with ZipFile(path) as package:
            files={name:package.read(name) for name in package.namelist()}
        files['ppt/slides/_rels/slide2.xml.rels']=files['ppt/slides/_rels/slide7.xml.rels'].replace(b'comment7.xml',b'comment2.xml')
        files['ppt/comments/comment2.xml']=files['ppt/comments/comment7.xml'].replace(b'@@test-modern',b'@@test-modern(v1)')
        with ZipFile(path,'w') as package:
            for name,payload in files.items():package.writestr(name,payload)
        manuscript=self.root/'论文草稿.md'
        manuscript.write_text(manuscript.read_text(encoding='utf-8')+'\n{{pptfig:"画图/modern.pptx"|test-modern(v1)}}',encoding='utf-8')
        self.assertEqual(provenance.run(self.root,True)['errors'],[])
        deck=provenance.Deck(path)
        self.assertEqual(len(deck.managed()['modern']),1)
        self.assertEqual(deck.managed()['test-modern(v1)'][0][0].page,1)
        records=provenance.load_records(self.root,[])
        derived=next(r for r in records if r.identifier=='test-modern(v1)')
        self.assertEqual(derived.metadata['inputs'],next(r for r in records if r.identifier=='modern').metadata['inputs'])
        self.assertEqual(derived.metadata['rebuild']['figure'],'test-modern')
        self.assertEqual(provenance.run(self.root)['errors'],[])
        self.assertEqual(provenance.base_figure('x-NO_LEVEL(v12)'),'x-NO_LEVEL')
        self.assertEqual(provenance.base_figure('x-color1'),'x-color1')

    def test_figure_editor_uses_existing_author_without_adding_an_account(self):
        path=self.root/'画图/modern.pptx';deck=provenance.Deck(path)
        authors=deck.tree('ppt/authors.xml');existing=authors[0]
        alias=XML.fromstring(XML.tostring(existing))
        alias.set('id','placeholder');alias.set('name','Figure Editor');alias.set('initials','FE');authors.append(alias)
        existing.set('name','Hongen Peng');existing.set('initials','HP')
        comments=deck.comments('ppt/comments/comment7.xml');comments[0].set('authorId','placeholder')
        texts=[provenance.comment_text(c) for c in comments]
        deck.use_author('Hongen Peng','HP')
        self.assertEqual(len(authors),1)
        self.assertEqual(comments[0].get('authorId'),existing.get('id'))
        self.assertEqual(texts,[provenance.comment_text(c) for c in comments])

    def test_legacy_author_merge_keeps_comment_indices_unique(self):
        deck=provenance.Deck(self.root/'画图/legacy.pptx')
        authors=deck.tree('ppt/commentAuthors.xml');authors[0].set('name','Hongen Peng')
        alias=XML.fromstring(XML.tostring(authors[0]));alias.set('id','1');alias.set('name','Figure Editor');authors.append(alias)
        comments=deck.tree('ppt/comments/comment7.xml')
        copied=XML.fromstring(XML.tostring(comments[0]));copied.set('authorId','1');comments.append(copied)
        deck.use_author('Hongen Peng','HP')
        keys=[(c.get('authorId'),c.get('idx')) for c in comments]
        self.assertEqual(len(keys),len(set(keys)))
        self.assertEqual(len(authors),1)
        self.assertGreater(int(authors[0].get('lastIdx')),2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
