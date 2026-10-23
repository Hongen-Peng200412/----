import path from 'node:path';
// 所有视觉操作均写成 ChimeraX 原生命令; 数据处理 Python 不修改相机或外观。
import fs from 'node:fs';
import { fileURLToPath as provenanceFilePath } from 'node:url';
import { existsSync as provenanceExists } from 'node:fs';

// 从脚本位置识别论文仓库, 不依赖目录层数或调用时的工作目录.
let repoRoot = path.dirname(provenanceFilePath(import.meta.url));
while (!(provenanceExists(path.join(repoRoot, 'AGENTS.md')) && provenanceExists(path.join(repoRoot, '论文草稿.md')))) {
  const parent = path.dirname(repoRoot);
  if (parent === repoRoot) throw new Error('找不到含 AGENTS.md 与论文草稿.md 的仓库根目录');
  repoRoot = parent;
}
process.env.RUNTIME_NODE_MODULES ??= 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';

const p=repoRoot.replaceAll(path.sep,'/'),code=p+'/画图/画图代码/stage1/visualization/stage1-fourcase-main/base',out=p+'/画图/画图代码/stage1/output/stage1-fourcase-main/base',temp=p+'/temp/stage1_chimera_v3';
fs.mkdirSync(temp,{recursive:true});
const old=p+'/画图/画图代码/stage1/output/stage1-fourcase-main/source_history';
const turns={'9pqm':[30,-20,0],'9wq3':[25,-20,0],'9uwi':[55,15,0],'9x0x':[30,-20,0],'9bjj':[35,-25,0],'9wup':[20,-25,0],'9rmi':[35,-20,90]};
const extras={'9uwi':['turn x 180'],'9x0x':['turn y 90','turn z 90'],'9wup':['turn y 90','turn x 150']};
const views=[['receptor_real','2'],['receptor_ca2','3'],['gt','4,8'],['find_real','1,2,4,5'],['find_ca2','1,3,4,6'],['emap','1,4,7']];
fs.writeFileSync(code+'/density_style.cxc',`# 灰色密度表面配合不透明蓝色预测网格，避免多层透明表面遮挡。
color #2,3 #94ad9f target c
transparency #2,3 70 target c
color #4,12 & C #c97b29
volume #1 style surface color #7c858b transparency 0.82 surfaceSmoothing false
volume #5-7,9-11 style mesh color #239fd0 transparency 0 meshLighting false squareMesh true
volume #8 style mesh color #8daeb8 transparency 0 meshLighting false squareMesh true
`);
for(const c of JSON.parse(fs.readFileSync(code+'/cases.json','utf8'))){
 const dest=out+'/'+c.pdb,data=JSON.parse(fs.readFileSync(dest+'/data.json','utf8'));const [y,x,z]=turns[c.pdb];
 const fw=c.pdb==='9pqm'?34:JSON.parse(fs.readFileSync(old+'/'+c.pdb+'/scene_checks.json','utf8')).contrast_find_real.field_width*(c.pdb==='9wup'?1:1.25);
 const prep=['hide #2,3 cartoons','cartoon (#2,3 & (#4 :< 12))',`volume #1 step 1 level ${data.contour}`,'volume zone #1 nearAtoms #4 range 5 newMap false minimalBounds true'];
 const local=['windowsize 960 720','show #4 models','view #4 orient',`turn y ${y}`,`turn x ${x}`,`turn z ${z}`,...(extras[c.pdb]??[]),'view #4',`zoom pixelSize ${fw/960}`,'zoom 0.85','clip off','view name local'];
 const overview=['windowsize 960 675','show #2 models','cartoon #2','view #2 orient','turn x -20','turn y 30',...(['9pqm','9uwi','9rmi'].includes(c.pdb)?['turn z 90']:[]),'view #2 pad 0.08',...(c.pdb==='9rmi'?['zoom 0.72']:[]),'clip off','view name overview'];
 fs.writeFileSync(code+'/'+c.pdb+'_local.cxc',[...prep,...local].join('\n')+'\n');
 let a=[`runscript "${code}/source_tools/utf8_log.py"`,`runscript "${code}/open_data.py" ${c.pdb}`,`open "${code}/common_style.cxc"`,...prep,...local,...overview];
 for(const style of ['baseline','contrast','density']){
  fs.mkdirSync(dest+'/'+style,{recursive:true});
  a.push(`open "${code}/common_style.cxc"`);if(style!=='baseline')a.push(`open "${code}/${style}_style.cxc"`);
  a.push('windowsize 960 675','hide models','show #1,2,9,12 models','cartoon #2','transparency #2 0 target c','volume unzone #1',`volume #1 region all step 1 style surface color #92949c level ${data.contour} transparency 0.65`,'volume #9 style surface transparency 0.6','view overview','wait 2',`save "${dest}/${style}/overview.png" width 1600 height 1125 supersample 2`,`runscript "${code}/source_tools/record_scene.py" "${dest}" ${style}_overview`,...prep,'windowsize 960 720');
  if(style==='baseline')a.push('volume #1 style surface color #c9c9d2 transparency 0.80','transparency #2,3 40 target c');
  else a.push(`open "${code}/${style}_style.cxc"`);
  for(const [name,ids] of views)a.push('hide models',`show #${ids} models`,'view local','wait 2',`save "${dest}/${style}/${name}.png" width 1440 height 1080 supersample 2`,`runscript "${code}/source_tools/record_scene.py" "${dest}" ${style}_${name}`);
 }
 a.push(`open "${code}/common_style.cxc"`,`open "${code}/contrast_style.cxc"`,...prep,'hide models','show #1,2,4,5 models','view local',`save "${dest}/session.cxs" includeMaps true`,'exit');
 fs.writeFileSync(temp+'/render_'+c.pdb+'.cxc',a.join('\n')+'\n');
 fs.writeFileSync(code+'/'+c.pdb+'_reproduce.cxc',a.filter(l=>!l.includes(temp)&&l!=='exit').join('\n')+'\n');
 fs.writeFileSync(code+'/'+c.pdb+'_six_views.cxc',views.map(([name,ids])=>`# ${name}\nhide models\nshow #${ids} models\nview local\n`).join('\n'));
}
