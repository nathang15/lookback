from pandas import DataFrame
from utils.metrics import get_metrics

class Traditional:

    def __init__(self):
        pass

    def __str__(self):
        return f"Experiment with traditional simple strategies."
    
    @staticmethod
    # long strategy
    def long(df: DataFrame = None) -> None:
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