import yfinance as yf
import numpy as np
import pandas as pd
import os
import warnings
from datetime import timedelta, datetime
import xlsxwriter
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ---------------------------------------------------
#                 TECHNICAL INDICATORS
# ---------------------------------------------------

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute the Relative Strength Index (RSI)."""
    if series is None or series.empty:
        return pd.Series(dtype=float)

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Return MACD line, signal line, and histogram."""
    if series is None or series.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)

    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# ---------------------------------------------------
#                 HELPER FORMATS
# ---------------------------------------------------

def format_ratio(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def format_growth(value):
    return float(value) * 100 if isinstance(value, (int, float)) else None

def format_revenue(value):
    return round(value / 1e9, 2) if isinstance(value, (int, float)) and value > 0 else None

# ---------------------------------------------------
#            SIMPLE 5‑YEAR FUTURE VALUATION
# ---------------------------------------------------

def calculate_future_value(revenue, revenue_growth, market_cap, trailing_pe, profit_margin):
    """Return (future_value_billion, multibagger_rate, adjustments_str)."""
    adj = []

    if revenue in (None, 0) or revenue_growth is None or market_cap in (None, 0):
        return None, None, ""

    # Revenue‑growth guardrails
    if revenue_growth <= 0:
        adj.append(f"Revenue growth raised from {revenue_growth*100:.1f}% → 5%")
        revenue_growth = 0.05
    elif revenue_growth > 0.25:
        adj.append(f"Revenue growth capped from {revenue_growth*100:.1f}% → 25%")
        revenue_growth = 0.25

    # P/E guardrails
    if trailing_pe is None or trailing_pe == 0 or trailing_pe > 30:
        adj.append(f"P/E set to 30 from {trailing_pe if trailing_pe else 'N/A'}")
        trailing_pe = 30

    # Profit‑margin guardrails (input arrives as "%")
    if profit_margin is None:
        adj.append("Profit margin set to 10% from N/A")
        profit_margin = 10
    elif profit_margin < 1:
        adj.append(f"Profit margin raised from {profit_margin:.1f}% → 5%")
        profit_margin = 5

    profit_margin /= 100  # convert to decimal

    future_val = revenue * (1 + revenue_growth) ** 5 * profit_margin * trailing_pe
    future_val_b = round(future_val / 1e9, 2)
    multibagger = round(future_val / market_cap, 2)

    return future_val_b, multibagger, "; ".join(adj)

# ---------------------------------------------------
#               FIBONACCI CALCULATION
# ---------------------------------------------------

def calculate_fibonacci_levels(prices: pd.Series):
    if prices is None or prices.empty or prices.isnull().all():
        return []

    lo, hi = prices.min(), prices.max()
    rng = hi - lo
    if rng == 0:
        return []

    pivots = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.272, 1.618, 2, 2.618]
    levels = []
    for p in pivots:
        if p <= 1:
            price = hi - rng * p
            typ = 'Retracement'
        else:
            price = hi + rng * (p - 1)
            typ = 'Extension'
        levels.append({'Level': p, 'Price': price, 'Type': typ})
    return levels

# ---------------------------------------------------
#                 CORE DATA FRAME
# ---------------------------------------------------

def create_rsi_table(symbols):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Batch download (works fine, just pass auto_adjust= False to silence warning)
    try:
        price_data = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=False,
        )["Close"]
    except Exception as e:
        raise RuntimeError(f"Price download failed: {e}")

    if price_data.empty:
        raise RuntimeError("No price data returned. Check ticker list or network.")

    records = {}

    for ticker in symbols:
        series = price_data[ticker].dropna()
        if series.empty:
            print(f"Skipping {ticker}: no close prices in period")
            continue

        rsi_val = calculate_rsi(series).iloc[-1]
        today_close = series.iloc[-1]

        # --- Fundamentals via .info (guarded)
        try:
            info = yf.Ticker(ticker).info
        except Exception as e:
            print(f"{ticker} info fetch failed: {e}")
            continue

        rev = info.get('totalRevenue', 0)
        rev_g = info.get('revenueGrowth', 0)
        mcap = info.get('marketCap', 0)
        tpe = info.get('trailingPE', None)
        pmargin = format_growth(info.get('profitMargins', None))

        fut_val, multi, adjust = calculate_future_value(rev, rev_g, mcap, tpe, pmargin)
        price_target = today_close * (multi if multi else 1)

        records[ticker] = {
            'Company Name': info.get('longName', ticker),
            'Ticker': ticker,
            'Price': today_close,
            '5Y Price Target': price_target,
            '5Y Multibagger Rate': multi,
            'Adjustment Explanation': adjust,
            'Revenue Growth': format_growth(rev_g),
            'Forward P/E': format_ratio(info.get('forwardPE')),
            'Trailing P/E': format_ratio(tpe),
            'Profit Margin (%)': pmargin,
            'P/S Ratio': format_ratio(info.get('priceToSalesTrailing12Months')),
            'Total Revenue ($B)': format_revenue(rev),
            'Market Cap ($B)': format_revenue(mcap),
            'Future Val ($B)': fut_val,
            'RSI': format_ratio(rsi_val),
            '52W Low': format_ratio(info.get('fiftyTwoWeekLow')),
            '52W High': format_ratio(info.get('fiftyTwoWeekHigh')),
            'All-Time High': format_ratio(yf.Ticker(ticker).history(period="max")['Close'].max()),
        }

    df = pd.DataFrame.from_dict(records, orient='index')

    order = [
        'Company Name','Ticker','Price','5Y Price Target','5Y Multibagger Rate',
        'Adjustment Explanation','Revenue Growth','Forward P/E','Trailing P/E',
        'Profit Margin (%)','P/S Ratio','Total Revenue ($B)','Market Cap ($B)',
        'Future Val ($B)','RSI','52W Low','52W High','All-Time High'
    ]
    df = df[order]

    num_cols = [c for c in df.columns if c not in {'Company Name','Ticker','Adjustment Explanation'}]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce').round(2)
    return df

# ---------------------------------------------------
#           OPTIONAL: PRICE‑ACTION CHARTS
# ---------------------------------------------------

def plot_stock_chart(symbol, start_date, end_date, folder):
    data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False, progress=False, threads=False)
    if data.empty or data['Close'].isnull().all():
        print(f"Chart skipped for {symbol}: insufficient data")
        return None

    data['50_MA'] = data['Close'].rolling(50).mean()
    data['200_MA'] = data['Close'].rolling(200).mean()
    fibs = calculate_fibonacci_levels(data['Close'])

    fig,(ax1,ax2,ax3)=plt.subplots(3,1,figsize=(12,12))
    ax1.plot(data.index,data['Close'],label='Close')
    ax1.plot(data.index,data['50_MA'],'--',label='50 MA')
    ax1.plot(data.index,data['200_MA'],'--',label='200 MA')
    for f in fibs:
        ax1.axhline(f['Price'],linestyle='--' if f['Type']=='Retracement' else ':',
                    color='green' if f['Type']=='Retracement' else 'red',alpha=0.5)
        ax1.text(data.index[-1],f['Price'],f"{f['Level']:.3f}",fontsize=8)
    ax1.legend(); ax1.set_title(f"{symbol} Price & Fibonacci")

    rsi=calculate_rsi(data['Close']); ax2.plot(data.index,rsi); ax2.axhline(70,color='r',ls='--');ax2.axhline(30,color='g',ls='--');ax2.set_title('RSI')
    macd,signal,hist=calculate_macd(data['Close']); ax3.plot(data.index,macd); ax3.plot(data.index,signal); ax3.bar(data.index,hist,color=(hist>0).map({True:'g',False:'r'})); ax3.set_title('MACD')

    path=os.path.join(folder,f"{symbol}.png"); plt.savefig(path); plt.close(); return path

# ---------------------------------------------------
#                     MAIN ENTRY
# ---------------------------------------------------

def main(return_dataframe=False):
    today=datetime.today().strftime('%Y-%m-%d')
    symbols = [
    # Global mega‑cap platforms
    "AAPL", "AMZN", "GOOG", "META", "MSFT",

    # Semiconductors & equipment
    "AMD", "ASML", "AVGO", "MU", "NVDA", "QCOM", "TXN", "ARM", "INTC", "SMCI",

    # Enterprise software & cloud-native SaaS
    "ADBE", "CRM", "INTU", "MDB", "ORCL", "SNOW", "GTLB", "U", "DELL", "NOW", "ACN", "DOCN", "CFLT", "WIX", "IBM", "ZI", "ASAN", "TTD", "ZM", "HUBS", "ANET", "ADP", "MNDY",

    # Cybersecurity & AI-defense
    "AI", "CRWD", "PLTR", "S", "GEN", "BBAI", "NET", "SOUN", "S",

    # Payments & fintech
    "AXP", "HOOD", "MA", "NU", "PYPL", "SOFI", "V", "AFRM", "UPST", "OPRT", "LC", "BILL", "SCHW", "STNE", "COIN", "OLO", "MCO", "TOST", "LMND", "CVNA",

    # Bulge-bracket banks
    "BAC", "GS", "JPM", "MS", "WFC",

    # Diversified conglomerates
    "HON", "MMM", "ETN", "EMR",

    # Consumer staples & beverages
    "CELH", "KO", "PEP", "PG", "FIGS", "KR", 

    # Big-box / mass retail & home improvement
    "COST", "HD", "LOW", "TGT", "WMT", "DG", "DLTR", "BBY", "MO", "CL", "SYY", "VFC", "GIS", "KMB", 

    # Restaurants & food-service tech
    "CAKE", "DASH", "MCD", "SBUX", "WING", "CMG", "CAVA","TXRH","SFM", 

    # Health-care & life-sciences
    "JNJ", "NVO", "PFE", "TMDX", "UNH", "OSCR", "LLY", "ABBV", "MRK", "ABT", "TMO", "ALHC", "GH", "RXRX", "CI", "HCA", "CVS", "MDT","TGTX","ARGX", "COSM",

    # Energy & power
    "CEG", "SMR", "XOM", "CVX", "LIN", "BE", "PSX", "MPC", "ENPH",

    # Telecom carriers
    "T", "VZ", "TMUS", "CHTR",

    # Apparel, footwear & beauty
    "ANF", "ELF", "LULU", "NKE", "SKX", "CROX", "BIRD", "BYND", "HNST", "ONON","STKL", "LSF", "OTLY", "ZVIA", "SMPL", "VITL", 

    # Media, streaming & social
    "DIS", "FUBO", "NFLX", "RDDT", "ROKU", "SNAP", "SPOT", "BKNG", "DUOL", "CMCSA", "PINS",

    # Mobility & ride-hail
    "LYFT", "UBER", "GRAB", 

    # Autos & EV
    "TSLA", "LCID", "F", "GM", "RIVN", "ACHR",

    # Travel & hospitality
    "ABNB", "DAL", "UAL",

    # Sports betting & interactive entertainment
    "DKNG", "RBLX", "FVRR",

    # Industrial, aerospace & defense
    "BA", "GE", "RKLB", "CAT", "DE", "LMT",

    # High-growth disruptors & e‑commerce
    "MELI", "SHOP", "XYZ", "HIMS",
    "GLBE", "IOT",  "PATH", "ENVX", "APP", "ESTC"
]


    downloads=os.path.join(os.path.expanduser('~'),'Downloads')
    excel_path=os.path.join(downloads,f"{today}_2030_Price_Targets_AA.xlsx")

    df=create_rsi_table(symbols)



    with pd.ExcelWriter(excel_path,engine='xlsxwriter') as writer:
        df.to_excel(writer,sheet_name='RSI Analysis',index=False)
        wb=writer.book; ws=writer.sheets['RSI Analysis']
        ws.freeze_panes(1,0)
        for i in range(len(df.columns)):
            ws.set_column(i,i,14)
        even=wb.add_format({'bg_color':'#F2F2F2'}); odd=wb.add_format({'bg_color':'#FFFFFF'})
        for r in range(1,len(df)+1):
            ws.set_row(r,None,even if r%2==0 else odd)
        green=wb.add_format({'bg_color':'#C6EFCE','font_color':'#006100'}); red=wb.add_format({'bg_color':'#FFC7CE','font_color':'#9C0006'})
        def cf(col,crit,val,fmt): c=df.columns.get_loc(col); ws.conditional_format(1,c,len(df),c,{'type':'cell','criteria':crit,'value':val,'format':fmt})
        cf('RSI','>','70',red); cf('RSI','<','30',green)
        cf('Forward P/E','>','50',red); cf('Forward P/E','<','20',green)
        cf('Trailing P/E','>','50',red); cf('Trailing P/E','<','30',green)
        cf('5Y Multibagger Rate','>','2',green); cf('5Y Multibagger Rate','<','1',red)
        cf('Revenue Growth','>','20',green); cf('Revenue Growth','<','10',red)
        cf('Profit Margin (%)','>','20',green); cf('Profit Margin (%)','<','5',red)
        cf('P/S Ratio','>','8',red); cf('P/S Ratio','<','2',green)

    print(f"Excel report saved to {excel_path}")
    if return_dataframe:
        return df


if __name__=='__main__':
    main()