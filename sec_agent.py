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
from edgar import *
from edgar.xbrl.stitching import XBRLS
from typing import Literal
from collections.abc import Iterable
import pandas as pd
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode


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


# Chatbot Node (uses basic dict state)
def chatbot(state: dict) -> dict:
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}

# Define Tools (including web search, chatbot. Exclude human assistance)
tools = [web_search, get_ticker_given_name, get_cik, get_latest_filings, get_financial_statement, get_client_info, save_client_info]
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)
store = InMemoryStore() 

set_identity("your.name@example.com")

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




