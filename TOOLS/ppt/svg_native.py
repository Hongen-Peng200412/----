"""运输调用方SVG、原生XML和作者显示参数, 不读取科学原件或决定评价口径.

build_candidate接收明确页列表、EMU画布、作者署名和显示模板, 逐页构造可编辑PPT. build_static只运输调用方提供的静态图层和主题. export_figure导出已完成的Matplotlib画面. 本工具不内置图号、科学方法或默认阶段列表.
"""

from pathlib import Path
import copy
import numpy as np
from TOOLS.ppt.audit_panel_alignment import require_matplotlib_panel_alignment

import base64
import io
from PIL import Image
import math
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
    """解析SVG显式属性和style字体简写, 返回统一绘制属性字典.

    style_str: str或None, 原SVG的style文本, 如font: bold 8px Arial. attrib: dict或None, 原元素属性. 返回dict[str,str], style覆盖同名显式属性, font简写拆出font-size/font-weight, 不决定科学标签或颜色.
    """
    st = {}
    if attrib:
        for k in (
            "fill",
            "stroke",
            "stroke-width",
            "fill-opacity",
            "stroke-opacity",
            "opacity",
            "stroke-dasharray",
            "font-size",
            "font-weight",
            "text-anchor",
        ):
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
    """把SVG颜色写成六位大写RGB, 无填充返回None.

    color_str: str或None, 如#abc转换为AABBCC, white转换为FFFFFF. 未具名颜色沿原运输约定取243442, 不是科学类别映射. 返回str或None, 不改变原透明度.
    """
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
    """将SVG路径展开为带闭合标志的二维折线子路径.

    d_str: str, 如M 0 0 L 1 1 Z. tx/ty: float, 显式平移量pt. 返回list[dict], 每项pts是(x,y)点列表, closed是bool; 如[{'pts':[(0,0),(1,1)],'closed':True}]. 三次Bezier沿每段六等分采样, 不对科学数据做插值拟合.
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


def make_shape_xml(
    shape_id, name, subpaths, fill_hex, fill_alpha, stroke_hex, stroke_alpha, stroke_w_pt, dash_type, is_ellipse=None
):
    """把调用方二维子路径或椭圆尺寸写成原生PowerPoint形状.

    shape_id/name: int/str, 包内形状编号和名称, 如10/data_10. subpaths: list[dict], pts为pt坐标列表、closed为bool. fill_hex/stroke_hex: 六位RGB或None. fill_alpha/stroke_alpha: float或None, 0-1透明度. stroke_w_pt: float, 线宽pt. dash_type: str, 如solid. is_ellipse: tuple或None, 非空为中心x/y与半径x/y的pt值. 返回p:sp XML, 路径坐标以形状左上角为局部原点, 长度换为EMU.
    """
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
            ET.SubElement(
                m,
                f"{{{NS_A}}}pt",
                x=str(int(round((pts[0][0] - min_x) * PT_TO_EMU))),
                y=str(int(round((pts[0][1] - min_y) * PT_TO_EMU))),
            )
            for px, py in pts[1:]:
                ln = ET.SubElement(path_el, f"{{{NS_A}}}lnTo")
                ET.SubElement(
                    ln,
                    f"{{{NS_A}}}pt",
                    x=str(int(round((px - min_x) * PT_TO_EMU))),
                    y=str(int(round((py - min_y) * PT_TO_EMU))),
                )
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


def make_textbox_xml(
    shape_id, name, text_str, anchor_x_pt, baseline_y_pt, font_size_pt, is_bold, color_hex, text_anchor, angle_deg
):
    """把SVG基线锚点转为可编辑文字框, 保留字号、粗体和旋转.

    shape_id/name: int/str, 包内编号与名称. text_str: str, 原文字, 如Completion (%). anchor_x_pt/baseline_y_pt: float, 原SVG锚点和基线pt. font_size_pt: float, 原字号pt. is_bold: bool. color_hex: 六位RGB或None. text_anchor: str, start/middle/end. angle_deg: float, 旋转角度, 如-90. 返回p:sp XML, 按原字宽估计规则保留不换行单行框.
    """
    sp = ET.Element(f"{{{NS_P}}}sp")
    nvSpPr = ET.SubElement(sp, f"{{{NS_P}}}nvSpPr")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvPr", id=str(shape_id), name=name)
    ET.SubElement(nvSpPr, f"{{{NS_P}}}cNvSpPr", txBox="1")
    ET.SubElement(nvSpPr, f"{{{NS_P}}}nvPr")

    # 单行文字框宽高使用原运输的留白估计, 单位pt, 保持不换行与不裁字.
    char_w_pt = font_size_pt * 0.62
    box_w_pt = max(len(text_str) * char_w_pt + 10.0, 22.0)
    box_h_pt = font_size_pt * 1.45

    # baseline_y_pt是SVG文字基线; 局部视觉中心按原字号偏移换算, 不是实验坐标.
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
    bodyPr = ET.SubElement(
        txBody, f"{{{NS_A}}}bodyPr", wrap="none", lIns="0", tIns="0", rIns="0", bIns="0", anchor="ctr"
    )
    ET.SubElement(bodyPr, f"{{{NS_A}}}noAutofit")
    ET.SubElement(txBody, f"{{{NS_A}}}lstStyle")

    p_el = ET.SubElement(txBody, f"{{{NS_A}}}p")
    ET.SubElement(p_el, f"{{{NS_A}}}pPr", algn=algn)
    r_el = ET.SubElement(p_el, f"{{{NS_A}}}r")
    rPr = ET.SubElement(
        r_el, f"{{{NS_A}}}rPr", lang="en-US", sz=str(int(round(font_size_pt * 100))), b="1" if is_bold else "0"
    )
    sf = ET.SubElement(rPr, f"{{{NS_A}}}solidFill")
    ET.SubElement(sf, f"{{{NS_A}}}srgbClr", val=color_hex or "243442")
    ET.SubElement(rPr, f"{{{NS_A}}}latin", typeface="Arial")
    ET.SubElement(rPr, f"{{{NS_A}}}ea", typeface="Arial")
    ET.SubElement(rPr, f"{{{NS_A}}}cs", typeface="Arial")
    t_el = ET.SubElement(r_el, f"{{{NS_A}}}t")
    t_el.text = text_str
    return sp


def add_svg_to_pptx_slide(prs, svg_path):
    """将一份明确SVG的文字、路径和标记逐项加入新空白页.

    prs: pptx.Presentation, 当前候选容器. svg_path: Path, 本次图稿. 返回(slide,width_pt,height_pt), 画幅从SVG viewBox读取, 原shape名称按原绘制顺序编号. 只运输显式图元, 不识别方法、阈值或科学曲线.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()
    vb = [float(v) for v in root.attrib["viewBox"].split()]
    svg_w_pt, svg_h_pt = vb[2], vb[3]

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    spTree = slide.shapes._spTree

    # 收集SVG defs中的复用路径, use通过原id引用同一个标记几何.
    defs = {}
    for d in root.findall(".//{http://www.w3.org/2000/svg}defs/*"):
        did = d.attrib.get("id")
        if did and d.tag.endswith("path"):
            defs[did] = d

    shape_id = 10

    def extract_paint(st):
        """从已合并的SVG样式提取填充、线条与透明度.

        st: dict[str,str], 如{'fill':'#abcdef','stroke-width':'1.0'}. 返回填充RGB/alpha、线条RGB/alpha、线宽pt、虚线样式, 延续原SVG运输的缺省值.
        """
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
        """按SVG原层次递归运输一个节点及子节点.

        el: SVG XML节点. inherited_style: dict[str,str], 父节点已合并样式. defs/clipPath/metadata/style节点不作为可见图元; path/use/text/image沿原顺序写到当前slide, shape_id只作包内编号.
        """
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
                        sp_el = make_shape_xml(
                            shape_id, f"data_{shape_id}", subs, f_hex, f_alp, s_hex, s_alp, s_w, d_type
                        )
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
                # 原defs路径含三次Bezier时按圆形标记运输, 半径从原路径坐标取得.
                if "C" in d_str:
                    nums = [abs(float(v)) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_str)]
                    r_pt = max(nums) if nums else 2.5
                    sp_el = make_shape_xml(
                        shape_id,
                        f"marker_{shape_id}",
                        [],
                        f_hex,
                        f_alp,
                        s_hex,
                        s_alp,
                        s_w,
                        d_type,
                        is_ellipse=(ux, uy, r_pt, r_pt),
                    )
                    spTree.append(sp_el)
                    shape_id += 1
                else:
                    subs = parse_svg_path_d(d_str, tx=ux, ty=uy)
                    if subs:
                        sp_el = make_shape_xml(
                            shape_id, f"tick_{shape_id}", subs, f_hex, f_alp, s_hex, s_alp, s_w, d_type
                        )
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
                # Matplotlib栅格节点通过scale(1 -1)与translate翻转Y轴, 这里只运输原像素.
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
                sp_el = make_textbox_xml(
                    shape_id, f"text_{shape_id}", txt, tx, ty, fs_pt, is_bold, col_hex, t_anc, angle
                )
                spTree.append(sp_el)
                shape_id += 1
            return

        for child in el:
            walk(child, curr_style)

    walk(root, {})
    return slide, svg_w_pt, svg_h_pt


NUMBERS = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
NS = {"a": NS_A, "p": NS_P}


def make_shape(spec: dict, sources: dict, styles: list[str]):
    """用新图形的路径与数字, 配合作者显示模板构造一个原生形状.

    spec: dict, name对应新图元, style对应styles下标, delta是x/y/cx/cy四项EMU调整; static下标则表示明确静态作者图层. sources: dict[str,p:sp], 本次新图元. styles: list[str], 原生XML样式模板. 返回p:sp XML, 作者模板中的{value:0}按新图元数值顺序绑定.
    """
    if "static" in spec:
        # 仅规则示意图具有静态图形;其中的路径是流程箭头,不是实验曲线.
        return ET.fromstring(styles[spec["static"]].encode("utf-8"))
    source = sources[spec["name"]]
    shape = ET.fromstring(styles[spec["style"]].encode("utf-8"))
    shape.find("p:nvSpPr/p:cNvPr", NS).set("name", spec["name"])
    fresh_pr = source.find("p:spPr", NS)
    target_pr = shape.find("p:spPr", NS)
    target_xfrm = target_pr.find("a:xfrm", NS)
    source_xfrm = source.find("p:spPr/a:xfrm", NS)
    values = [
        int(source_xfrm.find("a:" + tag, NS).get(key)) + delta
        for (tag, key), delta in zip((("off", "x"), ("off", "y"), ("ext", "cx"), ("ext", "cy")), spec["delta"])
    ]
    for (tag, key), value in zip((("off", "x"), ("off", "y"), ("ext", "cx"), ("ext", "cy")), values):
        target_xfrm.find("a:" + tag, NS).set(key, str(value))
    for index, child in enumerate(fresh_pr):
        if ET.QName(child).localname in ("custGeom", "prstGeom"):
            target_pr.insert(min(index, len(target_pr)), copy.deepcopy(child))
    numbers = NUMBERS.findall("".join(source.xpath(".//a:t/text()", namespaces=NS)))
    for text in shape.findall(".//a:t", NS):
        if text.text:
            text.text = re.sub(r"\{value:(\d+)\}", lambda m: numbers[int(m[1])], text.text)
    return shape


def make_node(spec: dict, sources: dict, styles: list[str]):
    """按作者定义的分组层次构造当前图层树, 保持原叠放顺序.

    spec: dict, children为子层列表时group指styles中的组XML; 否则是make_shape的形状定义. sources/styles与make_shape相同. 返回原生形状或组XML, 组坐标只表达显示布局.
    """
    if "children" not in spec:
        return make_shape(spec, sources, styles)
    node = ET.fromstring(styles[spec["group"]].encode("utf-8"))
    for child in spec["children"]:
        node.append(make_node(child, sources, styles))
    return node


def panel_header(ax, letter, title, x_offset, fontsize, label_size, y_offset, pad, color):
    """按调用方显示参数放置面板标题与字母, 不选择图号或科学文字.

    ax: Axes, 当前面板. letter/title: str, 显式标签与标题. x_offset/y_offset: float, 字母的axes比例坐标, 如(-0.115,1.17). fontsize/label_size/pad: float, 标题字号、字母字号与标题间距, 单位pt. color: str, 显式颜色.
    """
    ax.set_title(title, loc="left", fontsize=fontsize, fontweight="bold", pad=pad, color=color)
    ax.text(
        x_offset,
        y_offset,
        letter,
        transform=ax.transAxes,
        fontsize=label_size,
        fontweight="bold",
        va="top",
        ha="left",
        color=color,
    )


def place_right_labels(ax, x_pos, raw_entries, min_gap, style):
    """只调整末端文字以避免相邻标签重叠, 不移动原曲线数值.

    raw_entries: list[tuple[float,str,str,bool]], 原纵坐标、文字、颜色、是否粗体. x_pos: float, 文字横坐标. min_gap: float, 原坐标轴内最小纵向间隔. style: dict, font_size为pt, line_start/line_end_gap/line_threshold是轴内坐标, line_width为pt, line_alpha为0-1比例. 仅相邻冲突簇围绕原均值展开, 没有冲突的标签原位保留.
    """
    entries = sorted(raw_entries, key=lambda item: item[0])
    ys = [item[0] for item in entries]
    clusters = [[0]]
    for i in range(1, len(ys)):
        if ys[i] - ys[clusters[-1][-1]] < min_gap:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    changed = True
    while changed:
        changed = False
        resolved_ys = list(ys)
        for cl in clusters:
            if len(cl) > 1:
                center = float(np.mean([ys[idx] for idx in cl]))
                span = (len(cl) - 1) * min_gap
                for k_i, idx in enumerate(cl):
                    resolved_ys[idx] = center - span / 2.0 + k_i * min_gap
        new_clusters = [clusters[0]]
        for cl in clusters[1:]:
            if resolved_ys[cl[0]] - resolved_ys[new_clusters[-1][-1]] < min_gap - 1e-6:
                new_clusters[-1].extend(cl)
                changed = True
            else:
                new_clusters.append(cl)
        clusters = new_clusters
    for idx, (orig_y, text, col, is_bold) in enumerate(entries):
        draw_y = resolved_ys[idx]
        if abs(draw_y - orig_y) > style["line_threshold"]:
            ax.plot(
                [style["line_start"], x_pos - style["line_end_gap"]],
                [orig_y, draw_y],
                color=col,
                linewidth=style["line_width"],
                alpha=style["line_alpha"],
                zorder=2,
            )
        ax.text(
            x_pos,
            draw_y,
            text,
            fontsize=style["font_size"],
            fontweight="bold" if is_bold else "normal",
            color=col,
            va="center",
            ha="left",
        )


def scale_figure_artists(fig, scale, title_pad, minimum_font):
    """按明确的物理比例运输线宽、标记和间距, 不改变任何坐标轴数据.

    fig: Figure, 已完成画面. scale: float, 各长度缩放倍数. title_pad: float, 缩放前标题间距pt. minimum_font: float或None, 明确下限pt, None表示保留原字号. 标记面积按scale平方, 其余长度按scale, 不缩放曲线的x/y数据.
    """
    from matplotlib.collections import Collection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.text import Text

    for item in fig.findobj(Line2D):
        item.set_linewidth(item.get_linewidth() * scale)
        item.set_markersize(item.get_markersize() * scale)
        item.set_markeredgewidth(item.get_markeredgewidth() * scale)
    for item in fig.findobj(Patch):
        item.set_linewidth(item.get_linewidth() * scale)
    for item in fig.findobj(Collection):
        if hasattr(item, "get_sizes"):
            item.set_sizes(item.get_sizes() * scale * scale)
        item.set_linewidths(item.get_linewidths() * scale)
    for ax in fig.axes:
        ax.xaxis.labelpad *= scale
        ax.yaxis.labelpad *= scale
        ax._set_title_offset_trans(title_pad * scale)
        for tick in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tick.set_pad(tick.get_pad() * scale)
    if minimum_font is not None:
        for text in fig.findobj(Text):
            text.set_fontsize(max(minimum_font, text.get_fontsize()))


# ================================================================================================
def export_figure(fig, directory, stem, dpi, strict):
    """导出已绘制画面并返回一页清单, 不计算指标或选择面板.

    fig: Matplotlib Figure, 当前图. directory: Path, 本次临时图稿目录. stem: str, 调用方的精确文件前缀. dpi: int, PNG分辨率. strict: bool, 是否将面板对齐警告也视为失败. 返回id/stem/width/height/notes, 画幅单位pt, notes为空占位.
    """
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    if len(fig.axes) > 1:
        require_matplotlib_panel_alignment(
            fig,
            json_out=directory / f"{stem}.alignment.json",
            overlay_svg=directory / f"{stem}.alignment.svg",
            tolerance_pt=1.5,
            strict=strict,
        )
    for suffix in ("svg", "pdf", "png"):
        fig.savefig(directory / f"{stem}.{suffix}", dpi=dpi, facecolor="white")
    page = {
        "id": stem,
        "stem": stem,
        "width": float(fig.get_figwidth() * 72),
        "height": float(fig.get_figheight() * 72),
        "notes": "",
    }
    plt.close(fig)
    return page


def identify(candidate: Path, figures, author):
    """给现有本次候选写入完整图名与显式作者署名, 不改变幻灯片图元.

    candidate: Path, 本次PPT. figures: list[str], 与页顺序对齐的完整图名. author: dict, name与initials, 如调用方提供的作者姓名和缩写. 注释时间仅标记本次包生成时间.
    """
    with ZipFile(candidate) as package:
        members = {name: package.read(name) for name in package.namelist()}
    content_types = ET.fromstring(members["[Content_Types].xml"])
    ns_ct = "http://schemas.openxmlformats.org/package/2006/content-types"
    ns_rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    authors = ET.Element(f"{{{NS_P}}}cmAuthorLst", nsmap={"p": NS_P})
    ET.SubElement(
        authors,
        f"{{{NS_P}}}cmAuthor",
        id="0",
        name=author["name"],
        initials=author["initials"],
        lastIdx=str(len(figures)),
        clrIdx="0",
    )
    members["ppt/commentAuthors.xml"] = ET.tostring(authors, xml_declaration=True, encoding="UTF-8", standalone=True)
    ET.SubElement(
        content_types,
        f"{{{ns_ct}}}Override",
        PartName="/ppt/commentAuthors.xml",
        ContentType="application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml",
    )
    rels = ET.fromstring(members["ppt/_rels/presentation.xml.rels"])
    ET.SubElement(
        rels,
        f"{{{ns_rel}}}Relationship",
        Id="rIdFigureAuthors",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/commentAuthors",
        Target="commentAuthors.xml",
    )
    members["ppt/_rels/presentation.xml.rels"] = ET.tostring(
        rels, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for number, figure in enumerate(figures, 1):
        comments = ET.Element(f"{{{NS_P}}}cmLst", nsmap={"p": NS_P})
        comment = ET.SubElement(comments, f"{{{NS_P}}}cm", authorId="0", dt=stamp, idx=str(number))
        ET.SubElement(comment, f"{{{NS_P}}}pos", x="0", y="0")
        ET.SubElement(comment, f"{{{NS_P}}}text").text = "@@" + figure
        part = f"ppt/comments/comment{number}.xml"
        members[part] = ET.tostring(comments, xml_declaration=True, encoding="UTF-8", standalone=True)
        ET.SubElement(
            content_types,
            f"{{{ns_ct}}}Override",
            PartName="/" + part,
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.comments+xml",
        )
        relpart = f"ppt/slides/_rels/slide{number}.xml.rels"
        relations = ET.fromstring(members[relpart])
        ET.SubElement(
            relations,
            f"{{{ns_rel}}}Relationship",
            Id="rIdFigureComment",
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
            Target=f"../comments/comment{number}.xml",
        )
        members[relpart] = ET.tostring(relations, xml_declaration=True, encoding="UTF-8", standalone=True)
    members["[Content_Types].xml"] = ET.tostring(content_types, xml_declaration=True, encoding="UTF-8", standalone=True)
    with ZipFile(candidate, "w", ZIP_DEFLATED) as package:
        for name, content in members.items():
            package.writestr(name, content)


def build_candidate(build: Path, pages, canvas, author, display):
    """把明确的SVG页装配为本次候选, 再应用对应作者显示参数.

    build: Path, 本次目录, figures/<stem>.svg已存在. pages: list[dict], 每页id/stem/width/height/notes. canvas: 两项int, EMU画布宽高, 保留来源图集的完整画布. author: dict, name/initials. display: dict, styles为XML样式列表, pages为本次图名与nodes层次. 不自动添加其他图.
    """
    prs = Presentation()
    prs.slide_width, prs.slide_height = map(Emu, canvas)
    counts = []
    for page in pages:
        slide, width, height = add_svg_to_pptx_slide(prs, build / "figures" / (page["stem"] + ".svg"))
        assert not any(shape.shape_type == 13 for shape in slide.shapes), "统计图必须保持原生图元"
        slide.notes_slide.notes_text_frame.text = page["notes"]
        counts.append({"id": page["id"], "shapes": len(slide.shapes), "width_pt": width, "height_pt": height})
    candidate = build / "candidate.pptx"
    prs.save(candidate)
    identify(candidate, [page["id"] for page in display["pages"]], author)
    with ZipFile(candidate) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    for index, page in enumerate(display["pages"], 1):
        part = f"ppt/slides/slide{index}.xml"
        slide = ET.fromstring(members[part])
        sources = {s.find("p:nvSpPr/p:cNvPr", NS).get("name"): s for s in slide.findall(".//p:sp", NS)}
        tree = slide.find("p:cSld/p:spTree", NS)
        for child in list(tree)[2:]:
            tree.remove(child)
        for node in page["nodes"]:
            tree.append(make_node(node, sources, display["styles"]))
        for number, props in enumerate(tree.findall(".//p:cNvPr", NS), 1):
            props.set("id", str(number))
        members[part] = ET.tostring(slide, xml_declaration=True, encoding="UTF-8", standalone=True)
    with ZipFile(candidate, "w", ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    (build / "native-shapes.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf8")
    return candidate


def build_static(layout, output: Path, figure: str, author):
    """把明确静态图层和主题写成单页候选, 不推断其科学含义.

    layout: dict, canvas为EMU宽高, nodes为完整原生XML图层列表, theme为主题XML. output: Path, 本次候选文件. figure: str, 完整图名. author: dict, name/initials. 所有静态文字来自调用方, 本工具不内置规则或阈值.
    """
    deck = Presentation()
    deck.slide_width, deck.slide_height = map(Emu, layout["canvas"])
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.notes_slide.notes_text_frame.text = ""
    for xml in layout["nodes"]:
        slide.shapes._spTree.append(ET.fromstring(xml.encode("utf8")))
    output.parent.mkdir(parents=True, exist_ok=True)
    deck.save(output)
    with ZipFile(output) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    members["ppt/theme/theme1.xml"] = layout["theme"].encode("utf8")
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    identify(output, [figure], author)
    return output
