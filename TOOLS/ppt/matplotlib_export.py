"""将调用方已经绘制的Matplotlib画面导出为SVG和可编辑场景, 不计算科学数据.

export_scene只运输调用方图形, 返回单页scene字典并在本次build保存SVG/PDF/PNG及面板几何检查. PNG分辨率由dpi参数决定. 字符定位和曲线路径均沿用输入SVG, 本工具不拥有方法名、图号或评价阈值.
"""

from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from TOOLS.ppt.svg_scene import convert
from TOOLS.ppt.audit_panel_alignment import require_matplotlib_panel_alignment


def flatten_positioned_text(svg):
    """展开公式定位tspan, 保留标准小数点、下标和原生可编辑文字.

    svg: Path, 本次Matplotlib导出的SVG. tspan的x/y字段是逐字符坐标, 单位由原SVG给定; 本函数逐字符展开, 不重新排版. 输出仍写入同一临时SVG.
    """
    namespace = "{http://www.w3.org/2000/svg}"
    tree = ET.parse(svg)
    for parent in list(tree.getroot().iter()):
        for text in list(parent):
            spans = list(text) if text.tag == namespace + "text" else []
            if not spans:
                continue
            group = ET.Element(namespace + "g", dict(text.attrib))
            for span in spans:
                xs = [float(value) for value in span.get("x", "0").split()]
                ys = [float(value) for value in span.get("y", "0").split()]
                characters = span.text or ""
                assert len(xs) == len(characters), "公式SVG必须提供逐字符横坐标"
                for i, character in enumerate(characters):
                    item = ET.SubElement(
                        group,
                        namespace + "text",
                        {
                            "style": span.get("style", ""),
                            "x": str(xs[i]),
                            "y": str(ys[min(i, len(ys) - 1)]),
                        },
                    )
                    item.text = character
            index = list(parent).index(text)
            parent.remove(text)
            parent.insert(index, group)
    tree.write(svg, encoding="utf-8", xml_declaration=True)


def export_scene(
    fig,
    figure_id,
    notes,
    build,
    alignment_exemptions,
    *,
    dpi=600,
    text_width_extra=0.5,
    font_policy="svg",
    default_font_size=7,
    require_panel_labels=False,
):
    """在当前目录导出同源图稿、对齐证据与原生PPT场景清单.

    输入参数:
        - fig: matplotlib.figure.Figure, 调用方已经画好的当前画面.
        - figure_id: str, 本图完整标识, 如调用方在正式图集中声明的图名; 同时作为本次文件名.
        - notes: str, 调用方提供的候选备注占位正文; 作者备注可在装配完成后由专门工具复制.
        - build: Path, 本次临时导出目录, 不承担长期产物保存职责.
        - alignment_exemptions: list[dict], 调用方明确声明的面板对齐例外, 空列表表示全部严格检查.

    返回值:
        - scene: dict, id/stem为figure_id, width/height为pt画幅, notes为输入正文, shapes按SVG原绘制顺序保存文字和几何; 本函数不选择实验范围或科学字段.
    """
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        json_out=build / f"{figure_id}.alignment.json",
        overlay_svg=build / f"{figure_id}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
        require_panel_labels=require_panel_labels,
        exemptions=alignment_exemptions,
    )
    fig.savefig(build / f"{figure_id}.svg", facecolor="white")
    fig.savefig(build / f"{figure_id}.pdf", facecolor="white")
    fig.savefig(build / f"{figure_id}.png", dpi=dpi, facecolor="white")
    flatten_positioned_text(build / f"{figure_id}.svg")
    scene = {
        "id": figure_id,
        "stem": figure_id,
        "width": float(fig.get_figwidth() * 72),
        "height": float(fig.get_figheight() * 72),
        "notes": notes,
        "shapes": convert(
            build / f"{figure_id}.svg",
            text_width_extra=text_width_extra,
            font_policy=font_policy,
            default_font_size=default_font_size,
        ),
    }
    plt.close(fig)
    return scene


def panel_title(ax, letter, text, *, title_size, label_size, pad, label_offset):
    """用调用者给出的点偏移放置面板标题和编号, 不选择图号或科学标签."""
    ax.set_title(text, loc="left", fontsize=title_size, fontweight="bold", pad=pad)
    ax.annotate(
        letter,
        (0, 1),
        xycoords="axes fraction",
        xytext=label_offset,
        textcoords="offset points",
        fontsize=label_size,
        fontweight="bold",
        annotation_clip=False,
    )


def y_grid(ax, *, color, linewidth):
    """为调用者已画好的坐标轴添加Y参考网格; 颜色和线宽为显式显示参数."""
    ax.grid(axis="y", color=color, linewidth=linewidth, zorder=0)
    ax.set_axisbelow(True)
