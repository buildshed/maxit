# Include libraries 
from langgraph.config import get_store
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from typing_extensions import List
from typing import Literal
from langgraph.graph import START, StateGraph, MessagesState, END
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from agents.core_utils import ClientMemory
from tool_registry import tools

# Access the last AI message
def get_last_ai_message(messages: List)-> BaseMessage:
    for message in reversed(messages):
        if isinstance(message, AIMessage): # Assuming "ai" is the role for AI messages
            return message
    return None # Handle the case where no AI message is found

# Access the last human message
def get_last_human_message(messages: List)-> BaseMessage:
    for message in reversed(messages):
        if isinstance(message, HumanMessage): # Assuming "ai" is the role for AI messages
            return message
    return None # Handle the case where no AI message is found


def manage_memory_connector_node(state: dict)->dict:
    return state

def should_update_or_save_memory(state: dict)->Literal["update_memory_node", "__end__"]:
    #if the conversation says anything about peers, get the list of peers and edit it 
    messages = state["messages"]
    last_human_message = get_last_human_message(messages)
    last_ai_message = get_last_ai_message(messages)
    if last_human_message and isinstance(last_human_message.content, str):
        if "peer" in last_human_message.content.lower():
            return ("update_memory_node")
    
    return END

def update_memory_node(state: dict)->dict: 
    return

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

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

store = InMemoryStore() 

# Define and complile graph  
# Build graph
builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_node("manage_memory_connector_node", manage_memory_connector_node)
builder.add_node("update_memory_node", update_memory_node)
builder.add_edge(START, "chatbot")
builder.add_conditional_edges(
    "chatbot",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
    {
        "tools": "tools",
        END: "manage_memory_connector_node" # ← acts like a dummy before ending
    } 
)
builder.add_edge("tools", "chatbot")
builder.add_conditional_edges("manage_memory_connector_node", should_update_or_save_memory) 
builder.add_edge("update_memory_node", END) 

# Compile graph
graph = builder.compile()


