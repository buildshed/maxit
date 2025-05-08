import os, requests 
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from edgar import *
from edgar.xbrl.stitching import XBRLS
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from collections.abc import Iterable

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

tools = [get_latest_filings, get_income_statement]

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
