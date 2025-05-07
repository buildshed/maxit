import os, requests 
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from typing import List, Tuple
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.errors import NodeInterrupt
from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch
from langgraph.types import Command, interrupt
from langchain_core.tools import tool

class Entity(BaseModel):
    name: str = Field(..., description="Name of the entity")
    ticker: str = Field(..., description="Ticker symbol of the entity")

class TopEntitiesInput(BaseModel):
    name_ticker_list: List[Entity] = Field(..., description="List of entity name-ticker pairs")
    n: int = Field(..., description="Number of top entities to include")

def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]  
    
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


def get_top_entities(name_ticker_list: List[Entity], n: int) -> str:
    """
    Give a long list of name-ticker pairs, this returns a string of the top `n` name-ticker pairs formatted as 'Name (TICKER)'.

    Args:
        name_ticker_list (List[Tuple[str, str]]): A list of (name, ticker) tuples.
        n (int): Number of top entries to include.

    Returns:
        str: Formatted string of top `n` entries.
    """
    top_n = name_ticker_list[:n]
    return ', '.join(f"{e.name} ({e.ticker})" for e in top_n)

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
        
        entities = response.json()
        print("Found {} entities".format(len(entities)))
        
        if len(entities) == 1: 
            return entities[0]["ticker"]
        elif len(entities) > 1: 
            name_ticker_list = [Entity(name=e['name'], ticker=e['ticker']) for e in entities]
            top_3 = get_top_entities(name_ticker_list, 3)
            raise NodeInterrupt(f"Found {len(entities)} matching entities — top 3 being: {top_3}. Please pick one.")

        elif len(entities) == 0:
            raise NodeInterrupt(f"No matching entities found. Please refine the entity name.")
        
    except Exception as e:
        return f"Error: {e}"

tavily_search_tool = TavilySearch(
    max_results=5,
    search_depth="basic",
    topic="general")

tools = [get_latest_filing, get_ticker_from_entity_name, get_top_entities, tavily_search_tool, human_assistance]

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
