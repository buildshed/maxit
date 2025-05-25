from datetime import datetime, timezone
from typing_extensions import TypedDict, NotRequired, List
from pydantic import BaseModel, Field
from collections.abc import Iterable
from finnhub import Client
import os
from edgar.company_reports import FilingStructure, TenK, TenQ


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

def generate_item_descriptions(structure: FilingStructure) -> str:
    lines = []
    for part, items in structure.structure.items():
        for item_code, content in items.items():
            title = content.get("Title", "No Title")
            desc = content.get("Description", "").strip()
            lines.append(f"  - \"{item_code}\": {title} — {desc}")
    return "\n".join(lines)

def get_finnhub_client() -> Client:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("Environment variable FINNHUB_API_KEY is not set")
    return Client(api_key=api_key)

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
