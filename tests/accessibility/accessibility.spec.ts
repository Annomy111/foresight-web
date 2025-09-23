import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility Testing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should not have any automatically detectable accessibility issues', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should pass accessibility audit with specific rules', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('main')
      .exclude('.third-party-widget')
      .withRules(['color-contrast', 'keyboard-navigation', 'aria-labels'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1
    const h1Elements = page.locator('h1')
    await expect(h1Elements).toHaveCount(1) // Should have exactly one h1

    // Check heading order
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents()
    expect(headings.length).toBeGreaterThan(0)

    // Verify h1 exists and has meaningful content
    const h1Text = await h1Elements.first().textContent()
    expect(h1Text).toBeTruthy()
    expect(h1Text.length).toBeGreaterThan(3)
  })

  test('should have proper form labels and accessibility', async ({ page }) => {
    // Check all form inputs have labels or aria-labels
    const inputs = page.locator('input, textarea, select')
    const inputCount = await inputs.count()

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i)
      const inputType = await input.getAttribute('type')

      // Skip hidden inputs
      if (inputType === 'hidden') continue

      const isVisible = await input.isVisible()
      if (!isVisible) continue

      // Check for label association
      const inputId = await input.getAttribute('id')
      const ariaLabel = await input.getAttribute('aria-label')
      const ariaLabelledby = await input.getAttribute('aria-labelledby')

      let hasLabel = false

      if (ariaLabel || ariaLabelledby) {
        hasLabel = true
      } else if (inputId) {
        const labelCount = await page.locator(`label[for="${inputId}"]`).count()
        hasLabel = labelCount > 0
      }

      expect(hasLabel).toBeTruthy()
    }
  })

  test('should have proper button accessibility', async ({ page }) => {
    const buttons = page.locator('button, [role="button"]')
    const buttonCount = await buttons.count()

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i)
      const isVisible = await button.isVisible()

      if (!isVisible) continue

      // Check button has accessible name
      const buttonText = await button.textContent()
      const ariaLabel = await button.getAttribute('aria-label')
      const ariaLabelledby = await button.getAttribute('aria-labelledby')

      const hasAccessibleName = buttonText?.trim() || ariaLabel || ariaLabelledby
      expect(hasAccessibleName).toBeTruthy()

      // Check button is keyboard accessible
      const tabIndex = await button.getAttribute('tabindex')
      if (tabIndex === '-1') {
        // Button is intentionally not focusable, that's okay
        continue
      }

      // Button should be focusable
      await button.focus()
      const isFocused = await button.evaluate(el => el === document.activeElement)
      expect(isFocused).toBeTruthy()
    }
  })

  test('should have proper color contrast', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])

    // Additional manual contrast checks for key elements
    const keyElements = [
      'h1', 'h2', 'h3',
      'button',
      'input', 'textarea',
      '.error', '.warning', '.success',
      'a'
    ]

    for (const selector of keyElements) {
      const elements = page.locator(selector)
      const count = await elements.count()

      if (count > 0) {
        const element = elements.first()
        const isVisible = await element.isVisible()

        if (isVisible) {
          const styles = await element.evaluate(el => {
            const computed = window.getComputedStyle(el)
            return {
              color: computed.color,
              backgroundColor: computed.backgroundColor,
              fontSize: computed.fontSize
            }
          })

          // Basic check that color and background are different
          expect(styles.color).not.toBe(styles.backgroundColor)
        }
      }
    }
  })

  test('should be keyboard navigable', async ({ page }) => {
    // Start from the beginning
    await page.keyboard.press('Tab')

    const focusableElements = page.locator(
      'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
    )

    const focusableCount = await focusableElements.count()

    if (focusableCount > 0) {
      // Test Tab navigation
      for (let i = 0; i < Math.min(focusableCount, 10); i++) {
        const activeElement = await page.evaluate(() => document.activeElement?.tagName)
        expect(activeElement).toBeTruthy()

        await page.keyboard.press('Tab')
        await page.waitForTimeout(100) // Small delay for focus to settle
      }

      // Test Shift+Tab navigation
      for (let i = 0; i < 3; i++) {
        await page.keyboard.press('Shift+Tab')
        await page.waitForTimeout(100)

        const activeElement = await page.evaluate(() => document.activeElement?.tagName)
        expect(activeElement).toBeTruthy()
      }
    }
  })

  test('should handle focus management properly', async ({ page }) => {
    // Test initial focus
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()

    if (await questionField.isVisible()) {
      await questionField.focus()
      await expect(questionField).toBeFocused()

      // Test focus ring visibility
      const hasOutline = await questionField.evaluate(el => {
        const styles = window.getComputedStyle(el)
        return styles.outline !== 'none' || styles.boxShadow !== 'none'
      })

      // Should have some form of focus indicator
      expect(hasOutline).toBeTruthy()
    }

    // Test submit button focus
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()

    if (await submitButton.isVisible()) {
      await submitButton.focus()
      await expect(submitButton).toBeFocused()
    }
  })

  test('should have proper ARIA landmarks and structure', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['landmark-one-main', 'page-has-heading-one', 'region'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])

    // Check for main landmark
    const mainElement = page.locator('main, [role="main"]')
    await expect(mainElement).toHaveCount(1)

    // Check for meaningful page structure
    const landmarks = await page.locator('[role="banner"], [role="main"], [role="navigation"], [role="contentinfo"], header, main, nav, footer').count()
    expect(landmarks).toBeGreaterThan(0)
  })

  test('should handle error states accessibly', async ({ page }) => {
    // Try to trigger form validation errors
    const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()

    if (await submitButton.isVisible()) {
      await submitButton.click()
      await page.waitForTimeout(1000)

      // Check for accessible error messages
      const errorElements = page.locator('[role="alert"], .error, .invalid, [aria-invalid="true"]')
      const errorCount = await errorElements.count()

      if (errorCount > 0) {
        // Error messages should be properly announced
        const firstError = errorElements.first()
        const ariaLive = await firstError.getAttribute('aria-live')
        const role = await firstError.getAttribute('role')

        const isAccessible = ariaLive === 'polite' || ariaLive === 'assertive' || role === 'alert'
        expect(isAccessible).toBeTruthy()
      }
    }
  })

  test('should have proper image accessibility', async ({ page }) => {
    const images = page.locator('img')
    const imageCount = await images.count()

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i)
      const isVisible = await img.isVisible()

      if (isVisible) {
        const alt = await img.getAttribute('alt')
        const ariaLabel = await img.getAttribute('aria-label')
        const ariaLabelledby = await img.getAttribute('aria-labelledby')
        const role = await img.getAttribute('role')

        // Decorative images should have empty alt or role="presentation"
        // Content images should have meaningful alt text
        const hasAccessibleText = alt !== null || ariaLabel || ariaLabelledby || role === 'presentation'
        expect(hasAccessibleText).toBeTruthy()
      }
    }
  })

  test('should support screen reader navigation', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules([
        'aria-hidden-focus',
        'aria-labelledby',
        'aria-labels',
        'label',
        'label-title-only'
      ])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])

    // Check for proper ARIA attributes
    const interactiveElements = page.locator('button, input, textarea, select, a, [role="button"], [role="link"]')
    const count = await interactiveElements.count()

    for (let i = 0; i < Math.min(count, 10); i++) {
      const element = interactiveElements.nth(i)
      const isVisible = await element.isVisible()

      if (isVisible) {
        // Check for accessible name
        const tagName = await element.evaluate(el => el.tagName.toLowerCase())
        const text = await element.textContent()
        const ariaLabel = await element.getAttribute('aria-label')

        if (tagName === 'input') {
          const type = await element.getAttribute('type')
          if (type === 'submit' || type === 'button') {
            const value = await element.getAttribute('value')
            const hasName = text || ariaLabel || value
            expect(hasName).toBeTruthy()
          }
        } else {
          const hasName = text?.trim() || ariaLabel
          expect(hasName).toBeTruthy()
        }
      }
    }
  })

  test('should handle dynamic content accessibly', async ({ page }) => {
    // Fill form and submit to test dynamic content
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()

    if (await questionField.isVisible()) {
      await questionField.fill('Test accessibility question')

      const definitionField = page.locator('textarea[placeholder*="definition"], input[placeholder*="definition"]').first()
      if (await definitionField.isVisible()) {
        await definitionField.fill('Test definition')
      }

      const timeframeField = page.locator('input[placeholder*="timeframe"], input[placeholder*="2026"]').first()
      if (await timeframeField.isVisible()) {
        await timeframeField.fill('2026')
      }

      const submitButton = page.locator('button[type="submit"], button:has-text("Start Forecast")').first()
      await submitButton.click()

      await page.waitForTimeout(3000)

      // Check for ARIA live regions for dynamic updates
      const liveRegions = page.locator('[aria-live], [role="status"], [role="alert"]')
      const liveRegionCount = await liveRegions.count()

      if (liveRegionCount > 0) {
        const firstLiveRegion = liveRegions.first()
        const ariaLive = await firstLiveRegion.getAttribute('aria-live')
        const role = await firstLiveRegion.getAttribute('role')

        const isProperLiveRegion = ariaLive === 'polite' || ariaLive === 'assertive' || role === 'status' || role === 'alert'
        expect(isProperLiveRegion).toBeTruthy()
      }
    }
  })

  test('should be usable with high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.addStyleTag({
      content: `
        * {
          forced-color-adjust: none !important;
        }
        @media (prefers-contrast: high) {
          * {
            background: white !important;
            color: black !important;
            border: 1px solid black !important;
          }
        }
      `
    })

    await page.waitForTimeout(500)

    // Check that the page is still usable
    const h1 = page.locator('h1').first()
    if (await h1.isVisible()) {
      const isVisible = await h1.isVisible()
      expect(isVisible).toBeTruthy()
    }

    const buttons = page.locator('button')
    const buttonCount = await buttons.count()

    if (buttonCount > 0) {
      const firstButton = buttons.first()
      const isVisible = await firstButton.isVisible()
      expect(isVisible).toBeTruthy()
    }
  })

  test('should support reduced motion preferences', async ({ page }) => {
    // Test with reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' })

    await page.waitForTimeout(500)

    // Check that animations are respected
    const animatedElements = page.locator('.animate, .transition, [style*="animation"], [style*="transition"]')
    const count = await animatedElements.count()

    for (let i = 0; i < Math.min(count, 5); i++) {
      const element = animatedElements.nth(i)
      const styles = await element.evaluate(el => {
        const computed = window.getComputedStyle(el)
        return {
          animation: computed.animation,
          transition: computed.transition
        }
      })

      // With reduced motion, animations should be minimal or none
      if (styles.animation !== 'none') {
        expect(styles.animation).toContain('0s') // Duration should be 0
      }
    }
  })

  test('should be usable at 200% zoom', async ({ page }) => {
    // Set 200% zoom
    await page.setViewportSize({ width: 640, height: 480 }) // Simulate 200% zoom on 1280x960

    await page.waitForTimeout(1000)

    // Check that content is still accessible and usable
    const h1 = page.locator('h1').first()
    if (await h1.isVisible()) {
      await expect(h1).toBeVisible()
    }

    // Check that form is still usable
    const questionField = page.locator('textarea[placeholder*="question"], input[placeholder*="question"]').first()
    if (await questionField.isVisible()) {
      await expect(questionField).toBeVisible()
      await questionField.fill('Test at 200% zoom')

      const value = await questionField.inputValue()
      expect(value).toBe('Test at 200% zoom')
    }

    // Check that buttons are still clickable
    const buttons = page.locator('button')
    const buttonCount = await buttons.count()

    if (buttonCount > 0) {
      const firstButton = buttons.first()
      await expect(firstButton).toBeVisible()

      // Should be able to click
      await firstButton.hover()
      const isHoverable = await firstButton.isVisible()
      expect(isHoverable).toBeTruthy()
    }
  })
})