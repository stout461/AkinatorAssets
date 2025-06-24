import requests

from schwab_api.rate_limiter import RateLimiter
import uuid
from schwab_api.exceptions import SchwabAPIError


class SchwabClient:
    BASE_URL = 'https://api.schwabapi.com/marketdata/v1'

    def __init__(self, auth):
        self.auth = auth
        self.ratelimiter = RateLimiter()

    def _get(self, endpoint, params=None):
        self.ratelimiter.wait()

        correlation_id = str(uuid.uuid4())
        headers = {
            'Authorization': f'Bearer {self.auth.get_access_token()}',
            'Accept': 'application/json',
            'Schwab-Client-CorrelId': correlation_id,
            'Schwab-Resource-Version': '1'
        }

        response = requests.get(f"{self.BASE_URL}/{endpoint}", headers=headers, params=params)

        if response.status_code == 200:
            return response.json()

        # Attempt to parse error payload
        try:
            error_payload = response.json()
            error_list = error_payload.get("errors", [])
            details = "; ".join([f"{e.get('detail', e.get('title', ''))}" for e in error_list])
        except ValueError:
            details = response.text

        raise SchwabAPIError(
            status_code=response.status_code,
            message=details or "Unknown error",
            errors=error_list if 'error_list' in locals() else [],
            correlation_id=correlation_id
        )

    def get_quotes(self, symbols: list[str] | str, fields: str = "all", indicative: bool = False) -> dict:
        """
        Get quotes for one or more symbols.

        Args:
            symbols: List of symbols or comma-separated string (e.g., ["AAPL", "TSLA"] or "AAPL,TSLA")
            fields: Optional comma-separated fields (e.g., "quote,fundamental")
            indicative: Whether to include indicative ETFs

        Returns:
            dict: Quote data from Schwab API
        """
        if isinstance(symbols, list):
            symbols = ",".join(symbols)

        endpoint = "/quotes"
        params = {
            "symbols": symbols,
            "fields": fields,
            "indicative": str(indicative).lower()
        }

        return self._get(endpoint, params)

    def get_single_quote(self, symbol: str, fields: str = "all") -> dict:
        """
        Get a quote for a single symbol using path parameter.
        """
        endpoint = f"/{symbol}/quotes"
        params = {"fields": fields}
        return self._get(endpoint, params)

    def get_option_chains(
        self,
        symbol: str,
        contract_type: str = "ALL",
        strike_count: int = None,
        include_underlying_quote: bool = False,
        strategy: str = "SINGLE",
        interval: float = None,
        strike: float = None,
        range_: str = None,
        from_date: str = None,
        to_date: str = None,
        volatility: float = None,
        underlying_price: float = None,
        interest_rate: float = None,
        days_to_expiration: int = None,
        exp_month: str = None,
        option_type: str = None,
        entitlement: str = None
    ) -> dict:
        """
        Retrieve option chain data for a given symbol.

        Args:
            symbol (str): The underlying symbol (e.g., "AAPL").
            contract_type (str): CALL, PUT, or ALL (default).
            strike_count (int): Number of strikes above/below ATM.
            include_underlying_quote (bool): Include underlying quote.
            strategy (str): Option strategy (default: SINGLE).
            interval (float): Strike interval for spread strategies.
            strike (float): Specific strike price.
            range_ (str): ITM, NTM, OTM, etc.
            from_date (str): yyyy-MM-dd format.
            to_date (str): yyyy-MM-dd format.
            volatility (float): Used for ANALYTICAL strategies.
            underlying_price (float): Used for ANALYTICAL strategies.
            interest_rate (float): Used for ANALYTICAL strategies.
            days_to_expiration (int): Used for ANALYTICAL strategies.
            exp_month (str): JAN–DEC or ALL.
            option_type (str): Optional filter.
            entitlement (str): PN, NP, PP (for retail accounts).

        Returns:
            dict: Option chain response from Schwab API.
        """
        params = {
            "symbol": symbol,
            "contractType": contract_type,
            "includeUnderlyingQuote": str(include_underlying_quote).lower(),
            "strategy": strategy,
        }

        # Only include optional params if provided
        optional_params = {
            "strikeCount": strike_count,
            "interval": interval,
            "strike": strike,
            "range": range_,
            "fromDate": from_date,
            "toDate": to_date,
            "volatility": volatility,
            "underlyingPrice": underlying_price,
            "interestRate": interest_rate,
            "daysToExpiration": days_to_expiration,
            "expMonth": exp_month,
            "optionType": option_type,
            "entitlement": entitlement
        }

        # Remove None values from optional params
        params.update({k: v for k, v in optional_params.items() if v is not None})

        return self._get("chains", params)

    def get_option_expiration_chain(self, symbol: str) -> dict:
        """
        Get option expiration series data for a given symbol.

        Args:
            symbol (str): The underlying optionable symbol (e.g., "AAPL")

        Returns:
            dict: Expiration series metadata (not individual contracts)
        """
        params = {"symbol": symbol}
        return self._get("expirationchain", params)
    def get_price_history(
            self,
            symbol: str,
            period_type: str = "day",
            period: int = 10,
            frequency_type: str = "minute",
            frequency: int = 1,
            start_date: int = None,
            end_date: int = None,
            need_extended_hours_data: bool = False,
            need_previous_close: bool = False
    ) -> dict:
        """
        Get historical OHLCV price data for a symbol.

        Args:
            symbol (str): Ticker symbol (e.g., "AAPL")
            period_type (str): "day", "month", "year", or "ytd"
            period (int): Number of periodType units (e.g., 10 days, 6 months)
            frequency_type (str): "minute", "daily", "weekly", "monthly"
            frequency (int): Interval (e.g., 1-minute, 5-minute, 1-daily)
            start_date (int): Epoch ms (optional)
            end_date (int): Epoch ms (optional)
            need_extended_hours_data (bool): Include pre/post-market data
            need_previous_close (bool): Include previous close in response

        Returns:
            dict: Candle data including open, high, low, close, volume
        """
        params = {
            "symbol": symbol,
            "periodType": period_type,
            "period": period,
            "frequencyType": frequency_type,
            "frequency": frequency,
            "needExtendedHoursData": str(need_extended_hours_data).lower(),
            "needPreviousClose": str(need_previous_close).lower()
        }

        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        return self._get("pricehistory", params)

    def get_market_movers(self, index: str = "$DJI", direction: str = "up", change: str = "percent") -> dict:
        """
        Get market movers for a major index.

        Args:
            index: One of "$DJI", "$COMPX", "$SPX.X"
            direction: "up" or "down"
            change: "value" or "percent"

        Returns:
            dict: List of movers
        """
        endpoint = f"movers"
        params = {
            "index": index,
            "direction": direction,
            "change": change
        }
        return self._get(endpoint, params)

    def get_movers(
            self,
            symbol_id: str = "$DJI",
            sort: str = "VOLUME",
            frequency: int = 0
    ) -> dict:
        """
        Get top 10 securities moving in a specific index.

        Args:
            symbol_id (str): Index symbol, e.g. "$DJI", "NASDAQ", "INDEX_ALL"
            sort (str): Sort by "VOLUME", "TRADES", "PERCENT_CHANGE_UP", "PERCENT_CHANGE_DOWN"
            frequency (int): 0, 1, 5, 10, 30, or 60 minute interval

        Returns:
            dict: Movers response
        """
        endpoint = f"movers/{symbol_id}"
        params = {
        "sort": sort,
        "frequency": frequency
        }
        return self._get(endpoint, params)

    def get_market_hours(
            self,
            markets: list[str],
            date: str = None
    ) -> dict:
        """
        Get market hours for specific markets on a given date.

        Args:
            markets (list[str]): List of markets like ["equity", "option", "forex"]
            date (str): Optional. Format: "YYYY-MM-DD". Defaults to today if not provided.

        Returns:
            dict: Market hours information by market
        """
        if not markets:
            raise ValueError("At least one market must be specified.")

        params = {
            "markets": ",".join(markets)
        }

        if date:
            params["date"] = date

        return self._get("markets", params)

    def get_single_market_hours(
            self,
            market_id: str,
            date: str = None
    ) -> dict:
        """
        Get market hours for a single market on a specific date.

        Args:
            market_id (str): One of "equity", "option", "bond", "future", or "forex"
            date (str): Optional date in "YYYY-MM-DD" format. Defaults to today if omitted.

        Returns:
            dict: Market hours details for the specified market
        """

        if market_id not in {"equity", "option", "bond", "future", "forex"}:
            raise ValueError(f"Invalid market_id: {market_id}")

        endpoint = f"markets/{market_id}"
        params = {"markets": market_id}
        if date:
            params["date"] = date

        return self._get(endpoint, params)


    def search_instruments(
            self,
            symbol: str,
            projection: str = "symbol-search"
    ) -> dict:
        """
        Search for instrument metadata using a specific projection.

        Args:
            symbol (str): Symbol or string to search (e.g., "AAPL", "AMAZON")
            projection (str): Type of search. Must be one of:
                "symbol-search", "symbol-regex", "desc-search",
                "desc-regex", "search", "fundamental"

        Returns:
            dict: Instrument data
        """
        valid_projections = {
            "symbol-search", "symbol-regex",
            "desc-search", "desc-regex",
            "search", "fundamental"
        }

        if projection not in valid_projections:
            raise ValueError(f"Invalid projection: {projection}")

        params = {
            "symbol": symbol,
            "projection": projection
        }

        return self._get("instruments", params)

    def get_instrument_by_cusip(self, cusip_id: str) -> dict:
        """
        Get instrument details for a specific CUSIP.

        Args:
            cusip_id (str): 9-character CUSIP identifier (e.g., "037833100")

        Returns:
            dict: Instrument metadata
        """
        if not cusip_id or len(cusip_id) != 9:
            raise ValueError("CUSIP must be a 9-character string.")

        endpoint = f"instruments/{cusip_id}"
        return self._get(endpoint)
