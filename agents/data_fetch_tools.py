from agents.core_utils import ensure_list, get_finnhub_client, convert_unix_to_datetime, set_sec_client
from edgar import *
from edgar.xbrl.stitching import XBRLS
import requests, pandas as pd
from typing import Literal

def get_financial_statement(
    ticker: str, 
    form_type: Literal["10-K", "10-Q"],
    statement_type: Literal["cashflow", "balance_sheet", "income"], 
    n: int = 1
) -> pd.DataFrame:
    """
    Fetches financial statement(s) (cash flow, balance sheet, or income statement) 
    as a pandas DataFrame for a given company ticker and form type

    Args:
        ticker (str): Stock ticker symbol (e.g., "AAPL", "MSFT").
        form_type (str): Type of SEC filing to use. Options: "10-K"- Annual financial statements (more comprehensive),"10-Q": Quarterly financial statements (more recent, but limited scope)
        statement_type (str): One of "cashflow", "balance_sheet", or "income".
        n (int): Number of recent 10-K filings to retrieve. Defaults to 5.

    Returns:
        pd.DataFrame: Structured DataFrame where rows are financial line items 
        and columns are reporting periods.

    Raises:
        ValueError: If the statement_type is invalid or if no filings/statements are found.
    """
    set_sec_client()

    c = Company(ticker)
    filings = c.get_filings(form=form_type).latest(n)
    filings = ensure_list(filings)

    xbs = XBRLS.from_filings(filings)

    # Select the statement based on the requested type
    if statement_type == "cashflow":
        stmt = xbs.statements.cashflow_statement()
    elif statement_type == "balance_sheet":
        stmt = xbs.statements.balance_sheet()
    elif statement_type == "income":
        stmt = xbs.statements.income_statement()
    else:
        raise ValueError(f"Unsupported statement type: {statement_type}")

    return stmt.to_dataframe()

def get_latest_filings(ticker: str, form_type: Optional[str] = None, n: int = 5, as_text: bool = True) -> str:
    """
    Fetches the latest filings for a given ticker using SEC-API.
    If form_type is specified, filters by that form (e.g., '10-K', '8-K').

    Args:
        ticker (str): The stock ticker (e.g., "AAPL").
        form_type (Optional[str]): The form type to filter (e.g., "10-K", "10-Q", "8-K"). If None, returns all types.
        n (int): Number of filings to retrieve. Defaults to 5.
        as_text (bool): for string output, use True. Defaults to False which gives a Filing object 
    
    Returns:
        str: A newline-separated string of the latest filings.
    """
    set_sec_client()

    c = Company(ticker)
    
    if form_type:
        filings = c.get_filings(form=form_type).latest(n)
    else:
        filings = c.get_filings().latest(n)
    
    filings = ensure_list(filings)
    if as_text:
        return "\n".join(str(f) for f in filings)
    else: 
        return filings

# Get the CIK 
def get_cik (name: str) -> str:
    """
    Fetches the CIK (Central Index Key) given the entity name.

    Args:
        name (str): The name of the entity (e.g., "Micron Technology").
    
    Returns:
        str: The CIK number of the entity (e.g. 'CIK0001730168').
    """
    set_sec_client()
    
    ticker = get_ticker_given_name(name)[0]['symbol']
    c = Company(ticker)    
    cik_raw = c.cik
    print(f"cik_raw={cik_raw} ({type(cik_raw)})")
    cik_formatted = f"CIK{int(cik_raw):010d}"
    return cik_formatted


## Get ticker given company name 
def get_ticker_given_name(company_name: str):
    """
    Searches for ticker symbols that match a given company name using Yahoo Finance's search API.
    If more than one ticker is returned, get human assistance. 
    Args:
        company_name (str): The name of the company to search for (e.g., "Apple").
    Returns:
        List[dict]: A list of dictionaries, each with:
            - 'name': The company's short name (str)
            - 'symbol': The stock ticker symbol (str)
    """

    url = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    params = {"q": company_name, "quotes_count": 5, "country": "United States"}

    res = requests.get(url=url, params=params, headers={'User-Agent': user_agent})
    data = res.json()
    result = [{"name": q["shortname"], "symbol": q["symbol"]} for q in data["quotes"]]
    return result

def get_earnings(ticker: str, n: int=1):
    """
    Retrieve the most recent quarterly earnings data for a given company ticker.
    This function uses the Finnhub API to fetch up to `n` earnings records for the specified
    company, including actual and estimated earnings per share (EPS), the reporting period,
    and earnings surprises.
    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL").
        n (int): The number of most recent earnings records to retrieve.
    Returns:
        list[dict]: A list of dictionaries, each containing:
            - actual (float): Reported EPS.
            - estimate (float): Analyst consensus EPS estimate.
            - period (str): Fiscal period end date (YYYY-MM-DD).
            - quarter (int): Fiscal quarter number.
            - year (int): Fiscal year.
            - surprise (float): Difference between actual and estimated EPS.
            - surprisePercent (float): Surprise as a percentage of the estimate.
            - symbol (str): Ticker symbol.
    Example:
        get_earnings("AAPL", 2)
    """
    finnhub_client = get_finnhub_client()
    earnings_items = finnhub_client.company_earnings(ticker, limit=n)
    return earnings_items

def get_analyst_rating_summary(ticker: str):
    """
    Retrieve the most recent analyst rating summary for a given company ticker.

    This function queries the Finnhub API to fetch analyst recommendations,
    including counts of buy, hold, sell, strong buy, and strong sell ratings
    for the latest available period.

    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL").

    Returns:
        list[dict]: A list containing a single dictionary with:
            - strongBuy (int): Number of analysts issuing a strong buy rating.
            - buy (int): Number of buy ratings.
            - hold (int): Number of hold ratings.
            - sell (int): Number of sell ratings.
            - strongSell (int): Number of strong sell ratings.
            - period (str): The date of the rating summary (YYYY-MM-DD).
            - symbol (str): Ticker symbol.

    Example:
        get_analyst_rating_summary("AAPL")
    """
    finnhub_client = get_finnhub_client()
    reco_items = finnhub_client.recommendation_trends(ticker)
    return reco_items


def get_stock_price(ticker: str):
    """
    Retrieve the latest stock price quote for a given company ticker.

    This function uses the Finnhub API to fetch real-time market data,
    including the current price, price change, opening price, and more.

    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL").

    Returns:
        dict: A dictionary containing the latest quote data with the following fields:
            - c (float): Current price.
            - d (float): Change in price from the previous close.
            - dp (float): Percentage change from the previous close.
            - h (float): High price of the current trading session.
            - l (float): Low price of the current trading session.
            - o (float): Opening price of the current trading session.
            - pc (float): Previous close price.
            - t (int): UNIX timestamp of the quote.

    Example:
        get_stock_price("AAPL")
    """
    finnhub_client = get_finnhub_client()
    quote_item = finnhub_client.quote(ticker)
    quote_item['t'] = convert_unix_to_datetime(quote_item['t'])
    return quote_item
 
