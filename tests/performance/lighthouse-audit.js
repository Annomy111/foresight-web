const lighthouse = require('lighthouse')
const chromeLauncher = require('chrome-launcher')
const fs = require('fs')
const path = require('path')

async function runLighthouseAudit() {
  const url = process.env.LIGHTHOUSE_URL || 'https://foresight-analyzer.netlify.app'

  console.log(`🔍 Running Lighthouse audit on: ${url}`)

  // Chrome launch options
  const chromeOptions = {
    chromeFlags: [
      '--headless',
      '--disable-gpu',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-features=TranslateUI'
    ]
  }

  // Lighthouse configuration
  const lighthouseConfig = {
    extends: 'lighthouse:default',
    settings: {
      // Audit settings
      onlyAudits: [
        'first-contentful-paint',
        'largest-contentful-paint',
        'cumulative-layout-shift',
        'first-input-delay',
        'speed-index',
        'total-blocking-time',
        'performance-budget',
        'accessibility',
        'best-practices',
        'seo',
        'interactive',
        'server-response-time',
        'render-blocking-resources',
        'unused-css-rules',
        'unused-javascript',
        'modern-image-formats',
        'efficient-animated-content',
        'uses-webp-images',
        'uses-optimized-images',
        'preload-lcp-image',
        'meta-description',
        'document-title',
        'viewport',
        'color-contrast',
        'tap-targets',
        'aria-labels',
        'button-name',
        'form-field-multiple-labels',
        'heading-order',
        'html-has-lang',
        'image-alt',
        'input-image-alt',
        'label',
        'link-name',
        'list',
        'listitem',
        'meta-refresh',
        'meta-viewport',
        'object-alt',
        'tabindex',
        'td-headers-attr',
        'th-has-data-cells',
        'valid-lang'
      ],

      // Performance budget
      budgets: [{
        resourceTypes: ['script', 'image', 'document', 'other'],
        resourceCounts: [30, 20, 1, 10],
        resourceSizes: [300, 500, 100, 200] // KB
      }],

      // Throttling settings for consistent results
      throttlingMethod: 'simulate',
      throttling: {
        rttMs: 150,
        throughputKbps: 1.6 * 1024,
        cpuSlowdownMultiplier: 4
      },

      // Emulation settings
      emulatedFormFactor: 'desktop',

      // Additional settings
      disableStorageReset: false,
      maxWaitForFcp: 30000,
      maxWaitForLoad: 45000
    }
  }

  // Mobile configuration
  const mobileConfig = {
    ...lighthouseConfig,
    settings: {
      ...lighthouseConfig.settings,
      emulatedFormFactor: 'mobile',
      throttling: {
        rttMs: 150,
        throughputKbps: 1.6 * 1024,
        cpuSlowdownMultiplier: 4
      }
    }
  }

  let chrome
  const results = []

  try {
    chrome = await chromeLauncher.launch(chromeOptions)
    const chromePort = chrome.port

    console.log('🖥️  Running desktop audit...')
    const desktopResult = await lighthouse(url, {
      port: chromePort,
      output: 'json',
      logLevel: 'info'
    }, lighthouseConfig)

    console.log('📱 Running mobile audit...')
    const mobileResult = await lighthouse(url, {
      port: chromePort,
      output: 'json',
      logLevel: 'info'
    }, mobileConfig)

    // Process and save results
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const reportsDir = path.join(__dirname, '../reports')

    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true })
    }

    // Save detailed reports
    fs.writeFileSync(
      path.join(reportsDir, `lighthouse-desktop-${timestamp}.json`),
      JSON.stringify(desktopResult.lhr, null, 2)
    )

    fs.writeFileSync(
      path.join(reportsDir, `lighthouse-mobile-${timestamp}.json`),
      JSON.stringify(mobileResult.lhr, null, 2)
    )

    // Generate HTML reports
    fs.writeFileSync(
      path.join(reportsDir, `lighthouse-desktop-${timestamp}.html`),
      desktopResult.report
    )

    fs.writeFileSync(
      path.join(reportsDir, `lighthouse-mobile-${timestamp}.html`),
      mobileResult.report
    )

    // Extract key metrics
    const extractMetrics = (result) => ({
      performance: result.lhr.categories.performance.score * 100,
      accessibility: result.lhr.categories.accessibility.score * 100,
      bestPractices: result.lhr.categories['best-practices'].score * 100,
      seo: result.lhr.categories.seo.score * 100,

      // Core Web Vitals
      firstContentfulPaint: result.lhr.audits['first-contentful-paint'].numericValue,
      largestContentfulPaint: result.lhr.audits['largest-contentful-paint'].numericValue,
      cumulativeLayoutShift: result.lhr.audits['cumulative-layout-shift'].numericValue,
      totalBlockingTime: result.lhr.audits['total-blocking-time'].numericValue,
      speedIndex: result.lhr.audits['speed-index'].numericValue,
      interactive: result.lhr.audits['interactive'].numericValue,

      // Additional metrics
      serverResponseTime: result.lhr.audits['server-response-time'].numericValue,
      renderBlockingResources: result.lhr.audits['render-blocking-resources'].details?.items?.length || 0,
      unusedCSS: result.lhr.audits['unused-css-rules'].details?.overallSavingsBytes || 0,
      unusedJavaScript: result.lhr.audits['unused-javascript'].details?.overallSavingsBytes || 0
    })

    const desktopMetrics = extractMetrics(desktopResult)
    const mobileMetrics = extractMetrics(mobileResult)

    // Performance thresholds
    const thresholds = {
      performance: 90,
      accessibility: 95,
      bestPractices: 90,
      seo: 90,
      firstContentfulPaint: 1500,
      largestContentfulPaint: 2500,
      cumulativeLayoutShift: 0.1,
      totalBlockingTime: 300,
      speedIndex: 3000,
      interactive: 3800,
      serverResponseTime: 600
    }

    // Check thresholds
    const checkThresholds = (metrics, device) => {
      const issues = []

      if (metrics.performance < thresholds.performance) {
        issues.push(`${device} Performance score: ${metrics.performance}% (threshold: ${thresholds.performance}%)`)
      }

      if (metrics.accessibility < thresholds.accessibility) {
        issues.push(`${device} Accessibility score: ${metrics.accessibility}% (threshold: ${thresholds.accessibility}%)`)
      }

      if (metrics.largestContentfulPaint > thresholds.largestContentfulPaint) {
        issues.push(`${device} LCP: ${metrics.largestContentfulPaint}ms (threshold: ${thresholds.largestContentfulPaint}ms)`)
      }

      if (metrics.cumulativeLayoutShift > thresholds.cumulativeLayoutShift) {
        issues.push(`${device} CLS: ${metrics.cumulativeLayoutShift} (threshold: ${thresholds.cumulativeLayoutShift})`)
      }

      if (metrics.totalBlockingTime > thresholds.totalBlockingTime) {
        issues.push(`${device} TBT: ${metrics.totalBlockingTime}ms (threshold: ${thresholds.totalBlockingTime}ms)`)
      }

      return issues
    }

    const desktopIssues = checkThresholds(desktopMetrics, 'Desktop')
    const mobileIssues = checkThresholds(mobileMetrics, 'Mobile')

    // Generate summary report
    const summary = {
      url,
      timestamp: new Date().toISOString(),
      desktop: desktopMetrics,
      mobile: mobileMetrics,
      issues: [...desktopIssues, ...mobileIssues],
      passed: desktopIssues.length === 0 && mobileIssues.length === 0
    }

    fs.writeFileSync(
      path.join(reportsDir, `lighthouse-summary-${timestamp}.json`),
      JSON.stringify(summary, null, 2)
    )

    // Console output
    console.log('\n🎯 LIGHTHOUSE AUDIT RESULTS')
    console.log('=' * 50)

    console.log('\n📊 DESKTOP SCORES:')
    console.log(`Performance: ${desktopMetrics.performance}%`)
    console.log(`Accessibility: ${desktopMetrics.accessibility}%`)
    console.log(`Best Practices: ${desktopMetrics.bestPractices}%`)
    console.log(`SEO: ${desktopMetrics.seo}%`)

    console.log('\n📱 MOBILE SCORES:')
    console.log(`Performance: ${mobileMetrics.performance}%`)
    console.log(`Accessibility: ${mobileMetrics.accessibility}%`)
    console.log(`Best Practices: ${mobileMetrics.bestPractices}%`)
    console.log(`SEO: ${mobileMetrics.seo}%`)

    console.log('\n⚡ CORE WEB VITALS (Desktop):')
    console.log(`FCP: ${Math.round(desktopMetrics.firstContentfulPaint)}ms`)
    console.log(`LCP: ${Math.round(desktopMetrics.largestContentfulPaint)}ms`)
    console.log(`CLS: ${desktopMetrics.cumulativeLayoutShift.toFixed(3)}`)
    console.log(`TBT: ${Math.round(desktopMetrics.totalBlockingTime)}ms`)

    console.log('\n📱 CORE WEB VITALS (Mobile):')
    console.log(`FCP: ${Math.round(mobileMetrics.firstContentfulPaint)}ms`)
    console.log(`LCP: ${Math.round(mobileMetrics.largestContentfulPaint)}ms`)
    console.log(`CLS: ${mobileMetrics.cumulativeLayoutShift.toFixed(3)}`)
    console.log(`TBT: ${Math.round(mobileMetrics.totalBlockingTime)}ms`)

    if (summary.issues.length > 0) {
      console.log('\n⚠️  PERFORMANCE ISSUES:')
      summary.issues.forEach(issue => console.log(`  - ${issue}`))
    } else {
      console.log('\n✅ All performance thresholds passed!')
    }

    console.log(`\n📁 Reports saved to: ${reportsDir}`)

    return summary

  } catch (error) {
    console.error('❌ Lighthouse audit failed:', error)
    throw error
  } finally {
    if (chrome) {
      await chrome.kill()
    }
  }
}

// Performance monitoring with multiple runs
async function runPerformanceMonitoring() {
  console.log('🔄 Running performance monitoring (3 runs for average)...')

  const results = []

  for (let i = 1; i <= 3; i++) {
    console.log(`\n📊 Run ${i}/3`)
    try {
      const result = await runLighthouseAudit()
      results.push(result)

      // Wait between runs
      if (i < 3) {
        console.log('⏳ Waiting 30 seconds before next run...')
        await new Promise(resolve => setTimeout(resolve, 30000))
      }
    } catch (error) {
      console.error(`Run ${i} failed:`, error.message)
    }
  }

  if (results.length > 0) {
    // Calculate averages
    const avgDesktop = {
      performance: results.reduce((sum, r) => sum + r.desktop.performance, 0) / results.length,
      accessibility: results.reduce((sum, r) => sum + r.desktop.accessibility, 0) / results.length,
      largestContentfulPaint: results.reduce((sum, r) => sum + r.desktop.largestContentfulPaint, 0) / results.length,
      cumulativeLayoutShift: results.reduce((sum, r) => sum + r.desktop.cumulativeLayoutShift, 0) / results.length
    }

    const avgMobile = {
      performance: results.reduce((sum, r) => sum + r.mobile.performance, 0) / results.length,
      accessibility: results.reduce((sum, r) => sum + r.mobile.accessibility, 0) / results.length,
      largestContentfulPaint: results.reduce((sum, r) => sum + r.mobile.largestContentfulPaint, 0) / results.length,
      cumulativeLayoutShift: results.reduce((sum, r) => sum + r.mobile.cumulativeLayoutShift, 0) / results.length
    }

    console.log('\n📈 AVERAGE RESULTS:')
    console.log(`Desktop Performance: ${avgDesktop.performance.toFixed(1)}%`)
    console.log(`Mobile Performance: ${avgMobile.performance.toFixed(1)}%`)
    console.log(`Desktop LCP: ${Math.round(avgDesktop.largestContentfulPaint)}ms`)
    console.log(`Mobile LCP: ${Math.round(avgMobile.largestContentfulPaint)}ms`)

    // Save averaged results
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    fs.writeFileSync(
      path.join(__dirname, '../reports', `lighthouse-averaged-${timestamp}.json`),
      JSON.stringify({
        averageDesktop: avgDesktop,
        averageMobile: avgMobile,
        individualResults: results,
        timestamp
      }, null, 2)
    )
  }

  return results
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2)
  const shouldRunMultiple = args.includes('--monitor')

  if (shouldRunMultiple) {
    runPerformanceMonitoring()
      .then(() => process.exit(0))
      .catch(() => process.exit(1))
  } else {
    runLighthouseAudit()
      .then(() => process.exit(0))
      .catch(() => process.exit(1))
  }
}

module.exports = { runLighthouseAudit, runPerformanceMonitoring }