from data_fetch_tools import get_financial_statement, get_stock_price, get_analyst_rating_summary, get_earnings
from typing import List, Dict, Any
from edgar.company_reports import FilingStructure

def gather_peer_data(tickers: List[str]) -> Dict[str, Any]:
    peer_data = {}

    for ticker in tickers:
        try:
            income = get_financial_statement(ticker, "10-K", "income")
            balance = get_financial_statement(ticker, "10-K", "balance_sheet")
            price = get_stock_price(ticker)
            rating = get_analyst_rating_summary(ticker)
            earnings = get_earnings(ticker, n=4)

            peer_data[ticker] = {
                "income_statement": income,
                "balance_sheet": balance,
                "stock_price": price,
                "analyst_rating": rating,
                "earnings": earnings
            }
        except Exception as e:
            peer_data[ticker] = {"error": str(e)}

    return peer_data

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
