import pandas as pd
from type_convert import convert_data

class LoadData:
    def __init__(self, prompt: str):
        # convert data from csv to dataframe
        self._tickers = pd.read_csv("../data/all_ticker_data.csv", header=0).transpose()
        self._tickers_columns = self._tickers.iloc[0]
        self._tickers = self._tickers[1:]
        self._tickers.reset_index(inplace=True)
        self._tickers.rename(columns={"index": "ticker"}, inplace=True)
        self._tickers = convert_data(self._tickers)

    @property
    def strategy_data(self):
        return self._strategy_data
    
    def execute(self) -> None:
        pass