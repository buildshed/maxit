from langchain_community.tools.tavily_search import TavilySearchResults
from util_tools import FilingItemSummary, REQUIRED_KEY_VALUES
from util_tools import util_ensure_list, get_finnhub_client
from langchain_openai import ChatOpenAI
from edgar import *
from edgar.xbrl.stitching import XBRLS
from edgar.company_reports import TenK
import finnhub, requests, pandas as pd
from typing import Literal

def get_financial_statement(
    ticker: str, 
    form_type: Literal["10-K", "10-Q"],
    statement_type: Literal["cashflow", "balance_sheet", "income"], 
    n: int = 5
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
    c = Company(ticker)
    filings = c.get_filings(form=form_type).latest(n)
    filings = util_ensure_list(filings)

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


def get_latest_filings(ticker: str, form_type: Optional[str] = None, n: int = 5) -> str:
    """
    Fetches the latest filings for a given ticker using SEC-API.
    If form_type is specified, filters by that form (e.g., '10-K', '8-K').

    Args:
        ticker (str): The stock ticker (e.g., "AAPL").
        form_type (Optional[str]): The form type to filter (e.g., "10-K", "10-Q", "8-K"). If None, returns all types.
        n (int): Number of filings to retrieve. Defaults to 5.

    Returns:
        str: A newline-separated string of the latest filings.
    """
    c = Company(ticker)
    
    if form_type:
        filings = c.get_filings(form=form_type).latest(n)
    else:
        filings = c.get_filings().latest(n)
    
    filings = util_ensure_list(filings)
    return "\n".join(str(f) for f in filings)


# Get the CIK 
def get_cik (name: str) -> str:
    """
    Fetches the CIK (Central Index Key) given the entity name.

    Args:
        name (str): The name of the entity (e.g., "Micron Technology").
    
    Returns:
        str: The CIK number of the entity (e.g. 'CIK0001730168').
    """
    ticker = get_ticker_given_name(name)
    c = Company(ticker)    
    cik_raw = c.cik
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


def get_earnings(ticker: str, n: int):
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
    quote_items = finnhub_client.quote(ticker)
    return quote_items


def generate_structured_item_from_10k(
    ticker: str,
    item_code: str
) -> FilingItemSummary:
    """
    Summarize and extract structured insights from a specific section of a 10-K filing.

    Use this tool when a user asks for an overview, summary, or key metrics related to a specific part
    of a company's 10-K filing. The function converts unstructured text into a structured summary with 
    section-wise insights and extracted key-value pairs.

    The `item_code` should be one of the standard 10-K sections:
      - "ITEM 1": Business — Overview of the company, products, markets, and operations
      - "ITEM 1A": Risk Factors — Material risks that could affect the business
      - "ITEM 1B": Any comments from the SEC staff on the company’s previous filings that are unresolved
      - "ITEM 2": Information about the physical properties owned or leased by the company
      - "ITEM 3": Details of significant ongoing legal proceedings
      - "ITEM 4": Relevant for mining companies, disclosures about mine safety and regulatory compliance
      - "ITEM 5": Information on the company’s equity, including stock performance and shareholder matters
      - "ITEM 7": Management's perspective on the financial condition, changes in financial condition, and results of operations.
      - "ITEM 7A": Market Risk — Exposure to FX, interest rates, and commodities, including hedging notionals
      - "ITEM 7": MD&A — Management’s Discussion and Analysis of financial condition and results
      - "ITEM 8": Financial Statements — Core financial reports (income, balance sheet, cash flow)
      - "ITEM 9": Evaluation of the effectiveness of the design and operation of the company’s disclosure controls and procedures
      - "ITEM 9A": Evaluation of internal controls over financial reporting.
      - "ITEM 13": Information on transactions between the company and its directors, officers and significant shareholders.
    Input:
      ticker: Stock ticker 
      item_code: The section of the filing to process (e.g., "ITEM 1A")
    
    Output:
      FilingItemSummary: A structured object containing section summaries and key data extracted from the text
    """
    #get an LLM with structure output 
    llm = ChatOpenAI(model="gpt-4o")
    
    # Get the latest 10-K filing
    company = find(ticker)  
    filing = company.get_filings(form="10-K").latest(1)
    #filing = filing[0]
    tenk = filing.obj()

    item = tenk.structure.get_item(item_code)
    if not item:
        raise ValueError(f"{item_code} not found in TenK.structure")
    item_txt = str(tenk[item_code])
    
    title = item["Title"]
    description = item["Description"]
    required_keys = REQUIRED_KEY_VALUES.get(item_code.upper(), [])
    required_key_text = (
    "- Try to extract the following key-value pairs if available:\n" +
    "".join(f"  • {key}\n" for key in required_keys) + "\n"
    if required_keys else "")

    prompt = (
    f"You are a financial analyst assistant. Read the following text from {title} ({item_code}) "
    "of a 10-K filing. Extract and populate the following structured format:\n\n"
    f"{description}\n\n"
    "- Divide the text into logical subsections.\n"
    "- For each subsection, write a 3–5 sentence summary.\n"
    "- Add important numeric or categorical values as key-value pairs.\n"
    f"{required_key_text}"
    "Format your output as a FilingItemSummary(title, description, sections=[...]).\n\n"
    f"TEXT:\n{item_txt}")
    #print (prompt)
    structured_llm = llm.with_structured_output(FilingItemSummary)
    return structured_llm.invoke(prompt)


## Web Search 
def web_search(query: str, num_results: int = 3) -> str:
    """
    Performs a web search using Tavily and returns the top results.

    Args:
        query (str): The search query.
        num_results (int): Number of top results to return. Defaults to 3.

    Returns:
        str: Combined snippets from top search results.
    """
    search = TavilySearchResults(max_results=num_results)
    results = search.run(query)
    return results

