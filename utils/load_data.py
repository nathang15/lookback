import pandas as pd
from utils.type_convert import convert_data

class LoadData:
    def __init__(self, prompt: str):
        # convert data from csv to dataframe
        self._tickers = pd.read_csv("./data/all_ticker_data.csv", header=0, low_memory=False).transpose()
        
        # Store column names from first row
        self._tickers_columns = self._tickers.iloc[0]
        
        # Remove the first row
        self._tickers = self._tickers[1:]
        self._tickers.reset_index(inplace=True)
        self._tickers.rename(columns={"index": "ticker"}, inplace=True)
        
        # Create and apply column mapping
        column_mapping = {i: name for i, name in enumerate(self._tickers_columns)}
        self._tickers = self._tickers.rename(columns=column_mapping)
        
        # Convert data types
        self._tickers = convert_data(self._tickers)

    @property
    def strategy_data(self):
        return self._strategy_data
    
    def execute(self) -> None:
        pass