/** 单独装配9LLG的冻结流程页, 科学视图、布局和图注均由共享实现原样提供. */
if(process.argv.slice(2).some(value=>value==='--pdb'||value.startsWith('--pdb='))) throw new Error('本入口固定装配9llg, 不接受另一个pdb');
process.argv.splice(2,0,'--pdb','9llg');
await import(new URL('../e2e-flow-shared/build_deck.mjs',import.meta.url).href);
