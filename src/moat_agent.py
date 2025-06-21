# =============================================================================
# MOAT AGENT - PRODUCTION VERSION
# Competitive MOAT and Market Positioning Analysis
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

from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# AWS CONFIGURATION
# =============================================================================

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = 'us-east-1'

try:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    models = bedrock.list_foundation_models()
except Exception as e:
    pass


#Competitors Search
@tool
def identify_competitors(ticker: str) -> str:
    """Specifically search for competitor names and competitive threats"""
    print(f"🎯 Identifying competitors for {ticker}...")

    competitor_queries = [
        f"{ticker} main competitors rivals",
        f"{ticker} competitive landscape analysis",
        f"companies competing with {ticker}",
        f"{ticker} market share vs competitors",
        f"{ticker} industry competitive threats",
        f"who are {ticker} biggest competitors",
        f"{ticker} vs competition direct rivals"
    ]

    all_results = []
    for i, query in enumerate(competitor_queries, 1):
        print(f"   [{i}/{len(competitor_queries)}] Competitor search: {query}")
        try:
            result = strategic_web_search(query, 3)
            all_results.append(f"COMPETITOR SEARCH {i}: {query}\n{result}\n{'='*50}\n")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"   ❌ Competitor search failed: {e}")
            continue

    compiled_results = "\n".join(all_results)
    print(f"✅ Competitor identification complete: {len(all_results)} searches executed")

    return f"COMPREHENSIVE COMPETITOR INTELLIGENCE FOR {ticker}:\n\n{compiled_results}"


# =============================================================================
# STRATEGIC WEB SEARCH TOOLS
# =============================================================================

@tool
def strategic_web_search(query: str, num_results: int = 5) -> str:
    """Strategic web search using multiple DuckDuckGo approaches to avoid blocking """
    current_year = datetime.now().year
    current_date = datetime.now().strftime("%Y-%m")

    if any(term in query.lower() for term in ['stock', 'competitive', 'MOAT', 'competition', 'market positioning']):
        if str(current_year) not in query and 'recent' in query.lower():
            query = f"{query} {current_year}"
        elif 'latest' in query.lower() or 'recent' in query.lower():
            query = f"{query} {current_date}"

    try:
        results = []
        search_successful = False

        # DuckDuckGo Instant API
        try:
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
                abstract = data.get('Abstract', '')
                abstract_source = data.get('AbstractSource', '')

                if abstract and len(abstract) > 50:
                    results.append(f"1. {abstract_source} - Key Information\n   {abstract}\n   Source: DuckDuckGo Instant API\n")
                    search_successful = True

                related_topics = data.get('RelatedTopics', [])
                for i, topic in enumerate(related_topics[:3], len(results) + 1):
                    if isinstance(topic, dict) and 'Text' in topic:
                        text = topic['Text']
                        if len(text) > 30:
                            results.append(f"{i}. Related Information\n   {text}\n   Source: DuckDuckGo Related Topics\n")
                            search_successful = True

        except Exception as e:
            pass

        time.sleep(1)

        # DuckDuckGo HTML Search (fallback)
        if len(results) < 2:
            try:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
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

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    search_results = []
                    selectors = ['.result', '.links_main', '.result__body', 'div[class*="result"]']

                    for selector in selectors:
                        found_results = soup.select(selector)
                        if found_results:
                            search_results = found_results
                            break

                    for i, result in enumerate(search_results[:num_results], len(results) + 1):
                        try:
                            title = None
                            title_selectors = ['.result__title a', '.result__a', 'h2 a', 'h3 a', 'a']

                            for title_sel in title_selectors:
                                title_elem = result.select_one(title_sel)
                                if title_elem:
                                    title = title_elem.get_text().strip()
                                    if len(title) > 10:
                                        break

                            snippet = None
                            snippet_selectors = ['.result__snippet', '.result__body', '.snippet', 'p']

                            for snippet_sel in snippet_selectors:
                                snippet_elem = result.select_one(snippet_sel)
                                if snippet_elem:
                                    snippet = snippet_elem.get_text().strip()
                                    if len(snippet) > 30:
                                        break

                            url_elem = result.select_one('a[href]')
                            url = url_elem.get('href', '') if url_elem else ''

                            if title and snippet and len(snippet) > 30:
                                results.append(f"{i}. {title}\n   {snippet}\n   URL: {url}\n")
                                search_successful = True

                        except Exception as e:
                            continue

            except Exception as e:
                pass

        # Financial knowledge fallback
        if not search_successful and any(term in query.lower() for term in ['stock', 'competition', 'MOAT', 'competitive advantage', 'market position']):
            try:
                ticker_match = re.search(r'\b[A-Z]{2,5}\b', query.upper())
                if ticker_match:
                    ticker = ticker_match.group()
                    financial_context = f"""
Competitive Advantages, Market Positioning, and MOAT Search for {ticker} ({current_year}):

Current market context suggests that investors are focusing on:
• The market positioning for the company in {current_year}
• Competitive trends in the current economic environment
• Market sentiment on the competitive advantages of the company
• The MOAT and market positioning of the company (key competitive advantages) 
• Industry-specific developments in {current_year}

For detailed {ticker} analysis, consider checking:
• Company investor relations page for latest {current_year} reports
• SEC filings and most recent earnings reports
• Financial news sources like Bloomberg, Reuters, CNBC for {current_year} coverage
• Analyst reports from major investment banks (latest updates)
"""
                    results.append(f"1. Market Context for {ticker} ({current_year})\n   {financial_context.strip()}\n   Source: Market Knowledge Base\n")
                    search_successful = True

            except Exception as e:
                pass

        if results:
            final_results = "\n".join(results)
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
            return f"🚨 Strategic search found no results for: {query}\nSuggestion: Try more specific or simpler search terms."

    except Exception as e:
        error_msg = f"Strategic search error: {str(e)}"
        return f"🚨 STRATEGIC SEARCH FAILED: {error_msg}"

@tool
def get_stock_data(ticker: str) -> dict:
    """Get comprehensive stock data including price, metrics, and company info"""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        hist = stock.history(period="1y")

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

        return data

    except Exception as e:
        error_msg = f"Error retrieving data for {ticker}: {str(e)}"
        return {'error': error_msg}

@tool
def enhanced_get_recent_news(ticker: str) -> str:
    """Enhanced news retrieval with strategic fallbacks"""
    try:
        stock = yf.Ticker(ticker.upper())
        news = stock.news

        if news and len(news) > 0:
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
            return strategic_web_search(f"{ticker} stock news recent earnings", 3)

    except Exception as e:
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
    """Create enhanced system prompt optimized for MOAT and competitive analysis"""
    return f"""You are "Competitive Strategy Analyst", an elite institutional investment analyst specializing in competitive moats, market positioning, strategic advantages, and competitve research. You work for a top-tier hedge fund and possess deep expertise in identifying sustainable competitive advantages that create long-term shareholder value but are highly critical and take into consideration competitors and future trends.

**CURRENT DATE CONTEXT:**
Today's date is {datetime.now().strftime("%B %d, %Y")}. Prioritize the most recent market developments and competitive dynamics.

**CORE ANALYTICAL FOCUS:**
Your primary mission is to evaluate:
1. **Competitive Moats**: Identify and analyze maintainable competitive advantages
2. **Market Positioning**: Assess the company's strategic position within its industry and competitor approaches
3. **Competitive Landscape & Review**: In depth analysis of the competitors, competitive threats, and the differentiation between the company and competitors
4. **Strategic Durability**: Evaluate the sustainability of competitive advantages over time versus established or emerging threats from competitors.


**CRITICAL SEARCH INTEGRATION:**
- ALWAYS cite specific search results with source attribution
- Quote key findings that support your competitive analysis
- Explicitly connect search data to moat strength and market positioning
- Prioritize 2024-2025 data over historical information

**REQUIRED TOOLS USAGE:**
1. **get_stock_data**: For financial context and valuation metrics
2. **enhanced_get_recent_news**: For market sentiment and recent developments
3. **strategic_web_search**: For competitive intelligence and market positioning data
4. **identify_competitors**: MANDATORY step to identify specific competitor names and threats


**MANDATORY OUTPUT STRUCTURE:**

## EXECUTIVE SUMMARY (in depth analysis) 
(6-12 sentences focusing on competitive position, moat strength, and market dynamics)

## MOAT ANALYSIS (in depth analysis) 
**Defensive Moats** (What protects the business):
- [Analyze barriers to entry, switching costs, network effects, brand strength, regulatory advantages]

**Offensive Moats** (What drives expansion):
- [Analyze scalability advantages, resource advantages, distribution advantages -- consider competitors]

**Moat Durability** (Sustainability over 5-10 years):
- [Assess threats to current advantages and evolution of competitive landscape -- consider competitors]

## MARKET POSITIONING (in depth analysis) 
**Industry Position**:
- [Market share, competitive ranking, industry dynamics, competitor names and perception relative to company]

**Strategic Positioning**:
- [Value proposition, customer segments, differentiation strategy -- consider competitors]

**Positioning Trends**:
- [How position is evolving, emerging opportunities/threats -- consider competitors]

## COMPETITIVE ADVANTAGES & LANDSCAPE (in depth analysis) 
**Core Competitive Advantages**:
- [Specific advantages with supporting evidence from searches. Highlight any competitor advantages in the market.]

**Competitive Threats**:
- [Direct and indirect competitors with those companies named, disruption risks]

**Competitive Approaches & Differences**:
- [How are other competitors navigating the space and what are the key differences]

**CITATION REQUIREMENTS:**
- Use quotation marks for direct quotes from search results
- Attribute sources clearly (e.g., "According to [Source Name]...")
- Connect each piece of evidence to specific competitive advantages
- Distinguish between confirmed facts and strategic speculation

This analysis serves institutional investment decision-making and should reflect the highest standards of competitive intelligence and strategic analysis."""

# =============================================================================
# MAIN ANALYSIS FUNCTION FOR WEB INTEGRATION
# =============================================================================

def analyze_stock_moat(ticker: str) -> dict:
    """
    Main function for web integration - analyzes stock's competitive moats and positioning

    Returns:
        dict: Analysis results formatted for web display
    """
    ticker = ticker.strip().upper()

    if not ticker.isalpha() or len(ticker) < 1 or len(ticker) > 5:
        return {
            'success': False,
            'error': 'Invalid ticker format. Please use 1-5 letters.',
            'sections': {
                'executive_summary': 'Analysis failed due to invalid ticker.',
                'moat_analysis': 'Please enter a valid stock ticker.',
                'market_positioning': 'Analysis unavailable.',
                'competitive_landscape': 'Analysis unavailable.'
            }
        }

    try:
        claude_37_model = setup_claude_model()
        enhanced_system_prompt = create_system_prompt()

        strategic_agent = Agent(
            model=claude_37_model,
            system_prompt=enhanced_system_prompt,
            tools=[
                get_stock_data,
                enhanced_get_recent_news,
                strategic_web_search,
                identify_competitors,
            ]
        )

        current_date = datetime.now().strftime("%B %d, %Y")
        analysis_start_time = time.time()

        # ADD THIS SECTION HERE - COMPETITOR INTELLIGENCE GATHERING
        print(f"🔍 Conducting competitor intelligence for {ticker}...")

        competitor_searches = [
            f"{ticker} main competitors 2025",
            f"{ticker} vs competitors market share",
            f"{ticker} competitive threats disruption",
            f"top differentiators for competitors of {ticker}",
            f"{ticker} industry competition analysis"
        ]

        competitor_intelligence = []
        for search_query in competitor_searches:
            print(f"   Searching: {search_query}")
            search_result = strategic_web_search(search_query, 3)
            competitor_intelligence.append(f"Query: {search_query}\n{search_result}\n{'='*50}\n")
            time.sleep(1)  # Rate limiting between searches

        # Combine all competitor intelligence
        compiled_competitor_data = "\n".join(competitor_intelligence)
        print(f"✅ Competitor intelligence gathered: {len(competitor_intelligence)} searches completed")

        # MODIFY THE EXISTING RESULT CALL TO INCLUDE COMPETITOR DATA
        result = strategic_agent(f"""
        Conduct a comprehensive competitive moat and market positioning analysis for {ticker} stock.
        
        CURRENT DATE: {current_date}
        
        COMPETITOR INTELLIGENCE ALREADY GATHERED:
        {compiled_competitor_data}
        
        CRITICAL: Use the competitor intelligence data above to identify specific competitor names and threats.
        
        ANALYTICAL MISSION:
        You are evaluating {ticker} as a potential high-conviction investment. Focus on:
        1. Sustainable competitive advantages (moats)
        2. Market positioning strength and evolution
        3. Competitive landscape dynamics with SPECIFIC COMPETITOR NAMES
        4. Strategic durability over 5-10 year horizon
        
        REQUIRED TOOL USAGE:
        1. get_stock_data: Gather financial metrics for competitive context
        2. enhanced_get_recent_news: Identify recent competitive developments
        3. strategic_web_search: Conduct additional targeted searches if needed
        4. identify_competitors: Understand how competitors are and then use strategic web_web_search to dive deeper into differences
        
        MANDATORY COMPETITOR REQUIREMENTS:
        - Identify at least 3-5 specific competitor company names from the intelligence gathered
        - For each named competitor, specify their exact threat to {ticker}
        - Distinguish between direct competitors, indirect competitors, and disruptors
        - Use the competitor intelligence data provided above as your primary source
        
        COMPETITIVE INTELLIGENCE PRIORITIES:
        - What are {ticker}'s most sustainable competitive advantages?
        - WHO are {ticker}'s main competitors BY NAME?
        - How is {ticker} positioned vs each named competitor?
        - What specific threats does each competitor pose?
        - How durable are {ticker}'s current advantages against named competitors?
        
        CRITICAL: Your analysis must include specific competitor names and their threats.
        Reference the competitor intelligence data gathered above.
        """)

        analysis_duration = time.time() - analysis_start_time
        analysis_text = str(result)

        # Parse the analysis into sections
        parsed_sections = parse_stock_analysis(analysis_text)

        return {
            'success': True,
            'ticker': ticker,
            'duration': analysis_duration,
            'sections': parsed_sections,
            'raw_analysis': analysis_text
        }

    except Exception as e:
        error_msg = f"Analysis failed for {ticker}: {str(e)}"
        return {
            'success': False,
            'error': error_msg,
            'sections': {
                'executive_summary': f'Analysis failed: {error_msg}',
                'moat_analysis': 'Analysis unavailable due to error.',
                'market_positioning': 'Analysis unavailable due to error.',
                'competitive_landscape': 'Analysis unavailable due to error.'
            }
        }

# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def parse_stock_analysis(analysis_text: str) -> dict:
    """Parse MOAT analysis text into structured sections for UI display"""

    if not analysis_text or not isinstance(analysis_text, str):
        return {
            'executive_summary': 'Analysis text not available',
            'moat_analysis': 'MOAT analysis not available',
            'market_positioning': 'Market positioning not available',
            'competitive_landscape': 'Competitive landscape not available'
        }

    # Define section markers
    markers = [
        '## EXECUTIVE SUMMARY',
        '## MOAT ANALYSIS',
        '## MARKET POSITIONING',
        '## COMPETITIVE ADVANTAGES & LANDSCAPE'
    ]

    # Find positions of each section
    section_positions = {}
    for marker in markers:
        pos = analysis_text.find(marker)
        if pos != -1:
            section_positions[marker] = pos

    # Extract sections
    def extract_section(start_marker, end_marker=None):
        start_pos = section_positions.get(start_marker, 0)
        if end_marker and end_marker in section_positions:
            end_pos = section_positions[end_marker]
        else:
            next_positions = [pos for pos in section_positions.values() if pos > start_pos]
            end_pos = min(next_positions) if next_positions else len(analysis_text)

        section_text = analysis_text[start_pos:end_pos].strip()
        lines = section_text.split('\n')
        if lines and any(marker.replace('##', '').strip() in lines[0] for marker in markers):
            section_text = '\n'.join(lines[1:]).strip()
        return section_text

    executive_summary = extract_section('## EXECUTIVE SUMMARY', '## MOAT ANALYSIS')
    moat_analysis = extract_section('## MOAT ANALYSIS', '## MARKET POSITIONING')
    market_positioning = extract_section('## MARKET POSITIONING', '## COMPETITIVE ADVANTAGES & LANDSCAPE')
    competitive_landscape = extract_section('## COMPETITIVE ADVANTAGES & LANDSCAPE')

    # Clean up sections
    def clean_section(text):
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'^\s*\n', '', text)
        return text.strip()

    return {
        'executive_summary': clean_section(executive_summary),
        'moat_analysis': clean_section(moat_analysis),
        'market_positioning': clean_section(market_positioning),
        'competitive_landscape': clean_section(competitive_landscape)
    }

# =============================================================================
# FLASK INTEGRATION FUNCTION
# =============================================================================

def run_moat_analysis_for_web(ticker: str) -> dict:
    """
    Main function to be called from Flask app
    Returns formatted analysis ready for web display
    """
    return analyze_stock_moat(ticker)