from agents.core_utils import summarize_item_text, infer_relevant_items,get_tenk_items, get_tenk_item_descriptions, ensure_list, get_finnhub_client, convert_unix_to_datetime, set_sec_client
from agents.schemas import FilingItemSummary
from edgar import *
from edgar.xbrl.stitching import XBRLS
import requests, pandas as pd
from typing import Literal


def get_latest_10K_item_summary(user_query: str, ticker:str, item_codes: Optional[List[str]]=None) -> FilingItemSummary:
    """
    Generate a summarized view of the latest 10-K filing items for a given company.

    If no item codes are provided, the function will infer the most relevant 10-K item(s) 
    based on the user's query using an LLM-based matching system. For each specified or 
    inferred item code, the function fetches the latest 10-K filing for the given ticker,
    extracts the section text, and produces a concise summary using a language model.

    Args:
        user_query (str): A natural language query describing the type of information the user is seeking.
        ticker (str): Stock ticker symbol of the company (e.g., "MU" for Micron).
        item_codes (Optional[List[str]]): A list of specific 10-K item codes to summarize (e.g., ["ITEM 1A"]).
            If None, relevant items will be inferred from the query.

    Returns:
        str: A formatted string containing the summarized text for each specified or inferred 10-K item
        from the most recent filing, including filing metadata and section headers.
    """
     
    # Case 1: item_code not specified — infer it from the user_query
    if item_codes is None:
        item_map = get_tenk_item_descriptions()
        relevant_items = infer_relevant_items(user_query, item_map)
        item_codes = relevant_items
    else:
        # Case 2: item_code specified — validate it
        allowed_items = get_tenk_items()
        invalid_items = [code for code in item_codes if code not in allowed_items]
        if invalid_items:
            raise ValueError(f"Invalid item codes: {invalid_items}. Must be one of: {sorted(allowed_items)}")
    
    # start processing. We have item_codes, ticker and num_last_10k_filings 
    form_type = "10-K"
    filing = get_latest_filings(ticker, form_type, n=1, as_text=False)
    filing = filing[0]
    tenk = filing.obj()
    filing_text = f"\n\n--- Filing: {filing.filing_date} ---\n"
    for item_code in item_codes:
        tenk_item = tenk.structure.get_item(item_code)
        title = tenk_item["Title"]
        description = tenk_item["Description"]
        item_txt = str(tenk[item_code])
        
        summarized_item_text = summarize_item_text(item_code, title, description, item_txt)
        filing_text += f"\n === Summary of {item_code}: {title} ===\n{summarized_item_text}"
            
    return filing_text.strip()



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
 
