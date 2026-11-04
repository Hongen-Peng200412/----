"""把经过核验的9NVS八视图页追加到Stage1图集, 保全旧页与作者批注.

只承担文件发布与 XML 运输, 不读取或改变科学统计.
运行参数为构建目录; 默认只写 formal-candidate.pptx, --publish 才原子替换正式图集.
publish-receipt.json 保存旧部件保全、追加页码和新图名; 写入前后检测作者并发修改.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import sys
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
sys.path.insert(0, str(ROOT / "转换工具/ops"))
from figure_provenance import Deck, FIGURE, comment_text, set_comment_text, relationship_target, xml_bytes

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def append_figures(build, publish):
    """按候选图名追加一页, 旧页面的图形、备注、批注及媒体解压字节全部保留."""
    formal = ROOT / "画图/stage1可视化.pptx"
    original = formal.read_bytes()
    deck = Deck(formal)
    candidate = Deck(build / "candidate.pptx")
    manifest = json.loads((build / "manifest.json").read_text(encoding="utf-8"))
    assert not (set(candidate.figures) & set(deck.figures)), "正式图集中已有新图名, 不重复追加"
    data = dict(deck.data)
    presentation = E.fromstring(data["ppt/presentation.xml"])
    presentation_rels = E.fromstring(data["ppt/_rels/presentation.xml.rels"])
    content_types = E.fromstring(data["[Content_Types].xml"])
    size = presentation.find(f"{{{P}}}sldSz")
    canvas_width, canvas_height = int(size.get("cx")), int(size.get("cy"))
    slide_ids = presentation.find(f"{{{P}}}sldIdLst")
    next_slide_id = max(int(x.get("id")) for x in slide_ids) + 1
    next_part = max(int(re.search(r"slide(\d+)\.xml$", p).group(1)) for p in data if re.fullmatch(r"ppt/slides/slide\d+\.xml", p)) + 1
    next_note = max(int(re.search(r"notesSlide(\d+)\.xml$", p).group(1)) for p in data if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", p)) + 1
    hp_ids = {node.get("id") for part in deck.author_parts for node in deck.tree(part) if node.get("name") == "Hongen Peng"}
    templates = [(part, node) for slide in deck.slides for part in slide.comments for node in deck.comments(part) if FIGURE.fullmatch(comment_text(node).strip()) and node.get("authorId") in hp_ids]
    assert templates, "必须复用作者 Hongen Peng 的现有批注身份"
    comment_template_part, comment_template = templates[0]
    assert not comment_template.get("authorId").isdigit(), "本图集应复用现有现代作者批注"
    template_slide = next(slide for slide in deck.slides if comment_template_part in slide.comments)
    template_rels = deck.tree(posixpath.join(posixpath.dirname(template_slide.part), "_rels", posixpath.basename(template_slide.part)+".rels"))
    comment_type = next(rel.get("Type") for rel in template_rels if relationship_target(template_slide.part, rel.get("Target")) == comment_template_part)
    comment_content_type = next(x.get("ContentType") for x in content_types if x.get("PartName") == "/"+comment_template_part)
    layout_rel = next(rel for rel in template_rels if rel.get("Type").endswith("/slideLayout"))
    layout_part = relationship_target(template_slide.part, layout_rel.get("Target"))
    note_master = next(p for p in data if re.fullmatch(r"ppt/notesMasters/notesMaster\d+\.xml", p))
    added = []
    for page_index, page in enumerate(manifest):
        source_slide = candidate.figures[page["id"]]
        number, note_number = next_part + page_index, next_note + page_index
        slide_part = f"ppt/slides/slide{number}.xml"
        note_part = f"ppt/notesSlides/notesSlide{note_number}.xml"
        comment_part = f"ppt/comments/stage1-author-9nvs-{number}.xml"
        slide = copy.deepcopy(candidate.tree(source_slide.part))
        shapes = slide.find(f"{{{P}}}cSld/{{{P}}}spTree")
        source_shapes = list(shapes)[2:]
        group = E.Element(f"{{{P}}}grpSp")
        nonvisual = E.SubElement(group, f"{{{P}}}nvGrpSpPr")
        ids = [int(x.get("id")) for x in shapes.iter(f"{{{P}}}cNvPr")]
        E.SubElement(nonvisual, f"{{{P}}}cNvPr", id=str(max(ids)+1), name=page["id"])
        E.SubElement(nonvisual, f"{{{P}}}cNvGrpSpPr")
        E.SubElement(nonvisual, f"{{{P}}}nvPr")
        properties = E.SubElement(group, f"{{{P}}}grpSpPr")
        transform = E.SubElement(properties, f"{{{A}}}xfrm")
        width, height = round(page["width"] * 12700), round(page["height"] * 12700)
        scale = min(canvas_width/width, canvas_height/height)
        E.SubElement(transform, f"{{{A}}}off", x=str((canvas_width-round(width*scale))//2), y=str((canvas_height-round(height*scale))//2))
        E.SubElement(transform, f"{{{A}}}ext", cx=str(round(width*scale)), cy=str(round(height*scale)))
        E.SubElement(transform, f"{{{A}}}chOff", x="0", y="0")
        E.SubElement(transform, f"{{{A}}}chExt", cx=str(width), cy=str(height))
        for shape in source_shapes:
            shapes.remove(shape)
            group.append(shape)
        shapes.append(group)
        data[slide_part] = xml_bytes(slide)
        source_rels_part = posixpath.join(posixpath.dirname(source_slide.part), "_rels", posixpath.basename(source_slide.part)+".rels")
        source_note = next(relationship_target(source_slide.part, x.get("Target")) for x in candidate.tree(source_rels_part) if x.get("Type").endswith("/notesSlide"))
        data[note_part] = candidate.data[source_note]
        note_rels = E.Element(f"{{{PKG}}}Relationships", nsmap={None: PKG})
        E.SubElement(note_rels, f"{{{PKG}}}Relationship", Id="rId1", Type=R+"/notesMaster", Target=posixpath.relpath(note_master, posixpath.dirname(note_part)))
        E.SubElement(note_rels, f"{{{PKG}}}Relationship", Id="rId2", Type=R+"/slide", Target=posixpath.relpath(slide_part, posixpath.dirname(note_part)))
        data[f"ppt/notesSlides/_rels/notesSlide{note_number}.xml.rels"] = xml_bytes(note_rels)
        comments = copy.deepcopy(deck.tree(comment_template_part))
        for child in list(comments):
            comments.remove(child)
        comment = copy.deepcopy(comment_template)
        comment.set("id", "{"+str(uuid.uuid4()).upper()+"}")
        set_comment_text(comment, "@@"+page["id"])
        comments.append(comment)
        data[comment_part] = xml_bytes(comments)
        relations = E.Element(f"{{{PKG}}}Relationships", nsmap={None: PKG})
        for rid, kind, target in (("rId1", R+"/slideLayout", layout_part), ("rId2", R+"/notesSlide", note_part), ("rId3", comment_type, comment_part)):
            E.SubElement(relations, f"{{{PKG}}}Relationship", Id=rid, Type=kind, Target=posixpath.relpath(target, "ppt/slides"))
        for image_index, relation in enumerate(candidate.tree(source_rels_part)):
            if not relation.get("Type").endswith("/image"):
                continue
            old_media = relationship_target(source_slide.part, relation.get("Target"))
            media = f"ppt/media/stage1-author-9nvs-{number}-{image_index}.png"
            data[media] = candidate.data[old_media]
            image_id = f"rIdImage{image_index}"
            for blip in slide.iter(f"{{{A}}}blip"):
                if blip.get(f"{{{R}}}embed") == relation.get("Id"):
                    blip.set(f"{{{R}}}embed", image_id)
            E.SubElement(relations, f"{{{PKG}}}Relationship", Id=image_id, Type=relation.get("Type"), Target=posixpath.relpath(media, posixpath.dirname(slide_part)))
        data[slide_part] = xml_bytes(slide)
        data[f"ppt/slides/_rels/slide{number}.xml.rels"] = xml_bytes(relations)
        relationship_id = "rIdStage1Author"+str(number)
        E.SubElement(presentation_rels, f"{{{PKG}}}Relationship", Id=relationship_id, Type=R+"/slide", Target=f"slides/slide{number}.xml")
        E.SubElement(slide_ids, f"{{{P}}}sldId", id=str(next_slide_id+page_index), attrib={f"{{{R}}}id": relationship_id})
        for part, kind in ((slide_part, "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"), (note_part, "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"), (comment_part, comment_content_type)):
            E.SubElement(content_types, f"{{{CT}}}Override", PartName="/"+part, ContentType=kind)
        added.append({"figure": page["id"], "page": len(deck.slides)+page_index+1, "slide_part": slide_part})
    for part, tree in (("ppt/presentation.xml", presentation), ("ppt/_rels/presentation.xml.rels", presentation_rels), ("[Content_Types].xml", content_types)):
        data[part] = xml_bytes(tree)
    # 新增页数同步到文件属性; 原有页面、备注、批注与媒体内容仍保持原字节.
    properties = E.fromstring(data['docProps/app.xml'])
    properties.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Slides').text = str(len(deck.slides)+len(manifest))
    data['docProps/app.xml'] = xml_bytes(properties)
    modified = [part for part in deck.data if data[part] != deck.data[part]]
    assert set(modified) == {"ppt/presentation.xml", "ppt/_rels/presentation.xml.rels", "[Content_Types].xml", "docProps/app.xml"}
    output = build / "formal-candidate.pptx"
    with ZipFile(output, "w", ZIP_DEFLATED) as package:
        for name, content in data.items():
            package.writestr(name, content)
    reread = Deck(output)
    assert set(candidate.figures) <= set(reread.figures)
    receipt = {"original_sha256": hashlib.sha256(original).hexdigest(), "old_parts_preserved": len(deck.data)-len(modified), "container_parts_modified": modified, "added": added, "published": False}
    if publish:
        assert formal.read_bytes() == original, "作者在构建期间保存了正式PPT, 发布中止以保留最新内容"
        (build / "formal-before-publish.pptx").write_bytes(original)
        os.replace(output, formal)
        receipt["published"] = True
    (build / "publish-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="保全旧部件后向Stage1图集追加一张新图")
    parser.add_argument("build", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    append_figures(args.build.resolve(), args.publish)
