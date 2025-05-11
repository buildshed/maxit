from langchain_core.runnables import RunnableConfig
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI

store = InMemoryStore() 
store.put(  
    ("users",),  
    "user_123",  
    {
        "name": "John Smith",
        "language": "English",
    } 
)
def get_user_info(config: RunnableConfig) -> str:
    """Look up user info."""
    # Same as that provided to `create_react_agent`
    store = get_store() 
    user_id = config["configurable"].get("user_id")
    user_info = store.get(("users",), user_id) 
    return str(user_info.value) if user_info else "Unknown user"

llm = ChatOpenAI(model="gpt-4o")

agent = create_react_agent(
    model=llm,
    tools=[get_user_info],
    store=store 
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    config={"configurable": {"user_id": "user_123"}}
)
print (response)