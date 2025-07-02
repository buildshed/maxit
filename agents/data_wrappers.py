from typing import List, Dict, Any
from agents.data_fetch_tools import get_financial_statement, get_stock_price, get_analyst_rating_summary, get_earnings

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