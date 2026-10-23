/** 对实际Node子进程屏蔽旧temp，冻结实验输入只读。 */
const fs = require('node:fs');
const path = require('node:path');
const {fileURLToPath} = require('node:url');
if (process.env.FIGURE_VERIFY_ROOT) {
  const workspace=path.resolve(process.env.FIGURE_VERIFY_ROOT), current=path.resolve(process.env.FIGURE_BUILD_ROOT);
  const inside=(file,root)=>{if(process.platform==='win32'){file=file.toLowerCase();root=root.toLowerCase();}return file===root||file.startsWith(root+path.sep);};
  const append=fs.appendFileSync.bind(fs);
  function inspect(value, writing=false) {
    if(typeof value==='number')return;
    const file=path.resolve(value instanceof URL?fileURLToPath(value):String(value));
    if(inside(file,path.join(workspace,'temp'))&&!inside(file,current))throw new Error('本次重建屏蔽旧temp: '+file);
    if(writing&&inside(file,workspace)&&!inside(file,current))throw new Error('重建只允许写本次构建目录: '+file);
    if(!writing&&inside(file,workspace)&&!inside(file,current))append(path.join(current,'node-reads.jsonl'),JSON.stringify(path.relative(workspace,file))+'\n');
  }
  for(const owner of [fs,fs.promises])for(const name of ['readFile','readFileSync','createReadStream','readdir','readdirSync'])if(owner[name]){
    const original=owner[name].bind(owner);owner[name]=function(file,...args){inspect(file);return original(file,...args);};
  }
  for(const owner of [fs,fs.promises])for(const name of ['writeFile','writeFileSync','createWriteStream','mkdir','mkdirSync'])if(owner[name]){
    const original=owner[name].bind(owner);owner[name]=function(file,...args){inspect(file,true);return original(file,...args);};
  }
  for(const owner of [fs,fs.promises])for(const name of ['copyFile','copyFileSync','rename','renameSync'])if(owner[name]){
    const original=owner[name].bind(owner);owner[name]=function(source,target,...args){inspect(source);inspect(target,true);return original(source,target,...args);};
  }
  for(const owner of [fs,fs.promises])for(const name of ['open','openSync'])if(owner[name]){
    const original=owner[name].bind(owner);owner[name]=function(file,flags,...args){const writing=typeof flags==='string'?/[wa+]/.test(flags):typeof flags==='number'&&Boolean(flags&(fs.constants.O_WRONLY|fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_TRUNC|fs.constants.O_APPEND));inspect(file,writing);return original(file,flags,...args);};
  }
  require('node:module').syncBuiltinESMExports();
}
