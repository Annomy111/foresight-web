const { chromium } = require('playwright');

(async () => {
  console.log('Testing Excel Export functionality on live site...\n');

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    // Navigate to the app
    console.log('1. Navigating to https://foresight-analyzer.netlify.app');
    await page.goto('https://foresight-analyzer.netlify.app', { waitUntil: 'networkidle' });

    // Fill in the form
    console.log('2. Filling out forecast form...');
    await page.fill('textarea[placeholder*="Will there be a ceasefire"]',
      'Will AI significantly impact the job market by 2026?');
    await page.fill('textarea[placeholder*="Clarify what counts"]',
      'Significant means at least 20% of jobs transformed or automated');

    // Click generate forecast
    console.log('3. Clicking Generate Forecast button...');
    await page.click('button:has-text("Generate Forecast")');

    // Wait for results
    console.log('4. Waiting for forecast results...');
    await page.waitForSelector('text=Forecast Result', { timeout: 60000 });

    // Check if Download Excel button exists
    console.log('5. Checking for Download Excel button...');
    const excelButton = await page.locator('button:has-text("Download Excel")');
    const buttonExists = await excelButton.isVisible();

    if (buttonExists) {
      console.log('✅ Download Excel button is visible!');

      // Set up download handler
      const downloadPromise = page.waitForEvent('download');

      // Click the Excel button
      console.log('6. Clicking Download Excel button...');
      await excelButton.click();

      // Wait for download
      const download = await Promise.race([
        downloadPromise,
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Download timeout')), 10000)
        )
      ]).catch(err => null);

      if (download) {
        const fileName = download.suggestedFilename();
        console.log(`✅ Excel file download initiated: ${fileName}`);

        // Save the file
        const path = `/tmp/${fileName}`;
        await download.saveAs(path);
        console.log(`✅ File saved to: ${path}`);
      } else {
        console.log('⚠️  Download did not trigger - checking for errors...');

        // Check for toast messages
        const toastMessage = await page.locator('.go2072408551').textContent().catch(() => null);
        if (toastMessage) {
          console.log(`Toast message: ${toastMessage}`);
        }
      }
    } else {
      console.log('❌ Download Excel button not found!');
    }

    // Take a screenshot
    await page.screenshot({ path: '/tmp/excel-export-test.png' });
    console.log('\n📸 Screenshot saved to /tmp/excel-export-test.png');

  } catch (error) {
    console.error('Test failed:', error.message);
    await page.screenshot({ path: '/tmp/excel-export-error.png' });
  }

  await browser.close();
  console.log('\nTest complete!');
})();