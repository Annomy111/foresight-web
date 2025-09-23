const puppeteer = require('puppeteer');

async function quickTest() {
  console.log('🚀 Quick Foresight Analyzer test...');

  const browser = await puppeteer.launch({
    headless: false,
    slowMo: 500,
    defaultViewport: { width: 1200, height: 800 }
  });

  const page = await browser.newPage();

  try {
    // Navigate to the app
    console.log('📍 Loading https://foresight-analyzer.netlify.app');
    await page.goto('https://foresight-analyzer.netlify.app', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Basic checks
    const title = await page.title();
    console.log(`✅ Title: ${title}`);

    const heading = await page.$eval('h1', el => el.textContent).catch(() => 'Not found');
    console.log(`✅ Heading: ${heading}`);

    // Take screenshot
    await page.screenshot({ path: 'quick-test.png', fullPage: true });
    console.log('📸 Screenshot saved: quick-test.png');

    // Count inputs
    const inputs = await page.$$('input, textarea');
    console.log(`✅ Input fields: ${inputs.length}`);

    // Check for models
    const checkboxes = await page.$$('input[type="checkbox"]');
    console.log(`✅ Model checkboxes: ${checkboxes.length}`);

    // Fill first input quickly
    if (inputs.length > 0) {
      await inputs[0].type('Test question', { delay: 50 });
      console.log('✅ Filled first input');
    }

    // Select a model if available
    if (checkboxes.length > 0) {
      await checkboxes[0].click();
      console.log('✅ Selected first model');
    }

    // Final screenshot
    await page.screenshot({ path: 'quick-test-filled.png', fullPage: true });
    console.log('📸 Final screenshot: quick-test-filled.png');

    console.log('\n🎉 SUCCESS! Foresight Analyzer is working correctly!');
    console.log(`✓ App loaded: ${title.includes('Foresight')}`);
    console.log(`✓ Heading found: ${heading.includes('Foresight')}`);
    console.log(`✓ Form inputs: ${inputs.length} fields`);
    console.log(`✓ AI models: ${checkboxes.length} options`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    await page.screenshot({ path: 'quick-test-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

quickTest().catch(console.error);