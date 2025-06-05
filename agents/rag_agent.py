from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_openai import ChatOpenAI
from edgar import *
from sec_agent_tools import get_latest_filings
from edgar.company_reports import FilingStructure, TenK, TenQ
from util_tools import util_ensure_list
from langchain_text_splitters import TokenTextSplitter

def get_filing_url(filing: Filing) -> str:
    """
    """
    return str(filing.text_url)

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Define application steps
def retrieve(state: State):
    #retrieved_docs = vector_store.similarity_search(state["question"], k=5)
    #return {"context": retrieved_docs}
    return state

def generate(state: State):
    #docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    #messages = prompt.invoke({"question": state["question"], "context": docs_content})
    #response = llm.invoke(messages)
    #return {"answer": response.content}
    return state

# Set identity for EdgarTools
set_identity("your_email@example.com")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = InMemoryVectorStore(embeddings)
#llm = ChatOpenAI(model="gpt-4o")

filings = get_latest_filings(ticker='MU', form_type= "10-K", n=5, as_text=False)
filings = util_ensure_list(filings)
filing = filings[0]
filing_url = get_filing_url(filing)
#print(filing_url)

headers = {"User-Agent": "MyResearchBot/1.0 (contact: your_email@example.com)",}

# Load and chunk contents of the blog
loader = WebBaseLoader(
    web_paths=(filing_url,),
    header_template=headers
)
docs = loader.load()
token_splitter = TokenTextSplitter(
    chunk_size=1000,  # Adjust per embedding model
    chunk_overlap=100
)
# Re-split using token count instead of character count
token_splits = token_splitter.split_documents(docs)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
all_splits = text_splitter.split_documents(docs)

print(f"Original docs: {len(docs)}")
print(f"Splits: {len(token_splits)}")
print(f"Longest split: {max(len(d.page_content) for d in token_splits)} chars")

# Index chunks
_ = vector_store.add_documents(documents=token_splits)

# Define prompt for question-answering
# N.B. for non-US LangSmith endpoints, you may need to specify
# api_url="https://api.smith.langchain.com" in hub.pull.
prompt = hub.pull("rlm/rag-prompt")

# Compile application and test
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

response = graph.invoke({"question": "What is management view on risk factors?"})
print(response["answer"])
