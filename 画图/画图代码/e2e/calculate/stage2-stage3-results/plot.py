"""从冻结逐实例统计绘制Match/Build联图；显示窗口不改变统计成员。"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').is_file())
BUILD = Path(os.environ.get('FIGURE_BUILD_ROOT', ROOT / 'temp/stage23_execution/build'))
SOURCE = BUILD / 'data/data.json'
NATURE = Path.home() / '.codex/skills/nature-figure/scripts'
sys.path.insert(0, str(NATURE))
from audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams.update({'font.family': 'Arial', 'font.size': 6, 'axes.labelsize': 6,
                     'xtick.labelsize': 5.6, 'ytick.labelsize': 5.6,
                     'axes.linewidth': .6, 'lines.linewidth': 1,
                     'svg.fonttype': 'none', 'pdf.fonttype': 42,
                     'xtick.major.size': 2, 'ytick.major.size': 2,
                     'axes.spines.top': False, 'axes.spines.right': False})
C = {'GT': '#2F6B9A', 'CA2': '#D68B3A', 'Emap2lig': '#529667',
     'official': '#7F8C8D', 'nodensity': '#8E5EA2', 'DG': '#2F6B9A'}
M = [('overall', 'Overall', '#1C2833', 'D'), ('small', 'Small molecule', '#2E86C1', 'o'),
     ('metal', 'Metal ion', '#28B463', 's'), ('sugar', 'Sugar', '#D35400', '^')]
WIDTH = 6.27


def title(ax, letter, text):
    """固定点偏移保证各面板编号同高。"""
    ax.set_title(text, loc='left', fontsize=6.8, fontweight='bold', pad=7)
    ax.annotate(letter, (0, 1), xycoords='axes fraction', xytext=(-19, 7),
                textcoords='offset points', fontsize=8, fontweight='bold', annotation_clip=False)


def grid(ax):
    """浅灰参考线不遮挡数据。"""
    ax.grid(axis='y', color='#E3E7E9', linewidth=.45, zorder=0)
    ax.set_axisbelow(True)


def save(fig, stem, notes, figure_id, alignment=True):
    """同一几何同时输出矢量图、预览、对齐证据和PPT场景。"""
    fig.canvas.draw()
    if alignment:
        require_matplotlib_panel_alignment(fig, json_out=BUILD / f'{stem}.alignment.json',
                                          overlay_svg=BUILD / f'{stem}.alignment.svg',
                                          tolerance_pt=1.5, require_panel_labels=True, strict=True)
    fig.savefig(BUILD / f'{stem}.svg', dpi=400)
    fig.savefig(BUILD / f'{stem}.pdf', dpi=400)
    fig.savefig(BUILD / f'{stem}.png', dpi=400)
    reader = scene_module.SceneReader(BUILD / f'{stem}.svg')
    reader.walk(reader.root, np.eye(3), {})
    page = {'stem': stem, 'id': figure_id, 'notes': notes,
            'width': fig.get_figwidth()*72, 'height': fig.get_figheight()*72,
            'shapes': reader.items}
    plt.close(fig)
    return page


def main_results(data):
    """Build三个面板使用235固定分母；第三行复用作者的三个原生病例视图。"""
    fig = plt.figure(figsize=(WIDTH, 6.55))
    gs = fig.add_gridspec(3, 3, left=.073, right=.987, bottom=.025, top=.945,
                          wspace=.34, hspace=.65, height_ratios=[1, 1, .85])
    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
    ax = axes[0]
    x = np.arange(4)
    for receptor, off in [('GT', -.19), ('CA2', .19)]:
        vals = [data['match']['categories'][receptor][m[0]]['accuracy_pct'] for m in M]
        ax.bar(x+off, vals, .36, color=C[receptor], alpha=.8, zorder=2)
        for pos, val in zip(x+off, vals):
            ax.text(pos, val+1.4, f'{val:.1f}', ha='center', fontsize=5.2, color=C[receptor])
    ax.set_xticks(x, ['Overall', 'Small\nmolecule', 'Metal\nion', 'Sugar'])
    ax.set_ylim(0, 107); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel('Matching accuracy (%)'); grid(ax); title(ax, 'a', 'Match: category accuracy')
    ax.legend(handles=[Patch(color=C[k], alpha=.8, label=k) for k in ('GT', 'CA2')],
              loc='lower left', fontsize=5.3, handlelength=1, borderpad=.3)
    for ax, receptor, letter in zip(axes[1:3], ['GT', 'CA2'], ['b', 'c']):
        for key, label, color, marker in M:
            yy = data['match']['by_candidate_count'][receptor][key]['accuracy_pct']
            ax.plot(np.arange(5), yy, color=color, marker=marker, ms=2.6,
                    ls='-' if key == 'overall' else '--', label=label, lw=1 if key == 'overall' else .8)
        ax.set_xticks(np.arange(5), ['1', '2', '3', '4', '≥5'])
        ax.set_xlim(-.12, 4.12); ax.set_ylim(35, 105); ax.set_yticks([40, 60, 80, 100])
        ax.set_xlabel('Candidate SMILES per PDB')
        ax.set_ylabel('Matching accuracy (%)'); grid(ax); title(ax, letter, f'Match ({receptor})')
        ax.legend(loc='lower left', fontsize=5.2, handlelength=1.5, labelspacing=.18,
                  borderpad=.3, framealpha=.95)
    build = data['main_build']; n = build['denominator']
    ax = axes[3]
    for name in ('Emap2lig', 'CA2', 'GT'):
        for pose, style in [('top1', '-'), ('top5', '--')]:
            arr = np.sort(build['series'][name][pose])
            # 严格小于阈值的经验分布；完整n参与分母，窗口只显示0–4Å。
            xx = np.unique(np.r_[[0,1,2,3,4], np.linspace(0, 4, 400), arr[(arr >= 0) & (arr <= 4)]])
            yy = np.searchsorted(arr, xx, side='left')/n*100
            ax.step(xx, yy, where='pre', color=C[name], ls=style, lw=1)
    ax.set_xlim(0, 4); ax.set_ylim(0, 103); ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xlabel('RMSD threshold (Å)'); ax.set_ylabel('Cumulative success (%)')
    for t, style in [(1, ':'), (2, '--')]: ax.axvline(t, color='#666666', ls=style, lw=.65)
    handles = [Line2D([], [], color=C[k], label=v) for k, v in
               [('Emap2lig', 'Emap2lig-Build'), ('CA2', 'DG (CA2)'), ('GT', 'DG (GT)')]]
    leg = ax.legend(handles=handles, loc='lower right', fontsize=5.2, borderpad=.3, labelspacing=.3)
    ax.add_artist(leg)
    ax.legend(handles=[Line2D([], [], color='#555555', ls=s, label=l) for s, l in
                       [('-', 'Top-1'), ('--', 'Top-5')]], loc='upper left', fontsize=5.2, borderpad=.3)
    title(ax, 'd', 'Build: cumulative accuracy'); grid(ax)
    ax = axes[4]; poses = ['top1', 'top5', 'best50']
    handles=[]
    for offset, name, label in [(-.25, 'Emap2lig', 'Emap2lig'), (0, 'CA2', 'DG (CA2)'), (.25, 'GT', 'DG (GT)')]:
        values = [np.asarray(build['series'][name][p]) for p in poses]
        low = [np.mean(a < 1)*100 for a in values]; high = [np.mean(a < 2)*100 for a in values]
        xx = np.arange(3)+offset
        ax.bar(xx, high, .22, color=C[name], alpha=.34, edgecolor=C[name], linewidth=.6, zorder=2)
        ax.bar(xx, low, .22, color=C[name], alpha=.95, zorder=3)
        for xp, lo, hi in zip(xx, low, high):
            ax.text(xp, hi+1.4, f'{hi:.0f}', ha='center', fontsize=5.2, color=C[name])
            ax.text(xp, max(lo/2, 3.5), f'{lo:.0f}', ha='center', va='center', fontsize=5.2, color='white')
        handles.extend([Patch(facecolor=C[name], label=label+' <1 Å'),
                        Patch(facecolor=C[name], alpha=.34, label=label+' <2 Å')])
    # 图例同模型同一行，左<1Å、右<2Å；matplotlib按列填充。
    order=[0,2,4,1,3,5]
    ax.legend(handles=[handles[i] for i in order], ncol=2, loc='upper center',
              fontsize=5.05, columnspacing=.6, handlelength=.9, handletextpad=.3,
              labelspacing=.18, borderpad=.25)
    ax.set_ylim(0, 137); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xticks(range(3), ['Top-1', 'Top-5', 'Best of 50']); ax.set_ylabel('Success rate (%)')
    title(ax, 'e', 'Build: success thresholds'); grid(ax)
    ax = axes[5]; e = np.asarray(build['series']['Emap2lig']['top1'])
    ax.fill_between([0, 5], [0, 0], [0, 5], color='#EAF2F8', alpha=.7)
    ax.plot([0, 5], [0, 5], '--', color='#333333', lw=.7)
    for name, marker in [('CA2', '^'), ('GT', 'o')]:
        arr = np.asarray(build['series'][name]['top1']); win=np.mean(arr < e)*100
        ax.scatter(np.minimum(e, 5), np.minimum(arr, 5), s=5.2, color=C[name], alpha=.55,
                   marker=marker, edgecolors='none', label=f'{name}: {win:.1f}% wins')
    ax.set_xlim(0, 5.15); ax.set_ylim(0, 5.15)
    for dim in ('x', 'y'):
        getattr(ax, f'set_{dim}ticks')([0, 1, 2, 3, 4, 5], ['0', '1', '2', '3', '4', '≥5'])
    ax.axhline(2, ls=':', color='#999999', lw=.55); ax.axvline(2, ls=':', color='#999999', lw=.55)
    ax.set_xlabel('Emap2lig-Build RMSD (Å)'); ax.set_ylabel('DG-PocketXMol RMSD (Å)')
    ax.legend(loc='upper left', fontsize=5.2, borderpad=.3, handlelength=1, labelspacing=.3)
    title(ax, 'f', 'Build: paired Top-1 poses')
    # 目标区域为SVG/PPT左上角起算的pt；分子原生对象稍后按同一尺寸注入。
    fig.text(.53, 1-351/(6.55*72), '9WUP · FAD (A:1103)', ha='center', fontsize=7, fontweight='bold')
    case_rects=[]
    for c, letter in enumerate('ghi'):
        box=gs[2,c].get_position(fig); x0=box.x0*WIDTH*72; y0=(1-box.y1)*6.55*72
        fig.text((x0-19)/(WIDTH*72), (6.55*72-y0+7)/(6.55*72), letter, fontsize=8, fontweight='bold')
        case_rects.append([x0-6, y0, box.width*WIDTH*72+8, box.height*6.55*72])
    (BUILD/'case_rects.json').write_text(json.dumps(case_rects),encoding='utf-8')
    notes=('配体身份匹配与构象构建。a，LigandSeek-Match在GT与CA2受体条件下的总体及分类匹配准确率。b、c，按每个PDB的候选SMILES身份数分层；Overall按正确数及支持数汇总。a–c的身份支持blob分别为1238（GT）与1160（CA2）。d–f使用三个方法共同检出且可评价的235个实例。d，Top-1（实线）和Top-5（虚线）的累计成功率。e，深色为RMSD<1 Å，浅色柱总高为<2 Å。Top-5及best-of-50分别取原排序前5个及全部50个候选的最小RMSD。f，Top-1配对比较；≥5 Å显示在边界，胜率由未截断值计算。g–i，9WUP的FAD（A:1103）：原始PocketXMol、DG-PocketXMol及Emap2lig-Build的原有视图，叠加显示沉积受体；前两者以该受体的标准Centre口袋为输入。D为推荐密度阈值覆盖的配体重原子比例，Clash为受体碰撞原子对数。\nENGLISH:\n'
           'Ligand identity matching and pose construction. a, Overall and class-specific accuracy of LigandSeek-Match with deposited (GT) and CryoAtom2 (CA2) receptors. b, c, Accuracy by the number of candidate SMILES identities per PDB; Overall pools correct assignments and supports. a–c include 1,238 (GT) and 1,160 (CA2) identity-supported blobs. d–f, Comparison on 235 jointly detected, evaluable instances. d, Cumulative success for Top-1 (solid) and Top-5 (dashed). e, Dark bars show RMSD <1 Å; total light-bar heights show <2 Å. Top-5 and best-of-50 report the minimum RMSD among the original top five and all 50 candidates, respectively. f, Paired Top-1 RMSDs; values ≥5 Å appear at the boundary, with wins calculated before capping. g–i, FAD (A:1103) in 9WUP: PocketXMol-official, DG-PocketXMol and Emap2lig-Build. Overlaid receptors are the deposited structures; the first two methods use standard Centre pockets. D denotes the fraction of ligand heavy atoms above the recommended density threshold; Clash counts receptor-clashing atom pairs.')
    return save(fig, 'results', notes, 'stage2-stage3-results')


def radar(ax, data, receptor, letter):
    """四轴均为身份准确率，不混入前景分类指标。"""
    categories=['overall','small','sugar','metal']; angles=np.arange(4)*np.pi/2
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
    for key,label,col,ls,marker in [('strongest','Strongest','#C0392B','-','o'),
              ('voxel','Voxel-only','#2980B9','--','s'),('density','Density-only','#27AE60','-.','^'),
              ('pocket','Pocket-only','#8E44AD',':','D')]:
        vals=[data['match']['ablation'][receptor][key][k]['accuracy_pct'] for k in categories]
        ax.plot(np.r_[angles,angles[0]],vals+vals[:1],color=col,ls=ls,marker=marker,ms=2.4,lw=1,label=label)
        if key=='strongest': ax.fill(np.r_[angles,angles[0]],vals+vals[:1],color=col,alpha=.07)
    ax.set_ylim(40,95); ax.set_yticks([40,60,80,95]); ax.set_yticklabels(['40%','60%','80%','95%'],fontsize=5.4,color='#666666')
    ax.set_xticks(angles,['Overall\nSMILES','Small\nmolecule','Sugar','Metal\nion'],fontsize=6)
    ax.tick_params(pad=2); ax.grid(color='#DDE3E6',lw=.5);ax.spines['polar'].set_color('#AAAAAA')
    title(ax,letter,f'Match ablation ({receptor})')


def boxes(ax, data, receptor, protocol, letter):
    """小提琴拟合全部有效值，箱体和精确百分位须独立从全分布计算。"""
    ax.set_box_aspect(1)
    for j, pose in enumerate(['top1','top5','best50']):
        for offset,model in [(-.25,'official'),(0,'nodensity'),(.25,'DG')]:
            values=data['ablation'][protocol][receptor][model][pose]
            arr=np.asarray([v for v in values if v is not None and np.isfinite(v)])
            pos=j+offset; col=C[model]
            kde=gaussian_kde(arr); y=np.linspace(0,10,220)
            density=kde(y); normalizer=np.max(kde(np.linspace(0,float(arr.max()),800)))
            width=density/normalizer*.115
            ax.fill_betweenx(y,pos-width,pos+width,color=col,alpha=.22,lw=0)
            p10,q1,med,q3,p85=np.quantile(arr,[.10,.25,.50,.75,.85])
            stat={'whislo':p10,'q1':q1,'med':med,'q3':q3,'whishi':p85,'fliers':[]}
            art=ax.bxp([stat],positions=[pos],widths=.15,patch_artist=True,showfliers=False,manage_ticks=False,
                       boxprops={'facecolor':col,'edgecolor':col,'alpha':.65,'linewidth':.6},
                       whiskerprops={'color':col,'linewidth':.7},capprops={'color':col,'linewidth':.7},
                       medianprops={'color':'white','linewidth':1.2})
            ax.text(pos,-.14,f'{med:.2f}',transform=ax.get_xaxis_transform(),ha='center',va='top',
                    fontsize=5.2,color=col,fontweight='bold',clip_on=False)
    ax.axhline(1,color='#777777',ls=':',lw=.65);ax.axhline(2,color='#333333',ls='--',lw=.7)
    ax.set_xlim(-.5,2.5);ax.set_ylim(0,10);ax.set_xticks(range(3),['Top-1','Top-5','Best of 50'])
    ax.set_yticks([0,2,4,6,8,10]);ax.set_ylabel('Ligand RMSD (Å)');grid(ax)
    ax.set_xlabel('Median RMSD (Å)',fontsize=5.5,labelpad=17)
    title(ax,letter,f'Build ablation ({receptor})')
    ax.legend(handles=[Patch(facecolor=C[m],alpha=.65,label=l) for m,l in
              [('official','PocketXMol-official'),('nodensity','PocketXMol–simple fine-tune'),('DG','DG-PocketXMol')]],
              loc='upper right',fontsize=5.4,borderpad=.3,handlelength=1.2,labelspacing=.35)


def ablation(data, envelope=False):
    """两种受体同一标准协议；Envelope采用相同箱线样式进入补充。"""
    fig=plt.figure(figsize=(WIDTH,3.2 if envelope else 6.1))
    gs=fig.add_gridspec(1 if envelope else 2,2,left=.10,right=.93,top=.91,bottom=.19 if envelope else .11,wspace=.31,hspace=.45)
    if not envelope:
        for col,(r,l) in enumerate([('GT','a'),('CA2','b')]):radar(fig.add_subplot(gs[0,col],projection='polar'),data,r,l)
        handles, labels=fig.axes[0].get_legend_handles_labels()
        fig.legend(handles,labels,ncol=4,loc='center',bbox_to_anchor=(.515,.515),fontsize=5.5,
                   frameon=False,columnspacing=1.0,handlelength=2)
    for col,(r,l) in enumerate([('GT','a' if envelope else 'c'),('CA2','b' if envelope else 'd')]):
        boxes(fig.add_subplot(gs[0 if envelope else 1,col]),data,r,'E' if envelope else 'C0',l)
    base=('Envelope口袋中的构象构建消融。a、b，GT与CA2受体条件。' if envelope else
          '身份匹配与密度引导构建的消融。a、b，沉积受体（GT）与CryoAtom2（CA2）条件下LigandSeek-Match四变体的身份准确率（分别1238、1160个身份支持blob）。c、d，GT与CA2条件下标准Centre口袋的三模型对照。')
    en=('Pose-construction ablation with Envelope pockets. a, b, Deposited (GT) and CryoAtom2 (CA2) receptors. ' if envelope else
        'Ablation of identity matching and density-guided pose construction. a, b, Identity accuracy of four LigandSeek-Match variants with deposited (GT) and CryoAtom2 (CA2) receptors (1,238 and 1,160 identity-supported blobs, respectively). c, d, Three-model comparison with standard Centre pockets and GT or CA2 receptors. ')
    zh=base+'Build使用完整446实例；原始模型GT有445个有效数值，其余各组446个。无密度微调模型新增核酸线性投影并共同微调整个网络。小提琴使用完整有效分布，箱体为第25–75百分位，白线为中位数，须为第10–85百分位，不绘离群散点。数字标注中位RMSD；参考线为1及2 Å。Top-5与best-of-50取原排序前5个及全部50个候选的最小RMSD。'
    en+='Build uses the complete 446-instance benchmark; PocketXMol-official has 445 finite GT values and all other groups have 446. Simple fine-tuning adds a nucleic-acid linear projection and jointly updates the network without density input. Violins use the complete finite distributions; boxes span the 25th–75th percentiles, white lines denote medians, and whiskers span the 10th–85th percentiles. Outlier points are omitted. Labels report median RMSD; reference lines mark 1 and 2 Å. Top-5 and best-of-50 take the minimum RMSD among the original top five and all 50 candidates.'
    return save(fig,'envelope' if envelope else 'ablation',zh+'\nENGLISH:\n'+en,
                'stage3-ablation-envelope' if envelope else 'stage2-stage3-ablation-centre')


def main():
    """构建目录只保存同次运行生成物，冻结输入只读。"""
    BUILD.mkdir(parents=True,exist_ok=True)
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    global scene_module
    scene_path=ROOT/'画图/画图代码/e2e/calculate/find-build-shared/svg_shapes.py'
    spec=importlib.util.spec_from_file_location('stage23_svg_scene',scene_path)
    scene_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(scene_module)
    pages=[main_results(data),ablation(data),ablation(data,True)]
    (BUILD/'scenes.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf-8')
    (BUILD/'manifest.json').write_text(json.dumps([{k:v for k,v in p.items() if k!='shapes'} for p in pages],ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
