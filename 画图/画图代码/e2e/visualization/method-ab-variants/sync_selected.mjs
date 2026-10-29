/** 按作者当前第3页同步第4、5页, 仅改变具名框线及填充. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const require=createRequire(path.join(runtime,'__method_ab_sync__.cjs'));
const JSZip=require('jszip'),{xml2js,js2xml}=require('xml-js');
let root=path.dirname(fileURLToPath(import.meta.url));
while(!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false)))root=path.dirname(root);
const build=process.env.FIGURE_BUILD_ROOT;if(!build)throw new Error('必须指定构建目录');
const config=JSON.parse((await fs.readFile(path.join(root,'画图/画图代码/e2e/output/method-ab-variants/source/selected-layout.json'),'utf8')).replace(/^\uFEFF/,''));
const bytes=await fs.readFile(path.join(root,config.pptx));
if(createHash('sha256').update(bytes).digest('hex')!==config.sha256)throw new Error('作者冻结输入散列改变');
const zip=await JSZip.loadAsync(bytes);
const parse=t=>xml2js(t,{compact:false,captureSpacesBetweenElements:true});
const children=n=>(n?.elements||[]).filter(e=>e.type==='element');
const child=(n,name)=>children(n).find(e=>e.name===name);
const at=(n,...names)=>names.reduce((p,k)=>child(p,k),n);
const all=(n,name)=>[...children(n).filter(e=>e.name===name),...children(n).flatMap(e=>all(e,name))];
const read=async p=>parse(await zip.file(p).async('string'));
const save=(p,n)=>zip.file(p,js2xml(n,{compact:false,spaces:0}));
const shapeKinds=new Set(['p:sp','p:grpSp','p:pic','p:cxnSp']);
const shapes=n=>children(n).flatMap(e=>[...(shapeKinds.has(e.name)?[e]:[]),...shapes(e)]);
const identity=s=>all(s,'p:cNvPr')[0].attributes;
const containerIds=new Set([13,235,237,243,299,662,1249,1443,1478]);
const dividerIds=new Set([303,1250,1479]);
const baseline=await read('ppt/slides/slide3.xml');
const baselineTree=at(baseline,'p:sld','p:cSld','p:spTree');
for(const s of shapes(baselineTree))if(identity(s).name.startsWith('Op |'))containerIds.add(Number(identity(s).id));
const baselineImages=children(child(await read('ppt/slides/_rels/slide3.xml.rels'),'Relationships')).filter(e=>e.attributes.Type.endsWith('/image')).map(e=>[e.attributes.Id,e.attributes.Target]).sort();
const operations={source:config.pptx,source_sha256:config.sha256,baseline_page:3,slide_count:5,container_ids:[...containerIds],divider_ids:[...dividerIds],border:'BEC7CE',divider:'C8CFD4',fill:'F4F6F7',pages:{}};
for(const page of [4,5]){
  const part=`ppt/slides/slide${page}.xml`,doc=await read(part),csld=at(doc,'p:sld','p:cSld');
  const images=children(child(await read(`ppt/slides/_rels/slide${page}.xml.rels`),'Relationships')).filter(e=>e.attributes.Type.endsWith('/image')).map(e=>[e.attributes.Id,e.attributes.Target]).sort();
  if(JSON.stringify(images)!==JSON.stringify(baselineImages))throw new Error('图像关系不同, 禁止直接复制对象树');
  const original=child(csld,'p:spTree'),tree=structuredClone(baselineTree);
  const edits=[];
  const setColour=(s,holder,value,scope)=>{
    const c=at(holder,'a:solidFill','a:srgbClr');if(!c || c.attributes.val===value)return;
    edits.push({id:Number(identity(s).id),name:identity(s).name,scope,before:c.attributes.val,after:value});c.attributes.val=value;
  };
  for(const s of shapes(tree)){
    const sid=Number(identity(s).id),sp=child(s,'p:spPr');
    if(containerIds.has(sid)){
      setColour(s,child(sp,'a:ln'),operations.border,'border');
      if(page===5)setColour(s,sp,operations.fill,'fill');
    }
    if(dividerIds.has(sid)){
      setColour(s,sp,operations.divider,'divider');setColour(s,child(sp,'a:ln'),operations.divider,'divider');
    }
  }
  csld.elements[csld.elements.indexOf(original)]=tree;
  save(part,doc);operations.pages[page]={colour_edits:edits};
}
// 只同步已登记的来源批注, 保留图名、作者批注及全部备注.
const tracePath='画图/画图代码/e2e/visualization/图表追溯.md';
const trace=(await fs.readFile(path.join(root,tracePath),'utf8')).replace(/\r\n?/g,'\n');
const records=new Map();
for(const m of trace.matchAll(/<!--\s*provenance:begin\s+([^\s>]+)\s*-->([\s\S]*?)<!--\s*provenance:end\s+\1\s*-->/g)){
  const body=m[2].replace(/^\s*<!--\s*provenance-meta\s+\{[\s\S]*?\}\s*-->\s*/,'').trim();
  records.set(m[1],'PROVENANCE v1\nid: '+m[1]+'\nsource: '+tracePath+'\n\n'+body);
}
for(const name of Object.keys(zip.files).filter(n=>n.startsWith('ppt/comments/')&&n.endsWith('.xml'))){
  const doc=await read(name);let changed=false;
  for(const cm of children(children(doc)[0]).filter(e=>e.name.endsWith(':cm'))){
    const tx=children(cm).find(e=>e.name.endsWith(':txBody'));if(!tx)continue;
    const paragraphs=children(tx).filter(e=>e.name==='a:p');
    const text=paragraphs.map(p=>all(p,'a:t').map(t=>(t.elements||[]).map(e=>e.text||'').join('')).join('')).join('\n');
    const m=text.match(/^PROVENANCE v1\nid: ([^\n]+)\n/);if(!m || !records.has(m[1]))continue;
    const wanted=records.get(m[1]);if(wanted===text)continue;
    tx.elements=children(tx).filter(e=>e.name!=='a:p');
    for(const line of wanted.split('\n'))tx.elements.push({type:'element',name:'a:p',elements:[{type:'element',name:'a:r',elements:[{type:'element',name:'a:t',elements:[{type:'text',text:line}]}]}]});
    changed=true;
  }
  if(changed)save(name,doc);
}
await fs.mkdir(build,{recursive:true});
await fs.writeFile(path.join(build,'candidate.pptx'),await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE',compressionOptions:{level:6}}));
await fs.writeFile(path.join(build,'selected_operations.json'),JSON.stringify(operations,null,2));
console.log('Five-slide author deck retained; pages 4 and 5 now share the exact page-3 object tree and expanded a/b frame palette.');
