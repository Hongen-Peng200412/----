"""将本次9WUP投影层映射到三列原生视图, 科学选择由本图geometry.py完成.

scene返回本图方法标题、密度/受体合并路径、逐键配体和碰撞线及原子圆形. 这里只规定9WUP的当前作者面板组合; 通用裁切与PPT形状运输由TOOLS完成.
"""

import math
from TOOLS.ppt.native_geometry import clip_segment


def scene(geometry, metrics):
    """把一个9WUP几何记录转成中性单页场景, 坐标均为局部显示像素.

    geometry: dict, geometry.json.cases[0], methods保存三方法层. metrics: dict, case_metrics.json[0], 含原RMSD(Å)、密度覆盖比例和真实三维碰撞对数. 返回page只供本次临时原生PPT注入.
    """
    shapes = []
    methods = [
        ("official", "PocketXMol-official"),
        ("tuned", "DG-PocketXMol"),
        ("build", "Emap2lig-Build"),
    ]
    for column, (method, label) in enumerate(methods):
        shapes.append(
            dict(
                kind="text",
                name=f"stage3-cases-main_{column}",
                x=30 + 312 * column,
                y=12,
                w=294,
                h=27,
                rotation=0,
                text=label,
                font_family="Arial",
                font=23,
                bold=True,
                color=geometry["methods"][method][3]["color"],
            )
        )
    for column, (method, _) in enumerate(methods):
        x, y, width, height = 24 + 312 * column, 835, 280, 140
        for layer in geometry["methods"][method]:
            name = f"9wup_2_{method}_{layer['name']}"
            if layer["kind"] == "lines":
                lines = [
                    clipped
                    for line in layer["lines"]
                    if (clipped := clip_segment(line, width, height)) is not None
                ]
                # 原显示将实验密度网格和受体各合为一路径; 配体键及碰撞线仍可逐条编辑.
                groups = (
                    [(name, lines)]
                    if layer["name"] in ["ExperimentalDensity", "Receptor"]
                    else [(f"{name}_{i}", [line]) for i, line in enumerate(lines)]
                )
                color = "#" + "".join(
                    f"{math.floor(int(layer['color'][i:i+2],16)*layer['alpha']+255*(1-layer['alpha'])+.5):02x}"
                    for i in [1, 3, 5]
                )
                for group_name, parts in groups:
                    if parts:
                        shapes.append(
                            dict(
                                kind="path",
                                name=group_name,
                                x=x,
                                y=y,
                                w=width,
                                h=height,
                                fill="none",
                                fill_alpha=1,
                                stroke=color,
                                stroke_alpha=1,
                                stroke_width=layer["width"],
                                dash="dashed" if layer.get("dashed", False) else "none",
                                parts=parts,
                            )
                        )
            else:
                for i, atom in enumerate(layer["atoms"]):
                    radius = atom["radius"]
                    if (
                        atom["x"] - radius < 0
                        or atom["x"] + radius > width
                        or atom["y"] - radius < 0
                        or atom["y"] + radius > height
                    ):
                        continue
                    shapes.append(
                        dict(
                            kind="ellipse",
                            name=f"{name}_{i}",
                            x=x + atom["x"] - radius,
                            y=y + atom["y"] - radius,
                            w=2 * radius,
                            h=2 * radius,
                            fill=atom["color"],
                            fill_alpha=1,
                            stroke="none",
                            stroke_alpha=1,
                            stroke_width=0,
                            dash="none",
                        )
                    )
        value = metrics[method]
        text = f"RMSD {value['rmsd']:.2f} Å   D {100*value['density_fraction']:.0f}%   Clash {value['clash_pairs']}"
        shapes.append(
            dict(
                kind="text",
                name=f"stage3-cases-main_{4+2*column}",
                x=x,
                y=976,
                w=293,
                h=22,
                rotation=0,
                text=text,
                font_family="Arial",
                font=16.5,
                bold=False,
                color="#34444E",
            )
        )
    return dict(
        id="stage3-cases-main",
        stem="stage3-cases-main",
        notes="",
        width=980,
        height=1256,
        shapes=shapes,
    )
