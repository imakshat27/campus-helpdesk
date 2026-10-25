/* Browser audit against tests.browser_server only; uses temporary credentials. */
const { chromium }=require(process.env.CAMPUS_PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const credentials=JSON.parse(fs.readFileSync(process.env.BROWSER_TEST_CREDENTIALS,'utf8'));
const base=process.env.BROWSER_TEST_URL || 'http://127.0.0.1:5173';
const output=process.env.BROWSER_TEST_OUTPUT || path.resolve(__dirname,'../../reports/implementation/minimal-ui');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 const context=await browser.newContext({viewport:{width:375,height:812},timezoneId:'Asia/Kolkata',reducedMotion:'reduce'});
 let page=await context.newPage();const checks=[];const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const visible=locator=>locator.waitFor({state:'visible',timeout:20000});
 const shot=name=>page.screenshot({path:path.join(output,'screenshots',name+'.png')});
 const fits=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Page has horizontal overflow');
 async function login(role){
  await page.goto(base);
  await page.getByLabel('Username',{exact:true}).fill(credentials[role+'_username']);
  await page.getByLabel('Password',{exact:true}).fill(credentials[role+'_password']);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await visible(page.getByRole('button',{name:'Sign out',exact:true}));
 }
 try{
  await page.goto(base);await visible(page.getByLabel('Username',{exact:true}));
  await page.evaluate(()=>document.fonts.ready);await fits();await shot('login-mobile');
  await login('student');await visible(page.getByRole('heading',{name:'Ask the helpdesk',exact:true}));
  await page.getByRole('button',{name:'Open navigation',exact:true}).click();
  await visible(page.getByRole('dialog',{name:'Sidebar',exact:true}));await shot('navigation-mobile');
  await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});
  assert.equal(await page.getByRole('button',{name:'Open navigation',exact:true}).evaluate(node=>node===document.activeElement),true);
  checks.push('Mobile navigation opens, Escape dismisses it and focus returns to its trigger');

  await page.goto(base+'/knowledge');
  await visible(page.getByRole('button',{name:/Controlled browser test source/}));await fits();
  await page.getByLabel('Search the knowledge base').fill('No matching source for this query');
  await visible(page.getByText('No matching sources',{exact:true}));await shot('knowledge-empty-mobile');
  await page.getByRole('button',{name:'Clear filters',exact:true}).click();
  const source=page.getByRole('button',{name:/Controlled browser test source/});await source.click();
  await visible(page.getByRole('dialog',{name:'Controlled browser test source',exact:true}));await fits();
  const close=page.getByRole('button',{name:'Close source',exact:true});const closeBox=await close.boundingBox();
  assert.ok(closeBox.width>=44 && closeBox.height>=44,'Source close target is too small');await shot('source-mobile');
  await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});
  await page.waitForFunction(node=>node===document.activeElement,await source.elementHandle(),{timeout:3000});
  checks.push('Mobile knowledge search, empty-state reset, source dialog, focus return and 44px close control');

  await page.goto(base);await visible(page.getByLabel('Ask a campus question',{exact:true}));
  let release;const failed=new Promise(resolve=>{release=resolve;});
  await page.route('**/api/conversations/*/messages',async route=>{await failed;await route.abort('failed');});
  const question='A question retained after a controlled failed send';
  await page.getByLabel('Ask a campus question',{exact:true}).fill(question);
  await page.getByRole('button',{name:'Send question',exact:true}).click();
  await visible(page.getByText('Searching campus sources…',{exact:true}));await shot('composer-pending-mobile');release();
  await visible(page.getByRole('alert'));assert.equal(await page.getByLabel('Ask a campus question',{exact:true}).inputValue(),question);
  await page.waitForFunction(()=>{const b=document.querySelector('.send-button');return b && !b.disabled && getComputedStyle(b).color===getComputedStyle(b.querySelector('span')).color;});
  const activeSend=await page.getByRole('button',{name:'Send question',exact:true}).evaluate(node=>({disabled:node.disabled,color:getComputedStyle(node).color,background:getComputedStyle(node).backgroundColor,label:getComputedStyle(node.querySelector('span')).color}));
  assert.equal(activeSend.disabled,false);assert.equal(activeSend.label,activeSend.color,'Send label must inherit the enabled button text color');
  await fits();await shot('composer-error-mobile');await page.unroute('**/api/conversations/*/messages');
  checks.push('Pending send has stable controls; failed send restores its draft and shows a readable inline error');

  await page.getByRole('button',{name:'Open navigation',exact:true}).click();
  await page.getByRole('link',{name:'New conversation',exact:true}).click();
  await visible(page.getByRole('heading',{name:'Ask the helpdesk',exact:true}));
  await page.getByLabel('Ask a campus question',{exact:true}).fill('private browser audit request');
  await page.getByRole('button',{name:'Send question',exact:true}).click();
  await page.getByRole('button',{name:'Yes, raise a ticket',exact:true}).click();
  await visible(page.getByLabel('Message student support',{exact:true}));
  const url=page.url();const layouts=[];
  for(const [width,height] of [[320,568],[375,812],[390,844],[768,1024],[844,390],[1024,900],[1280,720],[1440,1000]]){
   await page.setViewportSize({width,height});
   await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   await fits();
   const send=await page.getByRole('button',{name:'Send message',exact:true}).boundingBox();
   assert.ok(send && send.width>=44 && send.height>=44 && send.y>=0 && send.y+send.height<=height,'Send target outside viewport: '+JSON.stringify({width,height,send}));
   assert.equal(await page.locator('.composer textarea').evaluate(node=>getComputedStyle(node).resize),'none');
   const contextText=await page.locator('.composer-bottom').innerText();assert.equal(contextText.trim(),'Send');
   layouts.push({width,height,composerFits:true});
   if(width===375)await shot('composer-fixed-mobile');
   if(height===390)await shot('chat-landscape');
  }
  checks.push('Eight viewport sizes: compact Send control stays inside the viewport; no wrapped saved-message caption or resize handle');
  await page.setViewportSize({width:375,height:812});
  const input=page.getByLabel('Message student support',{exact:true});
  await input.fill('Line one\nLine two\nLine three\nLine four\nLine five\nLine six\nLine seven');
  const grown=await input.boundingBox();assert.ok(grown.height>=80 && grown.height<=140);await fits();await shot('composer-multiline-mobile');
  await input.fill('');
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(resolve)));
  assert.ok((await input.boundingBox()).height<grown.height,'Composer did not shrink after clearing');
  await page.locator('.composer').screenshot({path:path.join(output,'screenshots','composer-detail.png')});
  checks.push('Multiline composer grows to a cap then scrolls, and shrinks when cleared');

  await page.routeWebSocket('**/api/events',socket=>socket.close({code:1013,reason:'Controlled audit disconnect'}));
  await page.goto(url);await visible(page.getByText('Reconnecting…',{exact:true}));await fits();await shot('reconnecting-mobile');
  assert.equal(await page.getByRole('button',{name:'Open navigation',exact:true}).isVisible(),true);
  checks.push('Disconnected mobile header shows explicit reconnecting text and retains navigation and sign-out access');
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'ui-audit.json'),JSON.stringify({verdict:'PASS',environment:'Local Chromium with isolated SQLite and controlled request failure',checks,layouts,pageErrors:errors},null,2)+'\n');
  console.log(JSON.stringify({verdict:'PASS',checks:checks.length,layouts:layouts.length}));
 }catch(error){await shot('audit-failure').catch(()=>{});console.error(error.message);process.exitCode=1;}
 finally{await browser.close();}
})();
