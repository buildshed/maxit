# Include libraries 
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from typing_extensions import TypedDict, NotRequired, List
from langchain_community.tools.tavily_search import TavilySearchResults
import requests 
import finnhub, json, os
from edgar import *
from edgar.xbrl.stitching import XBRLS
from typing import Literal
from collections.abc import Iterable
import pandas as pd
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from datetime import datetime, timezone
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

# Define classes 
class PeerInfo(TypedDict):
    name: str
    ticker: str

class ClientMemory(TypedDict): 
    cik: str
    name: str
    tickers: List[str]
    peers: NotRequired[List[PeerInfo]]

# util functions 
def convert_unix_to_datetime(timestamp: int) -> str:
    """
    Convert a UNIX timestamp to a human-readable date and time (UTC).

    Args:
        timestamp (int): UNIX timestamp (seconds since epoch).

    Returns:
        str: Formatted date and time in 'YYYY-MM-DD HH:MM:SS' format (UTC).
    
    Example:
        convert_unix_to_datetime(1747771200)  # → '2025-05-20 20:00:00'
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def util_ensure_list(item):
    """
    Ensures the input is returned as a list.
    - If input is None → returns an empty list.
    - If input is a string → wraps it in a list.
    - If input is a non-iterable → wraps it in a list.
    - If input is an iterable (excluding string/bytes) → converts it to a list.
    """
    if item is None:
        return []
    if isinstance(item, str) or not isinstance(item, Iterable):
        return [item]
    
    return list(item)


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

# Get the CIK 
def get_cik (name: str) -> str:
    """
    Fetches the CIK (Central Index Key) given the entity name.

    Args:
        name (str): The name of the entity (e.g., "Micron Technology").
    
    Returns:
        str: The CIK number of the entity (e.g. 'CIK0001730168').
    """
    tickers = get_ticker_given_name(name)
    tickers = util_ensure_list(tickers)
    ticker = tickers[0]['symbol']
    
    filings = get_latest_filings(ticker,"10-K", n=1)
    filings = util_ensure_list(filings)
    
    cik_raw = filings[0].cik
    
    cik_formatted = f"CIK{int(cik_raw):010d}"

    return cik_formatted


# Get latest filings 
def get_latest_filings(ticker: str, form_type: str, n: int = 5) -> str:
    """
    Fetches the latest filings of the specified form type for a given ticker using SEC-API.

    Args:
        ticker (str): The stock ticker (e.g., "AAPL").
        form_type (str): The form type (e.g., "10-K" for annual reports, "10-Q" for quarterly, "8-K" for events).
        n (int): Number of filings to retrieve. Defaults to 5.

    Returns:
        str: A newline-separated string of the latest filings, or an error message.
    """
    c = Company(ticker)
    filings = c.get_filings(form=form_type).latest(n)  # Fixed this line
    
    filings = util_ensure_list(filings)
    
    s = filings # "\n".join(str(f) for f in filings)
    return s

## get cash flow or income statement or balance sheet 
def get_financial_statement(
    ticker: str, 
    statement_type: Literal["cashflow", "balance_sheet", "income"], 
    n: int = 5
) -> pd.DataFrame:
    """
    Fetches a financial statement (cash flow, balance sheet, or income statement) 
    as a pandas DataFrame for a given company ticker.

    Args:
        ticker (str): Stock ticker symbol (e.g., "AAPL", "MSFT").
        statement_type (str): One of "cashflow", "balance_sheet", or "income".
        n (int): Number of recent 10-K filings to retrieve. Defaults to 5.

    Returns:
        pd.DataFrame: Structured DataFrame where rows are financial line items 
        and columns are reporting periods.

    Raises:
        ValueError: If the statement_type is invalid or if no filings/statements are found.
    """
    c = Company(ticker)
    filings = c.get_filings(form="10-K").latest(n)
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

## Save client infor to memory store
def save_client_info(client_memory: ClientMemory) -> str: 
    """
    Saves client information into the memory store.
    Args:
        ClientMemory object: The ClientMemory object that contains the company CIK, company name, company tickers (min 1) and pers (optional) 

    Returns:
        str: Success message 
    """

    # Same as that provided to `create_react_agent`
    store = get_store() 
    store.put(("clients",), client_memory["cik"], client_memory) 
    return "Successfully saved user info."

## retrieve client infor from memory store
def get_client_info(company_cik: str) -> str:
    """
    Retrieves client information from the memory store.
    Args:
        Company CIK: CIK is of the format 'CIK0001730168'. Always use 'CIK' prefix 

    Returns:
        str: Status message 
    """
    
    store = get_store() 
    client_info = store.get(("clients",), company_cik) 
    return str(client_info.value) if client_info else "Unknown client"

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

    quote_items = finnhub_client.quote(ticker)
    return quote_items

# Chatbot Node (uses basic dict state)
def chatbot(state: dict) -> dict:
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}

# Define Tools (including web search, chatbot. Exclude human assistance)
tools = [web_search, YahooFinanceNewsTool(), get_stock_price, get_analyst_rating_summary, get_earnings, convert_unix_to_datetime, get_ticker_given_name, get_cik, get_latest_filings, get_financial_statement, get_client_info, save_client_info]
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)
store = InMemoryStore() 

# Set identity for EdgarTools
set_identity("your.name@example.com")

#Set finnhub_client
fn_api_key=os.getenv("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(api_key=fn_api_key)


# Define and complile graph  
# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Compile graph
graph = builder.compile()




