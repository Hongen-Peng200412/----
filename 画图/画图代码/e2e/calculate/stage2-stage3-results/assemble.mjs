// 将Python后端的同源几何逐个运输为原生PPT对象，不在此计算科学统计。
import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation,PresentationFile} from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const build=process.env.FIGURE_BUILD_ROOT;
if(!build) throw new Error('必须显式提供FIGURE_BUILD_ROOT');
const pages=JSON.parse(await fs.readFile(path.join(build,'scenes.json'),'utf8'));
const scale=4/3;
const pres=Presentation.create({slideSize:{width:pages[0].width*scale,height:pages[0].height*scale}});
pres.comments.setSelf({displayName:'Hongen Peng',initials:'HP',userId:'hongen-peng',providerId:'None'});
const color=(v,a)=>v==='none'?'none':a<1?`${v}/${Math.round(a*100)}`:v;
let sequence=0;
for(const page of pages){
  const slide=pres.slides.add();slide.background.fill='#FFFFFF';
  for(const item of page.shapes){
    const position={left:item.x*scale,top:item.y*scale,width:Math.max(.02,item.w*scale),height:Math.max(.02,item.h*scale)};
    if(item.kind==='text'){
      position.rotation=item.rotation;
      const shape=slide.shapes.add({geometry:'textbox',name:`text_${sequence++}`,position,fill:'none',line:{fill:'none',width:0}});
      shape.text=item.text;
      shape.text.style={typeface:'Arial',fontSize:item.font*scale,bold:item.bold,color:item.color,alignment:'left',verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
    }else{
      const config={name:`${page.stem}_${sequence++}`,position,fill:color(item.fill,item.fill_alpha),line:{fill:color(item.stroke,item.stroke_alpha),width:item.stroke==='none'?0:item.stroke_width*scale,style:item.dash==='none'?'solid':'dashed'}};
      if(item.kind==='ellipse')slide.shapes.add({geometry:'ellipse',...config});
      else{
        const commands=[];
        for(const part of item.parts){
          part.forEach((p,i)=>commands.push({[i?'lineTo':'moveTo']:{x:p[0]*scale,y:p[1]*scale}}));
          if(Math.hypot(part[0][0]-part.at(-1)[0],part[0][1]-part.at(-1)[1])<1e-5)commands.push({close:{}});
        }
        slide.shapes.add({geometry:'custom',...config,customPaths:[{width:position.width,height:position.height,commands}]});
      }
    }
  }
  slide.speakerNotes.textFrame.setText(page.notes);
  pres.comments.addThread({slide},'@@'+page.id,{position:{x:0,y:0,unit:'px'}});
  console.log(page.id,page.shapes.length,'editable shapes');
}
await(await PresentationFile.exportPptx(pres)).save(path.join(build,'candidate.pptx'));
