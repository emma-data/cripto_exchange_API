from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest


def market_data(symbol):
    try:
        # no keys required
        client = CryptoHistoricalDataClient()
        # single symbol request
        request_params = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = client.get_crypto_latest_quote(request_params)
        # must use symbol to access even though it is single symbol
        quotes = {
            'symbol' : latest_quote[symbol].symbol,
            'bid_price' : round(float(latest_quote[symbol].bid_price),2),
            'ask_price' : round(float(latest_quote[symbol].ask_price),2),
            'timestamp' : latest_quote[symbol].timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        return quotes
    except:
        return None