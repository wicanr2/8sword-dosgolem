// Disposable camp proposal: CDP only, no game or save writes.
const fs = require('node:fs');
const cp = require('node:child_process');
const path = require('node:path');
const assert = require('node:assert/strict');
const study = process.argv[2];
const toolbar = process.argv[3] === 'toolbar';
const receiptName = toolbar ? 'toolbar-browser-r1.json' : 'browser-r1.json';
assert(study && fs.statSync(study).uid === 1000 && !fs.existsSync(path.join(study, receiptName)));
const chrome = '/ms-playwright/chromium-1194/chrome-linux/chrome';
const browser = cp.spawn(chrome, ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--no-first-run', '--no-default-browser-check', '--remote-debugging-pipe', '--user-data-dir=/tmp/openkb-camp-browser'], {stdio:['ignore','ignore','pipe','pipe','pipe']});
let id = 0, buffered = '', session;
const pending = new Map();
browser.stderr.on('data', () => {});
browser.stdio[4].on('data', chunk => {
 buffered += chunk.toString();
 let at;
 while ((at = buffered.indexOf('\0')) >= 0) {
  const raw = buffered.slice(0,at); buffered = buffered.slice(at+1);
  if (!raw) continue;
  const value = JSON.parse(raw), callback = pending.get(value.id);
  if (callback) { pending.delete(value.id); value.error ? callback.reject(Error(JSON.stringify(value.error))) : callback.resolve(value.result); }
 }
});
function send(method, params = {}, inSession = true) {
 if (toolbar) fs.appendFileSync(path.join(study,'toolbar-browser-debug.jsonl'),JSON.stringify({method,expression:params.expression,time:new Date().toISOString()})+'\n');
 return new Promise((resolve,reject) => {
  const key = ++id; pending.set(key,{resolve,reject});
  const msg = {id:key,method,params}; if (session && inSession) msg.sessionId = session;
  browser.stdio[3].write(JSON.stringify(msg)+'\0');
 });
}
browser.on('exit',(code,signal)=>{for(const callback of pending.values())callback.reject(Error('browser exited '+code+' '+signal));pending.clear()});
async function evaluate(expression) {
 const r = await send('Runtime.evaluate', {expression,returnByValue:true,awaitPromise:true});
 assert(!r.exceptionDetails, JSON.stringify(r.exceptionDetails)); return r.result.value;
}
const timeout=setTimeout(()=>{browser.kill('SIGKILL');throw Error('bounded camp browser timed out')},45000);
(async()=>{try{
 const version=await send('Browser.getVersion',{},false);const target=await send('Target.createTarget',{url:'about:blank'},false);session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true},false)).sessionId;
 await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1200,height:1100,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url:'file://'+path.join(study,'proposal.html')});
 await evaluate(`new Promise(resolve=>{if(document.readyState==='complete')resolve();else window.addEventListener('load',resolve,{once:true})})`);await evaluate(`document.fonts.ready`);
 const count=await evaluate(`data.camps.length`);assert(count>0&&count<=120);assert.equal(await evaluate(`proposalState().cards`),8);assert.equal(await evaluate(`proposalState().originalKept`),true);
 await evaluate(`choose('openkb:wolf')`);assert.match(await evaluate(`proposalState().quote`),/原店仍可購買原兵種/);
 const a=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(study,'proposal-a.png'),Buffer.from(a.data,'base64'));
 await evaluate(`setMode('b');choose('openkb:wolf')`);assert.equal(await evaluate(`proposalState().originalKept`),false);assert.match(await evaluate(`document.querySelector('#original').textContent`),/野狼/);
 const b=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(study,'proposal-b.png'),Buffer.from(b.data,'base64'));
 await evaluate(`document.querySelector('#rank').value='5';render();choose('openkb:drag')`);assert.equal(await evaluate(`proposalState().rank`),5);
 await evaluate(`document.querySelector('#camp').value='${count-1}';render();setMode('a')`);assert.equal(await evaluate(`proposalState().originalKept`),true);assert.equal(await evaluate(`proposalState().cards`),8);
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});assert.equal(await evaluate(`document.documentElement.scrollWidth<=window.innerWidth`),true);
 fs.writeFileSync(path.join(study,'browser-r1.json'),JSON.stringify({status:'passed-camp-proposal-browser',browser:version.product,camps:count,units:8,mode_a_preserves_original:true,mode_b_replaces_original:true,rank_switch:true,camp_switch:true,mobile_horizontal_overflow:false,game_executed:false,save_writes:false},null,2)+'\n');process.stdout.write('camp proposal browser passed\n');
}finally{clearTimeout(timeout);await send('Browser.close',{},false).catch(()=>{});if(browser.exitCode===null)browser.kill('SIGTERM')}})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1});
