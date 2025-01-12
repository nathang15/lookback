from pandas import DataFrame
import groq
import openai
from utils.load_data import LoadData
from strategies import Traditional, TechnicalAnalysis, MachineLearning


class TraderEngine:
    def __str__(self):
        return f"Load tickers data from Yahoo Finance."

    def __init__(self):
        self.TraditionalStrategies = Traditional()

    def set_api_key(self, api_key: str):
        openai.api_key = api_key

    def query(self, query: str) -> str:
        # Load the data
        self._data_loader = LoadData(query)
        self._data_loader.execute()

    @property
    def strategy_data(self) -> DataFrame:
        df = self._data_loader.strategy_data
        df = df[
            [ticker for ticker in df.columns if ticker != "Date" and "_" not in ticker]
        ]
        return df