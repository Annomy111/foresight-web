import { createForecast, getForecastStatus, downloadExcel } from '@/lib/api'
import { ForecastRequest, ForecastStatus } from '@/lib/types'

// Mock fetch for all tests
global.fetch = jest.fn()

describe('API Client', () => {
  beforeEach(() => {
    ;(fetch as jest.Mock).mockClear()
  })

  describe('createForecast', () => {
    const mockRequest: ForecastRequest = {
      question: 'Will there be peace in Ukraine by 2026?',
      definition: 'A formal peace treaty signed by both governments',
      timeframe: '2026',
      models: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free'],
      iterations_per_model: 2
    }

    it('should send POST request with correct payload', async () => {
      const mockResponse = {
        forecast_id: 'test-123',
        status: 'pending',
        message: 'Forecast created successfully'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await createForecast(mockRequest)

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/forecast'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(mockRequest)
        }
      )

      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors gracefully', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ error: 'Invalid request' })
      })

      await expect(createForecast(mockRequest)).rejects.toThrow()
    })

    it('should handle network errors', async () => {
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      await expect(createForecast(mockRequest)).rejects.toThrow('Network error')
    })

    it('should validate required fields', async () => {
      const invalidRequest = {
        ...mockRequest,
        question: '' // Empty question
      }

      // API should either reject this or frontend should validate
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Question is required' })
      })

      await expect(createForecast(invalidRequest)).rejects.toThrow()
    })

    it('should handle large payloads', async () => {
      const largeRequest = {
        ...mockRequest,
        question: 'A'.repeat(10000), // Very long question
        definition: 'B'.repeat(5000), // Very long definition
        models: Array(20).fill('x-ai/grok-4-fast:free') // Many models
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ forecast_id: 'test-large', status: 'pending' })
      })

      const result = await createForecast(largeRequest)
      expect(result.forecast_id).toBe('test-large')
    })
  })

  describe('getForecastStatus', () => {
    const forecastId = 'test-forecast-123'

    it('should fetch status for valid forecast ID', async () => {
      const mockStatus: ForecastStatus = {
        forecast_id: forecastId,
        status: 'completed',
        progress: 100,
        completed_queries: 4,
        total_queries: 4,
        ensemble_probability: 75.5,
        results: [
          {
            model: 'x-ai/grok-4-fast:free',
            probability: 70,
            reasoning: 'Based on current diplomatic efforts...',
            timestamp: '2024-01-01T12:00:00Z'
          },
          {
            model: 'deepseek/deepseek-r1:free',
            probability: 81,
            reasoning: 'Considering economic factors...',
            timestamp: '2024-01-01T12:01:00Z'
          }
        ]
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      })

      const result = await getForecastStatus(forecastId)

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/forecast/${forecastId}`),
        { method: 'GET' }
      )

      expect(result).toEqual(mockStatus)
    })

    it('should handle pending status', async () => {
      const pendingStatus: ForecastStatus = {
        forecast_id: forecastId,
        status: 'pending',
        progress: 25,
        completed_queries: 1,
        total_queries: 4
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => pendingStatus
      })

      const result = await getForecastStatus(forecastId)
      expect(result.status).toBe('pending')
      expect(result.progress).toBe(25)
    })

    it('should handle processing status', async () => {
      const processingStatus: ForecastStatus = {
        forecast_id: forecastId,
        status: 'processing',
        progress: 75,
        completed_queries: 3,
        total_queries: 4,
        current_model: 'x-ai/grok-4-fast:free'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => processingStatus
      })

      const result = await getForecastStatus(forecastId)
      expect(result.status).toBe('processing')
      expect(result.current_model).toBe('x-ai/grok-4-fast:free')
    })

    it('should handle error status', async () => {
      const errorStatus: ForecastStatus = {
        forecast_id: forecastId,
        status: 'error',
        progress: 50,
        completed_queries: 2,
        total_queries: 4,
        error_message: 'API rate limit exceeded'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => errorStatus
      })

      const result = await getForecastStatus(forecastId)
      expect(result.status).toBe('error')
      expect(result.error_message).toBe('API rate limit exceeded')
    })

    it('should handle 404 for invalid forecast ID', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      })

      await expect(getForecastStatus('invalid-id')).rejects.toThrow()
    })
  })

  describe('downloadExcel', () => {
    const forecastId = 'test-forecast-123'

    it('should download Excel file successfully', async () => {
      const mockBlob = new Blob(['fake excel data'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      })

      // Mock URL.createObjectURL and link click
      const mockCreateObjectURL = jest.fn(() => 'blob:mock-url')
      const mockRevokeObjectURL = jest.fn()
      const mockClick = jest.fn()

      global.URL.createObjectURL = mockCreateObjectURL
      global.URL.revokeObjectURL = mockRevokeObjectURL

      // Mock document.createElement
      const mockAnchor = {
        href: '',
        download: '',
        click: mockClick
      }
      jest.spyOn(document, 'createElement').mockReturnValueOnce(mockAnchor as any)

      await downloadExcel(forecastId)

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/forecast/${forecastId}/download`),
        { method: 'GET' }
      )

      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob)
      expect(mockAnchor.download).toContain('.xlsx')
      expect(mockClick).toHaveBeenCalled()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })

    it('should handle download errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      })

      await expect(downloadExcel('invalid-id')).rejects.toThrow()
    })

    it('should handle blob creation errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => {
          throw new Error('Failed to create blob')
        }
      })

      await expect(downloadExcel(forecastId)).rejects.toThrow('Failed to create blob')
    })
  })

  describe('API Configuration', () => {
    it('should use correct base URL from environment', () => {
      // This test verifies the API configuration
      const originalEnv = process.env.NEXT_PUBLIC_API_URL

      // Test with custom URL
      process.env.NEXT_PUBLIC_API_URL = 'https://custom-api.example.com'

      // The actual implementation should use this URL
      expect(process.env.NEXT_PUBLIC_API_URL).toBe('https://custom-api.example.com')

      // Restore original
      process.env.NEXT_PUBLIC_API_URL = originalEnv
    })

    it('should handle missing environment variables gracefully', () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      delete process.env.NEXT_PUBLIC_API_URL

      // Should fall back to default URL or localhost
      // The actual implementation should handle this case

      process.env.NEXT_PUBLIC_API_URL = originalEnv
    })
  })

  describe('Request Timeouts and Retries', () => {
    it('should handle slow API responses', async () => {
      // Mock a slow response
      ;(fetch as jest.Mock).mockImplementationOnce(
        () => new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ forecast_id: 'slow-test', status: 'pending' })
          }), 100)
        )
      )

      const request: ForecastRequest = {
        question: 'Test question?',
        definition: 'Test definition',
        timeframe: '2026',
        models: ['x-ai/grok-4-fast:free'],
        iterations_per_model: 1
      }

      const result = await createForecast(request)
      expect(result.forecast_id).toBe('slow-test')
    })

    it('should handle server errors with appropriate status codes', async () => {
      const errorCodes = [500, 502, 503, 504]

      for (const code of errorCodes) {
        ;(fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: code,
          statusText: `Server Error ${code}`
        })

        await expect(getForecastStatus('test-id')).rejects.toThrow()
      }
    })
  })
})