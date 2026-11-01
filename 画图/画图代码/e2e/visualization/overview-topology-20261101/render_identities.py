"""在 PyMOL 内以每个分子一种材质渲染三个三维身份图标.

FIGURE_BUILD_ROOT 中的 SDF 和 scene.json 来自本次 prepare.py; 输出透明 PNG 与可编辑 PSE.
保留作者的球棍、白底、光照风格, 全部元素使用该配体的身份色.
"""
import json
import os
from pathlib import Path

import pymol2
from PIL import Image

build = Path(os.environ['FIGURE_BUILD_ROOT'])
scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
with pymol2.PyMOL() as pm:
    cmd = pm.cmd
    for identity, width, turn in zip(scene['identities'], [763, 784, 826], [40, 24, 24]):
        cmd.reinitialize()
        cmd.bg_color('white')
        settings = dict(orthoscopic=1, ray_opaque_background=0, ray_shadows=0, specular=0.18,
                        shininess=40, ambient=0.50, direct=0.68, antialias=2, depth_cue=0,
                        ray_trace_fog=0, sphere_quality=3, stick_quality=16, valence=1,
                        valence_size=0.10, sphere_scale=0.25, stick_radius=0.21)
        for key, value in settings.items():
            cmd.set(key, value)
        name = identity['id']
        cmd.load(str(build / f'identity-{name}.sdf'), 'identity')
        cmd.set_color('identity_material', [int(identity['color'][i:i+2], 16)/255 for i in (1, 3, 5)])
        cmd.color('identity_material', 'identity')
        cmd.hide('everything')
        cmd.show('sticks', 'identity')
        cmd.show('spheres', 'identity')
        orient_selection = 'identity'
        if identity['rings'] == 1:
            orient_selection += ' and index ' + '+'.join(str(i + 1) for i in identity['ring_atoms'])
        cmd.orient(orient_selection)
        cmd.turn('x', 24)
        cmd.turn('y', -18)
        cmd.turn('z', turn)
        cmd.viewport(width, 620)
        cmd.zoom('identity', 0.7, complete=1)
        cmd.png(str(build / f'identity-{name}.png'), width, 620, dpi=300, ray=1)
        # 仅裁去透明空白并按作者图片框补透明边, 不改变分子像素或纵横比例.
        image = Image.open(build / f'identity-{name}.png').convert('RGBA')
        image = image.crop(image.getchannel('A').getbbox())
        frame_width = max(image.width, round(image.height * width / 620)) + 20
        frame_height = round(frame_width * 620 / width)
        frame = Image.new('RGBA', (frame_width, frame_height))
        frame.paste(image, ((frame_width-image.width)//2, (frame_height-image.height)//2))
        frame.save(build / f'identity-{name}.png', dpi=(300, 300))
        cmd.save(str(build / f'identity-{name}.pse'))
        colors = []
        cmd.iterate('identity', 'colors.append(color)', space={'colors': colors})
        assert len(set(colors)) == 1
        print(name, flush=True)
