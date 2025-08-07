/**
 * Interface for user credentials used in authentication tests
 */
export interface UserCredentials {
  email: string;
  password: string;
  name?: string;
}

/**
 * Interface for chart test data configuration
 */
export interface ChartTestData {
  ticker: string;
  period: string;
  expectedDataPoints: number;
  technicalIndicators: string[];
  movingAverages: number[];
}

/**
 * Interface for MOAT analysis test data
 */
export interface MOATTestData {
  ticker: string;
  expectedAnalysisFields: string[];
  analysisTimeout: number;
}

/**
 * Static class for managing test data across all test suites
 * Provides consistent test data for reliable and repeatable testing
 */
export class TestDataManager {
  
  /**
   * Get a list of valid stock tickers for testing
   * @returns Array of valid stock ticker symbols
   */
  static getValidTickers(): string[] {
    return [
      'AAPL',  // Apple Inc.
      'GOOGL', // Alphabet Inc.
      'MSFT',  // Microsoft Corporation
      'TSLA',  // Tesla Inc.
      'AMZN',  // Amazon.com Inc.
      'NVDA',  // NVIDIA Corporation
      'META',  // Meta Platforms Inc.
      'NFLX'   // Netflix Inc.
    ];
  }

  /**
   * Get a list of invalid stock tickers for error testing
   * @returns Array of invalid stock ticker symbols
   */
  static getInvalidTickers(): string[] {
    return [
      'INVALID',
      'NOTFOUND',
      'FAKE123',
      'XXXYYY',
      '12345',
      'TOOLONG123456',
      '',
      ' ',
      'null'
    ];
  }

  /**
   * Get test user credentials for authentication flows
   * @returns UserCredentials object with test user data
   */
  static getTestCredentials(): UserCredentials {
    return {
      email: process.env.TEST_USER_EMAIL || 'test@test.com',
      password: process.env.TEST_USER_PASSWORD || 'Test1234',
      name: 'Test User'
    };
  }

  /**
   * Get invalid credentials for authentication error testing
   * @returns UserCredentials object with invalid test data
   */
  static getInvalidCredentials(): UserCredentials {
    return {
      email: 'invalid@nonexistent.com',
      password: 'wrongpassword123',
      name: 'Invalid User'
    };
  }

  /**
   * Get authentication test scenarios
   * @returns Array of authentication test scenarios
   */
  static getAuthTestScenarios(): Array<{
    name: string;
    credentials: UserCredentials;
    expectedResult: 'success' | 'failure';
    expectedError?: string;
  }> {
    return [
      {
        name: 'Valid credentials',
        credentials: this.getTestCredentials(),
        expectedResult: 'success'
      },
      {
        name: 'Invalid email format',
        credentials: { email: 'invalid-email', password: 'password123' },
        expectedResult: 'failure',
        expectedError: 'Invalid email format'
      },
      {
        name: 'Empty credentials',
        credentials: { email: '', password: '' },
        expectedResult: 'failure',
        expectedError: 'Email and password are required'
      },
      {
        name: 'Wrong password',
        credentials: { email: 'test@example.com', password: 'wrongpassword' },
        expectedResult: 'failure',
        expectedError: 'Invalid credentials'
      }
    ];
  }

  /**
   * Get protected routes that require authentication
   * @returns Array of protected route paths
   */
  static getProtectedRoutes(): string[] {
    return [
      '/dashboard',
      '/',
      '/detailed-graph/AAPL',
      '/api/moat-analysis'
    ];
  }

  /**
   * Get public routes that don't require authentication
   * @returns Array of public route paths
   */
  static getPublicRoutes(): string[] {
    return [
      '/login',
      '/auth/login',
      '/callback'
    ];
  }

  /**
   * Get additional test user credentials for multi-user scenarios
   * @returns Array of UserCredentials for different test scenarios
   */
  static getMultipleTestCredentials(): UserCredentials[] {
    return [
      {
        email: process.env.TEST_USER_EMAIL || 'test@example.com',
        password: process.env.TEST_USER_PASSWORD || 'TestPassword123!',
        name: 'Primary Test User'
      },
      {
        email: process.env.TEST_USER_EMAIL_2 || 'test2@example.com',
        password: process.env.TEST_USER_PASSWORD_2 || 'TestPassword456!',
        name: 'Secondary Test User'
      }
    ];
  }

  /**
   * Get chart test data configurations for different scenarios
   * @returns Array of ChartTestData objects
   */
  static getChartTestData(): ChartTestData[] {
    return [
      {
        ticker: 'AAPL',
        period: '1M',
        expectedDataPoints: 20,
        technicalIndicators: ['RSI', 'MACD', 'Volume'],
        movingAverages: [20, 50, 200]
      },
      {
        ticker: 'GOOGL',
        period: '3M',
        expectedDataPoints: 60,
        technicalIndicators: ['RSI', 'MACD'],
        movingAverages: [20, 50]
      },
      {
        ticker: 'MSFT',
        period: '1Y',
        expectedDataPoints: 252,
        technicalIndicators: ['Volume'],
        movingAverages: [50, 200]
      }
    ];
  }

  /**
   * Get a single chart test data configuration by ticker
   * @param ticker - Stock ticker symbol
   * @returns ChartTestData object or undefined if not found
   */
  static getChartTestDataByTicker(ticker: string): ChartTestData | undefined {
    return this.getChartTestData().find(data => data.ticker === ticker);
  }

  /**
   * Get available time periods for chart testing
   * @returns Array of time period strings
   */
  static getTimePeriods(): string[] {
    return ['1M', '3M', '6M', '1Y', '5Y'];
  }

  /**
   * Get available technical indicators for testing
   * @returns Array of technical indicator names
   */
  static getTechnicalIndicators(): string[] {
    return ['RSI', 'MACD', 'Volume', 'Bollinger Bands', 'Stochastic'];
  }

  /**
   * Get available chart modes for testing
   * @returns Array of chart mode names
   */
  static getChartModes(): string[] {
    return ['Fibonacci', 'Elliott Wave', 'Trendlines', 'Normal'];
  }

  /**
   * Get keyboard shortcuts for chart interactions
   * @returns Map of key to action mappings
   */
  static getKeyboardShortcuts(): Map<string, string> {
    return new Map([
      ['F', 'Fibonacci'],
      ['T', 'Trendlines'],
      ['E', 'Elliott Wave'],
      ['Escape', 'Back to Dashboard'],
      ['S', 'Settings Panel']
    ]);
  }

  /**
   * Get MOAT analysis test data
   * @returns Array of MOATTestData objects
   */
  static getMOATTestData(): MOATTestData[] {
    return [
      {
        ticker: 'AAPL',
        expectedAnalysisFields: ['moat_score', 'competitive_advantages', 'financial_strength', 'growth_prospects'],
        analysisTimeout: 30000
      },
      {
        ticker: 'GOOGL',
        expectedAnalysisFields: ['moat_score', 'competitive_advantages', 'financial_strength', 'growth_prospects'],
        analysisTimeout: 30000
      }
    ];
  }

  /**
   * Get test viewport sizes for responsive testing
   * @returns Array of viewport size objects
   */
  static getViewportSizes(): Array<{name: string, width: number, height: number}> {
    return [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1920, height: 1080 },
      { name: 'large-desktop', width: 2560, height: 1440 }
    ];
  }

  /**
   * Get browser configurations for cross-browser testing
   * @returns Array of browser configuration objects
   */
  static getBrowserConfigs(): Array<{name: string, channel?: string}> {
    return [
      { name: 'chromium' },
      { name: 'firefox' },
      { name: 'webkit' },
      { name: 'chromium', channel: 'chrome' },
      { name: 'chromium', channel: 'msedge' }
    ];
  }

  /**
   * Get mock API response data for testing
   * @returns Object containing mock API responses
   */
  static getMockAPIResponses(): Record<string, any> {
    return {
      stockData: {
        'AAPL': {
          symbol: 'AAPL',
          prices: Array.from({ length: 20 }, (_, i) => ({
            date: new Date(Date.now() - (19 - i) * 24 * 60 * 60 * 1000).toISOString(),
            open: 150 + Math.random() * 10,
            high: 155 + Math.random() * 10,
            low: 145 + Math.random() * 10,
            close: 150 + Math.random() * 10,
            volume: 50000000 + Math.random() * 10000000
          }))
        },
        'INVALID': null
      },
      moatAnalysis: {
        'AAPL': {
          ticker: 'AAPL',
          moat_score: 8.5,
          competitive_advantages: ['Brand loyalty', 'Ecosystem lock-in', 'Innovation'],
          financial_strength: 'Strong',
          growth_prospects: 'Positive'
        }
      },
      errors: {
        networkError: { error: 'Network request failed' },
        invalidTicker: { error: 'Invalid ticker symbol' },
        serverError: { error: 'Internal server error' }
      }
    };
  }

  /**
   * Get random test data for dynamic testing scenarios
   * @returns Object with randomly generated test data
   */
  static getRandomTestData(): {
    ticker: string;
    period: string;
    coordinates: { x: number; y: number };
    movingAverage: number;
  } {
    const tickers = this.getValidTickers();
    const periods = this.getTimePeriods();
    
    return {
      ticker: tickers[Math.floor(Math.random() * tickers.length)],
      period: periods[Math.floor(Math.random() * periods.length)],
      coordinates: {
        x: Math.floor(Math.random() * 800) + 100,
        y: Math.floor(Math.random() * 400) + 100
      },
      movingAverage: [5, 10, 20, 50, 100, 200][Math.floor(Math.random() * 6)]
    };
  }

  /**
   * Get test data for form validation scenarios
   * @returns Object containing various invalid input scenarios
   */
  static getFormValidationData(): Record<string, any> {
    return {
      emptyInputs: {
        ticker: '',
        email: '',
        password: ''
      },
      invalidFormats: {
        email: ['invalid-email', '@domain.com', 'user@', 'user.domain'],
        ticker: ['123', 'toolongtickerSymbol', '!@#$%'],
        numbers: ['abc', '12.34.56', 'NaN', 'Infinity']
      },
      boundaryValues: {
        movingAveragePeriods: [0, 1, 999, 1000, -1],
        chartCoordinates: [
          { x: -1, y: -1 },
          { x: 0, y: 0 },
          { x: 9999, y: 9999 }
        ]
      }
    };
  }
}