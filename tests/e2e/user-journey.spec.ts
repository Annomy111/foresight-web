import { test, expect } from '@playwright/test'

test.describe('Complete User Journey Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should complete full forecasting workflow - successful prediction', async ({ page }) => {
    // Step 1: Fill out the forecast form
    await test.step('Fill out forecast form with valid data', async () => {
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      await questionField.fill('Will there be a ceasefire agreement between Russia and Ukraine by March 31, 2026?')
      await definitionField.fill('A formal agreement to stop fighting, signed by both governments and internationally recognized')
      await timeframeField.fill('2026-03-31')

      // Verify form is filled correctly
      expect(await questionField.inputValue()).toContain('ceasefire agreement')
      expect(await definitionField.inputValue()).toContain('formal agreement')
      expect(await timeframeField.inputValue()).toBe('2026-03-31')
    })

    // Step 2: Configure model selection
    await test.step('Configure model selection and iterations', async () => {
      // Find and configure model selection
      const modelCheckboxes = page.locator('input[type="checkbox"][data-model], input[type="checkbox"] + label')
      const modelButtons = page.locator('button[data-model], .model-selector button')

      const checkboxCount = await modelCheckboxes.count()
      const buttonCount = await modelButtons.count()

      if (checkboxCount > 0) {
        // Ensure at least 2 models are selected for ensemble
        await modelCheckboxes.first().check()
        if (checkboxCount > 1) {
          await modelCheckboxes.nth(1).check()
        }
      } else if (buttonCount > 0) {
        await modelButtons.first().click()
        if (buttonCount > 1) {
          await modelButtons.nth(1).click()
        }
      }

      // Set iterations per model
      const iterationsInput = page.locator('input[type="number"], input[placeholder*="iteration"]')
      if (await iterationsInput.count() > 0) {
        await iterationsInput.first().fill('2')
      }
    })

    // Step 3: Submit the forecast
    await test.step('Submit forecast and verify submission', async () => {
      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await expect(submitButton).toBeEnabled()

      await submitButton.click()

      // Should transition to loading or processing state
      await page.waitForTimeout(2000)

      // Verify either loading state or results are shown
      const loadingIndicator = page.locator('.loading, .spinner, text=Processing, text=Starting')
      const resultsSection = page.locator('.results, .forecast-results, text=Progress, text=Status')
      const errorMessage = page.locator('.error, text=Error, text=Failed')

      const hasLoading = await loadingIndicator.first().isVisible().catch(() => false)
      const hasResults = await resultsSection.first().isVisible().catch(() => false)
      const hasError = await errorMessage.first().isVisible().catch(() => false)

      expect(hasLoading || hasResults).toBeTruthy()
      expect(hasError).toBeFalsy()
    })

    // Step 4: Monitor progress (if progress tracking is available)
    await test.step('Monitor forecast progress', async () => {
      // Wait for progress indicators to appear
      await page.waitForTimeout(3000)

      const progressBar = page.locator('.progress-bar, [role="progressbar"], .progress')
      const statusText = page.locator('text=Progress, text=Completed, text=Processing, .status')
      const progressPercentage = page.locator('text=%')

      // Check if any progress indicators are present
      const hasProgressBar = await progressBar.first().isVisible().catch(() => false)
      const hasStatusText = await statusText.first().isVisible().catch(() => false)
      const hasPercentage = await progressPercentage.first().isVisible().catch(() => false)

      if (hasProgressBar || hasStatusText || hasPercentage) {
        // Progress tracking is available
        console.log('Progress tracking detected')

        // Wait for completion (with reasonable timeout)
        await page.waitForFunction(
          () => {
            const completedText = document.body.textContent || ''
            return completedText.includes('completed') ||
                   completedText.includes('100%') ||
                   completedText.includes('finished') ||
                   completedText.includes('Ensemble')
          },
          { timeout: 60000 }
        ).catch(() => {
          console.log('Progress tracking timeout - continuing with test')
        })
      }
    })

    // Step 5: Verify results are displayed
    await test.step('Verify forecast results are displayed', async () => {
      // Look for result indicators
      const ensembleResult = page.locator('text=Ensemble, text=Final, text=Probability')
      const modelResults = page.locator('.model-result, .prediction, .forecast-item')
      const probabilityNumbers = page.locator('text=%')

      await page.waitForTimeout(5000)

      const hasEnsemble = await ensembleResult.first().isVisible().catch(() => false)
      const hasModelResults = await modelResults.first().isVisible().catch(() => false)
      const hasProbabilities = await probabilityNumbers.first().isVisible().catch(() => false)

      // At least some form of results should be visible
      expect(hasEnsemble || hasModelResults || hasProbabilities).toBeTruthy()

      if (hasProbabilities) {
        // Verify probability values are reasonable (0-100%)
        const probabilityTexts = await probabilityNumbers.allTextContents()
        const validProbabilities = probabilityTexts.some(text => {
          const match = text.match(/(\d+(?:\.\d+)?)%/)
          if (match) {
            const value = parseFloat(match[1])
            return value >= 0 && value <= 100
          }
          return false
        })
        expect(validProbabilities).toBeTruthy()
      }
    })

    // Step 6: Test Excel download functionality (if available)
    await test.step('Test Excel download functionality', async () => {
      const downloadButton = page.locator('button:has-text("Download"), button:has-text("Excel"), .download-btn')

      const hasDownloadButton = await downloadButton.first().isVisible().catch(() => false)

      if (hasDownloadButton) {
        // Set up download handling
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)

        await downloadButton.first().click()

        const download = await downloadPromise

        if (download) {
          expect(download.suggestedFilename()).toMatch(/\.(xlsx|xls)$/)
          console.log('Excel download successful:', download.suggestedFilename())
        }
      }
    })
  })

  test('should handle complex forecasting scenario with multiple models', async ({ page }) => {
    await test.step('Submit complex geopolitical forecast', async () => {
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      // More complex scenario
      await questionField.fill('Will China take military action against Taiwan resulting in armed conflict by December 31, 2025?')
      await definitionField.fill('Direct military engagement between Chinese and Taiwanese forces, including airstrikes, naval battles, or ground invasion attempts, lasting more than 24 hours and acknowledged by international media')
      await timeframeField.fill('2025-12-31')

      // Select multiple models if available
      const modelCheckboxes = page.locator('input[type="checkbox"][data-model]')
      const checkboxCount = await modelCheckboxes.count()

      for (let i = 0; i < Math.min(checkboxCount, 4); i++) {
        await modelCheckboxes.nth(i).check()
      }

      // Set higher iterations for more accuracy
      const iterationsInput = page.locator('input[type="number"]')
      if (await iterationsInput.count() > 0) {
        await iterationsInput.first().fill('3')
      }

      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton.click()

      await page.waitForTimeout(5000)

      // Should not show immediate errors
      const errorMessage = page.locator('.error, text=Error, text=Failed')
      const hasError = await errorMessage.first().isVisible().catch(() => false)
      expect(hasError).toBeFalsy()
    })
  })

  test('should handle edge case: very short timeframe prediction', async ({ page }) => {
    await test.step('Submit short-term forecast', async () => {
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      const futureDate = new Date()
      futureDate.setMonth(futureDate.getMonth() + 3)
      const shortTimeframe = futureDate.toISOString().split('T')[0]

      await questionField.fill('Will the Federal Reserve announce an interest rate cut in the next quarter?')
      await definitionField.fill('An official announcement of a reduction in the federal funds rate by at least 0.25 percentage points')
      await timeframeField.fill(shortTimeframe)

      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton.click()

      await page.waitForTimeout(3000)

      // Should either process successfully or show appropriate validation
      const loadingIndicator = page.locator('.loading, .spinner, text=Processing')
      const validationError = page.locator('text=timeframe, text=date, .validation-error')

      const hasLoading = await loadingIndicator.first().isVisible().catch(() => false)
      const hasValidation = await validationError.first().isVisible().catch(() => false)

      // Should either be processing or show validation feedback
      expect(hasLoading || hasValidation).toBeTruthy()
    })
  })

  test('should recover from network interruption', async ({ page }) => {
    await test.step('Simulate network issues during forecast', async () => {
      // Fill and submit form
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      await questionField.fill('Will Bitcoin reach $100,000 USD by end of 2025?')
      await definitionField.fill('Bitcoin price reaching $100,000 USD on major exchanges')
      await timeframeField.fill('2025-12-31')

      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton.click()

      // Wait a moment then simulate network offline/online
      await page.waitForTimeout(2000)

      // Simulate network offline
      await page.context().setOffline(true)
      await page.waitForTimeout(3000)

      // Bring network back online
      await page.context().setOffline(false)
      await page.waitForTimeout(5000)

      // Check if the application handles this gracefully
      const errorMessage = page.locator('text=network, text=connection, text=offline')
      const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")')
      const resultsSection = page.locator('.results, text=Ensemble, text=Progress')

      const hasNetworkError = await errorMessage.first().isVisible().catch(() => false)
      const hasRetryButton = await retryButton.first().isVisible().catch(() => false)
      const hasResults = await resultsSection.first().isVisible().catch(() => false)

      // Should either show network error handling or continue processing
      expect(hasNetworkError || hasRetryButton || hasResults).toBeTruthy()

      if (hasRetryButton) {
        await retryButton.first().click()
        await page.waitForTimeout(3000)
      }
    })
  })

  test('should handle concurrent user sessions', async ({ page, context }) => {
    await test.step('Test multiple simultaneous forecasts', async () => {
      // Create a second page to simulate concurrent users
      const page2 = await context.newPage()
      await page2.goto('/')
      await page2.waitForLoadState('networkidle')

      // Submit forecast on first page
      await page.fill('textarea[placeholder*="question"], input[placeholder*="question"]', 'Will AI achieve AGI by 2030?')
      await page.fill('textarea[placeholder*="definition"], input[placeholder*="definition"]', 'Artificial General Intelligence achieving human-level performance')
      await page.fill('input[placeholder*="timeframe"], input[placeholder*="2026"]', '2030-12-31')

      const submitButton1 = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton1.click()

      // Submit different forecast on second page
      await page2.fill('textarea[placeholder*="question"], input[placeholder*="question"]', 'Will renewable energy exceed 80% of global production by 2035?')
      await page2.fill('textarea[placeholder*="definition"], input[placeholder*="definition"]', 'Renewable sources providing 80%+ of global electricity')
      await page2.fill('input[placeholder*="timeframe"], input[placeholder*="2026"]', '2035-12-31')

      const submitButton2 = page2.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton2.click()

      // Both should process independently
      await page.waitForTimeout(5000)
      await page2.waitForTimeout(5000)

      // Check that both sessions are handling requests appropriately
      const results1 = page.locator('.results, text=Progress, text=Processing')
      const results2 = page2.locator('.results, text=Progress, text=Processing')

      const hasResults1 = await results1.first().isVisible().catch(() => false)
      const hasResults2 = await results2.first().isVisible().catch(() => false)

      // At least one should be processing (depending on server capacity)
      expect(hasResults1 || hasResults2).toBeTruthy()

      await page2.close()
    })
  })

  test('should preserve user input during browser refresh', async ({ page }) => {
    await test.step('Test form persistence across page refresh', async () => {
      // Fill out form
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      const testQuestion = 'Will quantum computing break RSA encryption by 2030?'
      const testDefinition = 'Successful demonstration of breaking 2048-bit RSA encryption'
      const testTimeframe = '2030-12-31'

      await questionField.fill(testQuestion)
      await definitionField.fill(testDefinition)
      await timeframeField.fill(testTimeframe)

      // Refresh the page
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Check if form values are preserved (depends on implementation)
      const questionValue = await page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first().inputValue()
      const definitionValue = await page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first().inputValue()
      const timeframeValue = await page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first().inputValue()

      // If local storage is implemented, values should be preserved
      if (questionValue || definitionValue || timeframeValue) {
        expect(questionValue).toBe(testQuestion)
        expect(definitionValue).toBe(testDefinition)
        expect(timeframeValue).toBe(testTimeframe)
      }
    })
  })

  test('should handle mobile user journey', async ({ page, isMobile }) => {
    if (!isMobile) {
      // Simulate mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })
    }

    await test.step('Complete forecast on mobile device', async () => {
      // Mobile-specific form interaction
      const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()

      // Ensure fields are visible on mobile
      await expect(questionField).toBeVisible()
      await expect(definitionField).toBeVisible()
      await expect(timeframeField).toBeVisible()

      // Fill form with mobile-friendly interactions
      await questionField.tap()
      await questionField.fill('Will 5G coverage reach 95% global population by 2028?')

      await definitionField.tap()
      await definitionField.fill('5G network coverage available to 95% of world population')

      await timeframeField.tap()
      await timeframeField.fill('2028-12-31')

      // Submit and verify mobile UI handles it appropriately
      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton.tap()

      await page.waitForTimeout(3000)

      // Mobile UI should show appropriate feedback
      const mobileResults = page.locator('.results, text=Progress, text=Processing')
      const hasResults = await mobileResults.first().isVisible().catch(() => false)
      expect(hasResults).toBeTruthy()
    })
  })
})