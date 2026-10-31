const { chromium } = require('playwright');
(async () => {
  const out = '/tmp/drawer/out';
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1632, height: 1056 }, deviceScaleFactor: 2 });
  await page.goto('file://' + out + '/sheet.html');
  await page.waitForTimeout(500);
  const pages = await page.$$('svg.page');
  for (let i = 0; i < pages.length; i++) {
    await pages[i].screenshot({ path: `${out}/page${i + 1}.png` });
  }
  await page.pdf({ path: `${out}/sheet.pdf`, width: '17in', height: '11in', printBackground: true });
  await browser.close();
  console.log('rendered', pages.length);
})();
