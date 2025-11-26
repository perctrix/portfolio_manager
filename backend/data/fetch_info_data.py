from curl_cffi import requests


def get_ticker_info(symbol: str) -> dict:
    """
    Get the info data of a stock, equivalent to yfinance.Ticker().info

    Args:
        symbol: Stock code, e.g. 'AAPL'

    Returns:
        A dictionary containing the stock info
    """
    
    session = requests.Session(impersonate='chrome')

    # Step 1: Get cookie
    session.get('https://fc.yahoo.com', timeout=30, allow_redirects=True)
    
    # Step 2: Get crumb
    crumb_response = session.get(
        'https://query1.finance.yahoo.com/v1/test/getcrumb',
        timeout=30,
        allow_redirects=True
    )
    crumb = crumb_response.text
    
    # Step 3: Access quoteSummary API
    url1 = f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}'
    params1 = {
        'modules': 'financialData,quoteType,defaultKeyStatistics,assetProfile,summaryDetail',
        'crumb': crumb
    }
    response1 = session.get(url1, params=params1, timeout=30)
    data1 = response1.json()
    
    # Step 4: Access quote API to get additional data
    url2 = 'https://query1.finance.yahoo.com/v7/finance/quote'
    params2 = {
        'symbols': symbol,
        'formatted': 'false',
        'crumb': crumb
    }
    response2 = session.get(url2, params=params2, timeout=30)
    data2 = response2.json()
    
    # Merge data
    info = {}
    # Extract data from quoteSummary
    if data1.get('quoteSummary', {}).get('result'):
        result = data1['quoteSummary']['result'][0]
        for module_name, module_data in result.items():
            if isinstance(module_data, dict):
                info.update(module_data)
    # Extract data from quote
    if data2.get('quoteResponse', {}).get('result'):
        quote_result = data2['quoteResponse']['result'][0]
        info.update(quote_result)

    return info


if __name__ == '__main__':
    # Test code
    symbol = 'AAPL'
    print(f'Getting info data for {symbol}...\n')
    info = get_ticker_info(symbol)
    # Print some key information
    print(f"Company Name: {info.get('longName')}")
    print(f"Industry: {info.get('industry')}")
    print(f"Sector: {info.get('sector')}")
    print(f"Market Cap: {info.get('marketCap')}")
