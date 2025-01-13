import numpy as np
from pandas import DataFrame

from utils.metrics import get_metrics
from utils.plot import plot_results

class TechnicalAnalysis:

    def __init__(self):
        pass

    def __str__(self):
        return f"Experiment with technical strategies."
    
    # momentum trading
    @staticmethod
    def momentum(df: DataFrame = None, window: int = 5) -> None:
        original_len_cols = len(df.columns)
        for stock in df.columns[:original_len_cols]:
            df[f"{stock}_return"] = df[stock].pct_change()
            df[f"{stock}_momentum"] = (
                df[f"{stock}_return"].rolling(window=window).mean()
            )
            df[f"{stock}_position"] = np.where(
                df[f"{stock}_momentum"].isna(),
                0,
                np.where(df[f"{stock}_momentum"] > 0, 1, -1),
            )
            df[f"{stock}_strategy"] = (
                df[f"{stock}_position"].shift(1) * df[f"{stock}_return"]
            )

            # Add buy and sell signals only when position changes
            df[f"{stock}_signal"] = np.where(
                df[f"{stock}_position"] != df[f"{stock}_position"].shift(),
                np.where(
                    df[f"{stock}_position"] == 1,
                    "Buy",
                    np.where(df[f"{stock}_position"] == -1, "Sell", None),
                ),
                None,
            )

        # Calculate total return across all stocks
        df["Total_Return"] = df[
            [col for col in df.columns if col.endswith("_strategy")]
        ].mean(axis=1)
        df["Cumulative_Return"] = (1 + df["Total_Return"]).cumprod()
        df["Drawdown"] = (
            df["Cumulative_Return"] / df["Cumulative_Return"].cummax()
        ) - 1

        # Generate outputs
        metrics = get_metrics(df, "momentum")
        figures = plot_results(df, metrics)
        
        return metrics, figures
    
    