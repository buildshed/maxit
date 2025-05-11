from langchain_core.runnables import RunnableConfig
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from typing_extensions import TypedDict, NotRequired, List

class PeerInfo(TypedDict):
    name: str
    ticker: str

class ClientMemory(TypedDict): 
    cik: str
    name: str
    tickers: List[str]
    peers: NotRequired[List[PeerInfo]]

store = InMemoryStore() 
# Create ClientMemory object for Micron

micron: ClientMemory = {
    "cik": "CIK0000723125",
    "name": "Micron Technology",
    "tickers": ["MU"]
}
store.put(("clients",), "CIK0000723125", micron)

broadcom: ClientMemory = {
    "cik": "CIK0001730168",
    "name": "Broadcom Inc.",
    "tickers": ["AVGO"]
}
store.put(("clients",), "CIK0001730168", broadcom)

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

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(
    model=llm,
    tools=[get_client_info,save_client_info],
    store=store 
)

# Run the agent to retrieve
response = agent.invoke(
    {"messages": [{"role": "user", "content": "look up client information for CIK0000723125"}]}
)
# Get the first AIMessage with non-empty content
ai_message = next(
    msg for msg in response["messages"]
    if isinstance(msg, AIMessage) and msg.content.strip()
)
print(ai_message.content)
print(response)

# Run the agent to save
response = agent.invoke(
    {"messages": [{"role": "user", "content": "save client information for NVIDIA CIK0001045810 ticker NVDA"}]}
)
# Get the first AIMessage with non-empty content
ai_message = next(
    msg for msg in response["messages"]
    if isinstance(msg, AIMessage) and msg.content.strip()
)
print(ai_message.content)
print(response)

# Run the agent to retrieve
response = agent.invoke(
    {"messages": [{"role": "user", "content": "look up client information for CIK0001045810"}]}
)
# Get the first AIMessage with non-empty content
ai_message = next(
    msg for msg in response["messages"]
    if isinstance(msg, AIMessage) and msg.content.strip()
)
print(ai_message.content)
print(response)