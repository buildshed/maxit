from typing_extensions import List
from agents.data_fetch_tools import (
    get_stock_price, get_analyst_rating_summary, get_earnings,
    get_ticker_given_name, get_cik, get_latest_filings,
    get_financial_statement
)
from agents.generic_tools import web_search
from agents.analysis_tools import run_peer_comparison
from agents.query_ar_index import query_ar_index
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

# Define the base tool list (functions and tool instances)
_base_tools = [
    web_search, YahooFinanceNewsTool(), get_stock_price, get_analyst_rating_summary,
    get_earnings, get_ticker_given_name, get_cik, get_latest_filings,
    get_financial_statement, run_peer_comparison #query_ar_index,
]

def list_tools() -> str:
    """
    Lists all tools the assistant can use, based on their docstrings.
    """
    descriptions = []
    for tool in _base_tools + [list_tools]:
        name = getattr(tool, "__name__", str(tool))
        doc = getattr(tool, "__doc__", "(No docstring provided)")
        descriptions.append(f"**{name}**:\n{doc.strip()}")
    return "\n\n".join(descriptions)

# Final export
tools: List = _base_tools + [list_tools]
