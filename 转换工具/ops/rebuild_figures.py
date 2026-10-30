"""从冻结输入完整重建指定论文图；每次运行均屏蔽其他temp内容。

入口main读取八份追溯记录，按图调用既有计算、渲染和装配程序。
产物为独立构建目录内的图片、candidate.pptx、命令日志和receipt.json。
正式PPT仅提供作者图注，不作为实验图片缓存；本程序不发布到正式图集。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from lxml import etree as XML

from figure_provenance import Deck, comment_text, load_records, relationship_target, set_comment_text, xml_bytes

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "画图/画图代码"
SUPPORT = Path(__file__).parent / "rebuild_support"
NODE = Path(os.environ.get("FIGURE_NODE", str(Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")))
PYMOL = Path(os.environ.get("FIGURE_PYMOL_PYTHON", "D:/Pymol/python.exe"))


def run_step(command, build: Path, environment: dict, steps: list) -> None:
    """反复运行显式前置步骤，命令、退出码和控制台保存在本次目录。"""
    log = build / f"step-{len(steps)+1:02d}.log"
    print("  " + subprocess.list2cmdline([str(value) for value in command]), flush=True)
    with log.open("w", encoding="utf-8") as handle:
        result = subprocess.run([str(value) for value in command], cwd=ROOT, env=environment, stdout=handle, stderr=subprocess.STDOUT)
    steps.append({"command": [str(value) for value in command], "exit_code": result.returncode, "log": log.name})
    native_report=build/'native-completion.json'
    if str(command[0]).lower().endswith('powershell.exe') and native_report.exists():
        report=json.loads(native_report.read_text(encoding='utf-8'))
        if not report['passed']:raise RuntimeError(f"原生渲染失败: {report.get('error')}，详见 {build/'chimerax.html'}")
    if result.returncode:
        raise RuntimeError(f"重建步骤失败，见 {log}\n{log.read_text(encoding='utf-8',errors='replace')[-2200:]}")


def native_commands(figure: str, build: Path) -> list[list]:
    """从长期CXC重建原生三维图片，只重定向保存路径和现场相机记录。"""
    scripts = []
    asset_root = build / "display"
    native_root = build / "native"
    if figure == "stage1-fourcase-main":
        source = CODE / "stage1/visualization/stage1-fourcase-main"
        frozen = CODE / "stage1/output/stage1-fourcase-main"
        for pdb in ("9pqm", "9uwi", "9wup", "9rmi"):
            destination = asset_root / pdb
            for palette in ("baseline", "contrast", "density"):
                (destination/palette).mkdir(parents=True,exist_ok=True)
            config = json.loads((frozen/f"display/{pdb}/data.json").read_text(encoding="utf-8"))
            lines = ["close all"] + [f'open "{(frozen/f"base/{pdb}/assets"/name).as_posix()}"' for name in config["files"]]
            for line in (source/f"{pdb}_reproduce.cxc").read_text(encoding="utf-8").splitlines()[1:]:
                if line.startswith(("save ","log save ")):
                    match = re.search(r'"([^"]+)"',line)
                    old = Path(match[1]); parts=old.as_posix().split(f"/regenerated/{pdb}/",1)
                    if len(parts)!=2:raise ValueError(f"未识别的原生保存路径: {old}")
                    line=line.replace(match[1],(destination/parts[1]).as_posix())
                lines.append(line)
                if line.startswith("save ") and "/overview.png\"" in line:
                    palette=Path(re.search(r'"([^"]+)"',line)[1]).parent.name
                    lines.append(f'runscript "{(source/"source_tools/record_scene.py").as_posix()}" "{destination.as_posix()}" {palette}_overview')
            script=build/f"native-{pdb}.cxc";script.write_text("\n".join(lines)+"\n",encoding="utf-8");scripts.append(script)
    elif figure.startswith("e2e-flow-"):
        pdb=figure.removeprefix("e2e-flow-")
        source=CODE/"e2e/visualization/e2e-flow-shared"
        frozen=CODE/"e2e/output/e2e-flow"
        for destination in (native_root/pdb,asset_root/pdb):
            (destination/"renders").mkdir(parents=True,exist_ok=True)
        for name in ("projection_boxes_manifest.json",):
            shutil.copy2(frozen/"display"/name,asset_root/name)
        for filename,destination in [(f"base/{pdb}_reproduce.cxc",native_root/pdb),(f"{pdb}_global_find.cxc",asset_root/pdb),(f"{pdb}_global_density_same_scale.cxc",asset_root/pdb)]:
            lines=[]
            for line in (source/filename).read_text(encoding="utf-8").splitlines():
                if line.startswith("open ") and f"/views/{pdb}/global_session.cxs" in line:
                    line=f'open "{(native_root/pdb/"global_session.cxs").as_posix()}"'
                if line.startswith(("save ","log save ")):
                    match=re.search(r'"([^"]+)"',line);old=match[1]
                    tail=old.split(f"/regenerated/{pdb}/",1)[-1]
                    if tail==old:raise ValueError(f"未识别的原生保存路径: {old}")
                    line=line.replace(old,(destination/tail).as_posix())
                lines.append(line)
            script=build/(Path(filename).stem+".cxc");script.write_text("\n".join(lines)+"\n",encoding="utf-8");scripts.append(script)
    elif figure == "fig-overview_v2":
        source=CODE/"e2e/visualization/fig-overview_v2"
        lines=[f'open "{(source/"view_density.cxc").as_posix()}"',f'runscript "{(source/"export_geometry.py").as_posix()}"',f'runscript "{(source/"blob_geometry.py").as_posix()}"']
        script=build/"overview.cxc";script.write_text("\n".join(lines)+"\n",encoding="utf-8");scripts.append(script)
    master=build/"render.py"
    master.write_text('from pathlib import Path\nimport json,traceback,runpy\nrunpy.run_path('+repr(str(SUPPORT/'sitecustomize.py'))+')\nfrom chimerax.core.commands import run\n'+
        'report={"passed":False}\ntry:\n'+''.join('    run(session, '+repr(f'open "{p.as_posix()}"')+')\n' for p in scripts)+
        '    report["passed"]=True\nexcept Exception:\n    report["error"]=traceback.format_exc()\nfinally:\n'+
        '    run(session, '+repr(f'log save "{(build/"chimerax.html").as_posix()}"')+')\n'+
        '    Path('+repr(str(build/'native-completion.json'))+').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")\n',encoding="utf-8")
    return [["powershell.exe","-NoProfile","-File",SUPPORT/"run_chimerax.ps1","-CxcPath",master,"-LogPrefix",build/"chimerax"]]


def commands_for(figure: str, build: Path) -> list[list]:
    """按稳定图名装配既有完整步骤；同组算法保持共享，临时文件统一由环境定位。"""
    # 后缀只区分保留的无 level 图; 科学条件由 main 显式绑定, 同一模板无需复制.
    figure = figure.removesuffix("-NO_LEVEL")
    python = [sys.executable,"-X","utf8","-B"]
    node = [NODE]
    p=lambda relative,*args:python+[CODE/relative,*args]
    n=lambda relative,*args:node+[CODE/relative,*args]
    if figure.startswith('fig-method-build-'):
        prefix='e2e/visualization/method-build-variants/'
        return [[PYMOL,'-B',CODE/(prefix+'render_native.py')],n(prefix+'build_deck.mjs'),['powershell.exe','-NoProfile','-File',CODE/(prefix+'render_slides.ps1'),'-BuildRoot',build],p(prefix+'audit.py'),n(prefix+'finalize.mjs')]
    if figure in ('fig-method-ab-a1','fig-method-ab-a4','fig-method-ab-a5'):
        prefix='e2e/visualization/method-ab-variants/'
        selected=json.loads((CODE/'e2e/output/method-ab-variants/source/selected-layout.json').read_text(encoding='utf-8-sig'))
        return [n(prefix+'sync_selected.mjs'),['powershell.exe','-NoProfile','-File',CODE/(prefix+'render_native.ps1'),'-BuildRoot',build,'-AuthorSource',ROOT/selected['pptx']],p(prefix+'audit_selected.py'),n(prefix+'finalize.mjs','selected')]
    if figure.startswith('fig-method-ab-a'):
        prefix='e2e/visualization/method-ab-variants/'
        return [n(prefix+'build_variants.mjs'),['powershell.exe','-NoProfile','-File',CODE/(prefix+'render_native.ps1'),'-BuildRoot',build],p(prefix+'audit.py'),n(prefix+'finalize.mjs')]
    if figure.startswith('fig-overview-v4-'):
        prefix='e2e/visualization/overview-redesign-20261028/'
        native_script=CODE/(prefix+'render_chimerax.py')
        return [p(prefix+'prepare_scene.py'),[PYMOL,'-B',CODE/(prefix+'render_native.py')],['powershell.exe','-NoProfile','-File',SUPPORT/'run_chimerax.ps1','-CxcPath',native_script,'-LogPrefix',build/'chimerax'],['powershell.exe','-NoProfile','-File',SUPPORT/'run_chimerax.ps1','-CxcPath',CODE/(prefix+'render_transparent.py'),'-LogPrefix',build/'transparent'],p(prefix+'assemble.py'),p(prefix+'package_delivery.py')]
    if figure.startswith('fig-overview_v3') or figure.startswith('fig-method-v9'):
        prefix='e2e/visualization/fig12-revision/'
        return [p(prefix+'prepare_geometry.py'),[PYMOL,'-B',CODE/(prefix+'render_structures.py')],n(prefix+'build_components.mjs'),p(prefix+'assemble.py')]
    if figure in ('stage1-additional-analysis', 'stage1-no-level-comparison'):
        # 两页共享独立补充目录的统计与布局, 图元及原生装配仍复用原 Stage1 实现.
        return [p('stage1/calculate/stage1-additional-analysis/prepare_data.py'), p('stage1/calculate/stage1-additional-analysis/plot.py'), n('stage1/calculate/stage1-results-revision/build_deck.mjs')]
    if figure in ("stage1-overall-performance", "stage1-candidate-quality", "stage1-strict-threshold", "stage1-completion-curves"):
        prefix="stage1/calculate/stage1-results-revision/"
        return [p(prefix+"plot.py"),n(prefix+"build_deck.mjs")]
    if figure.startswith("stage1-level-global-local-"):
        # 同一完整链重建五个原生案例及候选PPT; 科学输入来自独立 level 冻结目录. 
        return [["powershell.exe","-NoProfile","-File",CODE/"stage1/visualization/stage1-level-global-local/rebuild.ps1","-OutputDirectory",build/"native-cases"]]
    if figure.startswith("supp-e2e-completion-"):
        return [p(f"e2e/calculate/{figure}/plot.py"),p("e2e/calculate/e2e-instance-completion/svg_shapes.py"),n("e2e/calculate/e2e-instance-completion/assemble.mjs")]
    if figure in ("find-only-instance-completion","stage3-predicted-region-head-to-head","supp-find-correct-match-build"):
        stage={"find-only-instance-completion":"stage1","stage3-predicted-region-head-to-head":"stage3","supp-find-correct-match-build":"e2e"}[figure]
        return [p(f"{stage}/calculate/{figure}/plot.py"),p("e2e/calculate/find-build-shared/svg_shapes.py","--build-root",build),n("e2e/calculate/find-build-shared/assemble.mjs",build)]
    if figure == "stage1-main-sixpanel":
        prefix="stage1/calculate/stage1-main-sixpanel/"
        return [p(prefix+"plot_figures.py"),p(prefix+"svg_to_scene.py"),n(prefix+"build_deck.mjs"),n(prefix+"finalize.mjs")]
    if figure == "ligandseek2-vs-ligandseek1":
        prefix="stage1/calculate/ligandseek2-vs-ligandseek1/"
        return [p(prefix+"plot_figures.py","--plot-data",CODE/"stage1/output/ligandseek2-vs-ligandseek1/data/statistics/plot_data.json","--output-root",build/"figures","--build-root",build,"--nature-scripts",Path.home()/".codex/skills/nature-figure/scripts"),n(prefix+"build_deck.mjs",build/"manifest.json",build)]
    if figure in ("stage2-radar-pair","stage2-strongest-pair"):
        return [p(f"stage2/calculate/{figure}/ops/render.py","--output",build/"render"),n("stage2/calculate/stage2-results-shared/build_editable_deck.mjs","--output",build/"ppt")]
    if figure == "stage3-official-tuned":
        return [p("stage3/calculate/stage3-official-tuned/plot_stage3.py"),n("stage3/calculate/stage3-official-tuned/build_editable_deck.mjs")]
    if figure in ("e2e-all-find-match","e2e-small-pipeline"):
        return [p(f"e2e/calculate/{figure}/build.py")]
    if figure == "e2e-find-build-direct-comparison":
        return [p("e2e/calculate/e2e-find-build-direct-comparison/plot_find_build_direct.py"),n("e2e/calculate/e2e-find-build-direct-comparison/assemble.mjs")]
    if figure == "e2e-accounting-rules-draft":
        return [p("e2e/calculate/e2e-accounting/build_ppt.py","--rules-only")]
    if figure in ("stage3-cases-main", "stage3-cases-density", "stage3-cases-clash"):
        prefix="stage3/visualization/stage3-cases-main/"
        return [p(prefix+"measure_cases.py"),p(prefix+"make_geometry.py"),p(prefix+"render_figure.py"),n(prefix+"build_deck.mjs")]
    if figure in ("stage1-fourcase-main", "stage1-threecase-main"):
        return native_commands("stage1-fourcase-main",build)+[n("stage1/visualization/stage1-fourcase-main/build_deck.mjs")]
    if figure.startswith("e2e-flow-"):
        frozen=CODE/"e2e/output/e2e-flow"
        return native_commands(figure,build)+[p("e2e/visualization/e2e-flow-shared/draw_identities.py","--source-root",frozen/"source","--output-root",build/"display"),n(f"e2e/visualization/{figure}/build_deck.mjs")]
    if figure == "fig-overview_v2":
        return native_commands(figure,build)+[n("e2e/visualization/fig-overview_v2/build_figure.mjs"),p("e2e/visualization/fig-overview_v2/group_objects.py"),n("e2e/visualization/fig-overview_v2/finalize.mjs")]
    if figure == "fig-method-v8":
        prefix="e2e/visualization/fig-method-v8/"
        return [[PYMOL,"-B",CODE/(prefix+"ops/"+name)] for name in ("render_receptor.py","render_density.py","render_build_pose.py")]+[p(prefix+"assemble.py")]
    if figure == 'multiligand-workbench' or figure.startswith('multiligand-workbench-'):
        return [p('e2e/visualization/multiligand-workbench/ops/rebuild.py','--figure',figure,'--build-root',build)]
    raise ValueError(f"图名未登记重建步骤: {figure}")


def finish_candidate(figure: str, build: Path, records: list, generated_captions: bool=False) -> dict:
    """选择本次候选，补入作者双语备注与完整来源；原正式PPT始终只读。"""
    record=next(record for record in records if record.metadata.get("figure")==figure)
    candidates=[]
    for path in build.rglob("*.pptx"):
        if path.name=='rebuilt.pptx' or any(word in path.parts for word in ("backups","rendered")):continue
        try:
            deck=Deck(path)
            if figure.endswith('-NO_LEVEL') and figure not in deck.figures:
                # 为本次旧条件候选的全部页面补后缀, 避免未登记辅助页误接新条件备注; 不改图形.
                for original_name in list(deck.figures):
                    if original_name.endswith('-NO_LEVEL'):
                        continue
                    qualified_name = original_name + '-NO_LEVEL'
                    page = deck.figures.pop(original_name)
                    for part in page.comments:
                        for comment in deck.comments(part):
                            if comment_text(comment).strip() == '@@' + original_name:
                                set_comment_text(comment, '@@' + qualified_name)
                                deck.changed.add(part)
                    page.names = [qualified_name]
                    deck.figures[qualified_name] = page
            if figure in deck.figures:candidates.append((path,deck))
        except (ValueError,KeyError):
            continue
    if not candidates:raise ValueError(f"本次未生成含@@{figure}的PPT: {build}")
    path,deck=next((item for item in candidates if item[0].name=="candidate.pptx"),candidates[0])
    notes_type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
    annotated=[];caption_preserved=False
    for page_record in records:
        name=page_record.metadata.get('figure')
        if page_record.metadata['kind']!='figure' or name not in deck.figures:continue
        current=Deck(ROOT/page_record.metadata['pptx'])
        slide=deck.figures[name];author_slide=current.figures.get(name)
        for owner,page in ((deck,slide),(current,author_slide)):
            if page is None:
                source_note=None
                continue
            rel=page.part.rsplit('/',1)[0]+'/_rels/'+page.part.rsplit('/',1)[1]+'.rels'
            note=next((relationship_target(page.part,x.get('Target')) for x in owner.tree(rel) if x.get('Type')==notes_type),None)
            if owner is deck:target_note=note
            else:source_note=note
        if target_note and source_note and not generated_captions:
            ns={"p":"http://schemas.openxmlformats.org/presentationml/2006/main","a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
            source_body=current.tree(source_note).xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)
            target_body=deck.tree(target_note).xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)
            if source_body and target_body:
                import copy
                target_body[0].getparent().replace(target_body[0],copy.deepcopy(source_body[0]));deck.changed.add(target_note)
                if name==figure:caption_preserved=True
        owned=deck.managed().get(page_record.identifier,[])
        if owned:
            _,part,comment=owned[0];set_comment_text(comment,page_record.comment);deck.changed.add(part)
        else:deck.append(slide,page_record.comment)
        annotated.append(name)
    target=build/'rebuilt.pptx'
    with ZipFile(path) as source,ZipFile(target,'w') as output:
        for info in source.infolist():output.writestr(info,xml_bytes(deck.trees[info.filename]) if info.filename in deck.changed else source.read(info.filename))
    reread=Deck(target)
    assert figure in reread.figures and reread.managed()[record.identifier]
    image_files=[str(p.relative_to(build)) for p in build.rglob('*') if p.suffix.lower() in ('.png','.svg','.pdf')]
    if not image_files:raise ValueError(f"没有本次生成的图稿: {figure}")
    return {"candidate":"rebuilt.pptx","figure":figure,"image_files":image_files,"slide_count":len(reread.slides),"source_comment_synced":True,"annotated_figures":annotated,"author_caption_preserved":caption_preserved,"generated_captions_requested":generated_captions}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--figure',action='append',help='稳定图名，可重复指定')
    group.add_argument('--all',action='store_true',help='重建四稿当前引用的全部图')
    parser.add_argument('--build-root',type=Path,help='新的仓库temp子目录；已有非空单图目录不复用')
    parser.add_argument('--generated-captions',action='store_true',help='本轮明确修订图注时保留新生成图注；默认沿用已有作者图注')
    args=parser.parse_args();errors=[];records=load_records(ROOT,errors)
    if errors:raise ValueError('\n'.join(errors))
    names=[r.metadata['figure'] for r in records if r.metadata['kind']=='figure']
    selected=names if args.all else args.figure
    if set(selected)-set(names):raise ValueError(f'未知图名: {set(selected)-set(names)}')
    base=(args.build_root or ROOT/'temp/figure_rebuild'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')).resolve()
    if not base.is_relative_to(ROOT/'temp'):raise ValueError('构建目录必须位于仓库temp内')
    base.mkdir(parents=True,exist_ok=True);results=[]
    for figure in selected:
        build=base/figure
        if build.exists() and any(build.iterdir()):raise FileExistsError(f'不复用已有构建: {build}')
        build.mkdir(parents=True,exist_ok=True);(build/'render').mkdir()
        environment=dict(os.environ)
        environment.update(FIGURE_ID=figure,FIGURE_VERIFY_ROOT=str(ROOT),FIGURE_BUILD_ROOT=str(build),FIGURE_RENDER_ROOT=str(build/'render'),FIGURE_ASSET_ROOT=str(build/'display'),FIGURE_NATIVE_ROOT=str(build/'native'),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
        environment['PYTHONPATH']=os.pathsep.join(str(p) for p in (SUPPORT,ROOT/'.manuscript_deps/figure_runtime',ROOT))
        environment['NODE_OPTIONS']='--require='+str(SUPPORT/'node_guard.cjs')
        environment['MPLCONFIGDIR']=str(build/'matplotlib')
        environment['STAGE1_FIGURE_VERSION']='v5'
        record = next(item for item in records if item.metadata.get('figure') == figure)
        # 追溯 inputs 明确绑定科学条件; 不能按同名 data.json 或全局默认值猜测使用哪次实验.
        explicit_level = any('explicit_emdb_level' in path for path in record.metadata.get('inputs', []))
        environment['EMAP2LIG_CONDITION'] = 'explicit_emdb_level' if explicit_level else 'no_level'
        if explicit_level:
            # 新共享统计只服务 level 条件的公平对接/完成度; 原无 level JSON 永久保留原位.
            level_root = CODE / 'e2e/output/find-build-shared/explicit_emdb_level'
            environment['FIND_BUILD_DATA'] = str(level_root / 'data.json')
            environment['E2E_TOPK_DATA'] = str(level_root / 'topk_data.json')
            # 新病例资产保持原 GT-C0 输入和科学定义, 只替换相应条件的 Emap2lig Top-1.
            environment['FIGURE_SOURCE_ROOT'] = str(CODE / 'stage3/output/stage3-cases-main/explicit_emdb_level')
        else:
            for name in ('FIND_BUILD_DATA', 'E2E_TOPK_DATA', 'FIGURE_SOURCE_ROOT'):
                environment.pop(name, None)
        steps=[];receipt={'figure':figure,'build':str(build),'old_temp_blocked':True,'steps':steps,'passed':False}
        print(f'重建 {figure}',flush=True)
        try:
            for command in commands_for(figure,build):run_step(command,build,environment,steps)
            receipt.update(finish_candidate(figure,build,records,args.generated_captions));receipt['passed']=True
        except Exception as error:
            receipt['error']=str(error);raise
        finally:
            (build/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
            results.append(receipt);(base/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'通过 {figure}: {build/"rebuilt.pptx"}',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
