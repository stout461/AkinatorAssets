# =============================================================================
# COMPLETE FUNCTION-BASED STOCK ANALYZER
# =============================================================================

import requests
import json
import yfinance as yf
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse
import random
import os
import boto3

#import strands

from strands import Agent, tool
from strands.models import BedrockModel
#from strands_tools import http_request

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# AWS CONFIGURATION
# =============================================================================

# Method 3: For testing ONLY - Set in this notebook session (keys not saved)
# ⚠️  ONLY use this for temporary testing, never commit to git!

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = 'us-east-1'

# Silent AWS setup - no print statements
try:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    # Test credentials silently
    models = bedrock.list_foundation_models()
except Exception as e:
    # Silent fail - credentials will be tested when function is called
    pass

# =============================================================================
# STRATEGIC WEB SEARCH TOOLS
# =============================================================================

@tool
def strategic_web_search(query: str, num_results: int = 5) -> str:
    """Strategic web search using multiple DuckDuckGo approaches to avoid blocking

    Args:
        query: Search query (e.g., "AAPL stock news", "Tesla earnings")
        num_results: Number of results to return (default 5)

    Returns:
        search_results: Formatted search results with titles and snippets
    """
    # ADD 2025 CONTEXT: Enhance query with current year context for financial searches
    current_year = datetime.now().year
    current_date = datetime.now().strftime("%Y-%m")

    # Add 2025 context to financial queries
    if any(term in query.lower() for term in ['stock', 'earnings', 'financial', 'performance', 'results']):
        if str(current_year) not in query and 'recent' in query.lower():
            query = f"{query} {current_year}"
        elif 'latest' in query.lower() or 'recent' in query.lower():
            query = f"{query} {current_date}"

    print(f"🔍 STRATEGIC WEB SEARCH: '{query}' at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📅 Context: Searching with {current_year} awareness")

    try:
        results = []
        search_successful = False

        # STRATEGY 1: DuckDuckGo Instant API (most reliable)
        try:
            print("   🎯 Strategy 1: DuckDuckGo Instant API...")

            ddg_instant_url = 'https://api.duckduckgo.com/'
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; research/1.0)',
                'Accept': 'application/json'
            }

            response = requests.get(ddg_instant_url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract abstract information
                abstract = data.get('Abstract', '')
                abstract_source = data.get('AbstractSource', '')

                if abstract and len(abstract) > 50:
                    print(f"   ✅ Found abstract from {abstract_source}")
                    results.append(f"1. {abstract_source} - Key Information\n   {abstract}\n   Source: DuckDuckGo Instant API\n")
                    search_successful = True

                # Extract related topics
                related_topics = data.get('RelatedTopics', [])
                for i, topic in enumerate(related_topics[:3], len(results) + 1):
                    if isinstance(topic, dict) and 'Text' in topic:
                        text = topic['Text']
                        if len(text) > 30:
                            print(f"   ✅ Found related topic {i}")
                            results.append(f"{i}. Related Information\n   {text}\n   Source: DuckDuckGo Related Topics\n")
                            search_successful = True

            else:
                print(f"   ⚠️  Instant API returned: {response.status_code}")

        except Exception as e:
            print(f"   ⚠️  Instant API failed: {str(e)}")

        # Add small delay to be respectful
        time.sleep(1)

        # STRATEGY 2: DuckDuckGo HTML Search (if Instant API didn't get enough)
        if len(results) < 2:
            try:
                print("   🎯 Strategy 2: DuckDuckGo HTML Search...")

                # Use the HTML endpoint with strategic headers
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

                # Rotate user agents to appear more natural
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
                ]

                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }

                response = requests.get(search_url, headers=headers, timeout=12)
                print(f"   📡 HTML Search status: {response.status_code}, Length: {len(response.content)} bytes")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Try multiple selectors for results
                    search_results = []
                    selectors = ['.result', '.links_main', '.result__body', 'div[class*="result"]']

                    for selector in selectors:
                        found_results = soup.select(selector)
                        if found_results:
                            search_results = found_results
                            print(f"   ✅ Found {len(found_results)} results with selector: {selector}")
                            break

                    # Extract results
                    for i, result in enumerate(search_results[:num_results], len(results) + 1):
                        try:
                            # Try multiple ways to get title
                            title = None
                            title_selectors = ['.result__title a', '.result__a', 'h2 a', 'h3 a', 'a']

                            for title_sel in title_selectors:
                                title_elem = result.select_one(title_sel)
                                if title_elem:
                                    title = title_elem.get_text().strip()
                                    if len(title) > 10:  # Quality filter
                                        break

                            # Try multiple ways to get snippet
                            snippet = None
                            snippet_selectors = ['.result__snippet', '.result__body', '.snippet', 'p']

                            for snippet_sel in snippet_selectors:
                                snippet_elem = result.select_one(snippet_sel)
                                if snippet_elem:
                                    snippet = snippet_elem.get_text().strip()
                                    if len(snippet) > 30:  # Quality filter
                                        break

                            # Get URL
                            url_elem = result.select_one('a[href]')
                            url = url_elem.get('href', '') if url_elem else ''

                            if title and snippet and len(snippet) > 30:
                                print(f"   ✅ Result {i}: {title[:50]}...")
                                results.append(f"{i}. {title}\n   {snippet}\n   URL: {url}\n")
                                search_successful = True

                        except Exception as e:
                            continue

                elif response.status_code == 202:
                    print("   ⚠️  Got 202 - DuckDuckGo is rate limiting")
                else:
                    print(f"   ⚠️  HTML Search returned: {response.status_code}")

            except Exception as e:
                print(f"   ⚠️  HTML Search failed: {str(e)}")

        # STRATEGY 3: Financial News fallback (if others fail)
        if not search_successful and any(term in query.lower() for term in ['stock', 'earnings', 'financial', 'nasdaq', 'nyse']):
            try:
                print("   🎯 Strategy 3: Financial knowledge fallback...")

                # Extract ticker from query
                ticker_match = re.search(r'\b[A-Z]{2,5}\b', query.upper())
                if ticker_match:
                    ticker = ticker_match.group()

                    # Provide general financial context with 2025 awareness
                    financial_context = f"""
Financial Information Search for {ticker} ({current_year}):

Current market context suggests that investors are focusing on:
• Earnings performance and guidance for {current_year}
• Revenue growth trends in the current economic environment
• Market sentiment and analyst ratings
• The MOAT and market positioning of the company (key competitive advantages) 
• Industry-specific developments in {current_year}
• Economic indicators impact on stock performance

For detailed {ticker} analysis, consider checking:
• Company investor relations page for latest {current_year} reports
• SEC filings and most recent earnings reports
• Financial news sources like Bloomberg, Reuters, CNBC for {current_year} coverage
• Analyst reports from major investment banks (latest updates)
"""
                    results.append(f"1. Financial Market Context for {ticker} ({current_year})\n   {financial_context.strip()}\n   Source: Financial Knowledge Base\n")
                    search_successful = True
                    print(f"   ✅ Added {current_year} financial context for {ticker}")

            except Exception as e:
                print(f"   ⚠️  Financial fallback failed: {str(e)}")

        # Compile results
        if results:
            final_results = "\n".join(results)
            print(f"   📊 SEARCH SUMMARY: {len(results)} results, {len(final_results)} characters")

            # Add verification header with 2025 context
            verification_header = f"""
🔍 STRATEGIC WEB SEARCH RESULTS - {datetime.now().strftime('%H:%M:%S')}
Query: "{query}" (with {current_year} context)
Results found: {len(results)}
Status: {'SUCCESS' if search_successful else 'LIMITED'}
Strategy used: {'Multi-approach' if search_successful else 'Knowledge fallback'}
Year Context: {current_year} awareness applied
{'='*60}

"""
            return verification_header + final_results
        else:
            print("   ❌ No results found with any strategy")
            return f"🚨 Strategic search found no results for: {query}\nSuggestion: Try more specific or simpler search terms."

    except Exception as e:
        error_msg = f"Strategic search error: {str(e)}"
        print(f"   ❌ ERROR: {error_msg}")
        return f"🚨 STRATEGIC SEARCH FAILED: {error_msg}"

@tool
def get_stock_data(ticker: str) -> dict:
    """Get comprehensive stock data including price, metrics, and company info"""
    print(f"📊 FETCHING STOCK DATA for {ticker.upper()}")

    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        hist = stock.history(period="1y")

        # Calculate key metrics
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        year_high = hist['High'].max() if len(hist) > 0 else 0
        year_low = hist['Low'].min() if len(hist) > 0 else 0

        data = {
            'ticker': ticker.upper(),
            'company_name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'current_price': current_price,
            'market_cap': info.get('marketCap', 0),
            'current_pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe_ratio': info.get('forwardPE', 'N/A'),
            'price_to_book': info.get('priceToBook', 'N/A'),
            'debt_to_equity': info.get('debtToEquity', 'N/A'),
            'revenue_growth': info.get('revenueGrowth', 'N/A'),
            'profit_margins': info.get('profitMargins', 'N/A'),
            'year_high': year_high,
            'year_low': year_low,
            'price_change_1y': ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100) if len(hist) > 0 else 0,
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            'analyst_rating': info.get('recommendationKey', 'N/A')
        }

        print(f"   ✅ Retrieved data for {data['company_name']} - ${current_price}")
        return data

    except Exception as e:
        error_msg = f"Error retrieving data for {ticker}: {str(e)}"
        print(f"   ❌ ERROR: {error_msg}")
        return {'error': error_msg}

@tool
def enhanced_get_recent_news(ticker: str) -> str:
    """Enhanced news retrieval with strategic fallbacks"""
    print(f"📰 ENHANCED NEWS FETCH for {ticker.upper()}")

    try:
        # Try yfinance first
        stock = yf.Ticker(ticker.upper())
        news = stock.news

        if news and len(news) > 0:
            print(f"   ✅ Retrieved {len(news)} news articles from yfinance")

            news_text = f"Recent news for {ticker.upper()}:\n\n"

            for i, article in enumerate(news[:5], 1):
                title = article.get('title', 'No title')
                summary = article.get('summary', 'No summary available')
                publisher = article.get('publisher', 'Unknown')
                publish_time = datetime.fromtimestamp(article.get('providerPublishTime', 0))

                news_text += f"{i}. {title}\n"
                news_text += f"   Publisher: {publisher}\n"
                news_text += f"   Date: {publish_time.strftime('%Y-%m-%d %H:%M')}\n"
                news_text += f"   Summary: {summary[:200]}...\n\n"

            return news_text
        else:
            print(f"   ⚠️  No yfinance news, trying strategic search...")
            # Fallback to strategic search
            return strategic_web_search(f"{ticker} stock news recent earnings", 3)

    except Exception as e:
        print(f"   ⚠️  News fetch failed, using strategic search: {str(e)}")
        # Fallback to strategic search
        return strategic_web_search(f"{ticker} stock latest news", 3)

# =============================================================================
# MODEL CONFIGURATION AND SYSTEM PROMPT
# =============================================================================

def setup_claude_model():
    """Setup Claude model configuration"""
    return BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name="us-east-1",
        additional_request_fields={
            "thinking": {"type": "disabled"},
            "max_tokens": 4000,
            "temperature": 0.1
        }
    )

def create_system_prompt():
    """Create enhanced system prompt with strategic search integration"""
    return f"""You are "Stock Analysis Expert", a sophisticated financial analysis assistant with strategic search integration capabilities. You are acting as a psuedo investment analysis from goldman sachs or one of the top hedge funds in the world, with a Harvard MBA, so please format responses as such in complete sentences with detailed investment explanation as one of your peers will be utilizing your report.

**CURRENT DATE CONTEXT:**
Today's date is {datetime.now().strftime("%B %d, %Y")}. When analyzing stocks and interpreting search results, prioritize the most recent information available and note when data may be outdated.

**CRITICAL SEARCH INTEGRATION REQUIREMENTS:**
- ALWAYS explicitly reference specific search results when available
- Quote relevant findings from strategic web searches
- Acknowledge when search data is limited or when fallback strategies were used
- Show clear connection between search results and your bull/bear analysis
- Note the recency of information and prioritize 2024-2025 data over older information

**ANALYSIS FRAMEWORK:**
1. **Data Collection** (use ALL tools strategically):
   - get_stock_data (comprehensive financial metrics)
   - enhanced_get_recent_news (news with strategic fallbacks)
   - strategic_web_search (multi-approach search with 2025 context)

2. **Search Integration Requirements**:
   - Reference specific search findings in bull/bear cases
   - Quote relevant information from search results
   - Acknowledge search limitations and fallback strategies used
   - Show how search data influenced your investment perspective
   - Note when data is from 2023 vs 2024-2025

**OUTPUT FORMAT:**
1. **Executive Summary** (5-6 sentences including an overview of the company and their market positioning)
2. **Key Metrics Snapshot**
3. **🐂 BULL CASE** (4-6 detailed positions containing 2-4 sentences with search evidence when available)
4. **🐻 BEAR CASE** (4-6 detailed positions containing 2-4 sentences with search evidence when available)
5. **📊 INVESTMENT TAKEAWAY**
6. **🔍 SEARCH INTEGRATION SUMMARY** (mandatory section)
7. **🤔 ANALYTICAL REASONING** (detailed investment analysis opinion like you are a goldman sachs analyst) 

**SEARCH INTEGRATION SUMMARY REQUIREMENTS:**
You MUST include a "🔍 SEARCH INTEGRATION SUMMARY" section that explicitly states:
- What strategic search queries were executed (with 2025 context)
- Which search strategies were successful (Instant API, HTML, Knowledge Fallback)
- Key findings from successful searches
- How search data influenced your bull/bear analysis
- Any limitations encountered and fallback strategies used
- The recency of information found (2023 vs 2024-2025)

**TRANSPARENCY REQUIREMENTS:**
- Be transparent about which search strategies worked
- Acknowledge when searches were limited and knowledge fallbacks were used
- Show specific connections between search findings and your analysis
- Explain how different search strategies provided different types of insights
- Note when information may be outdated (pre-2024)

Remember: This is educational analysis, not investment advice. Always show your reasoning process and the recency of your data sources."""

# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_stock(ticker: str, verbose: bool = True, wait_time: int = 3) -> dict:
    """
    Analyze a stock ticker using strategic search integration with 2025 context.

    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'MSFT')
        verbose (bool): Whether to print progress messages (default: True)
        wait_time (int): Seconds to wait before analysis (default: 3)

    Returns:
        dict: Analysis results containing:
            - 'success': bool indicating if analysis completed
            - 'ticker': the analyzed ticker
            - 'analysis': the complete analysis text
            - 'duration': analysis duration in seconds
            - 'search_calls': number of strategic searches performed
            - 'error': error message if analysis failed
    """

    # Validate ticker input
    ticker = ticker.strip().upper()
    if not ticker.isalpha() or len(ticker) < 1 or len(ticker) > 5:
        return {
            'success': False,
            'ticker': ticker,
            'analysis': None,
            'duration': 0,
            'search_calls': 0,
            'error': 'Invalid ticker format. Please use 1-5 letters.'
        }

    current_date = datetime.now().strftime("%B %d, %Y")

    if verbose:
        print(f"🎯 ANALYZING {ticker}")
        print("="*50)
        print("🔄 Using strategic multi-approach search...")
        print(f"📅 Analysis Date: {current_date}")

    try:
        # Setup model and system prompt
        claude_37_model = setup_claude_model()
        enhanced_system_prompt = create_system_prompt()

        # Create fresh strategic agent
        if verbose:
            print("🔄 CREATING STRATEGIC AGENT (with enhanced search capabilities)")

        strategic_agent = Agent(
            model=claude_37_model,
            system_prompt=enhanced_system_prompt,
            tools=[
                get_stock_data,
                enhanced_get_recent_news,
                strategic_web_search,
            ]
        )

        if verbose:
            print("✅ Strategic agent created")
            print(f"⏱️  Waiting {wait_time} seconds...")

        time.sleep(wait_time)
        analysis_start_time = time.time()

        # Run the analysis
        result = strategic_agent(f"""
        Analyze {ticker} stock using strategic search integration with 2025 context.
        
        CURRENT DATE: {current_date}
        
        REQUIREMENTS:
        1. Use get_stock_data for comprehensive financial metrics
        2. Use enhanced_get_recent_news for market sentiment (with strategic fallbacks)
        3. Use strategic_web_search for current market context about {ticker} (searches will include 2025 context)
        4. EXPLICITLY reference any search findings in your analysis
        5. Include the required "🔍 SEARCH INTEGRATION SUMMARY" section
        6. Show how search results influenced your bull/bear cases
        7. Be transparent about which search strategies worked and which didn't
        8. Note the recency of information - prioritize 2024-2025 data over older information
        
        The strategic search uses:
        - DuckDuckGo Instant API (most reliable)
        - DuckDuckGo HTML search with anti-blocking headers
        - Financial knowledge fallbacks when searches are blocked
        - Automatic 2025 context addition to financial queries
        
        Make sure to integrate any findings and acknowledge the search strategy used.
        When you find information from 2023, note that this may be outdated and seek more recent data.
        """)

        analysis_end_time = time.time()
        analysis_duration = analysis_end_time - analysis_start_time

        # Count search calls
        search_calls = count_strategic_searches(strategic_agent)

        if verbose:
            print("✅ ANALYSIS COMPLETE!")
            print(f"⏱️  Duration: {analysis_duration:.1f} seconds")
            print(f"🔍 Strategic searches performed: {search_calls}")

        return {
            'success': True,
            'ticker': ticker,
            'analysis': result,
            'duration': analysis_duration,
            'search_calls': search_calls,
            'error': None,
            'agent': strategic_agent  # Include agent for further inspection if needed
        }

    except Exception as e:
        error_msg = f"Analysis failed for {ticker}: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")

        return {
            'success': False,
            'ticker': ticker,
            'analysis': None,
            'duration': 0,
            'search_calls': 0,
            'error': error_msg,
            'agent': None
        }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def count_strategic_searches(agent) -> int:
    """Count the number of strategic search calls made by the agent"""
    search_calls = 0

    for message in agent.messages:
        if message['role'] == 'assistant':
            for content in message['content']:
                if isinstance(content, dict) and 'toolUse' in content:
                    tool_use = content['toolUse']
                    if 'strategic_web_search' in tool_use['name']:
                        search_calls += 1

    return search_calls

def get_analysis_summary(result_dict: dict) -> str:
    """Extract a brief summary from the analysis result"""
    if not result_dict['success'] or not result_dict['analysis']:
        return f"Analysis failed for {result_dict['ticker']}: {result_dict.get('error', 'Unknown error')}"

    analysis_text = result_dict['analysis']

    # Try to extract the executive summary
    lines = analysis_text.split('\n')
    for i, line in enumerate(lines):
        if 'Executive Summary' in line and i + 1 < len(lines):
            return lines[i + 1].strip()

    # Fallback: return first meaningful line
    for line in lines:
        if line.strip() and not line.startswith('#') and len(line.strip()) > 50:
            return line.strip()

    return f"Analysis completed for {result_dict['ticker']}"

# =============================================================================
# BATCH ANALYSIS FUNCTION (BONUS)
# =============================================================================

def analyze_multiple_stocks(tickers: list, verbose: bool = True, wait_between: int = 5) -> dict:
    """
    Analyze multiple stocks in sequence.

    Args:
        tickers (list): List of ticker symbols
        verbose (bool): Whether to print progress messages
        wait_between (int): Seconds to wait between analyses

    Returns:
        dict: Results for all tickers
    """

    results = {}
    total_start_time = time.time()

    if verbose:
        print(f"🎯 BATCH ANALYSIS: {len(tickers)} stocks")
        print("="*60)

    for i, ticker in enumerate(tickers, 1):
        if verbose:
            print(f"\n📈 [{i}/{len(tickers)}] Analyzing {ticker}...")

        result = analyze_stock(ticker, verbose=verbose, wait_time=2)
        results[ticker] = result

        if verbose:
            if result['success']:
                summary = get_analysis_summary(result)
                print(f"✅ {ticker}: {summary[:100]}...")
            else:
                print(f"❌ {ticker}: {result['error']}")

        # Wait between analyses (except for the last one)
        if i < len(tickers) and wait_between > 0:
            if verbose:
                print(f"⏱️  Waiting {wait_between} seconds before next analysis...")
            time.sleep(wait_between)

    total_duration = time.time() - total_start_time

    if verbose:
        successful = sum(1 for r in results.values() if r['success'])
        print(f"\n🏆 BATCH COMPLETE: {successful}/{len(tickers)} successful")
        print(f"⏱️  Total duration: {total_duration:.1f} seconds")

    return {
        'results': results,
        'total_duration': total_duration,
        'successful_count': sum(1 for r in results.values() if r['success']),
        'total_count': len(tickers)
    }

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def example_usage():
    """Example of how to use the analyze_stock function"""

    # Example 1: Simple analysis
    print("=== EXAMPLE 1: Simple Analysis ===")
    result = analyze_stock('AAPL')

    if result['success']:
        print(f"✅ Analysis completed for {result['ticker']}")
        print(f"Duration: {result['duration']:.1f} seconds")
        print(f"Search calls: {result['search_calls']}")
        # The full analysis is in result['analysis']
    else:
        print(f"❌ Analysis failed: {result['error']}")

    # Example 2: Silent analysis (no verbose output)
    print("\n=== EXAMPLE 2: Silent Analysis ===")
    result = analyze_stock('TSLA', verbose=False)
    print(f"Silent analysis result: {get_analysis_summary(result)}")

    # Example 3: Batch analysis
    print("\n=== EXAMPLE 3: Batch Analysis ===")
    batch_results = analyze_multiple_stocks(['MSFT', 'GOOGL'], verbose=True, wait_between=3)

    print(f"Batch results: {batch_results['successful_count']}/{batch_results['total_count']} successful")

# =============================================================================
# INTEGRATION READY - USE THESE FUNCTIONS IN YOUR SOLUTION
# =============================================================================

# Main function for single stock analysis
# result = analyze_stock('AAPL')

# Function for multiple stocks
# batch_results = analyze_multiple_stocks(['AAPL', 'TSLA', 'MSFT'])

# To integrate with your existing solution, simply call:
# analysis_result = analyze_stock(user_provided_ticker)
# if analysis_result['success']:
#     display_analysis(analysis_result['analysis'])
# else:
#     show_error(analysis_result['error'])


import re

def parse_stock_analysis(analysis_text: str) -> dict:
    """
    Parse stock analysis text into structured sections for UI display.

    Args:
        analysis_text (str): The complete analysis text from analyze_stock()

    Returns:
        dict: Parsed sections containing:
            - 'company_info': Executive Summary + Key Metrics + Search Integration Summary
            - 'bull_case': Bull case points only
            - 'bear_case': Bear case points only
            - 'analytical_reasoning': Investment Takeaway + Analytical Reasoning (no Search Integration Summary)
            - 'raw_text': Original text for fallback
    """

    if not analysis_text or not isinstance(analysis_text, str):
        return {
            'company_info': 'Analysis text not available',
            'bull_case': 'Bull case not available',
            'bear_case': 'Bear case not available',
            'analytical_reasoning': 'Analytical reasoning not available',
            'raw_text': analysis_text or ''
        }

    # Find the positions of each section marker
    section_positions = {}

    # Define the exact section markers to look for
    markers = [
        '## Executive Summary',
        '## 🐂 BULL CASE',
        '## 🐻 BEAR CASE',
        '## 📊 INVESTMENT TAKEAWAY',
        '## 🔍 SEARCH INTEGRATION SUMMARY',
        '## 🤔 ANALYTICAL REASONING'
    ]

    # Find position of each marker
    for marker in markers:
        pos = analysis_text.find(marker)
        if pos != -1:
            section_positions[marker] = pos

    # Extract sections based on your specific requirements

    # Section 1: Executive Summary through Bull Case (excluding Bull Case header)
    start_pos = section_positions.get('## Executive Summary', 0)
    end_pos = section_positions.get('## 🐂 BULL CASE', len(analysis_text))
    section_1_part1 = analysis_text[start_pos:end_pos].strip()

    # Section 1 addition: Search Integration Summary through Analytical Reasoning (excluding Analytical Reasoning header)
    start_pos = section_positions.get('## 🔍 SEARCH INTEGRATION SUMMARY', len(analysis_text))
    end_pos = section_positions.get('## 🤔 ANALYTICAL REASONING', len(analysis_text))
    section_1_part2 = analysis_text[start_pos:end_pos].strip()

    # Combine Section 1 parts
    company_info = f"{section_1_part1}\n\n{section_1_part2}".strip()

    # Section 2: Bull Case through Bear Case (excluding Bear Case header)
    start_pos = section_positions.get('## 🐂 BULL CASE', len(analysis_text))
    end_pos = section_positions.get('## 🐻 BEAR CASE', len(analysis_text))
    bull_case = analysis_text[start_pos:end_pos].strip()

    # Section 3: Bear Case through Investment Takeaway (excluding Investment Takeaway header)
    start_pos = section_positions.get('## 🐻 BEAR CASE', len(analysis_text))
    end_pos = section_positions.get('## 📊 INVESTMENT TAKEAWAY', len(analysis_text))
    bear_case = analysis_text[start_pos:end_pos].strip()

    # Section 4: Investment Takeaway through Search Integration Summary (excluding Search Integration Summary header)
    # FIXED: This should stop before Search Integration Summary to avoid duplication
    start_pos = section_positions.get('## 📊 INVESTMENT TAKEAWAY', len(analysis_text))
    end_pos = section_positions.get('## 🔍 SEARCH INTEGRATION SUMMARY', len(analysis_text))
    section_4_part1 = analysis_text[start_pos:end_pos].strip()

    # Section 4 addition: Analytical Reasoning through end
    start_pos = section_positions.get('## 🤔 ANALYTICAL REASONING', len(analysis_text))
    section_4_part2 = analysis_text[start_pos:].strip()

    # Combine Section 4 parts (Investment Takeaway + Analytical Reasoning, no Search Integration Summary)
    analytical_reasoning = f"{section_4_part1}\n\n{section_4_part2}".strip()

    # Clean up sections
    def clean_section(text):
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        return text.strip()

    return {
        'company_info': clean_section(company_info),
        'bull_case': clean_section(bull_case),
        'bear_case': clean_section(bear_case),
        'analytical_reasoning': clean_section(analytical_reasoning),
        'raw_text': analysis_text
    }

def extract_key_metrics(company_info_section: str) -> dict:
    """
    Extract key financial metrics from the company info section.

    Args:
        company_info_section (str): The company info section text

    Returns:
        dict: Extracted metrics like price, market cap, PE ratio, etc.
    """

    metrics = {}

    # Define patterns to extract metrics
    patterns = {
        'current_price': r'Current Price[:\s]*\$?([\d,]+\.?\d*)',
        'market_cap': r'Market Cap[:\s]*\$?([\d,]+\.?\d*)\s*(trillion|billion|million)?',
        'pe_ratio': r'P/E Ratio[:\s]*([\d,]+\.?\d*)',
        'revenue_growth': r'Revenue Growth[:\s]*([\d,]+\.?\d*)%?',
        'profit_margin': r'Profit Margin[:\s]*([\d,]+\.?\d*)%?',
        'dividend_yield': r'Dividend Yield[:\s]*([\d,]+\.?\d*)%?',
        'analyst_rating': r'Analyst Rating[:\s]*([A-Za-z\s]+)',
        'year_high': r'52-Week.*?[\$\s]*([\d,]+\.?\d*).*?-.*?\$?([\d,]+\.?\d*)',
        'price_change_1y': r'1-Year Price Change[:\s]*[+\-]?([\d,]+\.?\d*)%?'
    }

    for metric_name, pattern in patterns.items():
        match = re.search(pattern, company_info_section, re.IGNORECASE)
        if match:
            if metric_name == 'year_high':
                # Special handling for 52-week range
                metrics['year_low'] = match.group(1)
                metrics['year_high'] = match.group(2)
            else:
                metrics[metric_name] = match.group(1).strip()

    return metrics

def get_executive_summary(company_info_section: str) -> str:
    """
    Extract just the executive summary from company info section.

    Args:
        company_info_section (str): The company info section text

    Returns:
        str: Executive summary text
    """

    lines = company_info_section.split('\n')
    summary_started = False
    summary_lines = []

    for line in lines:
        if 'Executive Summary' in line:
            summary_started = True
            continue
        elif summary_started:
            if line.strip() and not line.startswith('#') and not line.startswith('##'):
                if any(keyword in line for keyword in ['Key Metrics', 'Metrics Snapshot', '🔍']):
                    break
                summary_lines.append(line.strip())
            elif line.strip() == '':
                continue
            else:
                break

    return ' '.join(summary_lines).strip()

# Test the parser with your actual analysis
def test_parser_with_real_data():
    """Test the parser with the actual AAPL analysis output"""

    real_analysis = """# Apple Inc. (AAPL) Stock Analysis - June 3, 2025

## Executive Summary
Apple Inc. continues to demonstrate resilience in 2025 with solid Q2 financial results showing 5% revenue growth and 8% EPS growth year-over-year, though the stock currently trades at $203.27, approximately 22% below its 52-week high of $259.47.

## Key Metrics Snapshot
- **Current Price**: $203.27
- **Market Cap**: $3.04 trillion
- **P/E Ratio**: 24.46
- **Revenue Growth**: 5.1%
- **Profit Margin**: 24.3%
- **Dividend Yield**: 0.52%
- **Analyst Rating**: Buy
- **52-Week Range**: $168.99 - $259.47

## 🐂 BULL CASE
1. **Strong Q2 2025 Financial Performance**: According to search results, "Apple today announced financial results for its fiscal 2025 second quarter ended March 29, 2025. The Company posted quarterly revenue of $95.4 billion, up 5 percent year over year, and quarterly diluted earnings per share of $1.65, up 8 percent year over year" (Source: apple.com/newsroom/2025/05).

2. **Continued Product Innovation Pipeline**: Search results reveal that Apple is preparing to launch the iPhone 17 lineup in September 2025 with potentially significant innovations. According to MacRumors (May 30, 2025), the iPhone 17 models could feature larger display sizes, and Korea's Sisa Journal reported in January 2025 that "the so-called iPhone 17 Air will be 6.25mm thick" with pricing "in the same price range as the iPhone 16 Plus."

3. **Analyst Confidence**: Multiple search results indicate strong analyst support, with "70 analysts [giving] Apple (AAPL) a consensus rating of Buy" (Public.com), suggesting continued institutional confidence in Apple's business model and growth prospects.

4. **Healthy Profit Margins**: With a profit margin of 24.3%, Apple continues to maintain industry-leading profitability, demonstrating pricing power and operational efficiency despite competitive pressures in the consumer electronics market.

## 🐻 BEAR CASE
1. **Current Price Weakness**: The stock is currently trading at $203.27, which is approximately 22% below its 52-week high of $259.47, indicating potential investor concerns about growth prospects or market positioning.

2. **High Valuation Metrics**: With a P/E ratio of 24.46 and an extremely high price-to-book ratio of 45.46, Apple trades at premium valuations that could limit upside potential, especially if growth rates slow further.

3. **Debt Concerns**: Apple's debt-to-equity ratio of 146.99% is relatively high, which could become problematic in the current higher interest rate environment if refinancing becomes necessary.

4. **Potential Market Saturation**: Search results hint at concerns about "increasing saturation in global smartphone markets" (tradingnews.com), which could limit Apple's growth potential in its core iPhone business despite the upcoming iPhone 17 launch.

## 📊 INVESTMENT TAKEAWAY
Apple remains a solid blue-chip technology investment with strong fundamentals, consistent profitability, and continued product innovation. The current price point ($203.27) represents a potential entry opportunity at approximately 22% below recent highs, with analyst consensus maintaining a "Buy" rating. However, investors should be mindful of the premium valuation metrics and potential growth challenges in saturated markets. The upcoming iPhone 17 launch in September 2025 could serve as a catalyst for stock performance in the second half of 2025.

## 🔍 SEARCH INTEGRATION SUMMARY
- **Search Queries Executed**:
  1. "Apple AAPL stock performance 2025 latest news" (successful)
  2. "Apple Vision Pro sales performance 2025 latest developments" (no results)
  3. "Apple AI features 2025 WWDC announcements" (no results)
  4. "Apple iPhone 17 rumors 2025" (successful)

- **Successful Search Strategies**:
  - Multi-approach strategy yielded results for general Apple stock performance and iPhone 17 rumors
  - Most valuable information came from the first and fourth searches
  - 2025 context awareness was successfully applied to searches

- **Key Search Findings**:
  - Q2 2025 financial results showing 5% revenue growth and 8% EPS growth (very recent - May 2025)
  - iPhone 17 launch details expected for September 2025 (from May 30, 2025 MacRumors article)
  - Analyst consensus rating of "Buy" with various price targets
  - Potential concerns about smartphone market saturation

- **Search Limitations**:
  - No results for Vision Pro sales performance or AI features queries
  - Enhanced news retrieval tool returned no usable news articles
  - Had to rely on web search for recent news and developments

- **Recency of Information**:
  - Most search results provided 2025 data (Q2 2025 earnings, May 2025 iPhone rumors)
  - Financial metrics from get_stock_data appear to be current as of June 2025

## 🤔 ANALYTICAL REASONING
Apple's current position reflects a company that continues to execute well financially (as evidenced by the Q2 2025 results) while facing some market skepticism about future growth potential. The stock's current trading level at $203.27 represents a significant discount from its 52-week high, suggesting investor concerns despite solid fundamentals.

The upcoming iPhone 17 launch in September 2025 represents a potential catalyst, with search results indicating continued innovation in the product line. However, the high valuation metrics (P/E of 24.46, P/B of 45.46) suggest that Apple needs to maintain its growth trajectory to justify current price levels.

The analyst consensus "Buy" rating indicates professional confidence in Apple's prospects, but investors should consider both the premium valuation and potential market saturation concerns when making investment decisions. Apple's strong profit margins (24.3%) and consistent revenue growth (5.1%) provide a solid foundation, but the high debt-to-equity ratio (146.99%) warrants monitoring in the current interest rate environment."""

    # Parse the real analysis
    parsed = parse_stock_analysis(real_analysis)

    print("=== TESTING WITH REAL AAPL ANALYSIS ===")
    print("\n📋 SECTION 1 - COMPANY INFO:")
    print(parsed['company_info'])
    print("\n📈 SECTION 2 - BULL CASE:")
    print(parsed['bull_case'])
    print("\n📉 SECTION 3 - BEAR CASE:")
    print(parsed['bear_case'])
    print("\n🧠 SECTION 4 - ANALYTICAL REASONING:")
    print(parsed['analytical_reasoning'])
    print("\n💰 BONUS - INVESTMENT TAKEAWAY:")
    print(parsed['investment_takeaway'])

# Run the test
# test_parser_with_real_data()

def analyze_and_parse_stock(ticker: str, verbose: bool = False) -> dict:
    """
    Complete function that analyzes stock and returns parsed sections.

    Args:
        ticker (str): Stock ticker symbol
        verbose (bool): Whether to print progress messages

    Returns:
        dict: Contains both analysis results and parsed sections
    """

    # Run the analysis (assumes analyze_stock function exists)
    analysis_result = analyze_stock(ticker, verbose=verbose)

    if not analysis_result['success']:
        return {
            'success': False,
            'error': analysis_result['error'],
            'ticker': ticker,
            'parsed_sections': None,
            'metrics': None
        }

    # Convert AgentResult to string
    analysis_text = str(analysis_result.get('analysis', ''))
    if verbose:
        print(f"Debug: Analysis text length: {len(analysis_text)}")
        print(f"Debug: First 200 chars: {analysis_text[:200]}...")

    # Parse the analysis text into sections
    parsed_sections = parse_stock_analysis(analysis_text)

    # Extract key metrics
    metrics = extract_key_metrics(parsed_sections['company_info'])

    # Get executive summary
    executive_summary = get_executive_summary(parsed_sections['company_info'])

    return {
        'success': True,
        'ticker': ticker,
        'duration': analysis_result['duration'],
        'search_calls': analysis_result['search_calls'],
        'parsed_sections': parsed_sections,
        'metrics': metrics,
        'executive_summary': executive_summary,
        'raw_analysis': analysis_text
    }

# Quick test function to verify the parser works with your OSCR data



