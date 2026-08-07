const { chromium } = require('/usr/local/lib/node_modules/omniroute/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const out = '/home/nkabandi/Downloads/screenshots';
  const fs = require('fs');
  fs.mkdirSync(out, { recursive: true });

  await page.goto('http://localhost:8199/docs/index.html', { waitUntil: 'networkidle' });

  // Full page
  await page.screenshot({ path: out + '/01-full-page.png', fullPage: true });

  // Sections by selector
  const cuts = [
    ['hero', '.hero'],
    ['cover', '.coverplate'],
    ['promise', '.promise'],
    ['reports', '.reports'],
    ['method', '#method'],
    ['products', '.products'],
    ['contact', '.contact'],
    ['footer', '.footer'],
  ];
  for (const [name, sel] of cuts) {
    const el = await page.$(sel);
    if (!el) { console.log('MISS', sel); continue; }
    await el.screenshot({ path: out + '/02-' + name + '.png', type: 'png' });
  }

  // Mobile
  const mob = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mob.goto('http://localhost:8199/docs/index.html', { waitUntil: 'networkidle' });
  await mob.screenshot({ path: out + '/03-mobile-top.png', fullPage: false });
  await mob.screenshot({ path: out + '/04-mobile-full.png', fullPage: true });

  await browser.close();
  console.log('done');
})();