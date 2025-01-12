from typing import List
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .metrics import get_metrics

def plot_results(df: pd.DataFrame, stats: dict) -> List[Figure]:
    # Ensure 'Date' column exists
    if "Date" not in df.columns:
        df["Date"] = pd.to_datetime(df.index)

    figures = []  # List to store individual figures
    plt.style.use("seaborn-v0_8-whitegrid")

    # Create main strategy figure
    fig_strategy = plt.figure(figsize=(16, 6))
    ax = fig_strategy.add_subplot(111)
    
    ax.fill_between(
        df["Date"],
        df["Cumulative_Return"] - 1,
        0,
        alpha=0.3,
        color="#1e90ff",
        label="Cumulative Return",
    )
    ax.plot(df["Date"], df["Cumulative_Return"] - 1, color="#1e90ff", linewidth=2)
    ax.set_title("Strategy Cumulative Return", fontsize=14)
    ax.set_ylabel("Return", fontsize=12)
    ax.set_xlabel("Date", fontsize=12)
    ax.legend(loc="upper left")

    # Add stats text box to strategy figure
    stats_text = f"""
    Strategy: {stats['strategy']}
    Return: {stats['Return [%]']:.2f}%
    Sharpe Ratio: {stats['Sharpe Ratio']:.2f}
    Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%
    """
    fig_strategy.text(
        0.02,
        0.02,
        stats_text,
        fontsize=10,
        va="bottom",
        ha="left",
        bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
    )

    plt.tight_layout()
    figures.append((fig_strategy, "Strategy Overview"))

    # Create individual figures for each stock
    stock_columns = [
        col for col in df.columns if col.endswith("_return") and col != "Total_Return"
    ]

    for column in stock_columns:
        stock_name = column.split("_")[0]
        fig_stock = plt.figure(figsize=(16, 6))
        ax = fig_stock.add_subplot(111)

        # Calculate cumulative return for the stock
        cumulative_return = (1 + df[column]).cumprod() - 1

        ax.plot(
            df["Date"],
            cumulative_return,
            label=f"{stock_name} Cumulative",
            linewidth=1.5,
        )

        # Plot buy and sell signals
        signal_column = f"{stock_name}_signal"
        if signal_column in df.columns:
            buy_mask = df[signal_column] == "Buy"
            sell_mask = df[signal_column] == "Sell"

            ax.scatter(
                df.loc[buy_mask, "Date"],
                cumulative_return.loc[buy_mask],
                marker="^",
                color="g",
                s=100,
                label="Buy",
            )
            ax.scatter(
                df.loc[sell_mask, "Date"],
                cumulative_return.loc[sell_mask],
                marker="v",
                color="r",
                s=100,
                label="Sell",
            )

        ax.set_title(f"{stock_name} Cumulative Return", fontsize=14)
        ax.set_ylabel("Return", fontsize=12)
        ax.set_xlabel("Date", fontsize=12)
        ax.legend(loc="upper left")

        plt.tight_layout()
        figures.append((fig_stock, f"{stock_name} Performance"))

    return figures