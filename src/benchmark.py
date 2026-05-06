"""
Benchmark comparison module for the Dynamic Asset Allocation Strategy.

This module creates a NIFTY-only benchmark portfolio that runs in parallel
with the strategy portfolio to compare drawdown protection benefits.
"""

import pandas as pd
import numpy as np


def simulate_nifty_benchmark(daily_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Create a NIFTY-only benchmark portfolio.
    
    Uses the same investment days and amounts as the strategy,
    but invests 100% into NIFTY equity.
    
    Args:
        daily_df: Daily portfolio data from strategy (must have Is_Investment_Day column)
        config: Strategy config dict
    
    Returns:
        daily_df with added benchmark columns
    """
    
    date_col = config.get("date_column", "Date")
    price_col = config["price_column"]
    
    daily_df = daily_df.copy()
    
    benchmark_units = 0.0
    benchmark_total_invested = 0.0
    benchmark_peak_value = 0.0
    
    benchmark_units_list = []
    benchmark_values_list = []
    benchmark_invested_list = []
    benchmark_peak_list = []
    benchmark_profit_list = []
    benchmark_roi_list = []
    benchmark_drawdown_list = []
    
    for idx, row in daily_df.iterrows():
        # The allocation engine uses a normalized 'Price' column.
        price = row["Price"] if "Price" in row else row.get(price_col, 0.0)
        is_investment_day = row.get("Is Investment Day", row.get("Is_Investment_Day", False))
        
        # Get investment amount: either from direct column or sum of equity + bond investments
        if "Investment Amount Today" in daily_df.columns:
            investment_today = row["Investment Amount Today"]
        else:
            investment_today = row.get("Equity Investment Today", 0.0) + row.get("Bond Investment Today", 0.0)
        
        # On investment day, buy 100% into NIFTY
        if is_investment_day:
            units_bought = investment_today / price if price > 0 else 0.0
            benchmark_units += units_bought
            benchmark_total_invested += investment_today
        
        # Calculate benchmark daily values
        benchmark_value = benchmark_units * price
        benchmark_peak_value = max(benchmark_peak_value, benchmark_value)
        
        # Calculate benchmark profit and ROI
        benchmark_profit = benchmark_value - benchmark_total_invested
        benchmark_roi = (benchmark_profit / benchmark_total_invested * 100) if benchmark_total_invested > 0 else 0.0
        
        # Calculate benchmark drawdown
        if benchmark_peak_value > 0:
            benchmark_dd_pct = ((benchmark_value - benchmark_peak_value) / benchmark_peak_value) * 100
        else:
            benchmark_dd_pct = 0.0
        
        # Store values
        benchmark_units_list.append(benchmark_units)
        benchmark_values_list.append(benchmark_value)
        benchmark_invested_list.append(benchmark_total_invested)
        benchmark_peak_list.append(benchmark_peak_value)
        benchmark_profit_list.append(benchmark_profit)
        benchmark_roi_list.append(benchmark_roi)
        benchmark_drawdown_list.append(benchmark_dd_pct)
    
    # Add benchmark columns to dataframe
    daily_df["Benchmark NIFTY Units"] = benchmark_units_list
    daily_df["Benchmark NIFTY Value"] = benchmark_values_list
    daily_df["Benchmark Total Invested"] = benchmark_invested_list
    daily_df["Benchmark Peak Value"] = benchmark_peak_list
    daily_df["Benchmark Profit"] = benchmark_profit_list
    daily_df["Benchmark ROI %"] = benchmark_roi_list
    daily_df["Benchmark Drawdown %"] = benchmark_drawdown_list
    
    return daily_df


def calculate_comparison_columns(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add comparison columns between strategy and benchmark.
    
    Compares:
    - Total asset values
    - Drawdown differences
    - ROI differences
    - Drawdown benefits
    """
    
    daily_df = daily_df.copy()
    
    # Comparison metrics
    strategy_value = daily_df["Total Asset Value"]
    benchmark_value = daily_df["Benchmark NIFTY Value"]
    
    strategy_dd = daily_df["Portfolio Drawdown %"]
    benchmark_dd = daily_df["Benchmark Drawdown %"]
    
    strategy_roi = daily_df["ROI %"]
    benchmark_roi = daily_df["Benchmark ROI %"]
    
    # Value difference
    value_diff = strategy_value - benchmark_value
    value_diff_pct = pd.Series(
        np.where(
            benchmark_value != 0,
            value_diff / benchmark_value * 100,
            0.0,
        ),
        index=daily_df.index,
    )
    
    # Drawdown benefit (positive = strategy had smaller drawdown)
    # Formula: abs(benchmark_dd) - abs(strategy_dd)
    drawdown_benefit = np.abs(benchmark_dd) - np.abs(strategy_dd)
    
    # ROI difference
    roi_diff = strategy_roi - benchmark_roi
    
    # Add to dataframe
    daily_df["Strategy Total Asset Value"] = strategy_value
    daily_df["Benchmark Total Asset Value"] = benchmark_value
    daily_df["Strategy Portfolio Drawdown %"] = strategy_dd
    daily_df["Benchmark Portfolio Drawdown %"] = benchmark_dd
    daily_df["Drawdown Benefit %"] = drawdown_benefit
    daily_df["Value Difference"] = value_diff
    daily_df["Value Difference %"] = value_diff_pct
    daily_df["ROI Difference %"] = roi_diff
    
    return daily_df


def calculate_drawdown_benefit_summary(daily_df: pd.DataFrame) -> dict:
    """
    Calculate comprehensive drawdown benefit summary metrics.
    
    Includes:
    - Max drawdown benefit
    - Average drawdown benefit during stress periods
    - Capital protection ratio
    - Worst case analysis
    """
    
    # Extract key values from last row for final metrics
    last_row = daily_df.iloc[-1]
    first_row = daily_df.iloc[0]
    
    strategy_max_dd = daily_df["Strategy Portfolio Drawdown %"].min()
    benchmark_max_dd = daily_df["Benchmark Portfolio Drawdown %"].min()
    
    strategy_final_value = last_row["Total Asset Value"]
    benchmark_final_value = last_row["Benchmark NIFTY Value"]
    
    strategy_final_roi = last_row["ROI %"]
    benchmark_final_roi = last_row["Benchmark ROI %"]
    
    strategy_total_invested = last_row["Total Invested"]
    benchmark_total_invested = last_row["Benchmark Total Invested"]
    
    strategy_profit = strategy_final_value - strategy_total_invested
    benchmark_profit = benchmark_final_value - benchmark_total_invested
    
    # Calculate CAGR if we have multiple years
    days_elapsed = (last_row["Date"] - first_row["Date"]).days
    years = days_elapsed / 365.25
    
    if years > 0 and strategy_total_invested > 0:
        strategy_cagr = ((strategy_final_value / strategy_total_invested) ** (1 / years) - 1) * 100
    else:
        strategy_cagr = 0.0
    
    if years > 0 and benchmark_total_invested > 0:
        benchmark_cagr = ((benchmark_final_value / benchmark_total_invested) ** (1 / years) - 1) * 100
    else:
        benchmark_cagr = 0.0
    
    # Max drawdown benefit
    max_dd_benefit = abs(benchmark_max_dd) - abs(strategy_max_dd)
    
    # Average drawdown benefit during stress (benchmark drawdown < 0)
    stress_mask = daily_df["Benchmark Portfolio Drawdown %"] < 0
    avg_dd_benefit = daily_df.loc[stress_mask, "Drawdown Benefit %"].mean() if stress_mask.any() else 0.0
    
    # Average drawdown benefit during -10% stress
    stress_10_mask = daily_df["Benchmark Portfolio Drawdown %"] <= -10
    avg_dd_benefit_10 = daily_df.loc[stress_10_mask, "Drawdown Benefit %"].mean() if stress_10_mask.any() else 0.0
    
    # Average drawdown benefit during -20% stress
    stress_20_mask = daily_df["Benchmark Portfolio Drawdown %"] <= -20
    avg_dd_benefit_20 = daily_df.loc[stress_20_mask, "Drawdown Benefit %"].mean() if stress_20_mask.any() else 0.0
    
    # Average drawdown benefit during -30% stress
    stress_30_mask = daily_df["Benchmark Portfolio Drawdown %"] <= -30
    avg_dd_benefit_30 = daily_df.loc[stress_30_mask, "Drawdown Benefit %"].mean() if stress_30_mask.any() else 0.0
    
    # Worst strategy drawdown when benchmark DD >= 30%
    severe_stress_mask = daily_df["Benchmark Portfolio Drawdown %"] <= -30
    if severe_stress_mask.any():
        worst_strategy_dd_severe = daily_df.loc[severe_stress_mask, "Strategy Portfolio Drawdown %"].min()
        avg_strategy_dd_severe = daily_df.loc[severe_stress_mask, "Strategy Portfolio Drawdown %"].mean()
    else:
        worst_strategy_dd_severe = 0.0
        avg_strategy_dd_severe = 0.0
    
    # Capital protection ratio
    if abs(benchmark_max_dd) > 0:
        capital_protection_ratio = abs(strategy_max_dd) / abs(benchmark_max_dd)
    else:
        capital_protection_ratio = 0.0
    
    # Drawdown reduction percentage
    drawdown_reduction_pct = (1 - capital_protection_ratio) * 100
    
    # Days with lower drawdown
    lower_dd_mask = daily_df["Strategy Portfolio Drawdown %"] > daily_df["Benchmark Portfolio Drawdown %"]
    days_lower_dd = lower_dd_mask.sum()
    pct_days_lower_dd = (days_lower_dd / len(daily_df) * 100) if len(daily_df) > 0 else 0.0
    
    # Days with higher value
    higher_value_mask = daily_df["Total Asset Value"] > daily_df["Benchmark NIFTY Value"]
    days_higher_value = higher_value_mask.sum()
    pct_days_higher_value = (days_higher_value / len(daily_df) * 100) if len(daily_df) > 0 else 0.0
    
    # Final extra value vs benchmark
    final_value_diff = strategy_final_value - benchmark_final_value
    final_value_diff_pct = (final_value_diff / benchmark_final_value * 100) if benchmark_final_value > 0 else 0.0
    
    summary = {
        # Benchmark metrics
        "Benchmark Final Value": benchmark_final_value,
        "Benchmark Total Invested": benchmark_total_invested,
        "Benchmark Profit": benchmark_profit,
        "Benchmark ROI %": benchmark_final_roi,
        "Benchmark CAGR %": benchmark_cagr,
        "Benchmark Max Drawdown %": benchmark_max_dd,
        
        # Strategy metrics
        "Strategy Final Value": strategy_final_value,
        "Strategy Total Invested": strategy_total_invested,
        "Strategy Profit": strategy_profit,
        "Strategy ROI %": strategy_final_roi,
        "Strategy CAGR %": strategy_cagr,
        "Strategy Max Drawdown %": strategy_max_dd,
        
        # Drawdown benefit metrics
        "Max Drawdown Benefit %": max_dd_benefit,
        "Average Drawdown Benefit %": avg_dd_benefit,
        "Average Drawdown Benefit During 10% Stress %": avg_dd_benefit_10,
        "Average Drawdown Benefit During 20% Stress %": avg_dd_benefit_20,
        "Average Drawdown Benefit During 30% Stress %": avg_dd_benefit_30,
        "Worst Strategy Drawdown When Benchmark DD >= 30%": worst_strategy_dd_severe,
        "Average Strategy Drawdown When Benchmark DD >= 30%": avg_strategy_dd_severe,
        "Capital Protection Ratio": capital_protection_ratio,
        "Drawdown Reduction %": drawdown_reduction_pct,
        
        # Action metrics
        "Days Strategy Had Lower Drawdown Than Benchmark": days_lower_dd,
        "% Days Strategy Had Lower Drawdown Than Benchmark": pct_days_lower_dd,
        "Days Strategy Value Was Higher Than Benchmark": days_higher_value,
        "% Days Strategy Value Was Higher Than Benchmark": pct_days_higher_value,
        "Final Extra Value vs Benchmark": final_value_diff,
        "Final Extra Value % vs Benchmark": final_value_diff_pct,
    }
    
    return summary


def create_drawdown_comparison_table(daily_df: pd.DataFrame, thresholds=None) -> pd.DataFrame:
    """
    Create a comparison table for different drawdown thresholds.
    
    For each threshold (-10%, -20%, -30%, -40%, -50%):
    - Count days below threshold
    - Calculate average drawdowns
    - Calculate value metrics
    """
    
    if thresholds is None:
        thresholds = [10, 20, 30, 40, 50]
    
    records = []
    
    for threshold in thresholds:
        threshold_neg = -threshold
        
        # Filter days where benchmark drawdown is at or below threshold
        mask = daily_df["Benchmark Portfolio Drawdown %"] <= threshold_neg
        
        if mask.any():
            filtered_df = daily_df[mask]
            
            num_days = len(filtered_df)
            avg_benchmark_dd = filtered_df["Benchmark Portfolio Drawdown %"].mean()
            avg_strategy_dd = filtered_df["Strategy Portfolio Drawdown %"].mean()
            avg_dd_benefit = filtered_df["Drawdown Benefit %"].mean()
            
            worst_benchmark_dd = filtered_df["Benchmark Portfolio Drawdown %"].min()
            worst_strategy_dd = filtered_df["Strategy Portfolio Drawdown %"].min()
            
            best_dd_benefit = filtered_df["Drawdown Benefit %"].max()
            worst_dd_benefit = filtered_df["Drawdown Benefit %"].min()
            
            avg_strategy_value = filtered_df["Total Asset Value"].mean()
            avg_benchmark_value = filtered_df["Benchmark NIFTY Value"].mean()
            avg_value_diff = filtered_df["Value Difference"].mean()
            avg_value_diff_pct = filtered_df["Value Difference %"].mean()
        else:
            num_days = 0
            avg_benchmark_dd = np.nan
            avg_strategy_dd = np.nan
            avg_dd_benefit = np.nan
            worst_benchmark_dd = np.nan
            worst_strategy_dd = np.nan
            best_dd_benefit = np.nan
            worst_dd_benefit = np.nan
            avg_strategy_value = np.nan
            avg_benchmark_value = np.nan
            avg_value_diff = np.nan
            avg_value_diff_pct = np.nan
        
        records.append({
            "Threshold %": -threshold,
            "Days Below Threshold": num_days,
            "Avg Benchmark Drawdown %": avg_benchmark_dd,
            "Avg Strategy Drawdown %": avg_strategy_dd,
            "Avg Drawdown Benefit %": avg_dd_benefit,
            "Worst Benchmark Drawdown %": worst_benchmark_dd,
            "Worst Strategy Drawdown %": worst_strategy_dd,
            "Best Drawdown Benefit %": best_dd_benefit,
            "Worst Drawdown Benefit %": worst_dd_benefit,
            "Avg Strategy Value": avg_strategy_value,
            "Avg Benchmark Value": avg_benchmark_value,
            "Avg Value Difference": avg_value_diff,
            "Avg Value Difference %": avg_value_diff_pct,
        })
    
    return pd.DataFrame(records)


def create_monthly_comparison_table(daily_df: pd.DataFrame, date_col="Date") -> pd.DataFrame:
    """
    Create a monthly comparison table showing month-end metrics.
    
    For each month-end:
    - Portfolio values
    - ROI comparison
    - Drawdown comparison
    - Value difference
    """
    
    daily_df = daily_df.copy()
    daily_df[date_col] = pd.to_datetime(daily_df[date_col])
    
    # Group by month-end
    monthly_df = daily_df.groupby(daily_df[date_col].dt.to_period("M")).last().reset_index()
    
    records = []
    for _, row in monthly_df.iterrows():
        better = "Strategy" if row["Total Asset Value"] > row["Benchmark NIFTY Value"] else "Benchmark"
        
        records.append({
            "Date": row[date_col],
            "Strategy Total Asset Value": row["Total Asset Value"],
            "Benchmark Total Asset Value": row["Benchmark NIFTY Value"],
            "Strategy ROI %": row["ROI %"],
            "Benchmark ROI %": row["Benchmark ROI %"],
            "Strategy Portfolio Drawdown %": row["Strategy Portfolio Drawdown %"],
            "Benchmark Portfolio Drawdown %": row["Benchmark Portfolio Drawdown %"],
            "Drawdown Benefit %": row["Drawdown Benefit %"],
            "Value Difference": row["Value Difference"],
            "Value Difference %": row["Value Difference %"],
            "Better Portfolio": better,
        })
    
    return pd.DataFrame(records)
