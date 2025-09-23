import { test, expect } from '@playwright/test'

test.describe('Form Interactions and Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should handle basic form input validation', async ({ page }) => {
    // Locate form fields
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()

    // Test empty form submission
    await submitButton.click()

    // Check for validation (either HTML5 or custom)
    const questionRequired = await questionField.getAttribute('required')
    if (questionRequired !== null) {
      // HTML5 validation should focus the first invalid field
      await expect(questionField).toBeFocused()
    } else {
      // Custom validation should show error messages
      await page.waitForTimeout(1000)
      const errorMessages = page.locator('.error, .invalid, [role="alert"]')
      const hasErrors = await errorMessages.count() > 0
      expect(hasErrors).toBeTruthy()
    }

    // Test partial form completion
    await questionField.fill('Test question?')
    await submitButton.click()

    // Should still show validation for missing fields
    await page.waitForTimeout(500)
    const definitionRequired = await definitionField.getAttribute('required')
    if (definitionRequired !== null) {
      await expect(definitionField).toBeFocused()
    }
  })

  test('should accept valid form input and submit successfully', async ({ page }) => {
    // Fill out complete form
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

    await questionField.fill('Will there be a ceasefire agreement between Russia and Ukraine by March 31, 2026?')
    await definitionField.fill('A formal agreement to stop fighting, signed by both governments')
    await timeframeField.fill('2026-03-31')

    // Submit form
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
    await submitButton.click()

    // Should show loading state or transition to results
    await page.waitForTimeout(2000)

    // Check for either loading indicators or results
    const loadingIndicator = page.locator('.loading, .spinner, text=Processing, text=Loading')
    const resultsSection = page.locator('.results, .forecast-results, text=Progress, text=Ensemble')
    const errorMessage = page.locator('.error, text=Error, text=Failed')

    const hasLoading = await loadingIndicator.first().isVisible().catch(() => false)
    const hasResults = await resultsSection.first().isVisible().catch(() => false)
    const hasError = await errorMessage.first().isVisible().catch(() => false)

    // Should either be loading or showing results (not error)
    expect(hasLoading || hasResults).toBeTruthy()
    expect(hasError).toBeFalsy()
  })

  test('should handle model selection properly', async ({ page }) => {
    // Look for model selection controls
    const modelCheckboxes = page.locator('input[type="checkbox"][data-model], input[type="checkbox"] + label')
    const modelButtons = page.locator('button[data-model], .model-selector button')
    const modelSelect = page.locator('select[data-models], select option[value*="grok"], select option[value*="deepseek"]')

    const checkboxCount = await modelCheckboxes.count()
    const buttonCount = await modelButtons.count()
    const selectCount = await modelSelect.count()

    if (checkboxCount > 0) {
      // Test checkbox-based model selection
      const firstCheckbox = modelCheckboxes.first()
      await expect(firstCheckbox).toBeVisible()

      // Check if any models are pre-selected
      const isChecked = await firstCheckbox.isChecked()

      // Toggle selection
      await firstCheckbox.click()
      const newState = await firstCheckbox.isChecked()
      expect(newState).toBe(!isChecked)

      // Ensure at least one model is selected before proceeding
      if (!newState) {
        // If we unchecked the only one, check another one
        if (checkboxCount > 1) {
          await modelCheckboxes.nth(1).click()
        } else {
          await firstCheckbox.click() // Re-check the first one
        }
      }
    } else if (buttonCount > 0) {
      // Test button-based model selection
      const firstButton = modelButtons.first()
      await expect(firstButton).toBeVisible()
      await firstButton.click()
    } else if (selectCount > 0) {
      // Test select-based model selection
      const selectElement = modelSelect.first()
      await expect(selectElement).toBeVisible()
      await selectElement.selectOption({ index: 1 })
    }

    // Test iterations per model setting
    const iterationsInput = page.locator('input[type="number"], input[placeholder*="iteration"], [data-testid="iterations"]')
    if (await iterationsInput.count() > 0) {
      await iterationsInput.first().fill('2')
      const value = await iterationsInput.first().inputValue()
      expect(value).toBe('2')
    }
  })

  test('should handle character limits and input validation', async ({ page }) => {
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()

    // Test very long input
    const longText = 'A'.repeat(5000)
    await questionField.fill(longText)

    const questionValue = await questionField.inputValue()

    // Check if there's a character limit
    const maxLength = await questionField.getAttribute('maxlength')
    if (maxLength) {
      expect(questionValue.length).toBeLessThanOrEqual(parseInt(maxLength))
    }

    // Test special characters
    const specialText = 'Question with special chars: @#$%^&*()[]{}|\\:";\'<>?,./'
    await definitionField.fill(specialText)
    const definitionValue = await definitionField.inputValue()
    expect(definitionValue).toContain('special chars')

    // Test Unicode characters
    const unicodeText = 'Question with émojis 😀 and ünïcödé characters'
    await questionField.fill(unicodeText)
    const unicodeValue = await questionField.inputValue()
    expect(unicodeValue).toContain('émojis')
  })

  test('should maintain form state during interactions', async ({ page }) => {
    // Fill out form
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

    const testQuestion = 'Will there be peace in Ukraine?'
    const testDefinition = 'A formal peace treaty'
    const testTimeframe = '2026'

    await questionField.fill(testQuestion)
    await definitionField.fill(testDefinition)
    await timeframeField.fill(testTimeframe)

    // Interact with other parts of the page
    await page.click('h1') // Click on heading
    await page.keyboard.press('Tab') // Navigate with keyboard

    // Verify form values are maintained
    expect(await questionField.inputValue()).toBe(testQuestion)
    expect(await definitionField.inputValue()).toBe(testDefinition)
    expect(await timeframeField.inputValue()).toBe(testTimeframe)

    // Test form persistence after page interactions
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.evaluate(() => window.scrollTo(0, 0))

    // Values should still be there
    expect(await questionField.inputValue()).toBe(testQuestion)
    expect(await definitionField.inputValue()).toBe(testDefinition)
    expect(await timeframeField.inputValue()).toBe(testTimeframe)
  })

  test('should handle keyboard navigation properly', async ({ page }) => {
    // Start from question field
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    await questionField.focus()
    await expect(questionField).toBeFocused()

    // Tab through form fields
    await page.keyboard.press('Tab')

    // Should move to definition field
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

    // One of these should be focused after tab
    const definitionFocused = await definitionField.isVisible() && await definitionField.evaluate(el => el === document.activeElement)
    const timeframeFocused = await timeframeField.isVisible() && await timeframeField.evaluate(el => el === document.activeElement)

    expect(definitionFocused || timeframeFocused).toBeTruthy()

    // Continue tabbing to submit button
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
    const submitFocused = await submitButton.evaluate(el => el === document.activeElement).catch(() => false)

    // Submit button should eventually receive focus
    if (!submitFocused) {
      // Try a few more tabs
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
    }
  })

  test('should handle form submission with Enter key', async ({ page }) => {
    // Fill out form
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

    await questionField.fill('Test question for Enter key submission')
    await definitionField.fill('Test definition')
    await timeframeField.fill('2026')

    // Try submitting with Enter key from timeframe field
    await timeframeField.focus()
    await page.keyboard.press('Enter')

    // Should trigger form submission
    await page.waitForTimeout(1000)

    const loadingIndicator = page.locator('.loading, .spinner, text=Processing')
    const hasLoading = await loadingIndicator.first().isVisible().catch(() => false)

    // Should either show loading or results
    expect(hasLoading).toBeTruthy()
  })

  test('should show helpful placeholder text and hints', async ({ page }) => {
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
    const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

    // Check for meaningful placeholder text
    const questionPlaceholder = await questionField.getAttribute('placeholder')
    const definitionPlaceholder = await definitionField.getAttribute('placeholder')
    const timeframePlaceholder = await timeframeField.getAttribute('placeholder')

    expect(questionPlaceholder).toBeTruthy()
    expect(questionPlaceholder.length).toBeGreaterThan(10)

    if (definitionPlaceholder) {
      expect(definitionPlaceholder.length).toBeGreaterThan(5)
    }

    if (timeframePlaceholder) {
      expect(timeframePlaceholder).toContain('2026')
    }

    // Check for help text or labels
    const helpTexts = page.locator('.help-text, .hint, .description, label')
    const helpCount = await helpTexts.count()
    expect(helpCount).toBeGreaterThan(0)
  })
})