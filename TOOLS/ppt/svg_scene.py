"""将 Matplotlib SVG 解析为可编辑 PPT 的几何与文字清单.

由调用方在本次 temp 的 scenes.json 保存每页 shape 列表. 曲线采样成折线, 散点保留为独立椭圆,
文字保留文本而非字体轮廓. 本转换器仅处理明示支持的 SVG 文字、路径和引用元素.
"""

import re, math
import xml.etree.ElementTree as ET
import numpy as np
from PIL import ImageFont

NS = "{http://www.w3.org/2000/svg}"
NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"


def transform(value):
    """把SVG transform属性还原为(3,3)齐次二维仿射矩阵.

    value为translate/scale/rotate/matrix组成的属性字符串, 矩阵作用于[x,y,1]列向量.
    平移沿SVG画布单位, 旋转输入为度; 多个变换保持原声明顺序.
    """
    mat = np.eye(3)
    for kind, body in re.findall(r"(\w+)\(([^)]*)\)", value):
        v = [float(x) for x in re.findall(NUMBER, body)]
        t = np.eye(3)
        if kind == "translate":
            t[:2, 2] = [v[0], v[1] if len(v) > 1 else 0]
        elif kind == "scale":
            t[0, 0] = v[0]
            t[1, 1] = v[1] if len(v) > 1 else v[0]
        elif kind == "rotate":
            a = math.radians(v[0])
            t[:2, :2] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
            if len(v) > 1:
                p = np.array(v[1:3])
                t[:2, 2] = p - t[:2, :2] @ p
        elif kind == "matrix":
            t = np.array([[v[0], v[2], v[4]], [v[1], v[3], v[5]], [0, 0, 1]])
        else:
            raise ValueError(kind)
        mat = mat @ t
    return mat


def path_points(d):
    """把SVG路径命令转为分段二维点列, 保持原路径方向和画布坐标.

    d为M/L/H/V/C/Q/Z及小写相对形式的路径字符串.
    返回list[np.ndarray], 每项形状(K,2), 一项对应一个连续子路径.
    曲线按原固定分段采样, 不改变科学数据或按显示范围重新筛点.
    """
    tokens = re.findall(r"[A-Za-z]|" + NUMBER, d)
    i = 0
    cmd = ""
    p = np.zeros(2)
    start = p.copy()
    parts = []
    part = []
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        if cmd.upper() == "Z":
            part.append(start.copy())
            parts.append(part)
            part = []
            p = start.copy()
            cmd = ""
            continue
        n = {"M": 2, "L": 2, "C": 6, "Q": 4, "H": 1, "V": 1}[cmd.upper()]
        v = np.array([float(x) for x in tokens[i : i + n]])
        i += n
        rel = cmd.islower()
        kind = cmd.upper()
        if kind in ("M", "L"):
            q = v + (p if rel else 0)
            if kind == "M":
                if part:
                    parts.append(part)
                part = []
                start = q.copy()
            part.append(q.copy())
            p = q
            cmd = "l" if rel else "L"
        elif kind in ("H", "V"):
            q = p.copy()
            axis = 0 if kind == "H" else 1
            q[axis] = v[0] + (p[axis] if rel else 0)
            part.append(q)
            p = q
        else:
            q = v.reshape(-1, 2) + (p if rel else 0)
            for t in np.linspace(0, 1, 9)[1:]:
                b = (
                    (1 - t) ** 3 * p
                    + 3 * (1 - t) ** 2 * t * q[0]
                    + 3 * (1 - t) * t * t * q[1]
                    + t**3 * q[2]
                    if kind == "C"
                    else (1 - t) ** 2 * p + 2 * (1 - t) * t * q[0] + t * t * q[1]
                )
                part.append(b)
            p = q[-1].copy()
    if part:
        parts.append(part)
    return parts


def convert(svg, text_width_extra=0.5, font_policy="svg", default_font_size=7):
    """解析SVG显示图元, 返回list[dict], 不解释调用方科学数据.

    svg为本次SVG文件地址. text_width_extra是文字矩形的画布余量; font_policy为svg或明确字体名,
    default_font_size为原SVG缺少字体声明时的显示字号. 这些缺省值保留现有调用方的显示契约.
    每项kind为text/path/ellipse, x/y/w/h为同一SVG画布坐标中的外接矩形.
    text项保存text/font/font_family/bold/rotation/color; font为字号, rotation为度.
    path项的parts是list[list[[x,y]]], 坐标相对本项矩形左上角, fill/stroke及各alpha分别保存颜色与透明度.
    ellipse项由已有等宽等高闭合引用路径识别, 不再携带parts; 图元顺序沿原SVG绘制顺序.
    """
    root = ET.parse(svg).getroot()
    defs = {el.get("id"): el for el in root.iter() if el.get("id")}
    items = []

    def walk(el, mat, parent_style, is_use=False):
        """递归运输当前XML元素, mat为(3,3)父级变换, parent_style为父级属性字典."""
        tag = el.tag.removeprefix(NS)
        if tag in ("defs", "metadata", "clipPath", "style"):
            return
        mat = mat @ transform(el.get("transform", ""))
        style = parent_style | dict(
            part.strip().split(":", 1)
            for part in el.get("style", "").split(";")
            if ":" in part
        )
        style = {k: v.strip() for k, v in style.items()}
        if tag == "use":
            ref = el.get("{http://www.w3.org/1999/xlink}href")[1:]
            shift = np.eye(3)
            shift[:2, 2] = [float(el.get("x", 0)), float(el.get("y", 0))]
            walk(defs[ref], mat @ shift, style, True)
            return
        if tag == "text":
            text = "".join(el.itertext())
            font = style.get("font", f"{default_font_size}px Arial")
            fs = float(re.search(NUMBER + r"(?=px)", font).group())
            bold = "700" in font or "bold" in font
            # 保留旧 Arial 场景; 新比较图使用支持阈值下标的 Calibri, 字宽按 SVG 同一字体度量.
            font_family = (
                font_policy
                if font_policy != "svg"
                else ("Calibri" if "Calibri" in font else "Arial")
            )
            font_file = (
                ("calibrib.ttf" if bold else "calibri.ttf")
                if font_family == "Calibri"
                else ("arialbd.ttf" if bold else "arial.ttf")
            )
            pil = ImageFont.truetype(
                "C:/Windows/Fonts/" + font_file, 1000
            )  # 1000 px 参考字号, 后续按 SVG 的 fs 等比换回 pt 字宽.
            width = pil.getlength(text) * fs / 1000
            x = float(el.get("x", 0))
            y = float(el.get("y", 0))
            anchor = style.get("text-anchor", "start")
            x -= width * (0.5 if anchor == "middle" else 1 if anchor == "end" else 0)
            # 文本矩形以字体基线计算, 旋转围绕矩形中心, 与 SVG 变换一致.
            h = fs * 1.25
            center = mat @ np.array([x + width / 2, y - fs * 0.79 + h / 2, 1])
            angle = math.degrees(math.atan2(mat[1, 0], mat[0, 0]))
            scale = math.hypot(mat[0, 0], mat[1, 0])
            items.append(
                {
                    "kind": "text",
                    "text": text,
                    "x": float(center[0] - width * scale / 2),
                    "y": float(center[1] - h * scale / 2),
                    "w": width * scale + text_width_extra,
                    "h": h * scale,
                    "font": fs * scale,
                    "font_family": font_family,
                    "bold": bold,
                    "rotation": angle,
                    "color": style.get("fill", "#000000"),
                }
            )
            return
        if tag == "path":
            parts = path_points(el.get("d", ""))
            if not parts:
                return
            points = [
                (np.c_[part, np.ones(len(part))] @ mat.T)[:, :2] for part in parts
            ]
            allpoints = np.concatenate(points)
            minimum = allpoints.min(0)
            maximum = allpoints.max(0)
            # SVG 默认 fill 为黑色, 默认无描边. 透明度单独保留.
            item = {
                "kind": "path",
                "x": float(minimum[0]),
                "y": float(minimum[1]),
                "w": float(maximum[0] - minimum[0]),
                "h": float(maximum[1] - minimum[1]),
                "parts": [(p - minimum).tolist() for p in points],
                "fill": style.get("fill", "#000000"),
                "stroke": style.get("stroke", "none"),
                "fill_alpha": float(style.get("fill-opacity", style.get("opacity", 1))),
                "stroke_alpha": float(
                    style.get("stroke-opacity", style.get("opacity", 1))
                ),
                "stroke_width": float(style.get("stroke-width", 1)),
                "dash": style.get("stroke-dasharray", "none"),
            }
            if is_use and "C" in el.get("d", "") and abs(item["w"] - item["h"]) < 1e-4:
                item["kind"] = "ellipse"
                item.pop("parts")
            items.append(item)
            return
        if tag == "image":
            raise ValueError("Raster image found in scientific vector artwork")
        for child in el:
            walk(child, mat, style)

    walk(root, np.eye(3), {})
    return items
