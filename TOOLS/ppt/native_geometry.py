"""提供显式参数的坐标投影、线段裁切和OOXML对象运输, 不包含科学选择或实验规则."""

import numpy as np
from copy import deepcopy
from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_PT = 12700


def clip_segment(segment, width, height):
    """按矩形裁切二维线段; segment为两个XY像素点, width/height为同单位视野尺寸, 无交集返回None."""
    (x0, y0), (x1, y1) = segment
    dx, dy = x1 - x0, y1 - y0
    low, high = 0.0, 1.0
    for p, q in zip([-dx, dx, -dy, dy], [x0, width - x0, y0, height - y0]):
        if p == 0:
            if q < 0:
                return None
        else:
            value = q / p
            if p < 0:
                low = max(low, value)
            else:
                high = min(high, value)
    if low > high:
        return None
    return [[x0 + low * dx, y0 + low * dy], [x0 + high * dx, y0 + high * dy]]


def group_native_shapes(shapes, source_rect, target_rect_pt, name, first_id, scale=None):
    """保留子对象坐标, 通过组变换把源矩形等比例放入目标矩形.

    shapes为DrawingML对象列表. source_rect为(x,y,width,height), 单位EMU;
    target_rect_pt为同结构目标矩形, 单位point, 1 point=12700 EMU.
    name为组名, first_id为起始对象编号; scale若显式给定则用该比例, 否则按目标矩形容纳.
    返回group为新的grpSp XML节点, next_id为下一个可用对象编号, ratio为无量纲显示比例.
    对象路径坐标保留, 字号按ratio同步缩放; 不解释对象中的科学值.
    """
    sx, sy, sw, sh = source_rect
    dx, dy, dw, dh = (float(v) * EMU_PER_PT for v in target_rect_pt)
    ratio = min(dw / sw, dh / sh) if scale is None else scale
    width, height = round(sw * ratio), round(sh * ratio)
    if width > dw + 1 or height > dh + 1:
        raise ValueError(f"{name} 的目标矩形不足以保持原视图比例")
    group = etree.Element(f"{{{NS['p']}}}grpSp")
    nv = etree.SubElement(group, f"{{{NS['p']}}}nvGrpSpPr")
    etree.SubElement(nv, f"{{{NS['p']}}}cNvPr", id=str(first_id), name=name)
    etree.SubElement(nv, f"{{{NS['p']}}}cNvGrpSpPr")
    etree.SubElement(nv, f"{{{NS['p']}}}nvPr")
    properties = etree.SubElement(group, f"{{{NS['p']}}}grpSpPr")
    transform = etree.SubElement(properties, f"{{{NS['a']}}}xfrm")
    for tag, attrs in (
        ("off", {"x": round(dx), "y": round(dy)}),
        ("ext", {"cx": width, "cy": height}),
        ("chOff", {"x": sx, "y": sy}),
        ("chExt", {"cx": sw, "cy": sh}),
    ):
        etree.SubElement(transform, f"{{{NS['a']}}}{tag}", **{k: str(v) for k, v in attrs.items()})
    next_id = first_id + 1
    for original in shapes:
        shape = deepcopy(original)
        if shape.xpath(".//@r:embed | .//@r:link | .//@r:id", namespaces=NS):
            raise ValueError("原生对象含外部关系, 不能直接运输")
        for nonvisual in shape.findall(".//p:cNvPr", NS):
            nonvisual.set("id", str(next_id))
            nonvisual.set("name", f"{name}/{nonvisual.get('name', '')}")
            next_id += 1
        # PowerPoint 的组变换缩放路径坐标,却不会同比缩小显式字号.
        # 同步字号才能让原指标和方法标题保持原来的占比与完整可读性.
        for run_properties in shape.xpath(".//a:*[@sz]", namespaces=NS):
            run_properties.set("sz", str(round(int(run_properties.get("sz")) * ratio)))
        group.append(shape)
    return group, next_id, ratio


def project(xyz, center, rotation, scale, offset):
    """把调用者坐标投影到面板坐标, 仅改变显示.

    Args:
        xyz: (N, 3), 调用者坐标单位.
        center: (3,), 显示中心, 调用者坐标单位.
        rotation: (3, 3), 调用者提供的相机基向量.
        scale: float, 每调用者长度单位对应的画布像素数.
        offset: (2,), 面板中心, 画布像素.
    Returns:
        (N, 3), 前两列为显示 XY 像素, 第三列为显示深度, 保持调用者坐标单位.
    """
    points = (xyz - center) @ rotation
    points[:, :2] = points[:, :2] * [scale, -scale] + offset
    return points


def bonds_layer(points, bonds, color, width, alpha, name):
    """将点索引对转换为独立可编辑线段, 不改变其连接关系.

    Args:
        points: (N, 3), 投影坐标; 前两列为画布像素.
        bonds: (B, 2) 或 (B, 3), 前两列为点索引; 其余列不参与显示.
        color: str, 十六进制显示颜色.
        width: float, 显示线宽, 像素.
        alpha: float, 不透明度, 0 至 1.
        name: str, PPT 图层名称, 如 layer_a.
    Returns:
        dict, lines 是 (B, 2, 2) 的像素端点; color、width、alpha 和 name 控制显示.
    """
    indices = np.asarray(bonds)[:, :2].astype(int)
    order = np.argsort(points[indices, 2].mean(1))
    return dict(
        kind="lines",
        name=name,
        color=color,
        width=width,
        alpha=alpha,
        lines=points[indices[order], :2].tolist(),
    )


def xfrm(shape):
    """返回原生形状的平移与尺寸,单位为EMU."""
    xf = shape.find("p:spPr/a:xfrm", NS)
    return xf.find("a:off", NS), xf.find("a:ext", NS)
