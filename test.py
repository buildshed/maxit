import requests
from edgar import *
from edgar.xbrl.stitching import XBRLS

def get_latest_filings(ticker:str):
    c = Company(ticker)
    filings = c.get_filings(form="8-K").latest(5)
    print (filings)

def get_cik(ticker):
    headers = {"User-Agent": "Gaurav your_email@example.com"}
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=headers)
    data = response.json()

    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            print("returning {}".format(str(entry["cik_str"]).zfill(10)))
            return str(entry["cik_str"]).zfill(10)  # CIK must be 10 digits

    return None

def get_income_dataframe(ticker:str):
    c = Company(ticker)
    filings = c.get_filings(form="10-K").latest(5)
    xbs = XBRLS.from_filings(filings)
    income_statement = xbs.statements.income_statement()
    income_df = income_statement.to_dataframe()
    return income_df

get_latest_filings("MU")
cik = get_cik('MU')
print(cik)
print(get_income_dataframe('MU').to_string(index=False))


