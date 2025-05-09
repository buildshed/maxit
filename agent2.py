import os, requests 
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from edgar import *
from edgar.xbrl.stitching import XBRLS
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from collections.abc import Iterable
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.types import Command, interrupt

set_identity("your.name@example.com")

def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]

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
    if len(result) > 1: 
        options = "\n".join([f"{i+1}. {r['name']} ({r['symbol']})" for i, r in enumerate(result)])
        return human_assistance(f"Found {len(result)} tickers:\n{options}\nHelp me select the right ticker.")
    elif len(result) == 1:
        return result[0]
    
    return "No matching ticker found."


def get_latest_filings (ticker: str, form_type: str, n: int = 5) -> str:
    """
    Fetches the latest filings of the specified form type for a given ticker using SEC-API.

    Args:
        ticker (str): The stock ticker (e.g., "AAPL").
        form_type (str): The form type (e.g., "10-K" for annual reports, "10-Q" for quarterly, "8-K" for events).
        n (int): Number of filings to retrieve. Defaults to 5.

    Returns:
        str: A newline-separated string of the latest filings, or an error message.
    """
    set_identity("your.name@example.com")
    c = Company(ticker)
    filings = c.get_filings(form=form_type).latest(n)  # Fixed this line
    
    if not isinstance(filings, Iterable): #handle edge case of n=1
        filings = [filings]
    
    s = "\n".join(str(f) for f in filings)
    return s

def get_cash_flow_stmnt(ticker:str, n: int = 5):
    """
    Fetches the cash flow statement as a pandas DataFrame for a given company ticker.

    Processing: 
    - Function retrieves the latest `n` 10-K filings in XBRL format for the specified ticker,
    -Parses the XBRL data, extracts the cash flow statement 
    - Converts them into a structured pandas DataFrame. Each row represents a financial line item
    (e.g., cash Flow from operations), and each column corresponds to a reporting date.

    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL", "MSFT").
        n (int, optional): Number of most recent 10-K filings to retrieve. Defaults to 5.

    Returns:
        pd.DataFrame: A DataFrame containing the balance sheet with columns:
            - `label`: Human-readable name of the financial item
            - `concept`: XBRL concept identifier
            - One column per reporting date with the corresponding value

    Raises:
        ValueError: If no filings or cash flow statemnet(s) are found.
        Any network or parsing-related exceptions from underlying libraries.
    """

    c = Company(ticker)
    filings = c.get_filings(form="10-K").latest(n)
    # Ensure filings is a list
    if not isinstance(filings, Iterable):
        filings = [filings]
    
    xbs = XBRLS.from_filings(filings)
    cash_flow_stmnt = xbs.statements.cashflow_statement()
    cash_flow_df = cash_flow_stmnt.to_dataframe()
    return cash_flow_df


def get_balance_sheet(ticker:str, n: int = 5):
    """
    Fetches the balance sheet as a pandas DataFrame for a given company ticker.

    Processing: 
    - Function retrieves the latest `n` 10-K filings in XBRL format for the specified ticker,
    -Parses the XBRL data, extracts the balance sheet 
    - Converts them into a structured pandas DataFrame. Each row represents a financial line item
    (e.g., Accounts Payable, Cash, Current Debt, Equity), and each column corresponds to a reporting date.

    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL", "MSFT").
        n (int, optional): Number of most recent 10-K filings to retrieve. Defaults to 5.

    Returns:
        pd.DataFrame: A DataFrame containing the balance sheet with columns:
            - `label`: Human-readable name of the financial item
            - `concept`: XBRL concept identifier
            - One column per reporting date with the corresponding value

    Raises:
        ValueError: If no filings or balance sheet statement(s) are found.
        Any network or parsing-related exceptions from underlying libraries.
    """

    c = Company(ticker)
    filings = c.get_filings(form="10-K").latest(n)
    # Ensure filings is a list
    if not isinstance(filings, Iterable):
        filings = [filings]
    
    xbs = XBRLS.from_filings(filings)
    balance_sheet = xbs.statements.balance_sheet()
    balance_sheet_df = balance_sheet.to_dataframe()
    return balance_sheet_df

def get_income_statement(ticker:str, n: int = 5):
    """
    Fetches the income statement as a pandas DataFrame for a given company ticker.

    Processing: 
    - Function retrieves the latest `n` 10-K filings in XBRL format for the specified ticker,
    -Parses the XBRL data, extracts the income statements 
    - Converts them into a structured pandas DataFrame. Each row represents a financial line item
    (e.g., Revenue, Net Income), and each column corresponds to a reporting date.

    Args:
        ticker (str): The stock ticker symbol of the company (e.g., "AAPL", "MSFT").
        n (int, optional): Number of most recent 10-K filings to retrieve. Defaults to 5.

    Returns:
        pd.DataFrame: A DataFrame containing the income statement with columns:
            - `label`: Human-readable name of the financial item
            - `concept`: XBRL concept identifier
            - One column per reporting date with the corresponding value

    Raises:
        ValueError: If no filings or income statements are found.
        Any network or parsing-related exceptions from underlying libraries.
    """

    c = Company(ticker)
    filings = c.get_filings(form="10-K").latest(n)
    # Ensure filings is a list
    if not isinstance(filings, Iterable):
        filings = [filings]
    
    xbs = XBRLS.from_filings(filings)
    income_statement = xbs.statements.income_statement()
    income_df = income_statement.to_dataframe()
    return income_df

tools = [get_latest_filings, get_income_statement,get_balance_sheet, get_cash_flow_stmnt, get_ticker_given_name, web_search, human_assistance]

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="You are a helpful assistant tasked with finding SEC filing information for listed entities.")

# Node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
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
