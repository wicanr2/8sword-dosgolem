// 030 DRAFT: Chrome DevTools over pipes; no packages, network or game process.
const fs = require('node:fs');
const cp = require('node:child_process');
const path = require('node:path');
const assert = require('node:assert/strict');
const study = process.argv[2];
const toolbar = process.argv[3] === 'toolbar';
const receiptName = toolbar ? 'toolbar-browser-r1.json' : 'browser-r1.json';
assert(study && fs.statSync(study).uid === 1000 && !fs.existsSync(path.join(study, receiptName)));
const chrome = '/ms-playwright/chromium-1194/chrome-linux/chrome';
const browser = cp.spawn(chrome, ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--no-first-run', '--no-default-browser-check', '--remote-debugging-pipe', '--user-data-dir=/tmp/formation-browser'], {stdio:['ignore','ignore','pipe','pipe','pipe']});
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
const timeout = setTimeout(() => { browser.kill('SIGKILL'); throw Error('bounded browser check timed out'); }, 30000);
(async () => {
 try {
  const version = await send('Browser.getVersion',{},false);
  const target = await send('Target.createTarget',{url:'about:blank'},false);
  session = (await send('Target.attachToTarget',{targetId:target.targetId,flatten:true},false)).sessionId;
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1200,height:1100,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:'file://'+path.join(study,toolbar?'formation-toolbar-prototype-r1.html':'formation-prototype-r1.html')});
  await evaluate(`new Promise(resolve=>{if(document.readyState==='complete')resolve();else window.addEventListener('load',resolve,{once:true})})`);
  assert.equal(await evaluate(`document.querySelector('#scenario').options.length`),19);
  if (toolbar) {
   assert.equal(await evaluate(`document.querySelector('#after').textContent`),'16人');
   await evaluate(`{const chosen=document.querySelector('#rules');chosen.value='formation';chosen.dispatchEvent(new Event('change'))}`);
   assert.equal(await evaluate(`document.querySelector('#after').textContent`),'12人');
   await evaluate(`document.querySelector('#battle').click()`);
   assert.equal(await evaluate(`document.querySelector('#rules').disabled`),true);
   assert.equal(await evaluate(`document.querySelector('#ai').disabled`),false);
   await evaluate(`document.querySelector('#ai').value='target';document.querySelector('#ai').dispatchEvent(new Event('change'))`);
   assert.equal(await evaluate(`document.querySelector('#rules').value`),'formation');
   assert.equal(await evaluate(`document.querySelector('#after').textContent`),'12人');
   await evaluate(`document.querySelector('#battle').click();document.querySelector('#rules').value='native';document.querySelector('#rules').dispatchEvent(new Event('change'))`);
   assert.equal(await evaluate(`document.querySelector('#rules').disabled`),false);
   assert.equal(await evaluate(`document.querySelector('#after').textContent`),'16人');
   await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
   assert.equal(await evaluate(`document.documentElement.scrollWidth<=window.innerWidth`),true);
   fs.writeFileSync(path.join(study,receiptName),JSON.stringify({status:'passed-interactions-only',browser:version.product,original_loss:16,formation_loss:12,rules_locked_during_battle:true,ai_independent:true,mobile_horizontal_overflow:false,screenshot_capture:'unresolved CDP capture timeout; not included in acceptance',game_executed:false},null,2)+'\n');
   process.stdout.write('separate rules/AI toolbar prototype interactions passed\n');
   return;
  }
  assert.equal(await evaluate(`document.querySelector('#before').textContent`),'16人');
  assert.equal(await evaluate(`document.querySelector('#after').textContent`),'12人');
  const shot = await send('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(study,'formation-desktop-r1.png'),Buffer.from(shot.data,'base64'));
  await evaluate(`document.querySelector('[data-rate="10"]').click()`);
  assert.equal(await evaluate(`document.querySelector('#after').textContent`),'14人');
  await evaluate(`const select=document.querySelector('#scenario');select.value='proposal-rear-ally';select.dispatchEvent(new Event('change'))`);
  assert.equal(await evaluate(`document.querySelector('#after').textContent`),'16人');
  await evaluate(`document.querySelector('#scenario').value='proposal-two-person';document.querySelector('#scenario').dispatchEvent(new Event('change'))`);
  assert.equal(await evaluate(`document.querySelector('#before').textContent`),'2人');
  assert.equal(await evaluate(`document.querySelector('#after').textContent`),'0人');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
  assert.equal(await evaluate(`document.documentElement.scrollWidth<=window.innerWidth`),true);
  const mobile = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  fs.writeFileSync(path.join(study,'formation-mobile-r1.png'),Buffer.from(mobile.data,'base64'));
  fs.writeFileSync(path.join(study,'browser-r1.json'),JSON.stringify({status:'passed',browser:version.product,node:process.version,cases:19,default_loss:[16,12],ten_percent_loss:14,rear_support_loss:16,two_person_threshold:[2,0],mobile_horizontal_overflow:false,game_executed:false},null,2)+'\n');
  process.stdout.write('browser interactions and desktop/mobile layout passed\n');
 } finally { clearTimeout(timeout); browser.kill('SIGTERM'); }
})().catch(error => { process.stderr.write(String(error)+'\n'); process.exitCode=1; });
