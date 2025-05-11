# Start 
# Tell me a company name and I will get you the peers 
# get ticker given name 
# get peer name, tickers 
# (if found) -> show 
# if (not found) -> ask 
# store name, tickers 
import requests 
from edgar import *
from edgar.xbrl.stitching import XBRLS
from collections.abc import Iterable

def get_ticker_given_name(company_name: str):

    """
    Searches for ticker symbols that match a given company name using Yahoo Finance's search API.
    If more than one ticker is returned, get human assistance. 

    Args:
        company_name (str): The name of the company to search for (e.g., "Apple").

    Returns:
        List[dict]: A list of dictionaries, each with:
            - 'name': The company's short name (str)
            - 'symbol': The stock ticker symbol (str)
    """

    url = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    params = {"q": company_name, "quotes_count": 5, "country": "United States"}

    res = requests.get(url=url, params=params, headers={'User-Agent': user_agent})
    data = res.json()
    #print(data)
    result = [{"name": q["shortname"], "symbol": q["symbol"]} for q in data["quotes"]]
    print("returning {}".format(result[0]))
    return result


def get_cik (name: str) -> str:
    """
    Fetches the CIK (Central Index Key) given the entity name.

    Args:
        name (str): The name of the entity (e.g., "Micron Technology").
    
    Returns:
        str: The CIK number of the entity (e.g. 'CIK0001730168').
    """
    tickers = get_ticker_given_name(name)
    
    if not isinstance(tickers, Iterable): #handle edge case of n=1
        tickers = [tickers]
    
    ticker = tickers[0]['symbol']
    filings = get_latest_filings(ticker,"10-K", n=1)

    if not isinstance(filings, Iterable): #handle edge case of n=1
        filings = [filings]

    cik_raw = filings[0].cik
    cik_formatted = f"CIK{int(cik_raw):010d}"

    return cik_formatted

def get_latest_filings (ticker: str, form_type: str, n: int = 5) -> Filings:
    """
    Fetches the latest filings of the specified form type for a given ticker using SEC-API.

    Args:
        ticker (str): The stock ticker (e.g., "AAPL").
        form_type (str): The form type (e.g., "10-K" for annual reports, "10-Q" for quarterly, "8-K" for events).
        n (int): Number of filings to retrieve. Defaults to 5.

    Returns:
        str: A newline-separated string of the latest filings, or an error message.
    """
    set_identity("your.name@example.com")
    c = Company(ticker)
    filings = c.get_filings(form=form_type).latest(n)  # Fixed this line
    
    if not isinstance(filings, Iterable): #handle edge case of n=1
        filings = [filings]
    
    s = filings # "\n".join(str(f) for f in filings)
    return s   

print(get_cik("Micron Technology"))
