# Foresight Analyzer - Comprehensive Test Suite

A complete testing framework for the AI-powered probabilistic forecasting platform.

## 🎯 Overview

This test suite provides comprehensive coverage for the Foresight Analyzer application including:

- **Unit Tests**: Jest-based testing for individual components and functions
- **E2E Tests**: Playwright-based end-to-end testing across real user journeys
- **API Tests**: Testing of Netlify serverless functions and backend integration
- **Performance Tests**: Lighthouse audits and Core Web Vitals monitoring
- **Load Tests**: Artillery-based stress testing and capacity planning
- **Accessibility Tests**: WCAG 2.1 AA compliance and inclusive design validation
- **Cross-browser Tests**: Compatibility testing across major browsers and devices

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- npm dependencies installed (`npm install`)
- Playwright browsers installed (`npm run playwright:install`)

### Running Tests

```bash
# Run all tests (comprehensive suite)
npm test

# Quick test run (skip load tests)
npm run test:quick

# CI-friendly test run
npm run test:ci

# Individual test suites
npm run test:unit          # Jest unit tests
npm run test:e2e           # Playwright E2E tests
npm run test:accessibility # Accessibility tests
npm run test:api           # API integration tests
npm run test:performance   # Lighthouse performance audit
npm run test:load          # Artillery load testing

# Development helpers
npm run test:watch         # Watch mode for unit tests
npm run test:coverage      # Coverage reporting
npm run playwright:ui      # Interactive Playwright UI
```

## 📁 Test Structure

```
tests/
├── accessibility/          # Accessibility testing with axe-core
│   └── accessibility.spec.ts
├── api/                    # API and backend testing
│   └── netlify-functions.test.ts
├── config/                 # Test configuration files
│   ├── jest.setup.js       # Jest setup and mocks
│   ├── global-setup.ts     # Playwright global setup
│   └── global-teardown.ts  # Playwright global teardown
├── e2e/                    # End-to-end tests
│   ├── homepage.spec.ts    # Homepage and UI components
│   ├── form-interactions.spec.ts  # Form validation and UX
│   └── user-journey.spec.ts       # Complete user workflows
├── performance/            # Performance and load testing
│   ├── artillery-load-test.yml    # Load testing configuration
│   └── lighthouse-audit.js        # Performance monitoring
├── reports/                # Generated test reports (auto-created)
├── runner/                 # Test orchestration
│   └── test-runner.js      # Main test runner and reporter
├── screenshots/            # Playwright screenshots (auto-created)
├── unit/                   # Unit tests
│   └── api.test.ts         # API client unit tests
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Set these environment variables for comprehensive testing:

```bash
# Testing target (defaults to production)
PLAYWRIGHT_BASE_URL=https://foresight-analyzer.netlify.app

# Lighthouse testing
LIGHTHOUSE_URL=https://foresight-analyzer.netlify.app

# API testing
NEXT_PUBLIC_API_URL=https://foresight-analyzer.netlify.app
```

### Test Configuration Files

- **`jest.config.js`**: Jest configuration with Next.js integration
- **`playwright.config.ts`**: Playwright E2E testing configuration
- **`tests/config/jest.setup.js`**: Global mocks and test utilities
- **`tests/performance/artillery-load-test.yml`**: Load testing scenarios

## 📊 Test Coverage Areas

### 🧪 Unit Tests (`tests/unit/`)

- API client functionality
- Utility functions
- Type safety and validation
- Error handling
- Mock data and test utilities

### 🎭 E2E Tests (`tests/e2e/`)

**Homepage & UI Components**:
- Page loading and rendering
- Responsive design validation
- Form field visibility and accessibility
- Navigation and interaction flows

**Form Interactions**:
- Input validation and error handling
- Model selection and configuration
- Keyboard navigation
- Special character and Unicode support

**User Journeys**:
- Complete forecasting workflows
- Multi-step form processes
- Real-time status updates
- Excel download functionality
- Error recovery scenarios
- Network interruption handling

### 🔌 API Tests (`tests/api/`)

- Netlify function endpoints
- Request/response validation
- Error handling and status codes
- Rate limiting and concurrency
- Data integrity and security
- CORS configuration

### ⚡ Performance Tests (`tests/performance/`)

**Lighthouse Audits**:
- Core Web Vitals (LCP, FID, CLS)
- Performance scoring
- Accessibility compliance
- Best practices validation
- SEO optimization

**Load Testing**:
- Concurrent user simulation
- API endpoint stress testing
- Error rate monitoring
- Response time analysis
- Resource utilization

### ♿ Accessibility Tests (`tests/accessibility/`)

- WCAG 2.1 AA compliance
- Screen reader compatibility
- Keyboard navigation
- Color contrast validation
- Focus management
- ARIA implementation
- High contrast mode support
- Reduced motion preferences

## 🎯 Key Testing Scenarios

### Critical User Paths

1. **Basic Forecasting Flow**:
   - Homepage load → Form completion → Model selection → Submission → Results

2. **Complex Geopolitical Forecast**:
   - Multi-model ensemble → Real-time progress → Excel export

3. **Error Handling**:
   - Network failures → Invalid inputs → API timeouts → Recovery

4. **Accessibility Journey**:
   - Screen reader navigation → Keyboard-only interaction → High contrast

### Performance Benchmarks

- **Page Load**: < 3 seconds on 3G
- **LCP**: < 2.5 seconds
- **CLS**: < 0.1
- **Accessibility**: 95+ score
- **Performance**: 90+ score
- **API Response**: < 5 seconds (95th percentile)

## 📈 Reporting

### Automated Reports

The test runner generates comprehensive reports in `tests/reports/`:

- **HTML Dashboard**: Visual test results with metrics
- **JSON Data**: Machine-readable test results
- **Lighthouse Reports**: Performance audit details
- **Artillery Reports**: Load testing analytics
- **Playwright Reports**: E2E test traces and screenshots

### Report Files

```
tests/reports/
├── test-report-[timestamp].html       # Main dashboard
├── test-results-[timestamp].json      # Raw test data
├── lighthouse-desktop-[timestamp].html # Performance audit
├── lighthouse-mobile-[timestamp].html  # Mobile performance
├── playwright-results.json             # E2E test results
├── artillery-results.json              # Load test results
└── coverage/                           # Code coverage reports
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run playwright:install
      - run: npm run test:ci
      - uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: tests/reports/
```

### Quality Gates

- ✅ All unit tests must pass
- ✅ E2E tests must pass on Chrome, Firefox, Safari
- ✅ Accessibility score ≥ 95
- ✅ Performance score ≥ 80
- ✅ API error rate < 5%
- ✅ Load test success rate > 95%

## 🛠️ Development Workflow

### Test-Driven Development

1. **Write Tests First**: Define expected behavior in tests
2. **Implement Feature**: Build functionality to pass tests
3. **Refactor**: Improve code while maintaining test coverage
4. **Validate**: Run full test suite before deployment

### Debugging Tests

```bash
# Debug specific test
npm run test:e2e -- --debug

# Run tests in headed mode
npm run test:e2e -- --headed

# Interactive testing
npm run playwright:ui

# Watch mode for development
npm run test:watch
```

### Adding New Tests

1. **Unit Tests**: Add to `tests/unit/[component].test.ts`
2. **E2E Tests**: Add to appropriate file in `tests/e2e/`
3. **API Tests**: Extend `tests/api/netlify-functions.test.ts`
4. **Performance**: Add scenarios to `artillery-load-test.yml`

## 🚨 Troubleshooting

### Common Issues

**Playwright browser issues**:
```bash
npm run playwright:install
```

**Timeout errors**:
- Increase timeout in `playwright.config.ts`
- Check network connectivity
- Verify application is accessible

**Lighthouse failures**:
- Ensure application is deployed and accessible
- Check for browser compatibility
- Verify network conditions

**Load test failures**:
- Check Artillery configuration
- Verify API endpoints are accessible
- Monitor server resources

### Getting Help

- Check test logs in `tests/reports/`
- Review Playwright traces for E2E failures
- Examine Lighthouse recommendations
- Analyze Artillery performance metrics

## 📚 Best Practices

### Writing Effective Tests

1. **Clear Test Names**: Describe expected behavior
2. **Isolated Tests**: Each test should be independent
3. **Realistic Data**: Use representative test data
4. **Error Scenarios**: Test both success and failure paths
5. **Performance Aware**: Consider test execution time

### Maintaining Tests

1. **Regular Updates**: Keep tests aligned with features
2. **Flaky Test Monitoring**: Address unstable tests promptly
3. **Coverage Goals**: Maintain high test coverage
4. **Performance Budgets**: Monitor and enforce performance thresholds

---

## 🎉 Success Metrics

With this comprehensive test suite, you can confidently:

- ✅ Deploy with 99.9% confidence
- ✅ Catch regressions before production
- ✅ Ensure accessibility compliance
- ✅ Monitor performance degradation
- ✅ Validate cross-browser compatibility
- ✅ Test under load conditions
- ✅ Maintain code quality standards

**Happy Testing! 🚀**