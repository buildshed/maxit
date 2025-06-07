from agents.data_fetch_tools import get_latest_filings
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_openai import ChatOpenAI

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

class FilingSummary(BaseModel):
    ticker: str
    filingdate: str 
    form: str
    filingitemsummaries: List[FilingItemSummary]

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
        "Sensitivity to Rate Movements", 
        "Key Exposure Currencies"
    ]
    }

def generate_structured_item(item_code: str, title: str, description: str,item_txt:str) -> FilingItemSummary:
    
    llm = ChatOpenAI(model="gpt-4o")
    required_keys = REQUIRED_KEY_VALUES.get(item_code.upper(), [])
    required_key_text = (
    "- Try to extract the following key-value pairs if available:\n" +
    "".join(f"  • {key}\n" for key in required_keys) + "\n"
    if required_keys else "")
    
    prompt = (
    f"You are a financial analyst assistant. Read the following text from {title} ({item_code}) "
    "of a 10-K filing. Extract and populate the following structured format:\n\n"
    f"{description}\n\n"
    "- Divide the text into logical subsections.\n"
    "- For each subsection, write a 3–5 sentence summary.\n"
    "- Add important numeric or categorical values as key-value pairs.\n"
    f"{required_key_text}"
    "Format your output as a FilingItemSummary(title, description, sections=[...]).\n\n"
    f"TEXT:\n{item_txt}")
    #print (prompt)
    structured_llm = llm.with_structured_output(FilingItemSummary)
    return structured_llm.invoke(prompt)


tickers = ["MU","AVGO", "NVDA","AMD", "INTC", "VZ", "T"]
items_of_interest = ["ITEM 1","ITEM 1A", "ITEM 1B", "ITEM 6", "ITEM 7","ITEM 7A" ]
all_filing_summaries = []

for ticker in tickers: 
    #get the last 5 ARs
    filings = get_latest_filings(ticker, form_type="10-K", n=1, as_text=False)
    # for each AR 
    for filing in filings:
        tenk = filing.obj()
        filing_item_summaries = []
        for item_code in items_of_interest:
            tenk_item = tenk.structure.get_item(item_code)
            title = tenk_item["Title"]
            description = tenk_item["Description"]
            item_txt = str(tenk[item_code])
            filing_item_summary = generate_structured_item(item_code, title, description,item_txt)
            filing_item_summaries.append(filing_item_summary)
    
        filing_summary = FilingSummary(
                ticker=ticker,
                filingdate=filing.report_date,
                form=filing.form,
                filingitemsummaries=filing_item_summaries
        )

        all_filing_summaries.append(filing_summary)

print(all_filing_summaries)
