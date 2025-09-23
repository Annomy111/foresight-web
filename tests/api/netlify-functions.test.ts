import { test, expect } from '@playwright/test'

test.describe('Netlify Functions API Tests', () => {
  const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'https://foresight-analyzer.netlify.app'

  test.beforeEach(async ({ page }) => {
    // Ensure we can reach the base URL
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should create forecast via API endpoint', async ({ request }) => {
    const forecastData = {
      question: 'Will there be peace in Ukraine by March 31, 2026?',
      definition: 'A formal peace treaty signed by both governments',
      timeframe: '2026-03-31',
      models: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free'],
      iterations_per_model: 2
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: forecastData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    expect(response.status()).toBe(200)

    const responseData = await response.json()
    expect(responseData).toHaveProperty('forecast_id')
    expect(responseData).toHaveProperty('status')
    expect(responseData.forecast_id).toBeTruthy()
    expect(['pending', 'processing', 'completed']).toContain(responseData.status)
  })

  test('should validate required fields in forecast creation', async ({ request }) => {
    const invalidData = {
      question: '', // Empty question
      definition: 'Test definition',
      timeframe: '2026',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: invalidData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // Should return 400 for invalid data
    expect(response.status()).toBe(400)

    const errorData = await response.json()
    expect(errorData).toHaveProperty('error')
  })

  test('should handle malformed JSON in forecast creation', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/forecast`, {
      data: 'invalid json',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    expect(response.status()).toBe(400)
  })

  test('should retrieve forecast status', async ({ request }) => {
    // First create a forecast
    const forecastData = {
      question: 'Will renewable energy exceed 50% of global production by 2030?',
      definition: 'Renewable sources providing more than 50% of global electricity',
      timeframe: '2030',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const createResponse = await request.post(`${baseURL}/api/forecast`, {
      data: forecastData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    expect(createResponse.status()).toBe(200)
    const createData = await createResponse.json()
    const forecastId = createData.forecast_id

    // Then check status
    const statusResponse = await request.get(`${baseURL}/api/forecast/${forecastId}`)

    expect(statusResponse.status()).toBe(200)

    const statusData = await statusResponse.json()
    expect(statusData).toHaveProperty('forecast_id', forecastId)
    expect(statusData).toHaveProperty('status')
    expect(['pending', 'processing', 'completed', 'error']).toContain(statusData.status)

    if (statusData.status === 'completed') {
      expect(statusData).toHaveProperty('ensemble_probability')
      expect(statusData).toHaveProperty('results')
      expect(Array.isArray(statusData.results)).toBeTruthy()
    }

    if (statusData.status === 'processing' || statusData.status === 'completed') {
      expect(statusData).toHaveProperty('progress')
      expect(statusData).toHaveProperty('completed_queries')
      expect(statusData).toHaveProperty('total_queries')
      expect(statusData.progress).toBeGreaterThanOrEqual(0)
      expect(statusData.progress).toBeLessThanOrEqual(100)
    }
  })

  test('should return 404 for non-existent forecast', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/forecast/non-existent-id`)

    expect(response.status()).toBe(404)
  })

  test('should handle multiple concurrent forecast requests', async ({ request }) => {
    const forecastData1 = {
      question: 'Will AI achieve AGI by 2030?',
      definition: 'Artificial General Intelligence matching human performance',
      timeframe: '2030',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const forecastData2 = {
      question: 'Will quantum computers break RSA encryption by 2035?',
      definition: 'Successful demonstration of breaking 2048-bit RSA',
      timeframe: '2035',
      models: ['deepseek/deepseek-r1:free'],
      iterations_per_model: 1
    }

    // Send concurrent requests
    const [response1, response2] = await Promise.all([
      request.post(`${baseURL}/api/forecast`, {
        data: forecastData1,
        headers: { 'Content-Type': 'application/json' }
      }),
      request.post(`${baseURL}/api/forecast`, {
        data: forecastData2,
        headers: { 'Content-Type': 'application/json' }
      })
    ])

    expect(response1.status()).toBe(200)
    expect(response2.status()).toBe(200)

    const data1 = await response1.json()
    const data2 = await response2.json()

    expect(data1.forecast_id).toBeTruthy()
    expect(data2.forecast_id).toBeTruthy()
    expect(data1.forecast_id).not.toBe(data2.forecast_id) // Should be different IDs
  })

  test('should handle large payloads gracefully', async ({ request }) => {
    const largePayload = {
      question: 'A'.repeat(10000), // Very long question
      definition: 'B'.repeat(5000), // Very long definition
      timeframe: '2030',
      models: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free'],
      iterations_per_model: 1
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: largePayload,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // Should either accept the payload or return appropriate error
    expect([200, 400, 413]).toContain(response.status())

    if (response.status() === 200) {
      const data = await response.json()
      expect(data.forecast_id).toBeTruthy()
    }
  })

  test('should handle special characters in forecast data', async ({ request }) => {
    const specialCharData = {
      question: 'Will robots with émojis 🤖 and ünïcödé characters work by 2030?',
      definition: 'Robots handling special chars: @#$%^&*()[]{}|\\:";\'<>?,./`~',
      timeframe: '2030',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: specialCharData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    expect(response.status()).toBe(200)

    const data = await response.json()
    expect(data.forecast_id).toBeTruthy()
  })

  test('should test Excel download endpoint', async ({ request }) => {
    // First create a forecast and wait for completion
    const forecastData = {
      question: 'Will Bitcoin reach $100,000 by 2026?',
      definition: 'Bitcoin price reaching $100,000 USD on major exchanges',
      timeframe: '2026',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const createResponse = await request.post(`${baseURL}/api/forecast`, {
      data: forecastData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    const createData = await createResponse.json()
    const forecastId = createData.forecast_id

    // Wait a moment for processing to start
    await new Promise(resolve => setTimeout(resolve, 5000))

    // Try to download Excel file
    const downloadResponse = await request.get(`${baseURL}/api/forecast/${forecastId}/download`)

    // Should either provide the file or indicate it's not ready
    expect([200, 404, 425]).toContain(downloadResponse.status())

    if (downloadResponse.status() === 200) {
      const contentType = downloadResponse.headers()['content-type']
      expect(contentType).toContain('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

      const contentDisposition = downloadResponse.headers()['content-disposition']
      expect(contentDisposition).toContain('attachment')
      expect(contentDisposition).toContain('.xlsx')
    }
  })

  test('should handle rate limiting appropriately', async ({ request }) => {
    const requests = []

    // Send many requests quickly to test rate limiting
    for (let i = 0; i < 10; i++) {
      requests.push(
        request.post(`${baseURL}/api/forecast`, {
          data: {
            question: `Test question ${i}`,
            definition: `Test definition ${i}`,
            timeframe: '2026',
            models: ['x-ai/grok-4-fast:free'],
            iterations_per_model: 1
          },
          headers: {
            'Content-Type': 'application/json',
          }
        })
      )
    }

    const responses = await Promise.all(requests)

    let successCount = 0
    let rateLimitedCount = 0

    for (const response of responses) {
      if (response.status() === 200) {
        successCount++
      } else if (response.status() === 429) {
        rateLimitedCount++
      }
    }

    // Should handle requests appropriately (either all succeed or some are rate limited)
    expect(successCount + rateLimitedCount).toBe(10)

    if (rateLimitedCount > 0) {
      console.log(`Rate limiting detected: ${rateLimitedCount} requests limited`)
    }
  })

  test('should validate model selection', async ({ request }) => {
    const invalidModelData = {
      question: 'Test question',
      definition: 'Test definition',
      timeframe: '2026',
      models: ['invalid-model-name', 'another-invalid-model'],
      iterations_per_model: 1
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: invalidModelData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // Should either filter invalid models or return error
    expect([200, 400]).toContain(response.status())

    if (response.status() === 400) {
      const errorData = await response.json()
      expect(errorData.error).toContain('model')
    }
  })

  test('should handle timeout scenarios', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/forecast/timeout-test-id`, {
      timeout: 30000 // 30 second timeout
    })

    // Should return 404 for non-existent ID or handle gracefully
    expect([404, 408, 500]).toContain(response.status())
  })

  test('should validate date format in timeframe', async ({ request }) => {
    const invalidDateData = {
      question: 'Test question',
      definition: 'Test definition',
      timeframe: 'invalid-date-format',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 1
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: invalidDateData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // Should either accept flexible date formats or return validation error
    expect([200, 400]).toContain(response.status())
  })

  test('should handle edge case: zero iterations', async ({ request }) => {
    const zeroIterationsData = {
      question: 'Test question',
      definition: 'Test definition',
      timeframe: '2026',
      models: ['x-ai/grok-4-fast:free'],
      iterations_per_model: 0
    }

    const response = await request.post(`${baseURL}/api/forecast`, {
      data: zeroIterationsData,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    expect(response.status()).toBe(400)

    const errorData = await response.json()
    expect(errorData.error).toContain('iterations')
  })

  test('should test CORS headers', async ({ request }) => {
    const response = await request.options(`${baseURL}/api/forecast`)

    const corsHeaders = response.headers()
    expect(corsHeaders['access-control-allow-origin']).toBeTruthy()
    expect(corsHeaders['access-control-allow-methods']).toContain('POST')
    expect(corsHeaders['access-control-allow-headers']).toContain('Content-Type')
  })

  test('should monitor API health and availability', async ({ request }) => {
    // Test basic connectivity
    const healthResponse = await request.get(`${baseURL}/api/health`, {
      timeout: 10000
    }).catch(() => null)

    if (healthResponse) {
      expect(healthResponse.status()).toBe(200)
    }

    // Test that main forecast endpoint is responsive
    const forecastResponse = await request.get(`${baseURL}/api/forecast/health-check`, {
      timeout: 10000
    })

    // Should return 404 (endpoint exists) rather than network error
    expect([404, 405]).toContain(forecastResponse.status())
  })
})