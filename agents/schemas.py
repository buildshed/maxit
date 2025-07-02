from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class KeyValuePair(BaseModel):
    key: str = Field(..., description="Name of the metric or fact")
    value: str = Field(..., description="Value associated with the key")

class FilingItemSummary(BaseModel):
    item_code: str = Field(..., description="Filing section code like 'ITEM 1A'")
    title: str = Field(..., description="Title of the filing section, e.g., 'Business' or 'Risk Factors'")
    description: str = Field(..., description="High-level description of what this item covers")
    summary: Optional[str] = Field(None, description="Summary of the item extracted from the filing")
    key_values: List[KeyValuePair] = Field(default_factory=list)

    @field_validator("item_code")
    def validate_item_code(cls, v):
        from agents.core_utils import get_tenk_items
        allowed_items = get_tenk_items()
        if v not in allowed_items:
            raise ValueError(f"Invalid item_code: {v}. Must be one of: {allowed_items}")
        return v

class FilingSummary(BaseModel):
    ticker: str
    filingdate: str 
    form: str
    filingitemsummaries: List[FilingItemSummary]

class FilingChunks(BaseModel):
    ticker: str
    filingdate: str 
    form: str
    item_code: str
    chunk: str 
    embedding: List[float]

class LLMGeneratedFilingItemSummary(BaseModel):
    summary: Optional[str]
    key_values: List[KeyValuePair] = Field(default_factory=list)

class InferredItemCodes(BaseModel):
    item_codes: List[str] = Field(..., description="List of relevant 10-K item codes like ['ITEM 1A', 'ITEM 7A']")
