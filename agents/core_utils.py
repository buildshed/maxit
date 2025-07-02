from agents.schemas import InferredItemCodes
from datetime import datetime, timezone
from typing_extensions import TypedDict, NotRequired, List
from pydantic import BaseModel, Field
from collections.abc import Iterable
from finnhub import Client
from typing import Dict, Any
import os
from edgar.core import set_identity
from edgar.company_reports import TenK
from edgar.company_reports import FilingStructure
from edgar.company_reports import TenK
from langchain_openai import ChatOpenAI


# Define classes 
class PeerInfo(TypedDict):
    name: str # as per ticker
    ticker: str

class ClientMemory(TypedDict): 
    cik: str
    name: str #as per ticker
    tickers: str
    peers: NotRequired[List[PeerInfo]]

class KeyValuePair(BaseModel):
    key: str = Field(..., description="Name of the metric or fact")
    value: str = Field(..., description="Value associated with the key")

class BusinessSection(BaseModel):
    heading: str = Field(..., description="Section heading")
    description: str = Field(..., description="Description of what the section covers")
    summary: str | None = Field(None, description="Summary extracted from the filing")
    key_values: List[KeyValuePair] = Field(default_factory=list)

class FilingItemSummary(BaseModel):
    title: str = Field(..., description="Title of the filing section, e.g., 'Business' or 'Risk Factors'")
    description: str = Field(..., description="High-level description of what this item covers")
    sections: List[BusinessSection]

REQUIRED_KEY_VALUES = {
    "ITEM 1": [
        "Number of Employees",
        "Countries of Operation",
        "Main Products",
        "Revenue Segments"
    ],
    "ITEM 1A": [
        "FX Hedging Notional",
        "Geopolitical Risk",
        "Interest Rate Risk",
        "Supply Chain Risk"
    ],
    "ITEM 7A": [
        "FX Hedging Notional",
        "Interest Rate Swap Notional",
        "Commodity Exposure",
        "Sensitivity to Rate Movements"
    ]
}

def summarize_item_text(item_code: str, title:str, description: str, item_text: str)-> str: 
    prompt = (
        f"You are a financial analyst assistant. Read the following text from {title} ({item_code}) "
        "of a 10-K filing. Extract and populate the following structured format:\n\n"
        f"{description}\n\n"
        "- Write a short summary (max 100 words).\n"
        "- Remember to include key numerical data \n"
        f"TEXT:\n{item_text}"
    )
    
    llm = ChatOpenAI(model="gpt-4o")

    response = llm.invoke(prompt)
    llmgen_summary = response.content
    return llmgen_summary 

def get_finnhub_client() -> Client:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("Environment variable FINNHUB_API_KEY is not set")
    return Client(api_key=api_key)

def set_sec_client():
    """
    Initializes and returns the SEC client with identity set.

    Identity (email) is fetched from the SEC_IDENTITY environment variable.
    """
    email = os.getenv("SEC_IDENTITY", "default@example.com")
    set_identity(email)
    # You can optionally return a client or None if set_identity is global
    return True

def ensure_list(item):
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

def convert_unix_to_datetime(timestamp: int) -> str:
    """
    Convert a UNIX timestamp to a human-readable date and time (UTC).

    Args:
        timestamp (int): UNIX timestamp (seconds since epoch).

    Returns:
        str: Formatted date and time in 'YYYY-MM-DD HH:MM:SS' format (UTC).
    
    Example:
        convert_unix_to_datetime(1747771200)  # → '2025-05-20 20:00:00'
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def get_tenk_items():
    all_items = []
    #print(dir(TenK.structure))  
    all_items = []
    for part_dict in TenK.structure.structure.values():
        all_items.extend(part_dict.keys())
    return all_items

def format_peer_comparison_prompt(peer_data: Dict[str, Any]) -> str:
    prompt = "Compare the following companies across:\n"
    prompt += "- Revenue\n- Cost Structure\n- Profitability\n- Leverage\n- Stock and Valuation\n\n"
    prompt += "Here is the raw data:\n"

    for ticker, data in peer_data.items():
        prompt += f"\n### {ticker} ###\n"
        if "error" in data:
            prompt += f"Error: {data['error']}\n"
            continue
        prompt += f"Income Statement: {data['income_statement']}\n"
        prompt += f"Balance Sheet: {data['balance_sheet']}\n"
        prompt += f"Stock Price: {data['stock_price']}\n"
        prompt += f"Analyst Rating: {data['analyst_rating']}\n"
        prompt += f"Earnings: {data['earnings']}\n"

    prompt += "\nPlease provide a concise peer comparison."
    return prompt

def generate_item_descriptions(structure: FilingStructure) -> str:
    lines = []
    for part, items in structure.structure.items():
        for item_code, content in items.items():
            title = content.get("Title", "No Title")
            desc = content.get("Description", "").strip()
            lines.append(f"  - \"{item_code}\": {title} — {desc}")
    return "\n".join(lines)

def get_tenk_item_descriptions() -> dict[str, str]:
    descriptions = {}
    for part_dict in TenK.structure.structure.values():
        for item_code, meta in part_dict.items():
            title = meta.get("Title", "")
            desc = meta.get("Description", "")
            descriptions[item_code] = f"{title}: {desc}"
    return descriptions

def infer_relevant_items(query: str, item_map: dict[str, str]) -> list[str]:
    item_list_str = "\n".join([f"{code}: {desc}" for code, desc in item_map.items()])
    prompt = (
        f"You are a smart assistant that maps user questions to relevant items from a 10-K filing.\n\n"
        f"Question: \"{query}\"\n\n"
        f"Choose one or more relevant items from the list below based on the topic of the question.\n"
        f"Format your output as InferredItemCodes(item_codes=[...])\n\n"
        f"Available Items:\n{item_list_str}"
    )
    llm = ChatOpenAI(model="gpt-4o")
    structured_llm =llm.with_structured_output(InferredItemCodes)
    response = structured_llm.invoke(prompt)
    return response.item_codes
