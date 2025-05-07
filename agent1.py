import os, requests 
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

def get_latest_filing(ticker: str, form_type: str):

    """
    Fetches the latest annual report filing given the ticker using SEC-API.

    Args:
        ticker (str): The stock ticker (e.g. "AAPL")
        form_type (str): the form type, "10-K" for annual report, "10-Q" for quarterly filing and "8-K" for material events filing 

    Returns:
        str: last filing date, else an error message
    """

    api_key = os.getenv("SEC_API_KEY")
    if not api_key:
        raise ValueError("SEC_API_KEY environment variable is not set.")

    url = "https://api.sec-api.io"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    payload = {
        "query": f'ticker:"{ticker.upper()}" AND formType:"{form_type}"',
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    if not data.get("filings"):
        return None

    latest_filing = data["filings"][0]
    #print (latest_filing) 
    return latest_filing['filedAt']

def get_ticker_from_entity_name(entity_name: str) -> str:
    """
    Fetches the stock ticker for a given entity name using SEC-API.

    Args:
        entity_name (str): Name of the entity (e.g. "Micron Technology")

    Returns:
        str: Ticker symbol if found, else an error message
    """
    api_key = os.getenv("SEC_API_KEY")
    if not api_key:
        return "Error: SEC_API_KEY environment variable not set."

    base_url = "https://api.sec-api.io/mapping/name/"
    url = f"{base_url}{entity_name.replace(' ', '%20')}"
    headers = {"Authorization": api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and "ticker" in data[0]:
            return data[0]["ticker"]
        else:
            return "Ticker not found"
    except Exception as e:
        return f"Error: {e}"

def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b

tools = [get_latest_filing, get_ticker_from_entity_name]

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
