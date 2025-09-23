import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(cb) {
    this.cb = cb
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) this.onopen()
    }, 100)
  }

  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  send() {}
  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) this.onclose()
  }
}

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock fetch
global.fetch = jest.fn()

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mocked-url')
global.URL.revokeObjectURL = jest.fn()

// Increase test timeout for async operations
jest.setTimeout(30000)

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'https://foresight-analyzer.netlify.app'

// Set up global test utilities
global.testUtils = {
  mockForecastData: {
    question: 'Will there be a ceasefire agreement between Russia and Ukraine by March 31, 2026?',
    definition: 'A formal agreement to stop fighting',
    timeframe: '2026',
    models: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free'],
    iterations_per_model: 2,
  },
  mockApiResponse: {
    forecast_id: 'test-forecast-123',
    status: 'pending',
    message: 'Forecast created successfully',
  },
  mockForecastStatus: {
    forecast_id: 'test-forecast-123',
    status: 'completed',
    progress: 100,
    completed_queries: 4,
    total_queries: 4,
    ensemble_probability: 65.5,
  }
}