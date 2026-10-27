"""用同一组原生几何绘制论文预览, 保存 PPT 布局以及面板对齐报告.

源 geometry.json 的坐标仅用于显示. 所有 RMSD、密度覆盖和碰撞均读取 cases.json 的三维计算结果.
"""
import os
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle

sys.path.insert(0,'C:/Users/15919/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
# SOURCE 指向当前条件的冻结资产根; OUT 保存其重新生成的图稿, 不写冻结原件.
SOURCE = Path(os.environ['FIGURE_SOURCE_ROOT']) if 'FIGURE_SOURCE_ROOT' in os.environ else ROOT/'画图/画图代码/stage3/output/stage3-cases-main'
OUT=Path(os.environ['FIGURE_RENDER_ROOT']) if 'FIGURE_RENDER_ROOT' in os.environ else SOURCE/'regenerated'
geometry=json.loads((OUT/'geometry.json').read_text(encoding='utf-8'))
cases={(r['pdb_id'],r['occurrence_id']):r for r in json.loads((OUT/'cases.json').read_text(encoding='utf-8'))}
mpl.rcParams.update({'font.family':'Arial','font.size':8,'svg.fonttype':'none','pdf.fonttype':42})


def text(fig, value, x, y, size, width, height, bold, color, records, total_width, total_height):
    """在固定物理画布中放置文字, 同时记录 PPT 的可编辑文字框.

    Args:
        fig: Matplotlib Figure, 本页画布.
        value: str, 实际展示文字.
        x,y,width,height: float, 文字框左上角及大小, 布局像素.
        size: float, 字体大小, 布局像素; PDF 按最终物理尺寸换算.
        bold: bool, 是否加粗.
        color: str, 十六进制文字色.
        records: list, 本页 PPT 文字对象, 原地追加.
        total_width,total_height: float, 完整画布大小, 布局像素.
    """
    fig.text(x/total_width,1-(y+height/2)/total_height,value,ha='left',va='center',fontsize=size*519/total_width,fontweight='bold' if bold else 'normal',color=color)
    records.append(dict(kind='text',value=value,x=x,y=y,width=width,height=height,size=size,bold=bold,color=color))


def clip_segment(segment):
    """裁切单个显示线段到 280×140 面板, 返回两端点或 None.

    segment 为 (2, 2) 的面板 XY 像素端点. 三维坐标和评价值不参与这个显示操作.
    显式裁切使 PDF 的路径本身不越界, 与 PPT 使用同一个矩形范围.
    """
    (x0, y0), (x1, y1) = segment
    dx, dy = x1-x0, y1-y0
    low, high = 0.0, 1.0
    for p, q in zip([-dx, dx, -dy, dy], [x0, 280-x0, y0, 140-y0]):
        if p == 0:
            if q < 0:
                return None
        elif p < 0:
            low = max(low, q/p)
        else:
            high = min(high, q/p)
    if low > high:
        return None
    return [[x0+low*dx, y0+low*dy], [x0+high*dx, y0+high*dy]]


pages=[]
by_key = {(r['pdb_id'],r['occurrence_id']):r for r in geometry['cases']}
density_keys = [('9q16',0),('9ub7',3),('9r3d',0)]
clash_keys = [('9u7j',2),('9wup',2),('9wq3',5)]
alternative_keys = [('9llg',2),('9lfa',0),('9bjj',16),('30ga',7)]
# 第四页 c/d 收纳主图换下的 9BJJ/30GA; 六个主图案例与四个备选互不重复.
if 'FIGURE_SOURCE_ROOT' in os.environ:
    # case_selection.json 保存明确条件的实例名单; 页内样式仍由下面的同一模板绘制.
    selection = json.loads((SOURCE / 'case_selection.json').read_text(encoding='utf-8'))
    density_keys = [tuple(key) for key in selection['density']]
    clash_keys = [tuple(key) for key in selection['clash']]
    main_keys = [tuple(key) for key in selection['main_density'] + selection['main_clash']]
    settings = [('main','stage3-cases-main',[by_key[k] for k in main_keys]),('density','stage3-cases-density',[by_key[k] for k in density_keys]),('clash','stage3-cases-clash',[by_key[k] for k in clash_keys])]
else:
    settings=[('main','stage3-cases-main',[by_key[k] for k in density_keys+clash_keys]),('density','stage3-cases-density',[by_key[k] for k in density_keys]),('clash','stage3-cases-clash',[by_key[k] for k in clash_keys]),('alternatives','stage3-cases-alternatives',[by_key[k] for k in alternative_keys])]
for name, figure_name, rows in settings:
    W,H=980,76+len(rows)*188+52
    width_mm = 183
    fig=plt.figure(figsize=(width_mm/25.4,width_mm/25.4*H/W),facecolor='white')
    page=dict(name=name,figure_name=figure_name,width=W,height=H,items=[])
    tuned_label = 'DG-PocketXmol' if 'FIGURE_SOURCE_ROOT' in os.environ else 'PocketXMol-tuned'
    for col,(method,label) in enumerate([('official','PocketXMol-official'),('tuned',tuned_label),('build','Emap2lig-Build')]):
        text(fig,label,30+col*312,12,23,294,27,True,geometry['colors'][method],page['items'],W,H)
    for row_index, row in enumerate(rows):
        key=(row['pdb_id'],row['occurrence_id']);case=cases[key]
        component=case['occurrence']['components'][0]
        y=54+row_index*188
        letter=chr(97+row_index) if name!='clash' else chr(100+row_index)
        label=f"{letter}  {row['pdb_id'].upper()} · {component['ccd_id']} ({component['auth_asym_id']}:{component['auth_seq_id']})"
        text(fig,label,26,y,19,630,24,True,'#24343E',page['items'],W,H)
        # 每例三格共用 5 Å 的比例尺, 根据各自 pixels_per_A 计算长度.
        length=5*row['pixels_per_A']
        fig.lines.append(mpl.lines.Line2D([(940-length)/W,940/W],[1-(y+15)/H]*2,transform=fig.transFigure,color='#455661',linewidth=1))
        page['items'].append(dict(kind='line',x1=940-length,y1=y+15,x2=940,y2=y+15,color='#455661',width=1.9))
        text(fig,'5 Å',945,y+3,14,33,22,False,'#455661',page['items'],W,H)
        for col,method in enumerate(['official','tuned','build']):
            x=24+col*312;top=y+29
            ax=fig.add_axes([x/W,1-(top+140)/H,280/W,140/H],label=f'{name}_{row_index}_{col}')
            ax.set_xlim(0,280);ax.set_ylim(140,0);ax.set_aspect('equal');ax.axis('off')
            for layer in row['methods'][method]:
                if layer['kind']=='lines':
                    segments = [s for line in layer['lines'] if (s := clip_segment(line)) is not None]
                    ax.add_collection(LineCollection(segments,colors=layer['color'],linewidths=layer['width']*519/W,alpha=layer['alpha'],linestyles='dashed' if layer.get('dashed') else 'solid'))
                else:
                    for atom in layer['atoms']:
                        if atom['radius'] <= atom['x'] <= 280-atom['radius'] and atom['radius'] <= atom['y'] <= 140-atom['radius']:
                            ax.add_patch(Circle((atom['x'],atom['y']),atom['radius'],facecolor=atom['color'],edgecolor='none'))
            page['items'].append(dict(kind='molecule',key=list(key),method=method,x=x,y=top,width=280,height=140,layers=row['methods'][method]))
            m=case[method]
            value=f"RMSD {m['rmsd']:.2f} Å   D {100*m['density_fraction']:.0f}%   Clash {m['clash_pairs']}"
            text(fig,value,x,y+170,16.5,293,22,False,'#34444E',page['items'],W,H)
    bottom=H-40
    legend=[('Reference ligand',geometry['colors']['gt'],24),('Experimental density',geometry['colors']['density'],255),('Receptor',geometry['colors']['receptor'],558),('Clashing atoms',geometry['colors']['clash'],740)]
    for label,color,x in legend:
        fig.lines.append(mpl.lines.Line2D([x/W,(x+20)/W],[1-(bottom+13)/H]*2,transform=fig.transFigure,color=color,linewidth=2))
        page['items'].append(dict(kind='line',x1=x,y1=bottom+13,x2=x+20,y2=bottom+13,color=color,width=3.6))
        text(fig,label,x+27,bottom,16.5,min(230,W-x-27),25,False,'#34444E',page['items'],W,H)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(OUT/f'{figure_name}.alignment.json'),overlay_svg=str(OUT/f'{figure_name}.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True,
        row_groups=[[f'{name}_{r}_{c}' for c in range(3)] for r in range(len(rows))],
        column_groups=[[f'{name}_{r}_{c}' for r in range(len(rows))] for c in range(3)])
    fig.savefig(OUT/f'{figure_name}.png',dpi=600)
    fig.savefig(OUT/f'{figure_name}.svg')
    fig.savefig(OUT/f'{figure_name}.pdf')
    plt.close(fig)
    pages.append(page)
(OUT/'deck_layout.json').write_text(json.dumps(pages),encoding='utf-8')
print(f'Rendered {len(pages)} figure pages and layout manifests')
