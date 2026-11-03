"""按作者提供的 SVG 转原生 PPT 模板运输几何和文字, 不参与统计或重画实验内容.

build_editable_candidate 读取同次 manifest.json 和 figures/*.svg, 在构建目录生成4页 candidate.pptx.
保留独立点、线、柱和路径, 读取 SVG font 简写中的实际字号和粗体, 使用与源图相同的 Arial.
候选每页含双语备注和作者 Hongen Peng/HP 的独立 @@ 图名批注; 正式 PPT 由发布步骤保全旧部件后追加新页.
"""

import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
sys.path.append(str(ROOT / ".manuscript_deps"))

import base64
import io
from PIL import Image
import math
import os
import json
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, timezone
import re
import lxml.etree as ET
from pptx import Presentation
from pptx.util import Emu

PT_TO_EMU = 12700.0  # 1 pt = 1/72 inch = 914400 / 72 = 12700 EMU

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
ET.register_namespace("p", NS_P)
ET.register_namespace("a", NS_A)


def parse_style(style_str, attrib=None):
    st = {}
    if attrib:
        for k in ("fill", "stroke", "stroke-width", "fill-opacity", "stroke-opacity",
                  "opacity", "stroke-dasharray", "font-size", "font-weight", "text-anchor"):
            if k in attrib:
                st[k] = attrib[k].strip()
    if style_str:
        for part in style_str.split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip()
    # Matplotlib 的 font 简写同时携带字重和字号, 不能全部回退成 8pt.
    if "font" in st:
        match = re.search(r"(?:(bold|[1-9]00)\s+)?([\d.]+)(?:px|pt)\s+", st["font"])
        if match:
            st["font-size"] = match.group(2)
            st["font-weight"] = match.group(1) or "normal"
    return st


def clean_hex(color_str):
    if not color_str or color_str == "none":
        return None
    color_str = color_str.strip()
    if color_str.startswith("#"):
        h = color_str[1:].upper()
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return h[:6]
    named = {"WHITE": "FFFFFF", "BLACK": "000000"}
    return named.get(color_str.upper(), "243442")


def parse_svg_path_d(d_str, tx=0.0, ty=0.0):
    """
    Parses SVG path 'd' into a list of subpaths, where each subpath is:
      {"pts": [(x, y), ...], "closed": bool, "is_circle": (cx, cy, r) or None}
    Samples cubic Beziers smoothly into polyline vertices.
    """
    tokens = re.findall(r"[MmLlHhVvCcZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_str)
    idx = 0
    subpaths = []
    curr_pts = []
    cx, cy = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    cmd = None

    while idx < len(tokens):
        tok = tokens[idx]
        if re.match(r"^[MmLlHhVvCcZz]$", tok):
            cmd = tok
            idx += 1
            if cmd in ("z", "Z"):
                if curr_pts:
                    subpaths.append({"pts": curr_pts, "closed": True})
                    curr_pts = []
                cx, cy = start_x, start_y
            continue

        if cmd == "M":
            x, y = float(tokens[idx]) + tx, float(tokens[idx + 1]) + ty
            idx += 2
            if curr_pts:
                subpaths.append({"pts": curr_pts, "closed": False})
            curr_pts = [(x, y)]
            cx, cy = x, y
            start_x, start_y = x, y
            cmd = "L"
        elif cmd == "m":
            x, y = cx + float(tokens[idx]), cy + float(tokens[idx + 1])
            idx += 2
            if curr_pts:
                subpaths.append({"pts": curr_pts, "closed": False})
            curr_pts = [(x, y)]
            cx, cy = x, y
            start_x, start_y = x, y
            cmd = "l"
        elif cmd == "L":
            x, y = float(tokens[idx]) + tx, float(tokens[idx + 1]) + ty
            idx += 2
            curr_pts.append((x, y))
            cx, cy = x, y
        elif cmd == "l":
            x, y = cx + float(tokens[idx]), cy + float(tokens[idx + 1])
            idx += 2
            curr_pts.append((x, y))
            cx, cy = x, y
        elif cmd == "H":
            x = float(tokens[idx]) + tx
            idx += 1
            curr_pts.append((x, cy))
            cx = x
        elif cmd == "V":
            y = float(tokens[idx]) + ty
            idx += 1
            curr_pts.append((cx, y))
            cy = y
        elif cmd == "C":
            x1, y1 = float(tokens[idx]) + tx, float(tokens[idx + 1]) + ty
            x2, y2 = float(tokens[idx + 2]) + tx, float(tokens[idx + 3]) + ty
            x3, y3 = float(tokens[idx + 4]) + tx, float(tokens[idx + 5]) + ty
            idx += 6
            for step in range(1, 7):
                t = step / 6.0
                mt = 1.0 - t
                bx = mt**3 * cx + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x3
                by = mt**3 * cy + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y3
                curr_pts.append((bx, by))
            cx, cy = x3, y3
        else:
            idx += 1

    if curr_pts:
        subpaths.append({"pts": curr_pts, "closed": False})
    return subpaths


def make_shape_xml(shape_id, name, subpaths, fill_hex, fill_alpha, stroke_hex, stroke_alpha, stroke_w_pt, dash_type, is_ellipse=None):
    sp = ET.Element(f"{{{NS_P}}}sp")
    nvSpPr = ET.SubElement(sp, f"{{{NS_P}}}nvSpPr")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvPr", id=str(shape_id), name=name)
    cNvSpPr = ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvSpPr")
    ET.SubElement(cNvSpPr, f"{{{NS_A}}}spLocks")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}nvPr")

    spPr = ET.SubElement(sp, f"{{{NS_P}}}spPr")

    if is_ellipse is not None:
        cx_pt, cy_pt, rx_pt, ry_pt = is_ellipse
        x_emu = int(round((cx_pt - rx_pt) * PT_TO_EMU))
        y_emu = int(round((cy_pt - ry_pt) * PT_TO_EMU))
        w_emu = max(int(round(2 * rx_pt * PT_TO_EMU)), 1)
        h_emu = max(int(round(2 * ry_pt * PT_TO_EMU)), 1)
        xfrm = ET.SubElement(spPr, f"{{{NS_A}}}xfrm")
        ET.SubElement(xfrm, f"{{{NS_A}}}off", x=str(x_emu), y=str(y_emu))
        ET.SubElement(xfrm, f"{{{NS_A}}}ext", cx=str(w_emu), cy=str(h_emu))
        prst = ET.SubElement(spPr, f"{{{NS_A}}}prstGeom", prst="ellipse")
        ET.SubElement(prst, f"{{{NS_A}}}avLst")
    else:
        all_pts = [pt for sub in subpaths for pt in sub["pts"]]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        x_emu = int(round(min_x * PT_TO_EMU))
        y_emu = int(round(min_y * PT_TO_EMU))
        w_emu = max(int(round((max_x - min_x) * PT_TO_EMU)), 1)
        h_emu = max(int(round((max_y - min_y) * PT_TO_EMU)), 1)

        xfrm = ET.SubElement(spPr, f"{{{NS_A}}}xfrm")
        ET.SubElement(xfrm, f"{{{NS_A}}}off", x=str(x_emu), y=str(y_emu))
        ET.SubElement(xfrm, f"{{{NS_A}}}ext", cx=str(w_emu), cy=str(h_emu))

        cust = ET.SubElement(spPr, f"{{{NS_A}}}custGeom")
        ET.SubElement(cust, f"{{{NS_A}}}avLst")
        ET.SubElement(cust, f"{{{NS_A}}}gdLst")
        ET.SubElement(cust, f"{{{NS_A}}}ahLst")
        ET.SubElement(cust, f"{{{NS_A}}}cxnLst")
        ET.SubElement(cust, f"{{{NS_A}}}rect", l="0", t="0", r="0", b="0")
        pathLst = ET.SubElement(cust, f"{{{NS_A}}}pathLst")
        path_el = ET.SubElement(pathLst, f"{{{NS_A}}}path", w=str(w_emu), h=str(h_emu))

        for sub in subpaths:
            pts = sub["pts"]
            if not pts:
                continue
            m = ET.SubElement(path_el, f"{{{NS_A}}}moveTo")
            ET.SubElement(m, f"{{{NS_A}}}pt",
                          x=str(int(round((pts[0][0] - min_x) * PT_TO_EMU))),
                          y=str(int(round((pts[0][1] - min_y) * PT_TO_EMU))))
            for px, py in pts[1:]:
                ln = ET.SubElement(path_el, f"{{{NS_A}}}lnTo")
                ET.SubElement(ln, f"{{{NS_A}}}pt",
                              x=str(int(round((px - min_x) * PT_TO_EMU))),
                              y=str(int(round((py - min_y) * PT_TO_EMU))))
            if sub["closed"]:
                ET.SubElement(path_el, f"{{{NS_A}}}close")

    if fill_hex:
        sf = ET.SubElement(spPr, f"{{{NS_A}}}solidFill")
        clr = ET.SubElement(sf, f"{{{NS_A}}}srgbClr", val=fill_hex)
        if fill_alpha is not None and fill_alpha < 0.999:
            ET.SubElement(clr, f"{{{NS_A}}}alpha", val=str(int(round(fill_alpha * 100000))))
    else:
        ET.SubElement(spPr, f"{{{NS_A}}}noFill")

    if stroke_hex and stroke_w_pt > 0:
        ln_el = ET.SubElement(spPr, f"{{{NS_A}}}ln", w=str(max(int(round(stroke_w_pt * PT_TO_EMU)), 3175)))
        sf = ET.SubElement(ln_el, f"{{{NS_A}}}solidFill")
        clr = ET.SubElement(sf, f"{{{NS_A}}}srgbClr", val=stroke_hex)
        if stroke_alpha is not None and stroke_alpha < 0.999:
            ET.SubElement(clr, f"{{{NS_A}}}alpha", val=str(int(round(stroke_alpha * 100000))))
        ET.SubElement(ln_el, f"{{{NS_A}}}prstDash", val=dash_type or "solid")
    else:
        ln_el = ET.SubElement(spPr, f"{{{NS_A}}}ln", w="0")
        ET.SubElement(ln_el, f"{{{NS_A}}}noFill")

    return sp


def make_textbox_xml(shape_id, name, text_str, anchor_x_pt, baseline_y_pt, font_size_pt, is_bold, color_hex, text_anchor, angle_deg):
    """
    Creates a native editable PowerPoint textbox positioned accurately around (anchor_x_pt, baseline_y_pt),
    supporting arbitrary rotation angle_deg (e.g. -90 for y-axis label or -32 for tilted labels).
    """
    sp = ET.Element(f"{{{NS_P}}}sp")
    nvSpPr = ET.SubElement(sp, f"{{{NS_P}}}nvSpPr")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvPr", id=str(shape_id), name=name)
    ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvSpPr", txBox="1")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}nvPr")

    # Estimate generous single-line box dimensions in pt so text never wraps or clips
    char_w_pt = font_size_pt * 0.62
    box_w_pt = max(len(text_str) * char_w_pt + 10.0, 22.0)
    box_h_pt = font_size_pt * 1.45

    # In SVG, baseline_y_pt is the text baseline (~0.32 * font_size below visual vertical center)
    local_cy = -0.28 * font_size_pt
    if text_anchor == "middle":
        local_cx = 0.0
        algn = "ctr"
    elif text_anchor == "end":
        local_cx = -box_w_pt / 2.0
        algn = "r"
    else:
        local_cx = box_w_pt / 2.0
        algn = "l"

    rad = math.radians(angle_deg)
    world_cx = anchor_x_pt + local_cx * math.cos(rad) - local_cy * math.sin(rad)
    world_cy = baseline_y_pt + local_cx * math.sin(rad) + local_cy * math.cos(rad)

    x_emu = int(round((world_cx - box_w_pt / 2.0) * PT_TO_EMU))
    y_emu = int(round((world_cy - box_h_pt / 2.0) * PT_TO_EMU))
    w_emu = int(round(box_w_pt * PT_TO_EMU))
    h_emu = int(round(box_h_pt * PT_TO_EMU))

    spPr = ET.SubElement(sp, f"{{{NS_P}}}spPr")
    xfrm_attrib = {}
    if abs(angle_deg) > 0.1:
        xfrm_attrib["rot"] = str(int(round(angle_deg * 60000)))
    xfrm = ET.SubElement(spPr, f"{{{NS_A}}}xfrm", **xfrm_attrib)
    ET.SubElement(xfrm, f"{{{NS_A}}}off", x=str(x_emu), y=str(y_emu))
    ET.SubElement(xfrm, f"{{{NS_A}}}ext", cx=str(w_emu), cy=str(h_emu))
    prst = ET.SubElement(spPr, f"{{{NS_A}}}prstGeom", prst="rect")
    ET.SubElement(prst, f"{{{NS_A}}}avLst")
    ET.SubElement(spPr, f"{{{NS_A}}}noFill")
    ln_el = ET.SubElement(spPr, f"{{{NS_A}}}ln", w="0")
    ET.SubElement(ln_el, f"{{{NS_A}}}noFill")

    txBody = ET.SubElement(sp, f"{{{NS_P}}}txBody")
    bodyPr = ET.SubElement(txBody, f"{{{NS_A}}}bodyPr", wrap="none", lIns="0", tIns="0", rIns="0", bIns="0", anchor="ctr")
    ET.SubElement(bodyPr, f"{{{NS_A}}}noAutofit")
    ET.SubElement(txBody, f"{{{NS_A}}}lstStyle")

    p_el = ET.SubElement(txBody, f"{{{NS_A}}}p")
    ET.SubElement(p_el, f"{{{NS_A}}}pPr", algn=algn)
    r_el = ET.SubElement(p_el, f"{{{NS_A}}}r")
    rPr = ET.SubElement(r_el, f"{{{NS_A}}}rPr", lang="en-US",
                        sz=str(int(round(font_size_pt * 100))),
                        b="1" if is_bold else "0")
    sf = ET.SubElement(rPr, f"{{{NS_A}}}solidFill")
    ET.SubElement(sf, f"{{{NS_A}}}srgbClr", val=color_hex or "243442")
    ET.SubElement(rPr, f"{{{NS_A}}}latin", typeface="Arial")
    ET.SubElement(rPr, f"{{{NS_A}}}ea", typeface="Arial")
    ET.SubElement(rPr, f"{{{NS_A}}}cs", typeface="Arial")
    t_el = ET.SubElement(r_el, f"{{{NS_A}}}t")
    t_el.text = text_str
    return sp


def add_svg_to_pptx_slide(prs, svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    vb = [float(v) for v in root.attrib["viewBox"].split()]
    svg_w_pt, svg_h_pt = vb[2], vb[3]

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    spTree = slide.shapes._spTree

    # Collect <defs> paths
    defs = {}
    for d in root.findall(".//{http://www.w3.org/2000/svg}defs/*"):
        did = d.attrib.get("id")
        if did and d.tag.endswith("path"):
            defs[did] = d

    shape_id = 10

    def extract_paint(st):
        op = float(st.get("opacity", "1.0"))
        fill_hex = clean_hex(st.get("fill"))
        if "fill" not in st:
            fill_hex = None
        fill_alpha = float(st.get("fill-opacity", "1.0")) * op
        stroke_hex = clean_hex(st.get("stroke"))
        stroke_alpha = float(st.get("stroke-opacity", "1.0")) * op
        sw_str = st.get("stroke-width", "1.0" if stroke_hex else "0.0").replace("px", "").replace("pt", "")
        stroke_w = float(sw_str) if sw_str else 0.0
        da = st.get("stroke-dasharray", "")
        dash_type = "solid"
        if da and da != "none":
            parts = [float(x) for x in re.findall(r"\d+\.?\d*", da)]
            if parts and parts[0] <= 1.5:
                dash_type = "sysDot"
            else:
                dash_type = "dash"
        return fill_hex, fill_alpha, stroke_hex, stroke_alpha, stroke_w, dash_type

    def walk(el, inherited_style):
        nonlocal shape_id
        tag = el.tag.split("}")[-1]
        if tag in ("defs", "clipPath", "metadata", "style"):
            return

        curr_style = dict(inherited_style)
        curr_style.update(parse_style(el.attrib.get("style"), el.attrib))

        if tag == "path":
            d_str = el.attrib.get("d", "")
            if d_str:
                subs = parse_svg_path_d(d_str)
                if subs:
                    f_hex, f_alp, s_hex, s_alp, s_w, d_type = extract_paint(curr_style)
                    if f_hex or (s_hex and s_w > 0):
                        sp_el = make_shape_xml(shape_id, f"data_{shape_id}", subs, f_hex, f_alp, s_hex, s_alp, s_w, d_type)
                        spTree.append(sp_el)
                        shape_id += 1

        elif tag == "use":
            href = el.attrib.get("{http://www.w3.org/1999/xlink}href", el.attrib.get("href", "")).lstrip("#")
            ux = float(el.attrib.get("x", "0"))
            uy = float(el.attrib.get("y", "0"))
            if href in defs:
                def_el = defs[href]
                merged_st = parse_style(def_el.attrib.get("style"), def_el.attrib)
                merged_st.update(curr_style)
                d_str = def_el.attrib.get("d", "")
                f_hex, f_alp, s_hex, s_alp, s_w, d_type = extract_paint(merged_st)
                # Check if def_el is a circular marker (contains 'C' cubic bezier around origin)
                if "C" in d_str:
                    nums = [abs(float(v)) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_str)]
                    r_pt = max(nums) if nums else 2.5
                    sp_el = make_shape_xml(shape_id, f"marker_{shape_id}", [], f_hex, f_alp, s_hex, s_alp, s_w, d_type,
                                           is_ellipse=(ux, uy, r_pt, r_pt))
                    spTree.append(sp_el)
                    shape_id += 1
                else:
                    subs = parse_svg_path_d(d_str, tx=ux, ty=uy)
                    if subs:
                        sp_el = make_shape_xml(shape_id, f"tick_{shape_id}", subs, f_hex, f_alp, s_hex, s_alp, s_w, d_type)
                        spTree.append(sp_el)
                        shape_id += 1

        elif tag == "image":
            href = el.attrib.get("{http://www.w3.org/1999/xlink}href", el.attrib.get("href", ""))
            if href.startswith("data:image/png;base64,"):
                b64_data = href.split(",", 1)[1]
                img_bytes = base64.b64decode(b64_data)
                ix = float(el.attrib.get("x", "0"))
                iy = float(el.attrib.get("y", "0"))
                iw = float(el.attrib.get("width", "10"))
                ih = float(el.attrib.get("height", "10"))
                tf = el.attrib.get("transform", "")
                # Matplotlib image has transform="scale(1 -1) translate(0 -ih)"
                if "scale(1 -1)" in tf:
                    m = re.search(r"translate\([-\d\.]+\s+([-\d\.]+)\)", tf)
                    ty_val = float(m.group(1)) if m else -ih
                    top_pt = -iy - ty_val - ih
                    pil_im = Image.open(io.BytesIO(img_bytes)).transpose(Image.FLIP_TOP_BOTTOM)
                    buf = io.BytesIO()
                    pil_im.save(buf, format="PNG")
                    img_bytes = buf.getvalue()
                else:
                    top_pt = iy
                slide.shapes.add_picture(
                    io.BytesIO(img_bytes),
                    Emu(int(round(ix * PT_TO_EMU))),
                    Emu(int(round(top_pt * PT_TO_EMU))),
                    Emu(int(round(iw * PT_TO_EMU))),
                    Emu(int(round(ih * PT_TO_EMU))),
                )

        elif tag == "text":
            txt = "".join(el.itertext()).strip()
            if txt:
                fs_str = curr_style.get("font-size", "8px").replace("px", "").replace("pt", "")
                fs_pt = float(fs_str)
                fw = curr_style.get("font-weight", "normal")
                is_bold = fw in ("bold", "700", "600", "800")
                t_anc = curr_style.get("text-anchor", "start")
                col_hex = clean_hex(curr_style.get("fill", "#243442"))
                tf = el.attrib.get("transform", "")
                tx = float(el.attrib.get("x", "0"))
                ty = float(el.attrib.get("y", "0"))
                angle = 0.0
                if "translate" in tf:
                    m_tr = re.search(r"translate\(\s*([-\d\.]+)[,\s]+([-\d\.]+)\s*\)", tf)
                    if m_tr:
                        tx += float(m_tr.group(1))
                        ty += float(m_tr.group(2))
                if "rotate" in tf:
                    m_rot = re.search(r"rotate\(\s*([-\d\.]+)", tf)
                    if m_rot:
                        angle = float(m_rot.group(1))
                sp_el = make_textbox_xml(shape_id, f"text_{shape_id}", txt, tx, ty, fs_pt, is_bold, col_hex, t_anc, angle)
                spTree.append(sp_el)
                shape_id += 1
            return

        for child in el:
            walk(child, curr_style)

    walk(root, {})
    return slide, svg_w_pt, svg_h_pt


def build_editable_candidate(build):
    """将同次四张 SVG 转成独立可编辑对象, 写备注与独立图名批注."""
    pages = json.loads((build / "manifest.json").read_text(encoding="utf-8"))
    prs = Presentation()
    prs.slide_width = Emu(round(max(p["width"] for p in pages) * PT_TO_EMU))
    prs.slide_height = Emu(round(max(p["height"] for p in pages) * PT_TO_EMU))
    counts = []
    for page in pages:
        slide, width, height = add_svg_to_pptx_slide(prs, build / "figures" / (page["stem"] + ".svg"))
        assert not any(shape.shape_type == 13 for shape in slide.shapes), "统计图必须保持原生图元"
        slide.notes_slide.notes_text_frame.text = page["notes"]
        counts.append({"id": page["id"], "shapes": len(slide.shapes), "width_pt": width, "height_pt": height})
    candidate = build / "candidate.pptx"
    prs.save(candidate)
    with ZipFile(candidate) as package:
        members = {name: package.read(name) for name in package.namelist()}
    content_types = ET.fromstring(members["[Content_Types].xml"])
    ns_ct = "http://schemas.openxmlformats.org/package/2006/content-types"
    ns_rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    author = ET.Element(f"{{{NS_P}}}cmAuthorLst", nsmap={"p": NS_P})
    ET.SubElement(author, f"{{{NS_P}}}cmAuthor", id="0", name="Hongen Peng", initials="HP", lastIdx=str(len(pages)), clrIdx="0")
    members["ppt/commentAuthors.xml"] = ET.tostring(author, xml_declaration=True, encoding="UTF-8", standalone=True)
    ET.SubElement(content_types, f"{{{ns_ct}}}Override", PartName="/ppt/commentAuthors.xml", ContentType="application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml")
    rels = ET.fromstring(members["ppt/_rels/presentation.xml.rels"])
    ET.SubElement(rels, f"{{{ns_rel}}}Relationship", Id="rIdE2EAuthors", Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/commentAuthors", Target="commentAuthors.xml")
    members["ppt/_rels/presentation.xml.rels"] = ET.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for number, page in enumerate(pages, 1):
        comments = ET.Element(f"{{{NS_P}}}cmLst", nsmap={"p": NS_P})
        comment = ET.SubElement(comments, f"{{{NS_P}}}cm", authorId="0", dt=stamp, idx=str(number))
        ET.SubElement(comment, f"{{{NS_P}}}pos", x="0", y="0")
        ET.SubElement(comment, f"{{{NS_P}}}text").text = "@@" + page["id"]
        part = f"ppt/comments/comment{number}.xml"
        members[part] = ET.tostring(comments, xml_declaration=True, encoding="UTF-8", standalone=True)
        ET.SubElement(content_types, f"{{{ns_ct}}}Override", PartName="/"+part, ContentType="application/vnd.openxmlformats-officedocument.presentationml.comments+xml")
        relpart = f"ppt/slides/_rels/slide{number}.xml.rels"
        relations = ET.fromstring(members[relpart])
        ET.SubElement(relations, f"{{{ns_rel}}}Relationship", Id="rIdE2EComment", Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments", Target=f"../comments/comment{number}.xml")
        members[relpart] = ET.tostring(relations, xml_declaration=True, encoding="UTF-8", standalone=True)
    members["[Content_Types].xml"] = ET.tostring(content_types, xml_declaration=True, encoding="UTF-8", standalone=True)
    with ZipFile(candidate, "w", ZIP_DEFLATED) as package:
        for name, content in members.items():
            package.writestr(name, content)
    (build / "native-shapes.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    build = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_top5_20261102/build"
    build_editable_candidate(build)
