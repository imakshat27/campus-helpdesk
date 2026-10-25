/* Isolated browser fixture only. Real rendering and independent student/staff sessions. */
const {chromium}=require(process.env.CAMPUS_PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');const {randomUUID}=require('node:crypto');
const credentials=JSON.parse(fs.readFileSync(process.env.BROWSER_TEST_CREDENTIALS,'utf8'));
const base=process.env.BROWSER_TEST_URL || 'http://127.0.0.1:5173';
const output=process.env.BROWSER_TEST_OUTPUT || path.resolve(__dirname,'../../reports/implementation/minimal-ui');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 const contexts=await Promise.all([browser.newContext({viewport:{width:390,height:844}}),browser.newContext({viewport:{width:1280,height:720}})]);
 const [student,staff]=await Promise.all(contexts.map(c=>c.newPage()));const checks=[];const errors=[];
 for(const page of [student,staff])page.on('pageerror',e=>errors.push(e.message));
 const visible=l=>l.waitFor({state:'visible',timeout:20000});
 const bottom=page=>page.waitForFunction(()=>{const n=document.querySelector('.conversation');return n && n.scrollHeight-n.clientHeight-n.scrollTop<3;});
 const top=async page=>{await page.locator('.conversation').evaluate(n=>{n.scrollTop=0;n.dispatchEvent(new Event('scroll'));});};
 async function post(page,url,body){const r=await page.request.post(base+'/api'+url,{headers:{Origin:base},data:body});assert.ok(r.ok(),`${url}: ${r.status()}`);return r.json();}
 async function send(page,text){await page.locator('#question').fill(text);await page.getByRole('button',{name:'Send message',exact:true}).click();await visible(page.getByText(text,{exact:true}));await page.getByRole('button',{name:'Send message',exact:true}).waitFor();await page.waitForFunction(()=>!document.querySelector('#question').disabled);await bottom(page);}
 try{
  for(const [i,role] of ['student','staff'].entries()){
   const page=[student,staff][i];await page.goto(base);await page.getByLabel('Username',{exact:true}).fill(credentials[role+'_username']);await page.getByLabel('Password',{exact:true}).fill(credentials[role+'_password']);await page.getByRole('button',{name:'Sign in',exact:true}).click();await visible(page.getByRole('button',{name:'Sign out',exact:true}));
  }
  const conv=await post(student,'/conversations',{id:randomUUID()});
  const detail=await post(student,`/conversations/${conv.id}/messages`,{message:'private timetable scroll audit',client_request_id:randomUUID()});
  await post(student,`/conversations/${conv.id}/escalate`,{message_id:detail.messages.find(m=>m.role==='user').id,confirmed:true});
  await post(staff,`/conversations/${conv.id}/accept`);
  for(let i=0;i<18;i++)await post(i%2?staff:student,`/conversations/${conv.id}/messages`,{message:`History ${i}: `+'A longer message makes the transcript scroll naturally. '.repeat(5),client_request_id:randomUUID()});
  await Promise.all([student.goto(base+'/conversations/'+conv.id),staff.goto(base+'/staff/'+conv.id)]);
  for(const page of [student,staff]){await visible(page.getByText(/History 17:/));await bottom(page);assert.ok(await page.locator('.conversation').evaluate(n=>n.scrollHeight-n.clientHeight>500));}
  checks.push('Opening long saved conversations starts at the newest message for both roles');
  for(const [sender,receiver,role] of [[student,staff,'student'],[staff,student,'staff']]){
   await top(sender);await send(sender,role+' sends from history');await visible(receiver.getByText(role+' sends from history',{exact:true}));await bottom(receiver);
   checks.push(role+' sending from history scrolls to the sent message; receiving at the bottom follows live');
   await top(receiver);const before=await receiver.locator('.conversation').evaluate(n=>n.scrollTop);
   await send(sender,role+' reply while reading');await visible(receiver.getByRole('button',{name:'New messages',exact:true}));
   assert.equal(await receiver.locator('.conversation').evaluate(n=>n.scrollTop),before);
   await receiver.getByRole('button',{name:'New messages',exact:true}).click();await bottom(receiver);assert.equal(await receiver.getByRole('button',{name:'New messages',exact:true}).count(),0);
   checks.push(role+' replies preserve the other reader’s position and offer a working New messages control');
  }
  await student.locator('#question').fill('One\nTwo\nThree\nFour\nFive');await bottom(student);
  await student.setViewportSize({width:844,height:390});await bottom(student);
  assert.equal(await student.evaluate(()=>window.scrollY),0);
  checks.push('Growing the composer and resizing the viewport keep the newest message visible without moving the page header');
  await staff.screenshot({path:path.join(output,'screenshots','staff-scroll.png')});
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(output,'scroll-audit.json'),JSON.stringify({verdict:'PASS',checks,pageErrors:errors},null,2)+'\n');console.log(JSON.stringify({verdict:'PASS',checks:checks.length}));
 }catch(e){console.error(e);process.exitCode=1;}finally{await browser.close();}
})();
