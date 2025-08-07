import { Page, Route, Request } from '@playwright/test';
import { TestDataManager } from './TestDataManager';

/**
 * Interface for mock response configuration
 */
export interface MockResponse {
  status?: number;
  contentType?: string;
  body?: any;
  headers?: Record<string, string>;
  delay?: number;
}

/**
 * Interface for network condition simulation
 */
export interface NetworkCondition {
  offline?: boolean;
  downloadThroughput?: number;
  uploadThroughput?: number;
  latency?: number;
}

/**
 * Helper class for API mocking and network simulation capabilities
 * Provides utilities for testing network error scenarios and API responses
 */
export class NetworkMockHelper {
  private static activeMocks: Map<string, Route> = new Map();

  /**
   * Mock stock data API responses for consistent testing
   * @param page - Playwright page instance
   * @param mockData - Optional custom mock data, uses TestDataManager if not provided
   */
  static async mockStockDataAPI(page: Page, mockData?: any): Promise<void> {
    const apiData = mockData || TestDataManager.getMockAPIResponses().stockData;

    await page.route('**/api/stock/**', async (route: Route, request: Request) => {
      const url = request.url();
      const ticker = this.extractTickerFromUrl(url);

      if (apiData[ticker]) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiData[ticker])
        });
      } else {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Stock not found' })
        });
      }
    });
  }

  /**
   * Mock MOAT analysis API responses
   * @param page - Playwright page instance
   * @param mockData - Optional custom mock data
   */
  static async mockMOATAnalysisAPI(page: Page, mockData?: any): Promise<void> {
    const apiData = mockData || TestDataManager.getMockAPIResponses().moatAnalysis;

    await page.route('**/api/moat/**', async (route: Route, request: Request) => {
      const url = request.url();
      const ticker = this.extractTickerFromUrl(url);

      // Simulate analysis processing time
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (apiData[ticker]) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiData[ticker])
        });
      } else {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Analysis failed for ticker' })
        });
      }
    });
  }

  /**
   * Simulate network errors for specific endpoints
   * @param page - Playwright page instance
   * @param endpoint - Endpoint pattern to simulate errors for
   * @param errorType - Type of error to simulate ('timeout', 'network', 'server')
   */
  static async simulateNetworkError(
    page: Page, 
    endpoint: string, 
    errorType: 'timeout' | 'network' | 'server' = 'network'
  ): Promise<void> {
    await page.route(endpoint, async (route: Route) => {
      switch (errorType) {
        case 'timeout':
          // Simulate timeout by delaying response beyond typical timeout
          await new Promise(resolve => setTimeout(resolve, 30000));
          await route.abort('timedout');
          break;
        
        case 'network':
          await route.abort('failed');
          break;
        
        case 'server':
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Internal server error' })
          });
          break;
      }
    });
  }

  /**
   * Simulate slow network responses
   * @param page - Playwright page instance
   * @param endpoint - Endpoint pattern to slow down
   * @param delay - Delay in milliseconds
   */
  static async simulateSlowResponse(page: Page, endpoint: string, delay: number): Promise<void> {
    await page.route(endpoint, async (route: Route) => {
      // Add artificial delay
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Continue with original request
      await route.continue();
    });
  }

  /**
   * Mock authentication API responses
   * @param page - Playwright page instance
   * @param shouldSucceed - Whether authentication should succeed
   */
  static async mockAuthenticationAPI(page: Page, shouldSucceed: boolean = true): Promise<void> {
    await page.route('**/auth/**', async (route: Route, request: Request) => {
      if (shouldSucceed) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            token: 'mock-jwt-token',
            user: {
              id: '123',
              email: 'test@example.com',
              name: 'Test User'
            }
          })
        });
      } else {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Invalid credentials'
          })
        });
      }
    });
  }

  /**
   * Mock API with custom response
   * @param page - Playwright page instance
   * @param endpoint - Endpoint pattern to mock
   * @param response - Mock response configuration
   */
  static async mockAPIResponse(
    page: Page, 
    endpoint: string, 
    response: MockResponse
  ): Promise<void> {
    await page.route(endpoint, async (route: Route) => {
      const { delay = 0, ...responseConfig } = response;
      
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }

      await route.fulfill({
        status: responseConfig.status || 200,
        contentType: responseConfig.contentType || 'application/json',
        headers: responseConfig.headers,
        body: typeof responseConfig.body === 'string' 
          ? responseConfig.body 
          : JSON.stringify(responseConfig.body)
      });
    });
  }

  /**
   * Simulate network conditions (offline, slow connection, etc.)
   * @param page - Playwright page instance
   * @param condition - Network condition to simulate
   */
  static async simulateNetworkCondition(page: Page, condition: NetworkCondition): Promise<void> {
    const context = page.context();
    
    if (condition.offline) {
      await context.setOffline(true);
    } else {
      await context.setOffline(false);
    }

    // Set network throttling if supported
    if (condition.downloadThroughput || condition.uploadThroughput || condition.latency) {
      // Note: Network throttling is not directly supported in Playwright
      // This would typically be handled at the browser level or using CDP
      console.warn('Network throttling simulation not fully implemented');
    }
  }

  /**
   * Mock multiple concurrent API requests
   * @param page - Playwright page instance
   * @param endpoints - Array of endpoint patterns to mock
   * @param responses - Array of corresponding mock responses
   */
  static async mockConcurrentRequests(
    page: Page, 
    endpoints: string[], 
    responses: MockResponse[]
  ): Promise<void> {
    if (endpoints.length !== responses.length) {
      throw new Error('Endpoints and responses arrays must have the same length');
    }

    for (let i = 0; i < endpoints.length; i++) {
      await this.mockAPIResponse(page, endpoints[i], responses[i]);
    }
  }

  /**
   * Intercept and log network requests for debugging
   * @param page - Playwright page instance
   * @param patterns - Array of URL patterns to log
   */
  static async logNetworkRequests(page: Page, patterns: string[] = ['**']): Promise<void> {
    for (const pattern of patterns) {
      await page.route(pattern, async (route: Route, request: Request) => {
        console.log(`[NETWORK] ${request.method()} ${request.url()}`);
        
        if (request.postData()) {
          console.log(`[NETWORK] Request body: ${request.postData()}`);
        }

        await route.continue();
      });
    }
  }

  /**
   * Mock API with rate limiting simulation
   * @param page - Playwright page instance
   * @param endpoint - Endpoint pattern to rate limit
   * @param requestsPerMinute - Number of requests allowed per minute
   */
  static async mockRateLimitedAPI(
    page: Page, 
    endpoint: string, 
    requestsPerMinute: number
  ): Promise<void> {
    const requestCounts = new Map<string, { count: number; resetTime: number }>();

    await page.route(endpoint, async (route: Route, request: Request) => {
      const clientId = request.headers()['x-client-id'] || 'default';
      const now = Date.now();
      const windowStart = Math.floor(now / 60000) * 60000; // Start of current minute

      if (!requestCounts.has(clientId) || requestCounts.get(clientId)!.resetTime < windowStart) {
        requestCounts.set(clientId, { count: 0, resetTime: windowStart + 60000 });
      }

      const clientData = requestCounts.get(clientId)!;
      clientData.count++;

      if (clientData.count > requestsPerMinute) {
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Rate limit exceeded',
            retryAfter: Math.ceil((clientData.resetTime - now) / 1000)
          }),
          headers: {
            'Retry-After': Math.ceil((clientData.resetTime - now) / 1000).toString()
          }
        });
      } else {
        await route.continue();
      }
    });
  }

  /**
   * Clear all active mocks
   * @param page - Playwright page instance
   */
  static async clearAllMocks(page: Page): Promise<void> {
    await page.unrouteAll();
    this.activeMocks.clear();
  }

  /**
   * Extract ticker symbol from URL
   * @param url - URL to extract ticker from
   * @returns Ticker symbol or empty string if not found
   */
  private static extractTickerFromUrl(url: string): string {
    const matches = url.match(/\/([A-Z]{1,5})(?:\/|$|\?)/);
    return matches ? matches[1] : '';
  }

  /**
   * Create a mock response for successful stock data
   * @param ticker - Stock ticker symbol
   * @param period - Time period for the data
   * @returns Mock stock data response
   */
  static createMockStockData(ticker: string, period: string): any {
    const dataPoints = period === '1M' ? 20 : period === '3M' ? 60 : 252;
    const basePrice = 100 + Math.random() * 100;

    return {
      symbol: ticker,
      period: period,
      prices: Array.from({ length: dataPoints }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (dataPoints - i));
        
        return {
          date: date.toISOString(),
          open: basePrice + (Math.random() - 0.5) * 10,
          high: basePrice + Math.random() * 15,
          low: basePrice - Math.random() * 15,
          close: basePrice + (Math.random() - 0.5) * 10,
          volume: Math.floor(Math.random() * 10000000) + 1000000
        };
      })
    };
  }

  /**
   * Create a mock response for MOAT analysis
   * @param ticker - Stock ticker symbol
   * @returns Mock MOAT analysis response
   */
  static createMockMOATAnalysis(ticker: string): any {
    return {
      ticker: ticker,
      moat_score: Math.random() * 10,
      competitive_advantages: [
        'Strong brand recognition',
        'Network effects',
        'Cost advantages'
      ],
      financial_strength: ['Weak', 'Moderate', 'Strong'][Math.floor(Math.random() * 3)],
      growth_prospects: ['Negative', 'Neutral', 'Positive'][Math.floor(Math.random() * 3)],
      analysis_date: new Date().toISOString()
    };
  }
}