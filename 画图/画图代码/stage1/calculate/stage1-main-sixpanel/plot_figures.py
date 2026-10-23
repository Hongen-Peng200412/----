"""按统一面板尺寸画六张单图和三行两列组合图, 不计算任何科学指标.

输入 formal/.../data/plot_data.json 已含均值、CI、中位数、四分位与 KDE.
本文件只负责坐标、配色、散点横向排布和图注装配. 常用参数见 plot_config.py.
各图输出 PDF/SVG/PNG; 临时 manifest 位于论文根 temp/.
"""
from pathlib import Path
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FormatStrFormatter
from plot_config import OUT, BUILD, VERSION, COLORS, LABELS, FONT, COMPOSITE_SIZE, SINGLE_SIZE, DPI, DOT_SIZE, DOT_ALPHA, BAR_ALPHA, COLORBAR_CMAP, COLORBAR_LIMITS

DATA_FILE = OUT/VERSION/'data/plot_data.json'
DATA = json.loads(DATA_FILE.read_text(encoding='utf-8'))
HIGH_METRIC = DATA.get('high_metric', 'oto06')  # v3 旧数据仍可按 τ=0.6 重现。
HIGH_TAU = '0.5' if HIGH_METRIC == 'oto05' else '0.6'
MODELS = ['GT','Cryo','Emap']
plt.rcParams.update({'font.family':'Arial','font.size':FONT['body'],'axes.labelsize':FONT['body'],
    'xtick.labelsize':FONT['tick'],'ytick.labelsize':FONT['tick'],'axes.linewidth':.65,
    'axes.spines.top':False,'axes.spines.right':False,'xtick.major.size':2.3,'ytick.major.size':2.3,
    'xtick.major.width':.55,'ytick.major.width':.55,'svg.fonttype':'none','pdf.fonttype':42,
    'savefig.facecolor':'white'})


def draw_panel(fig, kind, cohort, rect):
    """在指定矩形绘制一个面板, 参数 rect 为 Figure 坐标的左下宽高.

    同一个函数同时服务独立页与组合页. 这里只读科学输出; 水平抖动不改变值.
    """
    block=DATA['cohorts'][cohort]
    ax=fig.add_axes(rect)
    if kind=='bar':
        width=.23
        for j,m in enumerate(MODELS):
            for k,metric in enumerate(['dice','oto03',HIGH_METRIC]):
                x=k+(j-1)*width;c=COLORS[m]
                stats=block['models'][m]['bars'][metric];v=block['models'][m]['values'][metric]
                # 图形随机种子仅决定水平方向避让, 不参与统计或置信区间.
                jitter=np.random.default_rng(710+j*13+k).uniform(-width*.35,width*.35,len(v))
                ax.bar(x,stats['mean'],width*.88,color=c,alpha=BAR_ALPHA,edgecolor=c,lw=.65,zorder=1)
                ax.scatter(x+jitter,v,s=DOT_SIZE['bar'],color=c,alpha=DOT_ALPHA,linewidths=0,zorder=2,clip_on=False)
                ax.vlines(x,stats['lower'],stats['upper'],color=c,lw=.9,zorder=4)
                ax.hlines([stats['lower'],stats['upper']],x-.055,x+.055,color=c,lw=.9,zorder=4)
                ax.hlines(stats['mean'],x-.086,x+.086,color=c,lw=1.5,zorder=5)
        ax.set(xlim=(-.48,2.48),ylim=(0,1.035),yticks=[0,.5,1],ylabel='Score',xticks=[0,1,2],
               xticklabels=['Semantic\nDice','One-to-one\nPRAUC, τ = 0.3',f'One-to-one\nPRAUC, τ = {HIGH_TAU}'])
        ax.tick_params(axis='x',length=0,pad=5)
        ax.grid(axis='y',color='#E7EBED',lw=.45);ax.set_axisbelow(True)
    elif kind=='paired':
        x=block['models']['Emap']['values']['oto03'];y=block['models']['Cryo']['values']['oto03']
        ax.plot([0,1],[0,1],ls=(0,(3,3)),c='#939CA2',lw=.65,zorder=0)
        p=ax.scatter(x,y,c=block['resolution'],cmap=COLORBAR_CMAP,vmin=COLORBAR_LIMITS[0],vmax=COLORBAR_LIMITS[1],
            s=DOT_SIZE['paired'],alpha=.80,linewidths=.25,edgecolors='white',clip_on=False)
        ax.set(xlim=(0,1),ylim=(0,1),xticks=[0,.5,1],yticks=[0,.5,1],aspect='equal',
               xlabel='Emap2lig-Find',ylabel='Ligandseek-Find (CryoAtom2)')
        # 独立色条轴不会改变散点坐标轴的宽高比. 不透明色条避免矢量拼接横纹.
        left,bottom,width,height=ax.get_position().bounds
        cax=fig.add_axes([left+width+.020,bottom,.012,height])
        cb=fig.colorbar(p,cax=cax,ticks=[1,2,3,4])
        cb.ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        cb.set_label('Resolution (Å)',labelpad=3)
        cb.outline.set_visible(False);cb.solids.set_rasterized(False);cb.solids.set_alpha(1)
        cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.2)
    elif kind=='violin':
        for k,metric in enumerate(['precision','recall']):
            for j,m in enumerate(MODELS):
                center=k*4.1+j;c=COLORS[m];stats=block['models'][m]['distribution'][metric]
                y=np.array(stats['grid']);width=np.array(stats['density'])*.40
                ax.fill_betweenx(y,center-width,center+width,facecolor=c,alpha=.16,edgecolor=c,lw=.65)
                v=block['models'][m]['values'][metric]
                jitter=np.random.default_rng(970+j*13+k).uniform(-.26,.26,len(v))
                ax.scatter(center+jitter,v,s=DOT_SIZE['violin'],color=c,alpha=.43,linewidths=0,clip_on=False)
                q1,median,q3=stats['quartiles']
                ax.vlines(center,q1,q3,color=c,lw=1.7,zorder=4)
                ax.scatter([center],[median],s=13,facecolor='white',edgecolor=c,lw=.8,zorder=5,clip_on=False)
        ax.set(xlim=(-.65,6.75),ylim=(-.025,1.03),yticks=[0,.5,1],ylabel='Score',xticks=[1,5.1],xticklabels=['Precision','Recall'])
        ax.tick_params(axis='x',length=0,pad=5)
        ax.grid(axis='y',color='#E7EBED',lw=.45);ax.set_axisbelow(True)
    return ax


if __name__=='__main__':
    dest=Path(os.environ['FIGURE_RENDER_ROOT']) if 'FIGURE_RENDER_ROOT' in os.environ else OUT/'regenerated'/VERSION;dest.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    handles=[Patch(facecolor=COLORS[m],edgecolor='none',label=LABELS[m]) for m in MODELS]
    captions={};manifest=[]
    shared='Ligandseek-Find 均使用冻结的 F2–F1 Gaussian 流程，Emap2lig-Find 使用官方 Find/Li 流程。'
    for row,kind in enumerate(['bar','paired','violin']):
        for col,cohort in enumerate(['full','small']):
            letter='abcdef'[row*2+col];block=DATA['cohorts'][cohort]
            name='全配体' if cohort=='full' else '小分子-only'
            detail={'bar':f'Dice、one-to-one PRAUC@0.3 和 PRAUC@{HIGH_TAU}；柱高为 PDB 等权均值，点为逐 PDB 结果，误差线为 10,000 次 PDB bootstrap 的均值 95% 区间。',
                    'paired':'横轴为 Emap2lig-Find，纵轴为使用 CryoAtom2 受体的 Ligandseek-Find，虚线为等值线，点颜色为实验地图分辨率。',
                    'violin':'仅展示 one-to-one@0.3 Precision/Recall。点为逐 PDB 结果，白点为中位数，粗线为四分位范围。'}[kind]
            if kind=='paired':
                c=block['paired_counts'];detail+=f"Ligandseek-Find 较高、相等、Emap2lig-Find 较高分别为 {c['find_higher']}、{c['equal']}、{c['emap_higher']} 个 PDB。"
            caption=f'{name}，test_0，n={block["n"]} 个 PDB。'+detail+shared
            if cohort=='small':caption+='仅保留含小分子真实实例的 94 个 PDB；按固定归属规则忽略匹配非小分子的候选，未归属候选保留。'
            captions[letter]=caption
            fig=plt.figure(figsize=SINGLE_SIZE)
            # 三类单图分别控制留白, 不复用旧 PPT 大画布上的窄图形比例.
            rect={'bar':[.16,.29,.80,.48],'paired':[.18,.20,.60,.62],'violin':[.16,.26,.80,.50]}[kind]
            draw_panel(fig,kind,cohort,rect)
            heading={'bar':'Overall scores','paired':'One-to-one PRAUC · τ = 0.3','violin':'One-to-one detection · τ = 0.3'}[kind]
            fig.text(.16,.95,heading,fontsize=FONT['panel'],weight='bold',va='top')
            fig.text(.16,.865,'All ligands' if cohort=='full' else 'Small molecules only',fontsize=FONT['metric'])
            if kind!='paired':
                fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.54,.01),ncol=1,frameon=False,fontsize=6.5,
                           handlelength=.9,handletextpad=.4,labelspacing=.25)
            stem=f'{letter}_{cohort}_{kind}'
            for ext in ['svg','pdf','png']:fig.savefig(dest/f'{stem}.{ext}',dpi=DPI)
            manifest.append({'stem':stem,'name':'stage1-'+stem.replace('_','-'),'notes':caption,
                             'width':fig.get_figwidth()*72,'height':fig.get_figheight()*72})
            plt.close(fig)
    fig=plt.figure(figsize=COMPOSITE_SIZE)
    # 组合图统一两列边界; 小提琴的 P/R 直接在同一轴分组, 避免四个小轴间的大空白.
    xs=[.095,.565]
    for col,cohort in enumerate(['full','small']):
        fig.text(xs[col]+.192,.987,'All ligands' if cohort=='full' else 'Small molecules',
                 ha='center',va='top',fontsize=FONT['column'],weight='bold')
        for row,kind in enumerate(['bar','paired','violin']):
            rect={'bar':[xs[col],.710,.405,.177], 'paired':[xs[col]+.010,.337,.280,.256],
                  'violin':[xs[col],.060,.405,.154]}[kind]
            draw_panel(fig,kind,cohort,rect)
            top={'bar':.901,'paired':.619,'violin':.241}[kind]
            fig.text(xs[col]-.052,top,'abcdef'[row*2+col],weight='bold',fontsize=11,va='bottom')
            title={'bar':'Overall scores','paired':'One-to-one PRAUC · τ = 0.3','violin':'One-to-one detection · τ = 0.3'}[kind]
            fig.text(xs[col],top,title,fontsize=FONT['metric'],va='bottom')
    # 组合图图例的文字与横向锚点对齐已保存图集第 19 页, 单图仍使用原有图例。
    composite_labels=['Ligandseek-Find(deposited receptor)','Ligandseek-Find(CryoAtom2 receptor)','Emap2lig-Find']
    composite_handles=[Patch(facecolor=COLORS[m],edgecolor='none',label=label)
                       for m,label in zip(MODELS,composite_labels)]
    for handle, x in zip(composite_handles, [.1293, .4319, .7432]):
        fig.legend(handles=[handle],loc='upper left',bbox_to_anchor=(x,.953),frameon=False,
                   fontsize=FONT['legend'],handlelength=1.0,handletextpad=.45)
    caption=('图 2｜Stage1 配体区域检测。左列：全配体（179 PDB）；右列：小分子-only（94 PDB，821 实例）。'
      f'a、b，Dice、one-to-one PRAUC@0.3 和 PRAUC@{HIGH_TAU}；柱高为 macro 均值，误差线为 10,000 次 PDB bootstrap 的均值 95% 区间。'
      'c、d，one-to-one PRAUC@0.3 配对比较；Ligandseek-Find 较高/相等/Emap2lig-Find 较高为 112/40/27 和 40/36/18。'
      'e、f，同阈值 Precision/Recall；白点和粗线为中位数与四分位范围。各点代表一个 PDB。'
      'Ligandseek-Find 使用 F2–F1 Gaussian。小分子评估排除无小分子 GT 的 PDB，忽略固定归属非小分子的候选，未归属候选仍保留。'
      '两列的评价范围不同，均值差不表示性能变化。')
    for ext in ['svg','pdf','png']:fig.savefig(dest/f'Stage1_sixpanel.{ext}',dpi=DPI)
    manifest.append({'stem':'Stage1_sixpanel','name':'stage1-main-sixpanel','notes':caption,
                     'width':fig.get_figwidth()*72,'height':fig.get_figheight()*72})
    plt.close(fig)
    (BUILD/f'manifest_{VERSION}.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated six independent panels and one composite:',dest)
