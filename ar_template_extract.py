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

class Item1Business(BaseModel):
    title: str = Field(..., description="Section title")
    description: str = Field(..., description="Overview of the company's business operations, products, services, and market environment.")
    sections: List[BusinessSection]

    def get_section_by_heading(self, heading: str) -> Optional[BusinessSection]:
        for section in self.sections:
            if section.heading.lower() == heading.lower():
                return section
        return None

def generate_item1_extract(item1_txt: str) -> Item1Business: 

    return "Successfully saved user info."


set_identity("your.name@example.com")

# Get a 10-K filing
ticker = 'MU'
company = find(ticker)  
#filing = company.get_filings(form="10-K")[0]
filing = company.get_filings(form="10-K").latest(1)
tenk = filing.obj()

item = 'Item 1'
item_txt = str(tenk[item])

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Item1Business)
result = structured_llm.invoke(item_txt)
print(json.dumps(result.dict(), indent=2))

