"""复用原病例对象并通过PowerPoint渲染最终原生PPT候选。"""

import importlib.util
import json
import os
import time
from pathlib import Path

import win32com.client

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').is_file())
BUILD=Path(os.environ['FIGURE_BUILD_ROOT'])


def main():
    """仅打开本次候选，不关闭作者当前窗口或修改原病例PPT。"""
    helper=ROOT/'画图/画图代码/e2e/visualization/stage2-stage3-results/case_reuse.py'
    spec=importlib.util.spec_from_file_location('case_reuse',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    pptx=BUILD/'candidate.pptx'
    rects=json.loads((BUILD/'case_rects.json').read_text(encoding='utf-8'))
    report=module.inject_case_views(pptx,rects,legend_rect_pt=[29,461,333,9],scale_rect_pt=[393,459,42,12])
    (BUILD/'case_reuse_receipt.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    preview=BUILD/'ppt_preview';preview.mkdir(exist_ok=True)
    for attempt in range(3):
        pres=None
        try:
            app=win32com.client.DispatchEx('PowerPoint.Application')
            pres=app.Presentations.Open(str(pptx),False,False,False)
            for number in range(1,pres.Slides.Count+1):
                pres.Slides(number).Export(str(preview/f'slide-{number:02d}.png'),'PNG',2000,2090)
            pres.Save()
            pres.SaveAs(str(BUILD/'candidate.pdf'),32)
            break
        except Exception:
            if attempt==2:raise
            time.sleep(2)
        finally:
            if pres is not None:
                try:pres.Close()
                except Exception:pass
    print('PowerPoint原生渲染完成',pptx)


if __name__=='__main__':main()
