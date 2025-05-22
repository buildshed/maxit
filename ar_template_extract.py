import requests , json
from edgar import *
from edgar.xbrl.stitching import XBRLS
from collections.abc import Iterable
from langchain_openai import ChatOpenAI
from typing_extensions import Annotated
from typing import Callable, List
import inspect
from typing import List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from edgar.company_reports import TenK

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class KeyValuePair(BaseModel):
    key: str = Field(..., description="Name of the metric or fact")
    value: str = Field(..., description="Value associated with the key")

class BusinessSection(BaseModel):
    heading: str = Field(..., description="Section heading")
    description: str = Field(..., description="Description of what the section covers")
    summary: Optional[str] = Field(None, description="Summary extracted from the filing")
    key_values: List[KeyValuePair] = Field(default_factory=list)

class FilingItemSummary(BaseModel):
    title: str = Field(..., description="Title of the filing section, e.g., 'Business' or 'Risk Factors'")
    description: str = Field(..., description="High-level description of what this item covers")
    sections: List[BusinessSection]

    def get_section_by_heading(self, heading: str) -> Optional[BusinessSection]:
        for section in self.sections:
            if section.heading.lower() == heading.lower():
                return section
        return None

def generate_item1_extract(item1_txt: str) -> FilingItemSummary: 

    return "Successfully saved user info."

def generate_structured_item(
    llm,
    tenk: "TenK",
    item_code: str,
    raw_text: str
) -> FilingItemSummary:
    """
    Generate a structured summary of a 10-K item section using a predefined schema.
    
    Args:
        llm: An LLM instance (e.g., ChatOpenAI)
        tenk: An instance of the TenK class with FilingStructure
        item_code: The item code, e.g., "ITEM 1A" or "ITEM 7A"
        raw_text: The text content of the item section
    
    Returns:
        FilingItemSummary: structured output conforming to the schema
    """
    item = tenk.structure.get_item(item_code)
    if not item:
        raise ValueError(f"{item_code} not found in TenK.structure")

    print(item)
    title = item["Title"]
    description = item["Description"]

    prompt = (
        f"You are a financial analyst assistant. Read the following text from {title} ({item_code}) "
        "of a 10-K filing. Extract and populate the following structured format:\n"
        "- Use logical subsections (e.g., key themes, risk types, business lines).\n"
        "- For each section, write a 3–5 sentence summary.\n"
        "- Add any important numeric or categorical values as key-value pairs.\n\n"
        f"Section Context:\nTitle: {title}\nDescription: {description}\n\n"
        f"Text:\n{raw_text}"
    )

    structured_llm = llm.with_structured_output(FilingItemSummary)
    return structured_llm.invoke(prompt)


set_identity("your.name@example.com")

# Get a 10-K filing
ticker = 'MU'
company = find(ticker)  
#filing = company.get_filings(form="10-K")[0]
filing = company.get_filings(form="10-K").latest(1)
tenk = filing.obj()

item_code = 'Item 1A'
item_txt = str(tenk[item_code])
#print(item_txt)

llm = ChatOpenAI(model="gpt-4o")

result: FilingItemSummary = generate_structured_item(
    llm=llm,
    tenk=tenk,
    item_code=item_code,
    raw_text=item_txt
)
print(json.dumps(result.model_dump(), indent=2))

