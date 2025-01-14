from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame
from typing import List, Optional, Tuple, Dict
import numpy as np
from utils.metrics import get_metrics
from utils.plot import plot_results

class Traditional:
    def __init__(self):
        pass

    def __str__(self):
        return f"Experiment with traditional simple strategies."

    @staticmethod
    def long(df: DataFrame = None) -> Tuple[Dict, List[Figure]]:
        original_len_cols = len(df.columns)

        # Calculate the returns for holding long positions
        for stock in df.columns:
            df[f"{stock}_return"] = df[stock].pct_change()

        df["Total_Return"] = df[[col for col in df.columns if "return" in col]].mean(axis=1)
        df["Cumulative_Return"] = (1 + df["Total_Return"]).cumprod()
        df["Drawdown"] = (df["Cumulative_Return"] - df["Cumulative_Return"].cummax()) / df["Cumulative_Return"].cummax() - 1

        # Add market signal column
        for stock in df.columns[:original_len_cols]:
            df[f"{stock}_signal"] = 0
            df.loc[df.index[0], f"{stock}_signal"] = "Buy"
            df.loc[df.index[-1], f"{stock}_signal"] = "Sell"

        # Generate outputs
        metrics = get_metrics(df, "long")
        figures = plot_results(df, metrics)
        
        return metrics, figures

    @staticmethod
    def short(df: DataFrame) -> Tuple[Dict, List[Figure]]:
        original_len_cols = len(df.columns)

        # Calculate returns for short positions
        for stock in df.columns:
            df[f"{stock}_return"] = -1 * df[stock].pct_change()

        df["Total_Return"] = df[[col for col in df.columns if "return" in col]].mean(axis=1)
        df["Cumulative_Return"] = (1 + df["Total_Return"]).cumprod()
        df["Drawdown"] = (df["Cumulative_Return"] / df["Cumulative_Return"].cummax()) - 1

        # Add market signal column
        for stock in df.columns[:original_len_cols]:
            df[f"{stock}_signal"] = 0
            df.loc[df.index[0], f"{stock}_signal"] = "Sell"
            df.loc[df.index[-1], f"{stock}_signal"] = "Buy"

        # Generate outputs
        metrics = get_metrics(df, "short")
        figures = plot_results(df, metrics)
        
        return metrics, figures

    @staticmethod
    def long_short(
        df: DataFrame = None,
        long_tickers: Optional[List[str]] = None,
        short_tickers: Optional[List[str]] = None,
    ) -> Tuple[Dict, List[Figure]]:
        original_len_cols = len(df.columns)

        # Calculate returns
        for stock in df.columns:
            if stock in long_tickers:
                df[f"{stock}_return"] = df[stock].pct_change()
            elif stock in short_tickers:
                df[f"{stock}_return"] = -1 * (df[stock].pct_change())
            else:
                df[f"{stock}_return"] = 0

        df["Total_Return"] = df[[col for col in df.columns if "return" in col]].mean(axis=1)
        df["Cumulative_Return"] = (1 + df["Total_Return"]).cumprod()
        df["Drawdown"] = (df["Cumulative_Return"] / df["Cumulative_Return"].cummax()) - 1

        # Add market signal column
        for stock in df.columns[:original_len_cols]:
            df[f"{stock}_signal"] = 0
            if stock in long_tickers:
                df.loc[df.index[0], f"{stock}_signal"] = "Buy"
                df.loc[df.index[-1], f"{stock}_signal"] = "Sell"
            elif stock in short_tickers:
                df.loc[df.index[0], f"{stock}_signal"] = "Sell"
                df.loc[df.index[-1], f"{stock}_signal"] = "Buy"

        # Generate outputs
        metrics = get_metrics(df, "long_short")
        figures = plot_results(df, metrics)
        
        return metrics, figures