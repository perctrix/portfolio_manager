import logging
import threading
import time
from collections import defaultdict
from typing import Dict, List

import pandas as pd
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

logger: logging.Logger = logging.getLogger(__name__)


class IBDataDownloader(EClient, EWrapper):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.historical_data: Dict[int, List[Dict]] = defaultdict(list)
        self.data_ready: Dict[int, bool] = {}
        self.errors: Dict[int, str] = {}
        self.next_req_id: int = 1

    def nextValidId(self, orderId: int) -> None:
        self.next_req_id = orderId

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderReject: str = "") -> None:
        if errorCode not in [2104, 2106, 2158, 2176]:
            logger.error("IB error %d: %d - %s", reqId, errorCode, errorString)
            self.errors[reqId] = f"{errorCode}: {errorString}"
            self.data_ready[reqId] = True

    def historicalData(self, reqId: int, bar) -> None:
        self.historical_data[reqId].append({
            'DateTime': bar.date,
            'Open': bar.open,
            'High': bar.high,
            'Low': bar.low,
            'Close': bar.close,
            'Volume': bar.volume,
        })

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        self.data_ready[reqId] = True

    def download_historical_bars(self, symbol: str, end_datetime: str = "", duration: str = "1 D",
                                 bar_size: str = "1 min", what_to_show: str = "TRADES",
                                 use_rth: bool = True, exchange: str = "SMART") -> pd.DataFrame:
        req_id = self.next_req_id
        self.next_req_id += 1

        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = "USD"

        self.data_ready[req_id] = False

        self.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime=end_datetime,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=1 if use_rth else 0,
            formatDate=1,
            keepUpToDate=0,
            chartOptions=[]
        )

        start_time = time.time()
        while not self.data_ready.get(req_id, False):
            time.sleep(0.1)
            if time.time() - start_time > 30:
                break

        if req_id in self.errors or not self.historical_data[req_id]:
            return pd.DataFrame()

        df = pd.DataFrame(self.historical_data[req_id])
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df.set_index('DateTime', inplace=True)
        return df

def fetch_historical_data_ib(symbol: str, duration: str = "1 Y", bar_size: str = "1 day", 
                             what_to_show: str = "TRADES", host: str = "127.0.0.1", port: int = 4001,
                             clientId: int = 1) -> pd.DataFrame:
    """
    Fetches historical data from Interactive Brokers.

    Parameters
    symbol : str
        The ticker symbol of the stock.
    duration : str, optional
        The duration of the historical data to fetch. Default is "1 Y".
    bar_size : str, optional
        The size of the bars to fetch. Default is "1 day".
    what_to_show : str, optional
        The type of data to fetch. Default is "TRADES".
    host : str, optional
        The host address of the IB Gateway or TWS. Default is "127.0.0.1".
    port : int, optional
        The port number of the IB Gateway or TWS. Default is 4001. (P.S. 4001 is default for IB Gateway,7497 for TWS)
    clientId : int, optional
        The client ID to use for the connection. Default is 1.
    """
    app = IBDataDownloader()
    app.connect(host=host, port=port, clientId=clientId)
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    market_data = app.download_historical_bars(symbol=symbol, duration=duration, bar_size=bar_size, what_to_show=what_to_show)
    app.disconnect()
    return market_data


if __name__ == "__main__":
    symbol = "AAPL"
    market_data = fetch_historical_data_ib(symbol=symbol, duration="10 Y", bar_size="1 day", what_to_show="TRADES")
    market_data.index.name = "Date"
    print(market_data)
