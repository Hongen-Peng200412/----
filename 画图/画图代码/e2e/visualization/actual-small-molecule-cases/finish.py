"""向本次新 PPT 写传统图名批注, 双语图注, 并用 PowerPoint 原生导出 PNG/PDF."""

import argparse
import json
from pathlib import Path

import win32com.client


def main():
    """只打开本次 candidate.pptx, 不访问作者已有 PPT 或关闭作者窗口.

    CLI 参数 build-root 是当前构建目录, 必须含 candidate.pptx 和 presentation_data.json.
    presentation_data.json 的 id 是稳定图名, caption_zh/caption_en 是同一页的中英文图注.
    写回 candidate.pptx 的传统 @@图名批注和双语备注, 并写 powerpoint-preview.png、powerpoint-final.pdf 两份原生导出.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True)
    args = parser.parse_args()
    build = args.build_root.resolve()
    page = json.loads((build / 'presentation_data.json').read_text(encoding='utf-8'))
    app = win32com.client.DispatchEx('PowerPoint.Application')
    presentation = app.Presentations.Open(str(build / 'candidate.pptx'), False, False, False)
    try:
        slide = presentation.Slides(1)
        slide.Comments.Add(0, 0, 'Hongen Peng', 'HP', '@@' + page['id'])
        slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = page['caption_zh'] + '\nENGLISH:\n' + page['caption_en']
        presentation.Save()
        slide.Export(str(build / 'powerpoint-preview.png'), 'PNG', 2160, 2040)
        presentation.SaveAs(str(build / 'powerpoint-final.pdf'), 32)
    finally:
        presentation.Close()
    print('POWERPOINT_NATIVE_EXPORT_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
