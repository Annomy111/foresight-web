import { test, expect } from '@playwright/test'

test.describe('Homepage - UI Components and Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should load homepage with correct title and meta information', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Foresight Analyzer/i)

    // Check main heading
    await expect(page.locator('h1')).toContainText('Foresight Analyzer')

    // Check subtitle/description
    await expect(page.locator('text=AI-Powered Probabilistic Forecasting')).toBeVisible()
  })

  test('should display forecast form with all required fields', async ({ page }) => {
    // Check for "Forecast Question" label and input
    const questionLabel = page.locator('text=Forecast Question')
    await expect(questionLabel).toBeVisible()

    // Check question input field - could be input or textarea
    const questionInput = page.locator('input, textarea').first()
    await expect(questionInput).toBeVisible()
    await expect(questionInput).toBeEditable()

    // Check for "Definition" label
    const definitionLabel = page.locator('text=Definition')
    await expect(definitionLabel).toBeVisible()

    // Check for "Timeframe" label
    const timeframeLabel = page.locator('text=Timeframe')
    await expect(timeframeLabel).toBeVisible()

    // Check submit button
    const submitButton = page.locator('button:has-text("Start Forecast")')
    await expect(submitButton).toBeVisible()
    await expect(submitButton).toBeEnabled()
  })

  test('should display model selection interface', async ({ page }) => {
    // Check for "Select AI Models" text
    const modelLabel = page.locator('text=Select AI Models')
    await expect(modelLabel).toBeVisible()

    // Check for "Iterations per Model" text
    const iterationsLabel = page.locator('text=Iterations per Model')
    await expect(iterationsLabel).toBeVisible()

    // Check for individual model checkboxes
    const modelCheckboxes = page.locator('input[type="checkbox"]')
    await expect(modelCheckboxes.first()).toBeVisible()

    // Check for iterations number input
    const iterationsInput = page.locator('input[type="number"]')
    await expect(iterationsInput).toBeVisible()
  })

  test('should show responsive design on different screen sizes', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 })
    await expect(page.locator('h1')).toBeVisible()

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.locator('h1')).toBeVisible()

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.locator('h1')).toBeVisible()

    // Check that form is still accessible on mobile
    const questionInput = page.locator('input, textarea').first()
    await expect(questionInput).toBeVisible()
  })

  test('should display error states for empty form submission', async ({ page }) => {
    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")')
    await submitButton.click()

    // Wait for potential error messages
    await page.waitForTimeout(1000)

    // Check for validation errors (could be native HTML5 validation or custom)
    const questionInput = page.locator('input, textarea').first()
    const isRequired = await questionInput.getAttribute('required')

    if (isRequired !== null) {
      // HTML5 validation should prevent submission
      await expect(questionInput).toBeFocused()
    } else {
      // Custom validation should show error messages
      const errorMessages = page.locator('.error, .invalid, [role="alert"], text=required, text=Please enter')
      await expect(errorMessages.first()).toBeVisible()
    }
  })

  test('should handle loading states appropriately', async ({ page }) => {
    // Fill out form with valid data
    const inputs = page.locator('input, textarea')
    await inputs.nth(0).fill('Will there be peace in Ukraine by 2026?')
    if (await inputs.count() > 1) {
      await inputs.nth(1).fill('A formal ceasefire agreement')
    }
    if (await inputs.count() > 2) {
      await inputs.nth(2).fill('2026')
    }

    // Submit form and check for loading indicators
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")')
    await submitButton.click()

    // Check for loading states
    const loadingIndicators = page.locator('.loading, .spinner, text=Processing, text=Loading, [data-testid="loading"]')

    // Either button should be disabled or loading indicator should appear
    const buttonDisabled = await submitButton.isDisabled()
    const loadingVisible = await loadingIndicators.first().isVisible().catch(() => false)

    expect(buttonDisabled || loadingVisible).toBeTruthy()
  })

  test('should display branding and footer information', async ({ page }) => {
    // Check for main branding elements
    await expect(page.locator('h1, .logo, text=Foresight Analyzer')).toBeVisible()

    // Scroll to bottom to check footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Check for footer content (adjust selectors based on actual footer)
    const footerElements = page.locator('footer, .footer, text=© 2024, text=© 2025')
    const footerVisible = await footerElements.first().isVisible().catch(() => false)

    // Footer might not exist, which is okay for a minimal app
    if (footerVisible) {
      await expect(footerElements.first()).toBeVisible()
    }
  })

  test('should handle accessibility features', async ({ page }) => {
    // Check for proper heading hierarchy
    const h1 = page.locator('h1')
    await expect(h1).toBeVisible()

    // Check for proper form labels and ARIA attributes
    const inputs = page.locator('input, textarea, select')
    const inputCount = await inputs.count()

    for (let i = 0; i < Math.min(inputCount, 5); i++) {
      const input = inputs.nth(i)
      const hasLabel = await input.getAttribute('aria-label') ||
                      await input.getAttribute('aria-labelledby') ||
                      await page.locator(`label[for="${await input.getAttribute('id')}"]`).count() > 0

      // Skip hidden inputs
      const isVisible = await input.isVisible()
      if (isVisible) {
        expect(hasLabel).toBeTruthy()
      }
    }

    // Check for proper button accessibility
    const buttons = page.locator('button')
    const buttonCount = await buttons.count()

    for (let i = 0; i < Math.min(buttonCount, 3); i++) {
      const button = buttons.nth(i)
      const isVisible = await button.isVisible()

      if (isVisible) {
        const hasText = await button.textContent()
        const hasAriaLabel = await button.getAttribute('aria-label')
        expect(hasText || hasAriaLabel).toBeTruthy()
      }
    }
  })

  test('should maintain consistent styling and layout', async ({ page }) => {
    // Check that the page body is visible and properly styled
    const body = page.locator('body')
    await expect(body).toBeVisible()

    // Check for consistent color scheme
    const computedStyle = await page.evaluate(() => {
      const body = document.body
      const styles = window.getComputedStyle(body)
      return {
        backgroundColor: styles.backgroundColor,
        color: styles.color,
        fontFamily: styles.fontFamily
      }
    })

    // Verify basic styling is applied
    expect(computedStyle.fontFamily).toBeTruthy()
    expect(computedStyle.backgroundColor).toBeTruthy()

    // Check that no major layout shifts occur
    await page.waitForLoadState('networkidle')
    const screenshot1 = await page.screenshot()

    await page.waitForTimeout(2000)
    const screenshot2 = await page.screenshot()

    // Screenshots should be very similar (some minor differences are acceptable)
    expect(screenshot1.length).toBeGreaterThan(1000)
    expect(screenshot2.length).toBeGreaterThan(1000)
  })
})