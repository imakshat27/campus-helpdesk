/* Run against tests.browser_server with private generated test credentials. */
const { chromium } = require(process.env.CAMPUS_PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {randomUUID}=require('node:crypto');
const credentials = JSON.parse(fs.readFileSync(process.env.BROWSER_TEST_CREDENTIALS, 'utf8'));
const output = process.env.BROWSER_TEST_OUTPUT || path.resolve(__dirname, '../../reports/implementation');
const base = process.env.BROWSER_TEST_URL || 'http://127.0.0.1:5173';

(async () => {
  fs.mkdirSync(path.join(output, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_EXECUTABLE ? {executablePath:process.env.BROWSER_EXECUTABLE} : {}) });
  const studentContext = await browser.newContext({ viewport: { width: 1440, height: 1000 }, timezoneId:'Asia/Kolkata' });
  const staffContext = await browser.newContext({ viewport: { width: 1440, height: 1000 }, timezoneId:'Asia/Kolkata' });
  const student = await studentContext.newPage();
  const staff = await staffContext.newPage();
  const errors = [];
  for (const page of [student, staff]) page.on('pageerror', e => errors.push(e.message));
  const checks = [];
  async function visible(locator) { await locator.waitFor({ state: 'visible', timeout: 30000 }); }
  async function login(page, role) {
    await page.goto(base);
    await visible(page.getByLabel('Username', {exact:true}));
    if(role==='student'){
      await page.evaluate(()=>document.fonts.ready);
      await page.screenshot({path:path.join(output,'screenshots','login.png')});
    }
    await page.getByLabel('Username', { exact: true }).fill(credentials[role + '_username']);
    await page.getByLabel('Password', { exact: true }).fill(credentials[role + '_password']);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await visible(page.getByText('Live updates connected', { exact: true }));
  }
  try {
    await login(student, 'student'); await login(staff, 'staff');
    assert.match(staff.url(), /\/staff$/);
    if(process.env.BROWSER_CHECK_MINIMAL_UI){
      await student.evaluate(()=>document.fonts.ready);
      const fonts=await student.evaluate(()=>({body:getComputedStyle(document.body).fontFamily,
        input:getComputedStyle(document.querySelector('textarea')).fontFamily,
        faces:[...document.fonts].filter(face=>face.family==='Clear Pro' && face.status==='loaded').map(face=>face.weight)}));
      assert.match(fonts.body,/Clear Pro/);assert.match(fonts.input,/Clear Pro/);assert.ok(fonts.faces.includes('400'));
      for(const [width,height] of [[375,812],[1280,720],[1440,1000]]){
        await student.setViewportSize({width,height});
        await student.screenshot({path:path.join(output,'screenshots',`welcome-${width}.png`)});
        const overflow=await student.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
        assert.equal(overflow,false);
      }
      await student.getByRole('link',{name:'Knowledge base',exact:true}).click();
      await visible(student.getByRole('button',{name:/Controlled browser test source/}));
      await student.screenshot({path:path.join(output,'screenshots','knowledge.png')});
      await student.getByLabel('Topic',{exact:true}).selectOption('library');
      await visible(student.getByRole('button',{name:/Controlled browser test source/}));
      await student.getByRole('link',{name:'Ask a question',exact:true}).click();
      await visible(student.getByRole('heading',{name:'Ask the helpdesk',exact:true}));
      await staff.screenshot({path:path.join(output,'screenshots','staff-queue-empty.png')});
      checks.push('Clear Pro font files loaded for body and composer; welcome layouts and native topic filter verified');
    }
    const cookie = (await studentContext.cookies()).find(c => c.name === 'campus_session');
    assert.equal(cookie.httpOnly, true);
    checks.push('Separate student/staff logins and role redirects; HttpOnly cookie');

    await student.getByLabel('Ask a campus question',{exact:true}).fill('How do I renew library books?');
    await student.getByRole('button',{name:'Send question',exact:true}).click();
    const citation=student.getByRole('button',{name:'Controlled browser test source',exact:true});
    await visible(citation);await citation.click();
    await visible(student.getByRole('dialog',{name:'Controlled browser test source',exact:true}));
    await student.keyboard.press('Escape');
    await student.getByRole('dialog').waitFor({state:'hidden'});
    await student.getByRole('button',{name:'Ask staff about this answer',exact:true}).click();
    await visible(student.getByRole('heading',{name:'Raise a ticket for this question?',exact:true}));
    await student.getByRole('button',{name:'No thanks',exact:true}).click();
    assert.equal(await staff.getByRole('link').filter({hasText:'How do I renew library books?'}).count(),0);
    checks.push('Supported answers retain citations, keyboard-dismissible source dialog and explicit manual handoff consent');
    await student.getByRole('link',{name:'New conversation',exact:true}).click();
    await visible(student.getByRole('heading',{name:'Ask the helpdesk',exact:true}));

    const question = 'What is my private timetable for browser test '+Date.now()+'?';
    await student.getByLabel('Ask a campus question', { exact: true }).fill(question);
    await student.getByRole('button', { name: 'Send question', exact: true }).click();
    await visible(student.getByRole('button', { name: 'Yes, raise a ticket', exact: true }));
    assert.equal(await staff.getByRole('link').filter({hasText:question}).count(), 0);
    checks.push('Unsupported answer offers a ticket without creating a staff queue entry');
    await student.getByRole('button', { name: 'Yes, raise a ticket', exact: true }).click();
    const staffLink = staff.getByRole('link').filter({hasText:question});
    await visible(staffLink);
    if(process.env.BROWSER_CHECK_MINIMAL_UI)await staff.screenshot({path:path.join(output,'screenshots','staff-queue.png')});
    await staffLink.click();
    await visible(staff.getByRole('button', { name: 'Start chat', exact: true }));
    assert.equal(await staff.getByLabel('Message student', { exact: true }).isDisabled(), true);
    await staff.getByRole('button', { name: 'Start chat', exact: true }).click();
    await visible(student.getByText('Chatting with staff · AI replies are paused', { exact: true }));
    checks.push('Confirmed ticket appears live in staff queue; acceptance updates the student');

    await staff.getByLabel('Message student', { exact: true }).fill('A real-time staff response for this test.');
    await staff.getByRole('button', { name: 'Send message', exact: true }).click();
    await visible(student.getByText('A real-time staff response for this test.', { exact: true }));
    await student.getByLabel('Message student support', { exact: true }).fill('A student reply delivered live.');
    await student.getByRole('button', { name: 'Send message', exact: true }).click();
    await visible(staff.getByText('A student reply delivered live.', { exact: true }));
    checks.push('Two-way staff/student messages arrive without page refresh');

    const cid=student.url().split('/').pop();
    const concurrent=[
      {context:studentContext,message:'Student message submitted concurrently.'},
      {context:staffContext,message:'Staff message submitted concurrently.'},
    ].map(item=>({...item,data:{message:item.message,client_request_id:randomUUID()}}));
    const results=await Promise.all(concurrent.map(item=>item.context.request.post(base+'/api/conversations/'+cid+'/messages',{headers:{Origin:base},data:item.data})));
    let concurrentRetries=0;
    for(let i=0;i<results.length;i++){
      let result=results[i];
      if([409,503].includes(result.status())){concurrentRetries++;result=await concurrent[i].context.request.post(base+'/api/conversations/'+cid+'/messages',{headers:{Origin:base},data:concurrent[i].data});}
      assert.equal(result.status(),200);
    }
    const transcript=await (await studentContext.request.get(base+'/api/conversations/'+cid)).json();
    for(const item of concurrent)assert.equal(transcript.messages.filter(m=>m.content===item.message).length,1);
    assert.equal(new Set(transcript.messages.map(m=>m.sequence)).size,transcript.messages.length);
    checks.push('Concurrent student/staff sends persist once each with unique ordering; retry any SQLite write contention');

    const savedURL = student.url();
    await student.reload();
    await visible(student.getByText('A real-time staff response for this test.', { exact: true }));
    checks.push('Refresh restores persisted transcript and session');
    await studentContext.setOffline(true);
    await staff.getByLabel('Message student', { exact: true }).fill('Message saved while the student was offline.');
    await staff.getByRole('button', { name: 'Send message', exact: true }).click();
    await visible(staff.getByText('Message saved while the student was offline.', { exact: true }));
    await studentContext.setOffline(false);
    await visible(student.getByText('Message saved while the student was offline.', { exact: true }));
    checks.push('Reconnect reloads messages saved while offline');

    const layouts = [];
    for (const [width,height] of [[375,812],[768,1024],[1024,900],[1280,720],[1440,1000]]) {
      await student.setViewportSize({ width, height });
      await student.evaluate(()=>{window.scrollTo(0,document.documentElement.scrollHeight);const transcript=document.querySelector('.conversation');if(transcript)transcript.scrollTop=transcript.scrollHeight;});
      await student.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const dimensions = await student.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth }));
      assert.ok(dimensions.content <= dimensions.viewport, 'Horizontal overflow at ' + width);
      const composer=await student.getByRole('button',{name:'Send message',exact:true}).boundingBox();
      assert.ok(composer && composer.y>=0 && composer.y+composer.height<=height, 'Composer outside viewport at '+width);
      await student.screenshot({ path: path.join(output, 'screenshots', `student-${width}.png`), fullPage: false });
      layouts.push({ width, height, horizontalOverflow: false });
    }
    await staff.screenshot({ path: path.join(output, 'screenshots', 'staff-chat.png'), fullPage: false });
    checks.push('375, 768, 1024, 1280×720 and 1440 layouts: no horizontal overflow; composer visible');

    await staff.getByRole('button', { name: 'Mark resolved', exact: true }).click();
    await visible(student.getByRole('button', { name: 'Reopen conversation', exact: true }));
    assert.equal(await student.getByLabel('Message student support', { exact: true }).isDisabled(), true);
    await student.getByRole('button', { name: 'Reopen conversation', exact: true }).click();
    await visible(staff.getByRole('button', { name: 'Start chat', exact: true }));
    checks.push('Resolution closes the composer; student reopening returns it to the staff queue');

    await student.getByRole('button', { name: 'Sign out', exact: true }).click();
    await visible(student.getByRole('button', { name: 'Sign in', exact: true }));
    await login(student, 'student'); await student.goto(savedURL);
    await visible(student.getByText('A real-time staff response for this test.', { exact: true }));
    checks.push('Logout and new login preserve account-owned history');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'browser-checks.json'), JSON.stringify({ environment: 'Local Chromium; isolated SQLite; controlled answers; no Neon tickets/model calls', checks, layouts, concurrentRetries, pageErrors: errors, verdict: 'PASS' }, null, 2) + '\n');
    console.log(JSON.stringify({ verdict: 'PASS', checks: checks.length, layouts: layouts.length }));
  } catch (error) {
    await student.screenshot({ path: '/private/tmp/campus-browser-student-failure.png', fullPage: false }).catch(() => {});
    await staff.screenshot({ path: '/private/tmp/campus-browser-staff-failure.png', fullPage: false }).catch(() => {});
    console.error(error.message); process.exitCode = 1;
  } finally { await browser.close(); }
})();
