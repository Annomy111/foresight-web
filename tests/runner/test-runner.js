#!/usr/bin/env node

const { execSync, spawn } = require('child_process')
const fs = require('fs')
const path = require('path')
const os = require('os')

class TestRunner {
  constructor() {
    this.startTime = Date.now()
    this.results = {
      summary: {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        duration: 0
      },
      suites: {},
      reports: []
    }
    this.reportsDir = path.join(__dirname, '../reports')
    this.ensureReportsDir()
  }

  ensureReportsDir() {
    if (!fs.existsSync(this.reportsDir)) {
      fs.mkdirSync(this.reportsDir, { recursive: true })
    }
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString()
    const prefix = level === 'error' ? '❌' : level === 'success' ? '✅' : level === 'warning' ? '⚠️' : 'ℹ️'
    console.log(`${prefix} [${timestamp}] ${message}`)
  }

  async runCommand(command, options = {}) {
    return new Promise((resolve, reject) => {
      const proc = spawn('sh', ['-c', command], {
        stdio: options.silent ? 'pipe' : 'inherit',
        cwd: options.cwd || process.cwd(),
        env: { ...process.env, ...options.env }
      })

      let stdout = ''
      let stderr = ''

      if (options.silent) {
        proc.stdout.on('data', (data) => stdout += data.toString())
        proc.stderr.on('data', (data) => stderr += data.toString())
      }

      proc.on('close', (code) => {
        if (code === 0) {
          resolve({ code, stdout, stderr })
        } else {
          reject({ code, stdout, stderr, command })
        }
      })

      proc.on('error', (error) => {
        reject({ error, command })
      })
    })
  }

  async runJestTests() {
    this.log('🧪 Running Jest unit tests...')

    try {
      const result = await this.runCommand('npm run test:unit -- --json --outputFile=tests/reports/jest-results.json', {
        silent: true
      })

      // Parse Jest results
      let jestResults = {}
      try {
        const resultsFile = path.join(this.reportsDir, 'jest-results.json')
        if (fs.existsSync(resultsFile)) {
          jestResults = JSON.parse(fs.readFileSync(resultsFile, 'utf8'))
        }
      } catch (error) {
        this.log(`Warning: Could not parse Jest results: ${error.message}`, 'warning')
      }

      this.results.suites.jest = {
        name: 'Jest Unit Tests',
        status: result.code === 0 ? 'passed' : 'failed',
        tests: jestResults.numTotalTests || 0,
        passed: jestResults.numPassedTests || 0,
        failed: jestResults.numFailedTests || 0,
        duration: jestResults.testResults?.reduce((acc, test) => acc + (test.perfStats?.end - test.perfStats?.start), 0) || 0
      }

      this.log(`Jest tests completed: ${this.results.suites.jest.passed}/${this.results.suites.jest.tests} passed`, 'success')

    } catch (error) {
      this.results.suites.jest = {
        name: 'Jest Unit Tests',
        status: 'failed',
        error: error.message || 'Jest tests failed',
        tests: 0,
        passed: 0,
        failed: 1
      }
      this.log(`Jest tests failed: ${error.message}`, 'error')
    }
  }

  async runPlaywrightTests() {
    this.log('🎭 Running Playwright E2E tests...')

    try {
      const result = await this.runCommand('npx playwright test --reporter=json', {
        silent: true,
        env: {
          PLAYWRIGHT_JSON_OUTPUT_NAME: path.join(this.reportsDir, 'playwright-results.json')
        }
      })

      // Parse Playwright results
      let playwrightResults = {}
      try {
        const resultsFile = path.join(this.reportsDir, 'playwright-results.json')
        if (fs.existsSync(resultsFile)) {
          playwrightResults = JSON.parse(fs.readFileSync(resultsFile, 'utf8'))
        }
      } catch (error) {
        this.log(`Warning: Could not parse Playwright results: ${error.message}`, 'warning')
      }

      const stats = playwrightResults.stats || {}
      this.results.suites.playwright = {
        name: 'Playwright E2E Tests',
        status: result.code === 0 ? 'passed' : 'failed',
        tests: stats.expected || 0,
        passed: stats.expected - (stats.unexpected || 0) - (stats.flaky || 0),
        failed: stats.unexpected || 0,
        skipped: stats.skipped || 0,
        duration: playwrightResults.duration || 0
      }

      this.log(`Playwright tests completed: ${this.results.suites.playwright.passed}/${this.results.suites.playwright.tests} passed`, 'success')

    } catch (error) {
      this.results.suites.playwright = {
        name: 'Playwright E2E Tests',
        status: 'failed',
        error: error.message || 'Playwright tests failed',
        tests: 0,
        passed: 0,
        failed: 1
      }
      this.log(`Playwright tests failed: ${error.message}`, 'error')
    }
  }

  async runAccessibilityTests() {
    this.log('♿ Running accessibility tests...')

    try {
      const result = await this.runCommand('npx playwright test tests/accessibility/ --reporter=json', {
        silent: true
      })

      this.results.suites.accessibility = {
        name: 'Accessibility Tests',
        status: result.code === 0 ? 'passed' : 'failed',
        tests: 1, // Placeholder - would parse actual results
        passed: result.code === 0 ? 1 : 0,
        failed: result.code === 0 ? 0 : 1
      }

      this.log(`Accessibility tests completed`, result.code === 0 ? 'success' : 'error')

    } catch (error) {
      this.results.suites.accessibility = {
        name: 'Accessibility Tests',
        status: 'failed',
        error: error.message || 'Accessibility tests failed',
        tests: 0,
        passed: 0,
        failed: 1
      }
      this.log(`Accessibility tests failed: ${error.message}`, 'error')
    }
  }

  async runPerformanceTests() {
    this.log('⚡ Running performance tests...')

    try {
      const lighthouseScript = path.join(__dirname, '../performance/lighthouse-audit.js')
      const result = await this.runCommand(`node "${lighthouseScript}"`, {
        silent: true
      })

      // Check for Lighthouse results
      const lighthouseFiles = fs.readdirSync(this.reportsDir)
        .filter(file => file.startsWith('lighthouse-summary-'))
        .sort()
        .slice(-1) // Get the latest

      let performanceScore = 0
      if (lighthouseFiles.length > 0) {
        try {
          const lighthouseData = JSON.parse(
            fs.readFileSync(path.join(this.reportsDir, lighthouseFiles[0]), 'utf8')
          )
          performanceScore = Math.min(lighthouseData.desktop.performance, lighthouseData.mobile.performance)
        } catch (error) {
          this.log(`Warning: Could not parse Lighthouse results: ${error.message}`, 'warning')
        }
      }

      this.results.suites.performance = {
        name: 'Performance Tests',
        status: performanceScore >= 80 ? 'passed' : 'failed',
        score: performanceScore,
        tests: 1,
        passed: performanceScore >= 80 ? 1 : 0,
        failed: performanceScore >= 80 ? 0 : 1
      }

      this.log(`Performance tests completed: Score ${performanceScore}%`, performanceScore >= 80 ? 'success' : 'warning')

    } catch (error) {
      this.results.suites.performance = {
        name: 'Performance Tests',
        status: 'failed',
        error: error.message || 'Performance tests failed',
        tests: 0,
        passed: 0,
        failed: 1
      }
      this.log(`Performance tests failed: ${error.message}`, 'error')
    }
  }

  async runLoadTests() {
    this.log('🔄 Running load tests...')

    try {
      const artilleryConfig = path.join(__dirname, '../performance/artillery-load-test.yml')
      const result = await this.runCommand(`npx artillery run "${artilleryConfig}" --output ${this.reportsDir}/artillery-results.json`, {
        silent: true
      })

      // Parse Artillery results
      let loadTestResults = {}
      try {
        const resultsFile = path.join(this.reportsDir, 'artillery-results.json')
        if (fs.existsSync(resultsFile)) {
          loadTestResults = JSON.parse(fs.readFileSync(resultsFile, 'utf8'))
        }
      } catch (error) {
        this.log(`Warning: Could not parse Artillery results: ${error.message}`, 'warning')
      }

      const aggregate = loadTestResults.aggregate || {}
      const errorRate = (aggregate.errors || 0) / (aggregate.requestsCompleted || 1) * 100

      this.results.suites.loadTest = {
        name: 'Load Tests',
        status: errorRate < 5 ? 'passed' : 'failed',
        errorRate: errorRate.toFixed(2),
        requests: aggregate.requestsCompleted || 0,
        tests: 1,
        passed: errorRate < 5 ? 1 : 0,
        failed: errorRate < 5 ? 0 : 1
      }

      this.log(`Load tests completed: ${errorRate.toFixed(2)}% error rate`, errorRate < 5 ? 'success' : 'warning')

    } catch (error) {
      this.results.suites.loadTest = {
        name: 'Load Tests',
        status: 'failed',
        error: error.message || 'Load tests failed',
        tests: 0,
        passed: 0,
        failed: 1
      }
      this.log(`Load tests failed: ${error.message}`, 'error')
    }
  }

  calculateSummary() {
    let total = 0, passed = 0, failed = 0, skipped = 0

    Object.values(this.results.suites).forEach(suite => {
      total += suite.tests || 0
      passed += suite.passed || 0
      failed += suite.failed || 0
      skipped += suite.skipped || 0
    })

    this.results.summary = {
      total,
      passed,
      failed,
      skipped,
      duration: Date.now() - this.startTime,
      success: failed === 0
    }
  }

  generateHTMLReport() {
    const timestamp = new Date().toISOString()
    const duration = this.results.summary.duration

    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Foresight Analyzer Test Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }
        .header p { margin: 10px 0 0; opacity: 0.9; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; background: #fafafa; }
        .metric { text-align: center; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
        .metric-label { color: #666; text-transform: uppercase; font-size: 0.9em; letter-spacing: 0.5px; }
        .passed { color: #4CAF50; }
        .failed { color: #f44336; }
        .skipped { color: #FF9800; }
        .suites { padding: 30px; }
        .suite { margin-bottom: 30px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
        .suite-header { background: #f8f9fa; padding: 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
        .suite-name { font-size: 1.2em; font-weight: 600; }
        .suite-status { padding: 6px 12px; border-radius: 20px; font-size: 0.9em; font-weight: 500; }
        .status-passed { background: #e8f5e8; color: #2e7d2e; }
        .status-failed { background: #ffeaea; color: #d32f2f; }
        .suite-details { padding: 20px; }
        .suite-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 15px; }
        .stat { text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; }
        .stat-label { color: #666; font-size: 0.9em; }
        .error-details { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin-top: 15px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; border-top: 1px solid #e0e0e0; }
        @media (max-width: 768px) {
            .summary { grid-template-columns: 1fr 1fr; }
            .suite-header { flex-direction: column; align-items: flex-start; gap: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Foresight Analyzer Test Report</h1>
            <p>Comprehensive test results for the AI-powered forecasting platform</p>
            <p>Generated: ${new Date(timestamp).toLocaleString()}</p>
        </div>

        <div class="summary">
            <div class="metric">
                <div class="metric-value">${this.results.summary.total}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value passed">${this.results.summary.passed}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value failed">${this.results.summary.failed}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value skipped">${this.results.summary.skipped}</div>
                <div class="metric-label">Skipped</div>
            </div>
            <div class="metric">
                <div class="metric-value">${Math.round(duration / 1000)}s</div>
                <div class="metric-label">Duration</div>
            </div>
            <div class="metric">
                <div class="metric-value ${this.results.summary.success ? 'passed' : 'failed'}">
                    ${this.results.summary.success ? '✅' : '❌'}
                </div>
                <div class="metric-label">Overall</div>
            </div>
        </div>

        <div class="suites">
            <h2>Test Suite Results</h2>
            ${Object.entries(this.results.suites).map(([key, suite]) => `
                <div class="suite">
                    <div class="suite-header">
                        <span class="suite-name">${suite.name}</span>
                        <span class="suite-status status-${suite.status}">${suite.status.toUpperCase()}</span>
                    </div>
                    <div class="suite-details">
                        <div class="suite-stats">
                            <div class="stat">
                                <div class="stat-value">${suite.tests || 0}</div>
                                <div class="stat-label">Tests</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value passed">${suite.passed || 0}</div>
                                <div class="stat-label">Passed</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value failed">${suite.failed || 0}</div>
                                <div class="stat-label">Failed</div>
                            </div>
                            ${suite.score !== undefined ? `
                                <div class="stat">
                                    <div class="stat-value">${suite.score}%</div>
                                    <div class="stat-label">Score</div>
                                </div>
                            ` : ''}
                            ${suite.errorRate !== undefined ? `
                                <div class="stat">
                                    <div class="stat-value">${suite.errorRate}%</div>
                                    <div class="stat-label">Error Rate</div>
                                </div>
                            ` : ''}
                            ${suite.duration ? `
                                <div class="stat">
                                    <div class="stat-value">${Math.round(suite.duration / 1000)}s</div>
                                    <div class="stat-label">Duration</div>
                                </div>
                            ` : ''}
                        </div>
                        ${suite.error ? `
                            <div class="error-details">
                                <strong>Error:</strong> ${suite.error}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
        </div>

        <div class="footer">
            <p>🤖 Generated by Foresight Analyzer Test Suite</p>
            <p>Platform: ${os.platform()} | Node.js: ${process.version} | Time: ${new Date().toISOString()}</p>
        </div>
    </div>
</body>
</html>
    `

    const reportPath = path.join(this.reportsDir, `test-report-${Date.now()}.html`)
    fs.writeFileSync(reportPath, html.trim())
    this.log(`HTML report generated: ${reportPath}`, 'success')

    return reportPath
  }

  async run(options = {}) {
    this.log('🚀 Starting comprehensive test suite for Foresight Analyzer')

    // Run test suites
    if (!options.skip?.includes('unit')) {
      await this.runJestTests()
    }

    if (!options.skip?.includes('e2e')) {
      await this.runPlaywrightTests()
    }

    if (!options.skip?.includes('accessibility')) {
      await this.runAccessibilityTests()
    }

    if (!options.skip?.includes('performance')) {
      await this.runPerformanceTests()
    }

    if (!options.skip?.includes('load') && !options.quick) {
      await this.runLoadTests()
    }

    // Calculate summary
    this.calculateSummary()

    // Generate reports
    const reportPath = this.generateHTMLReport()

    // Save JSON results
    const jsonReportPath = path.join(this.reportsDir, `test-results-${Date.now()}.json`)
    fs.writeFileSync(jsonReportPath, JSON.stringify(this.results, null, 2))

    // Final summary
    this.log('📊 Test Summary:')
    this.log(`   Total: ${this.results.summary.total}`)
    this.log(`   Passed: ${this.results.summary.passed}`, 'success')
    this.log(`   Failed: ${this.results.summary.failed}`, this.results.summary.failed > 0 ? 'error' : 'info')
    this.log(`   Duration: ${Math.round(this.results.summary.duration / 1000)}s`)
    this.log(`   Overall: ${this.results.summary.success ? 'PASSED' : 'FAILED'}`, this.results.summary.success ? 'success' : 'error')

    this.log(`📄 Reports:`)
    this.log(`   HTML: ${reportPath}`)
    this.log(`   JSON: ${jsonReportPath}`)

    return this.results.summary.success
  }
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2)
  const options = {
    quick: args.includes('--quick'),
    skip: []
  }

  // Parse skip options
  const skipIndex = args.findIndex(arg => arg === '--skip')
  if (skipIndex !== -1 && args[skipIndex + 1]) {
    options.skip = args[skipIndex + 1].split(',')
  }

  const runner = new TestRunner()
  runner.run(options)
    .then(success => {
      process.exit(success ? 0 : 1)
    })
    .catch(error => {
      console.error('❌ Test runner failed:', error)
      process.exit(1)
    })
}

module.exports = TestRunner