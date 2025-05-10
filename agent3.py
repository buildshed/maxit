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
from typing_extensions import TypedDict
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from typing import TypedDict, List, Optional, Literal, Dict
from pydantic import BaseModel, Field

set_identity("your.name@example.com")

# Define allowed blueprints, steps and phases 
BlueprintName = Literal["Peer Comparison", "Debt Profiling", "Financing Need"]
StepName = Literal["Revenue Comparison", "Cost Comparison", "Proftability Comparison", "Leverage Comparison"] # Only for Peer Comparison for now
PhaseName = Literal["Set Parameters", "Collect Data", "Process Data", "Generate Output"]
Status = Literal["Not Started", "Started", "Completed", "Waiting"] # Applies to Steps and Phases 

class PhaseExecutionStatus(TypedDict, total=False):
    phase: PhaseName
    status: Status
    input: Optional[str]  # Optional user input tied to this phase

class StepExecutionStatus(TypedDict, total= False):
    step: StepName
    phases: List[PhaseExecutionStatus]
    input: Optional[str]  # Optional user input tied to this step

class BlueprintExecutionStatus(TypedDict, total=False):
    blueprint: BlueprintName
    steps: List[StepExecutionStatus]
    input: Optional[str]  # Optional user input tied to this Blueprint

class AgentState(TypedDict, total=False):
    user_id: str
    mode: Literal["chatbot", "blueprint"]
    current_blueprint: BlueprintName  # e.g., ["Revenue Comparison"]
    current_blueprint_execution_status: BlueprintExecutionStatus
    messages: Annotated[list, add_messages]

class BlueprintDecision(BaseModel):
    blueprint: Optional[BlueprintName] = Field(
        default=None,
        description="Detected blueprint from the user's intent, or None if no blueprint applies."
    )

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

# Chatbot Node
def chatbot(state: AgentState):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}

def detect_blueprint(state: AgentState):
    mode = state.get("mode")
    if mode == "blueprint":
        print(f"[detect_blueprint] Already in blueprint mode: {state.get('current_blueprint')}")
        return {}
    elif mode == "chatbot":
        print("[detect_blueprint] Chatbot mode active — skipping blueprint detection")
        return {}
    else:
        structured_llm = llm.with_structured_output(BlueprintDecision)
        prompt = (
                "You are an assistant that classifies whether a user's message corresponds to one of the known financial blueprints.\n"
                "Pick one of the blueprint names, or null if none applies."
            )
        last_message = str(state["messages"][-1].content)
        result = structured_llm.invoke(prompt + "\n\nUser message:\n" + last_message)
        blueprint = result.blueprint  # Optional[str]
        print(f"[detect_blueprint] Detected blueprint: {blueprint}")
        
        state_update = {}
        if blueprint: 
            state_update = {
                "mode": "blueprint",
                "current_blueprint": blueprint
            }
        else: 
            state_update = {
            "mode": "chatbot", 
            "current_blueprint": None
            }
        return state_update

def run_blueprint(state): # Run the peer comparison blueprint
    state.setdefault("current_blueprint_execution_status", {}) #should be moved into a dedicated fn. 
    state['current_blueprint_execution_status']['input'] = "jai Ho"
    return state


def select_blueprint_or_chat(state) -> Literal["chatbot", "run_blueprint"]:  
    if state['current_blueprint']: 
        return "run_blueprint"
    else:
        return "chatbot"

tools = [get_latest_filings, get_income_statement,get_balance_sheet, get_cash_flow_stmnt, get_ticker_given_name, web_search, human_assistance]

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="You are a helpful assistant.")

# Build graph

builder = StateGraph(AgentState)
builder.add_node("chatbot", chatbot)
builder.add_node("detect_blueprint", detect_blueprint)
builder.add_node("run_blueprint", run_blueprint)
builder.add_edge(START, "detect_blueprint")
builder.add_conditional_edges("detect_blueprint", select_blueprint_or_chat)

builder.add_node("tools", ToolNode(tools))
builder.add_conditional_edges(
    "chatbot",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "chatbot")

# Compile graph
graph = builder.compile()
