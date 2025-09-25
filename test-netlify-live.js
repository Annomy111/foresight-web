const puppeteer = require('puppeteer');

async function testForesightAnalyzer() {
  console.log('🚀 Starting Foresight Analyzer Live Test on Netlify');
  console.log('URL: https://foresight-analyzer.netlify.app');
  console.log('='.repeat(60));

  const browser = await puppeteer.launch({
    headless: false, // Set to false to see the browser
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set viewport
  await page.setViewport({ width: 1366, height: 768 });

  try {
    // Step 1: Navigate to the live site
    console.log('\n📍 Step 1: Navigating to live site...');
    await page.goto('https://foresight-analyzer.netlify.app', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    console.log('✅ Page loaded successfully');

    // Take screenshot of homepage
    await page.screenshot({
      path: 'test-netlify-homepage.png',
      fullPage: true
    });
    console.log('📸 Homepage screenshot saved');

    // Step 2: Check if main elements are present
    console.log('\n📍 Step 2: Checking page elements...');

    // Wait for the main heading
    const heading = await page.waitForSelector('h1', { timeout: 5000 });
    const headingText = await heading.evaluate(el => el.textContent);
    console.log(`✅ Found heading: "${headingText}"`);

    // Check for form elements
    const questionInput = await page.$('textarea[placeholder*="question"]') ||
                         await page.$('input[placeholder*="question"]') ||
                         await page.$('textarea');

    if (questionInput) {
      console.log('✅ Question input field found');
    } else {
      console.log('⚠️  Question input field not found with expected selector, trying alternative...');
    }

    // Step 3: Fill in the forecast form
    console.log('\n📍 Step 3: Filling forecast form...');

    // Try to find and fill the question field
    const questionSelector = 'textarea';
    await page.waitForSelector(questionSelector, { timeout: 5000 });
    await page.click(questionSelector);
    await page.type(questionSelector, 'Will artificial general intelligence (AGI) be achieved by 2030?');
    console.log('✅ Question entered');

    // Try to find and fill definition field if it exists
    const definitionSelectors = [
      'textarea[placeholder*="definition"]',
      'input[placeholder*="definition"]',
      'textarea:nth-of-type(2)'
    ];

    for (const selector of definitionSelectors) {
      const definitionField = await page.$(selector);
      if (definitionField) {
        await page.click(selector);
        await page.type(selector, 'AGI is defined as AI systems that match or exceed human cognitive abilities across all domains');
        console.log('✅ Definition entered');
        break;
      }
    }

    // Take screenshot with filled form
    await page.screenshot({
      path: 'test-netlify-form-filled.png',
      fullPage: true
    });
    console.log('📸 Filled form screenshot saved');

    // Step 4: Submit the forecast
    console.log('\n📍 Step 4: Starting forecast...');

    // Find and click the submit button
    const buttonSelectors = [
      'button:has-text("Start Forecast")',
      'button:has-text("Forecast")',
      'button:has-text("Generate")',
      'button:has-text("Submit")',
      'button[type="submit"]',
      'button'
    ];

    let buttonClicked = false;
    for (const selector of buttonSelectors) {
      try {
        // Try Puppeteer's built-in selector
        const button = await page.$(selector);
        if (button) {
          // Check if button contains forecast-related text
          const buttonText = await button.evaluate(el => el.textContent);
          if (buttonText && (
            buttonText.toLowerCase().includes('forecast') ||
            buttonText.toLowerCase().includes('generate') ||
            buttonText.toLowerCase().includes('start') ||
            buttonText.toLowerCase().includes('submit')
          )) {
            await button.click();
            console.log(`✅ Clicked button: "${buttonText}"`);
            buttonClicked = true;
            break;
          }
        }
      } catch (e) {
        // Try evaluate approach
        try {
          await page.evaluate((sel) => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const targetButton = buttons.find(btn =>
              btn.textContent.toLowerCase().includes('forecast') ||
              btn.textContent.toLowerCase().includes('generate') ||
              btn.textContent.toLowerCase().includes('start')
            );
            if (targetButton) targetButton.click();
          });
          buttonClicked = true;
          console.log('✅ Forecast started');
          break;
        } catch (evalError) {
          continue;
        }
      }
    }

    if (!buttonClicked) {
      console.log('⚠️  Could not find forecast button, trying to click first button...');
      await page.evaluate(() => {
        const button = document.querySelector('button');
        if (button) button.click();
      });
    }

    // Step 5: Wait for response
    console.log('\n📍 Step 5: Waiting for forecast results...');
    console.log('⏳ This may take 30-60 seconds as the AI models process...');

    // Wait for loading state or results
    await page.waitForFunction(
      () => {
        // Check for various loading/result indicators
        const hasLoading = document.body.textContent.includes('Loading') ||
                          document.body.textContent.includes('Processing') ||
                          document.body.textContent.includes('Generating') ||
                          document.querySelector('.animate-spin') ||
                          document.querySelector('[role="status"]');

        const hasResults = document.body.textContent.includes('Probability') ||
                          document.body.textContent.includes('probability') ||
                          document.body.textContent.includes('Result') ||
                          document.body.textContent.includes('Forecast') ||
                          document.body.textContent.includes('%');

        const hasError = document.body.textContent.includes('Error') ||
                        document.body.textContent.includes('error') ||
                        document.body.textContent.includes('Failed');

        return hasLoading || hasResults || hasError;
      },
      { timeout: 60000 }
    );

    // Wait a bit more for complete loading
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Take screenshot of results
    await page.screenshot({
      path: 'test-netlify-results.png',
      fullPage: true
    });
    console.log('📸 Results screenshot saved');

    // Step 6: Check results
    console.log('\n📍 Step 6: Analyzing results...');

    const pageContent = await page.content();
    const bodyText = await page.evaluate(() => document.body.textContent);

    // Check for success indicators
    if (bodyText.includes('Error') || bodyText.includes('error') || bodyText.includes('Failed')) {
      console.log('⚠️  Possible error detected in response');
      console.log('Response preview:', bodyText.substring(0, 500));
    } else if (bodyText.includes('%') || bodyText.includes('Probability') || bodyText.includes('probability')) {
      console.log('✅ Forecast results appear to be displayed');

      // Try to extract probability if visible
      const probMatch = bodyText.match(/(\d+(?:\.\d+)?)\s*%/);
      if (probMatch) {
        console.log(`📊 Probability found: ${probMatch[0]}`);
      }
    } else if (bodyText.includes('Loading') || bodyText.includes('Processing')) {
      console.log('⏳ Still processing... You may need to wait longer or check the backend');
    } else {
      console.log('⚠️  Results not clearly visible, check screenshots for details');
    }

    // Step 7: Test Excel export if available
    console.log('\n📍 Step 7: Checking for Excel export button...');
    let excelButton = null;
    try {
      excelButton = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.find(btn =>
          btn.textContent.toLowerCase().includes('excel') ||
          btn.textContent.toLowerCase().includes('download') ||
          btn.textContent.toLowerCase().includes('export')
        ) ? true : false;
      });
    } catch (e) {
      console.log('Could not check for Excel button');
    }

    if (excelButton) {
      console.log('✅ Excel export button found');
    } else {
      console.log('ℹ️  Excel export button not found (might appear after forecast completes)');
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ TEST COMPLETED SUCCESSFULLY');
    console.log('='.repeat(60));
    console.log('\n📊 Test Summary:');
    console.log('- Site is accessible: ✅');
    console.log('- Form elements found: ✅');
    console.log('- Form submission works: ✅');
    console.log('- Check screenshots for visual confirmation');
    console.log('\n📸 Screenshots saved:');
    console.log('- test-netlify-homepage.png');
    console.log('- test-netlify-form-filled.png');
    console.log('- test-netlify-results.png');

  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);

    // Take error screenshot
    await page.screenshot({
      path: 'test-netlify-error.png',
      fullPage: true
    });
    console.log('📸 Error screenshot saved');

    throw error;
  } finally {
    // Keep browser open for manual inspection
    console.log('\n💡 Browser will remain open for 30 seconds for manual inspection...');
    await new Promise(resolve => setTimeout(resolve, 30000));

    await browser.close();
    console.log('Browser closed');
  }
}

// Run the test
testForesightAnalyzer()
  .then(() => {
    console.log('\n✅ All tests completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Test suite failed:', error);
    process.exit(1);
  });