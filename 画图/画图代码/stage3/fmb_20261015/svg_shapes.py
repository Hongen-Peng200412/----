"""把本轮 Matplotlib SVG 转换成可编辑 PPT 的形状清单.

仅处理本轮实际使用的文字、路径和引用元素; 文字保留为文字, 每个散点为独立椭圆.
SVG 点坐标为 1/72 英寸; assemble.mjs 再转换为 artifact-tool 的 1/96 英寸.
"""

import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import ImageFont


BUILD = Path(__file__).resolve().parents[4] / "temp/fmb_20261015"
NS = "{http://www.w3.org/2000/svg}"
NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"


def style_dict(value):
    """将 SVG style 字符串拆成属性字典; 分号分隔属性, 冒号分隔键和值."""
    return dict(part.strip().split(":", 1) for part in value.split(";") if ":" in part)


def transform(value):
    """将 SVG 变换字符串转换为 (3,3) 齐次矩阵, 按声明顺序组合."""
    matrix = np.eye(3)
    for kind, body in re.findall(r"(\w+)\(([^)]*)\)", value):
        values = [float(x) for x in re.findall(NUMBER, body)]
        current = np.eye(3)
        if kind == "translate":
            current[:2, 2] = [values[0], values[1] if len(values) > 1 else 0]
        elif kind == "scale":
            current[0, 0] = values[0]
            current[1, 1] = values[1] if len(values) > 1 else values[0]
        elif kind == "rotate":
            angle = math.radians(values[0])
            current[:2, :2] = [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]]
            if len(values) > 1:
                pivot = np.array(values[1:3])
                current[:2, 2] = pivot - current[:2, :2] @ pivot
        elif kind == "matrix":
            current = np.array([[values[0], values[2], values[4]], [values[1], values[3], values[5]], [0, 0, 1]])
        matrix = matrix @ current
    return matrix


def path_points(value):
    """把 SVG 路径解析为折线分段, 每段返回 (Q,2) 的平面坐标.

    输入 value 为本轮 SVG 的 M/L/H/V/C/Q/Z 路径. 贝塞尔曲线分成八段,
    只影响显示轮廓; 科学事件阶梯本身均为原样 M/L 直线.
    """
    tokens = re.findall(r"[A-Za-z]|" + NUMBER, value)
    index, command = 0, ""
    point = np.zeros(2)
    start = point.copy()
    parts, part = [], []
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command.upper() == "Z":
            part.append(start.copy())
            parts.append(part)
            part, point, command = [], start.copy(), ""
            continue
        count = {"M": 2, "L": 2, "C": 6, "Q": 4, "H": 1, "V": 1}[command.upper()]
        values = np.array([float(x) for x in tokens[index:index + count]])
        index += count
        relative, kind = command.islower(), command.upper()
        if kind in ("M", "L"):
            target = values + (point if relative else 0)
            if kind == "M":
                if part:
                    parts.append(part)
                part, start = [], target.copy()
            part.append(target.copy())
            point, command = target, "l" if relative else "L"
        elif kind in ("H", "V"):
            target = point.copy()
            axis = 0 if kind == "H" else 1
            target[axis] = values[0] + (point[axis] if relative else 0)
            part.append(target)
            point = target
        else:
            control = values.reshape(-1, 2) + (point if relative else 0)
            for fraction in np.linspace(0, 1, 9)[1:]:
                if kind == "C":
                    interpolated = (1 - fraction)**3 * point + 3 * (1 - fraction)**2 * fraction * control[0] + 3 * (1 - fraction) * fraction**2 * control[1] + fraction**3 * control[2]
                else:
                    interpolated = (1 - fraction)**2 * point + 2 * (1 - fraction) * fraction * control[0] + fraction**2 * control[1]
                part.append(interpolated)
            point = control[-1].copy()
    if part:
        parts.append(part)
    return parts


class SceneReader:
    """遍历一份 SVG, 用同一变换链生成文字与原生几何.

    defs: dict[str, Element], marker 引用表; items: list[dict], 顺序与 SVG 绘制顺序相同.
    """

    def __init__(self, svg):
        """读取 svg 路径, 初始化引用表和空的形状输出列表."""
        self.root = ET.parse(svg).getroot()
        self.defs = {element.get("id"): element for element in self.root.iter() if element.get("id")}
        self.items = []

    def walk(self, element, matrix, parent_style, is_use=False):
        """递归展开一个元素; matrix 为 (3,3) 累计变换, style 为继承属性."""
        tag = element.tag.removeprefix(NS)
        if tag in ("defs", "metadata", "clipPath", "style"):
            return
        matrix = matrix @ transform(element.get("transform", ""))
        style = {key: value.strip() for key, value in (parent_style | style_dict(element.get("style", ""))).items()}
        if tag == "use":
            reference = element.get("{http://www.w3.org/1999/xlink}href")[1:]
            shift = np.eye(3)
            shift[:2, 2] = [float(element.get("x", 0)), float(element.get("y", 0))]
            self.walk(self.defs[reference], matrix @ shift, style, True)
        elif tag == "text":
            self.add_text(element, matrix, style)
        elif tag == "path":
            self.add_path(element, matrix, style, is_use)
        else:
            for child in element:
                self.walk(child, matrix, style)

    def add_text(self, element, matrix, style):
        """依据 Arial 基线与 SVG 锚点生成可编辑文字框, 不将文字转成轮廓."""
        text = "".join(element.itertext())
        font = style.get("font", "8px Arial")
        size = float(re.search(NUMBER + r"(?=px)", font).group())
        bold = "700" in font or "bold" in font
        face = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", 1000)
        width = face.getlength(text) * size / 1000
        x, y = float(element.get("x", 0)), float(element.get("y", 0))
        anchor = style.get("text-anchor", "start")
        x -= width * (0.5 if anchor == "middle" else 1 if anchor == "end" else 0)
        height = size * 1.25
        center = matrix @ np.array([x + width / 2, y - size * 0.79 + height / 2, 1])
        angle = math.degrees(math.atan2(matrix[1, 0], matrix[0, 0]))
        scale = math.hypot(matrix[0, 0], matrix[1, 0])
        self.items.append({"kind": "text", "text": text, "x": float(center[0] - width * scale / 2), "y": float(center[1] - height * scale / 2), "w": width * scale + 1, "h": height * scale, "font": size * scale, "bold": bold, "rotation": angle, "color": style.get("fill", "#000000")})

    def add_path(self, element, matrix, style, is_use):
        """变换路径坐标并保留填充、透明度和线型; 圆形 marker 单独保留椭圆."""
        parts = path_points(element.get("d", ""))
        if not parts:
            return
        points = [(np.c_[part, np.ones(len(part))] @ matrix.T)[:, :2] for part in parts]
        all_points = np.concatenate(points)
        minimum, maximum = all_points.min(axis=0), all_points.max(axis=0)
        item = {"kind": "path", "x": float(minimum[0]), "y": float(minimum[1]), "w": float(maximum[0] - minimum[0]), "h": float(maximum[1] - minimum[1]), "parts": [(part - minimum).tolist() for part in points], "fill": style.get("fill", "#000000"), "stroke": style.get("stroke", "none"), "fill_alpha": float(style.get("fill-opacity", style.get("opacity", 1))), "stroke_alpha": float(style.get("stroke-opacity", style.get("opacity", 1))), "stroke_width": float(style.get("stroke-width", 1)), "dash": style.get("stroke-dasharray", "none")}
        if is_use and "C" in element.get("d", "") and abs(item["w"] - item["h"]) < 1e-4:
            item["kind"] = "ellipse"
            item.pop("parts")
        self.items.append(item)


def main():
    """读取 本轮 manifest 和 SVG, 写出按页排序的 scenes.json 装配清单."""
    pages = json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))
    for page in pages:
        reader = SceneReader(BUILD / (page["stem"] + ".svg"))
        reader.walk(reader.root, np.eye(3), {})
        page["shapes"] = reader.items
    (BUILD / "scenes.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    print([(page["stem"], len(page["shapes"])) for page in pages])


if __name__ == "__main__":
    main()
