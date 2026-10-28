"""将已审读的本轮候选写回作者 PPT, 并发布三维编辑包.

仅用于本轮 4 页作者基底. FIGURE_BUILD_ROOT 必须指向完整重建通过且已审读的目录.
发布前比较正式基底与冻结作者 4 页的原生形状树; 保留作者前两页, 只替换第 3 页起的授权组件.
"""
import json
import os
from pathlib import Path
import shutil
from zipfile import ZipFile

from lxml import etree as XML
import win32com.client


def signature(path, page):
    """比较原生形状树, 忽略 Office 创建标识等不影响图形的扩展信息."""
    with ZipFile(path) as archive:
        root = XML.fromstring(archive.read(f'ppt/slides/slide{page}.xml'))
    tree = root.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree')
    for node in tree.xpath('.//*[local-name()="extLst"]'):
        node.getparent().remove(node)
    return XML.tostring(tree, method='c14n')


def main():
    root = next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    formal = root / '画图/总览图.pptx'
    frozen = root / '画图/画图代码/e2e/output/overview-redesign-20261028/source/author.pptx'
    candidate = build / 'rebuilt.pptx'
    assert json.loads((build/'receipt.json').read_text(encoding='utf8'))['passed']
    assert all(signature(formal,page)==signature(frozen,page) for page in range(1,5)), '作者基底已变化, 先合并新编辑'
    assert all(signature(candidate,page)==signature(frozen,page) for page in [1,2])
    backup = build / 'publication'
    backup.mkdir(exist_ok=True)
    app = win32com.client.GetActiveObject('PowerPoint.Application')
    existing = next((p for p in app.Presentations if p.FullName==str(formal)),None)
    target = existing if existing is not None else app.Presentations.Open(str(formal),0,0,0)
    assert target.Saved, '正式 PPT 有未保存的作者编辑'
    assert target.Slides.Count == 4
    target.SaveCopyAs(str(backup/'formal-before.pptx'))
    source = app.Presentations.Open(str(candidate),-1,0,0)
    while target.Slides.Count < source.Slides.Count:
        target.Slides.Add(target.Slides.Count+1,12)
    for page in range(3,source.Slides.Count+1):
        src, dst = source.Slides.Item(page), target.Slides.Item(page)
        for i in range(dst.Shapes.Count,0,-1):
            dst.Shapes.Item(i).Delete()
        for shape in src.Shapes:
            shape.Copy()
            pasted = dst.Shapes.Paste().Item(1)
            pasted.Left, pasted.Top = shape.Left, shape.Top
        for i in range(dst.Comments.Count,0,-1):
            dst.Comments.Item(i).Delete()
        for comment in src.Comments:
            dst.Comments.Add(comment.Left,comment.Top,'Figure','F',comment.Text)
        note = next(s.TextFrame.TextRange.Text for s in src.NotesPage.Shapes if s.Type==14 and s.PlaceholderFormat.Type==2)
        for shape in dst.NotesPage.Shapes:
            if shape.Type==14 and shape.PlaceholderFormat.Type==2:
                shape.TextFrame.TextRange.Text=note
        dst.Name=src.Name
    target.Save()
    for page in range(1,target.Slides.Count+1):
        target.Slides.Item(page).Export(str(backup/f'published-{page}.png'),'PNG',2500,960)
    target.SaveCopyAs(str(backup/'published.pdf'),32)
    source.Close()
    if existing is None:
        target.Close()
    assert all(signature(formal,page)==signature(frozen,page) for page in [1,2])
    package = root / '画图/总览图_ChimeraX'
    assert not package.exists(), '交付目录已存在, 不覆盖可能的作者编辑'
    shutil.copytree(build/'editing-package',package)
    shutil.copy2(build/'preview/slide-10.png',package/'组合预览_半透明.png')
    shutil.make_archive(str(package),'zip',root_dir=package.parent,base_dir=package.name)
    receipt={'published_pptx':str(formal),'slides':12,'author_slides_1_2_preserved':True,'native_package':str(package),'zip':str(package.with_suffix('.zip'))}
    (backup/'publication.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    main()
