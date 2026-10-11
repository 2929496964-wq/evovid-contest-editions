// DOM/API interaction test, not a visual browser rendering claim.
const fs=require('fs'),path=require('path'),{spawn}=require('child_process');
const {JSDOM}=require(process.env.JSDOM_PATH || '../.qa-node/node_modules/jsdom');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:8712';
const server=spawn(path.join(root,'.venv/bin/python'),['-m','uvicorn','vision.server:app','--host','127.0.0.1','--port','8712'],{cwd:root,env:{...process.env,VISION_DATA_DIR:path.join(root,'runtime-dom-qa')},stdio:'ignore'});
const checks=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,desc,limit=60000){const end=Date.now()+limit;while(Date.now()<end){if(await fn())return;await sleep(100);}throw Error('Timeout: '+desc);}
let dom;
(async()=>{try{
await until(async()=>{try{return(await fetch(base+'/api/health')).ok;}catch{return false;}},'server');
dom=new JSDOM(fs.readFileSync(path.join(root,'static/index.html'),'utf8'),{url:base,runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,d=w.document;w.fetch=(url,opts)=>fetch(new URL(url,base),opts);w.HTMLElement.prototype.scrollIntoView=function(){};
w.eval(fs.readFileSync(path.join(root,'static/app.js'),'utf8'));
await until(()=>d.getElementById('engine').textContent.includes('5.0.0'),'engine');
d.getElementById('demo').click();await until(()=>d.getElementById('state').textContent==='review','analysis');
checks.push({check:'Demo click performs real analysis and renders 12 interval controls',passed:d.querySelectorAll('.segment').length===12});
checks.push({check:'Synthetic provenance displayed',passed:d.getElementById('job-type').textContent.includes('SYNTHETIC')});
d.getElementById('target').value='4';d.getElementById('weight').value='4';d.getElementById('recommend').click();
await until(()=>d.getElementById('selected-summary').textContent.includes('4.00 seconds'),'recommendation');
checks.push({check:'Unapproved render button disabled',passed:d.getElementById('render').disabled});
d.getElementById('approved').checked=true;d.getElementById('approved').dispatchEvent(new w.Event('change'));
await until(()=>!d.getElementById('render').disabled,'approval enables render');d.getElementById('render').click();
await until(()=>d.getElementById('state').textContent==='complete','render');
checks.push({check:'Approve/render completes and download links appear',passed:!d.getElementById('downloads').hidden&&d.getElementById('download-video').href.includes('/media/output')});
checks.push({check:'Output video source points to real MP4 endpoint',passed:d.getElementById('after').src.includes('/media/output')&&!d.getElementById('after').hidden});
d.getElementById('load-logs').click();await until(()=>d.getElementById('logs').textContent.includes('render_finished'),'logs');
checks.push({check:'Session log loads real execution events',passed:true});
const first=d.querySelector('.include');first.checked=!first.checked;first.dispatchEvent(new w.Event('change'));
checks.push({check:'Changing a clip revokes previous approval',passed:!d.getElementById('approved').checked&&d.getElementById('render').disabled});
checks.push({check:'No visible error after normal flow',passed:d.getElementById('notice').hidden});
if(checks.some(c=>!c.passed))throw Error('DOM assertion failed');
}finally{if(dom)dom.window.close();server.kill('SIGTERM');fs.writeFileSync(path.join(root,'evidence/dom-qa.json'),JSON.stringify({checks,visual_rendering_verified:false},null,2));}
console.log(JSON.stringify(checks,null,2));})().catch(e=>{console.error(e);process.exitCode=1;});
