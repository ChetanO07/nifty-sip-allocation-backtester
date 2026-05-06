import json
import math
import pandas as pd
from pathlib import Path
import sys

# Import benchmark module
from benchmark import (
    simulate_nifty_benchmark,
    calculate_comparison_columns,
    calculate_drawdown_benefit_summary,
    create_drawdown_comparison_table,
    create_monthly_comparison_table,
)


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "strategy_config.json"


def parse_date_values(values: pd.Series) -> pd.Series:
    text_values = values.astype(str).str.strip()
    iso_date_mask = text_values.str.match(
        r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+.*)?$",
        na=False,
    )
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")

    if iso_date_mask.any():
        parsed.loc[iso_date_mask] = pd.to_datetime(
            text_values.loc[iso_date_mask],
            yearfirst=True,
            errors="coerce",
        )
    if (~iso_date_mask).any():
        parsed.loc[~iso_date_mask] = pd.to_datetime(
            text_values.loc[~iso_date_mask],
            dayfirst=True,
            errors="coerce",
        )

    return parsed


# =========================================================
# CONFIG LOADER
# =========================================================

def load_config(config_path: Path = CONFIG_FILE) -> dict:
    """
    Load strategy configuration from JSON file.
    Validates all required keys are present.
    """

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = [
        "excel_file_name",
        "start_date",
        "monthly_investment",
        "investment_frequency",
        "investment_day_rule",
        "price_column",
        "bond_annual_return",
        "bond_compounding",
        "allocation_rules",
        "bond_shift_rules",
        "trigger_mode",
        "metrics",
        "output_file_name",
    ]

    missing = [k for k in required_keys if k not in config]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")

    # Validate allocation_rules
    for i, rule in enumerate(config["allocation_rules"]):
        for field in ["min_drawdown", "max_drawdown", "equity_allocation", "bond_allocation"]:
            if field not in rule:
                raise KeyError(
                    f"allocation_rules[{i}] is missing required field: '{field}'"
                )

    # Validate bond_shift_rules
    for i, rule in enumerate(config["bond_shift_rules"]):
        for field in ["trigger_drawdown", "bond_shift_percentage", "trigger_once_per_ath_cycle"]:
            if field not in rule:
                raise KeyError(
                    f"bond_shift_rules[{i}] is missing required field: '{field}'"
                )

    # Validate investment_frequency
    valid_frequencies = ["monthly", "weekly", "daily"]
    if config["investment_frequency"] not in valid_frequencies:
        raise ValueError(
            f"investment_frequency must be one of {valid_frequencies}, "
            f"got '{config['investment_frequency']}'"
        )

    # Validate investment_day_rule
    valid_day_rules = ["first_trading_day", "last_trading_day"]
    if config["investment_day_rule"] not in valid_day_rules:
        raise ValueError(
            f"investment_day_rule must be one of {valid_day_rules}, "
            f"got '{config['investment_day_rule']}'"
        )

    # Validate trigger_mode
    valid_trigger_modes = ["highest_only", "all_crossed"]
    if config["trigger_mode"] not in valid_trigger_modes:
        raise ValueError(
            f"trigger_mode must be one of {valid_trigger_modes}, "
            f"got '{config['trigger_mode']}'"
        )

    # Validate bond_compounding
    valid_compounding = ["continuous", "annual", "daily"]
    if config["bond_compounding"] not in valid_compounding:
        raise ValueError(
            f"bond_compounding must be one of {valid_compounding}, "
            f"got '{config['bond_compounding']}'"
        )

    # Sort allocation rules by min_drawdown ascending for correct lookup
    config["allocation_rules"] = sorted(
        config["allocation_rules"], key=lambda r: r["min_drawdown"]
    )

    # Sort bond shift rules by trigger_drawdown ascending
    config["bond_shift_rules"] = sorted(
        config["bond_shift_rules"], key=lambda r: r["trigger_drawdown"]
    )

    print("Config loaded successfully.")
    print(f"  Investment frequency : {config['investment_frequency']}")
    print(f"  Investment day rule  : {config['investment_day_rule']}")
    print(f"  Trigger mode         : {config['trigger_mode']}")
    print(f"  Bond compounding     : {config['bond_compounding']}")
    print(f"  Allocation rules     : {len(config['allocation_rules'])}")
    print(f"  Bond shift rules     : {len(config['bond_shift_rules'])}")

    return config


# =========================================================
# DATA LOADING
# =========================================================

def load_price_data(config: dict) -> pd.DataFrame:
    """
    Load price data from CSV or Excel based on config.
    Filters by start_date and end_date if provided.
    """

    file_path = DATA_DIR / config["excel_file_name"]
    date_col = config.get("date_column", "Date")
    price_col = config["price_column"]
    start_date = config.get("start_date")
    end_date = config.get("end_date")

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip()

    print(f"\nColumns found: {df.columns.tolist()}")

    if date_col not in df.columns:
        raise KeyError(f"Date column '{date_col}' not found in data file.")
    if price_col not in df.columns:
        raise KeyError(f"Price column '{price_col}' not found in data file.")

    df[date_col] = parse_date_values(df[date_col])

    df = df.dropna(subset=[date_col, price_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    if start_date is not None:
        df = df[df[date_col] >= pd.to_datetime(start_date)].reset_index(drop=True)

    if end_date is not None:
        df = df[df[date_col] <= pd.to_datetime(end_date)].reset_index(drop=True)

    return df


def load_price_data_from_dataframe(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Normalize uploaded user data into the same shape used by the strategy.

    The uploaded file must contain at least Date and the configured price column.
    """

    date_col = config.get("date_column", "Date")
    price_col = config["price_column"]
    start_date = config.get("start_date")
    end_date = config.get("end_date")

    df = df.copy()
    df.columns = df.columns.str.strip()

    print(f"\nUploaded columns found: {df.columns.tolist()}")

    if date_col not in df.columns:
        raise KeyError(
            f"Uploaded dataset is missing required column '{date_col}'."
        )
    if price_col not in df.columns:
        raise KeyError(
            f"Uploaded dataset is missing required column '{price_col}'."
        )

    df[date_col] = parse_date_values(df[date_col])
    df = df.dropna(subset=[date_col, price_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    if start_date is not None:
        df = df[df[date_col] >= pd.to_datetime(start_date)].reset_index(drop=True)

    if end_date is not None:
        df = df[df[date_col] <= pd.to_datetime(end_date)].reset_index(drop=True)

    if df.empty:
        raise ValueError("Uploaded dataset does not contain any usable rows after validation.")

    return df


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def mark_investment_days(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Mark investment days based on investment_frequency and investment_day_rule.

    Supports:
        monthly  + first_trading_day / last_trading_day
        weekly   + first_trading_day / last_trading_day
        daily    (every trading day is an investment day)
    """

    df = df.copy()
    date_col = config.get("date_column", "Date")
    frequency = config["investment_frequency"]
    day_rule = config["investment_day_rule"]

    if frequency == "daily":
        df["Is_Investment_Day"] = True
        return df

    if frequency == "monthly":
        df["Period"] = df[date_col].dt.to_period("M")
    elif frequency == "weekly":
        # ISO week: year + week number
        df["Period"] = (
            df[date_col].dt.isocalendar().year.astype(str)
            + "-W"
            + df[date_col].dt.isocalendar().week.astype(str).str.zfill(2)
        )
    else:
        raise ValueError(f"Unsupported investment_frequency: {frequency}")

    if day_rule == "first_trading_day":
        df["Is_Investment_Day"] = df["Period"] != df["Period"].shift(1)
    elif day_rule == "last_trading_day":
        df["Is_Investment_Day"] = df["Period"] != df["Period"].shift(-1)
    else:
        raise ValueError(f"Unsupported investment_day_rule: {day_rule}")

    # Drop helper column
    df = df.drop(columns=["Period"])

    return df


def get_allocation(drawdown_decimal: float, allocation_rules: list) -> tuple:
    """
    Look up equity/bond allocation from config-driven allocation_rules.

    Rules are sorted by min_drawdown ascending.
    We find the last rule where min_drawdown <= drawdown_decimal < max_drawdown.
    If no rule matches, fall back to the last rule (highest drawdown bucket).
    """

    matched_rule = None

    for rule in allocation_rules:
        if rule["min_drawdown"] <= drawdown_decimal < rule["max_drawdown"]:
            matched_rule = rule
            break

    # If drawdown equals or exceeds the max of the last rule, use the last rule
    if matched_rule is None:
        matched_rule = allocation_rules[-1]

    return matched_rule["equity_allocation"], matched_rule["bond_allocation"]


def apply_bond_growth(
    bond_value: float,
    previous_date,
    current_date,
    annual_return: float,
    compounding: str = "continuous",
) -> float:
    """
    Apply bond growth between previous trading date and current trading date.

    Supports:
        continuous : bond_value * e^(r * days/365)
        annual     : bond_value * (1 + r) ^ (days/365)
        daily      : bond_value * (1 + r/365) ^ days
    """

    if previous_date is None:
        return bond_value

    days = (current_date - previous_date).days

    if days <= 0:
        return bond_value

    if compounding == "continuous":
        return bond_value * math.exp(annual_return * days / 365)
    elif compounding == "annual":
        return bond_value * ((1 + annual_return) ** (days / 365))
    elif compounding == "daily":
        return bond_value * ((1 + annual_return / 365) ** days)
    else:
        # Default to annual compounding
        return bond_value * ((1 + annual_return) ** (days / 365))


# =========================================================
# MAIN STRATEGY SIMULATION
# =========================================================

def simulate_asset_allocation(df: pd.DataFrame, config: dict):
    """
    Simulate the equity + bond asset allocation strategy.
    All logic is driven by the config dictionary.
    """

    date_col = config.get("date_column", "Date")
    price_col = config["price_column"]
    investment_amount = config["monthly_investment"]
    bond_annual_return = config["bond_annual_return"]
    bond_compounding = config["bond_compounding"]
    allocation_rules = config["allocation_rules"]
    bond_shift_rules = config["bond_shift_rules"]
    trigger_mode = config["trigger_mode"]

    equity_units = 0.0
    bond_value = 0.0
    total_invested = 0.0

    ath_price = None
    previous_date = None

    portfolio_peak = 0.0

    # Track triggered drawdown levels (by trigger_drawdown value)
    triggered_levels = set()

    daily_records = []
    action_records = []

    for _, row in df.iterrows():
        current_date = row[date_col]
        price = float(row[price_col])
        is_investment_day = bool(row["Is_Investment_Day"])

        equity_investment_today = 0.0
        bond_investment_today = 0.0
        bond_shifted_today = 0.0
        units_bought_today = 0.0

        # -------------------------------------------------
        # 1. Grow bond portfolio
        # -------------------------------------------------

        bond_value = apply_bond_growth(
            bond_value=bond_value,
            previous_date=previous_date,
            current_date=current_date,
            annual_return=bond_annual_return,
            compounding=bond_compounding,
        )

        # -------------------------------------------------
        # 2. Update ATH and reset triggers if new ATH
        # -------------------------------------------------

        if ath_price is None:
            ath_price = price

        elif price >= ath_price:
            ath_price = price

            if len(triggered_levels) > 0:
                action_records.append({
                    "Date": current_date,
                    "Price": price,
                    "Action": "Price reached new ATH. Reset all drawdown triggers.",
                    "Bond Shifted": 0.0,
                    "Bond Value After Action": bond_value,
                    "Equity Units After Action": equity_units,
                })

            triggered_levels.clear()

        # -------------------------------------------------
        # 3. Calculate drawdown from ATH
        # -------------------------------------------------

        drawdown_decimal = max(0.0, (ath_price - price) / ath_price)
        drawdown_percent = drawdown_decimal * 100

        # -------------------------------------------------
        # 4. Bond shifting based on drawdown triggers
        # -------------------------------------------------

        newly_reached = []

        for rule in bond_shift_rules:
            level = rule["trigger_drawdown"]
            once_per_cycle = rule["trigger_once_per_ath_cycle"]

            if drawdown_decimal >= level:
                if once_per_cycle and level in triggered_levels:
                    continue  # Already triggered in this ATH cycle
                newly_reached.append(rule)

        if len(newly_reached) > 0:
            if trigger_mode == "highest_only":
                # Use highest newly reached level only
                trigger_rule = max(newly_reached, key=lambda r: r["trigger_drawdown"])
                rules_to_apply = [trigger_rule]
            elif trigger_mode == "all_crossed":
                # Apply all newly crossed levels individually
                rules_to_apply = sorted(newly_reached, key=lambda r: r["trigger_drawdown"])
            else:
                rules_to_apply = []

            for rule in rules_to_apply:
                level = rule["trigger_drawdown"]
                shift_pct = rule["bond_shift_percentage"]

                shift_amount = bond_value * shift_pct
                units_from_shift = shift_amount / price if price > 0 else 0.0

                equity_units += units_from_shift
                bond_value -= shift_amount
                bond_shifted_today += shift_amount

                action_text = (
                    f"Drawdown reached {level * 100:.0f}%. "
                    f"Shifted {shift_pct * 100:.0f}% of bond portfolio to equity."
                )

                action_records.append({
                    "Date": current_date,
                    "Price": price,
                    "Action": action_text,
                    "Drawdown %": drawdown_percent,
                    "Bond Shifted": shift_amount,
                    "Units Bought From Shift": units_from_shift,
                    "Bond Value After Action": bond_value,
                    "Equity Units After Action": equity_units,
                })

            # Mark triggered levels
            if trigger_mode == "highest_only":
                highest_level = max(r["trigger_drawdown"] for r in rules_to_apply)
                for rule in bond_shift_rules:
                    if rule["trigger_drawdown"] <= highest_level:
                        triggered_levels.add(rule["trigger_drawdown"])
            elif trigger_mode == "all_crossed":
                for rule in rules_to_apply:
                    triggered_levels.add(rule["trigger_drawdown"])

        # -------------------------------------------------
        # 5. Investment on investment day
        # -------------------------------------------------

        if is_investment_day:
            equity_alloc, bond_alloc = get_allocation(drawdown_decimal, allocation_rules)

            equity_investment_today = investment_amount * equity_alloc
            bond_investment_today = investment_amount * bond_alloc

            units_bought_today = equity_investment_today / price if price > 0 else 0.0

            equity_units += units_bought_today
            bond_value += bond_investment_today
            total_invested += investment_amount

            action_records.append({
                "Date": current_date,
                "Price": price,
                "Action": f"Investment ({config['investment_frequency']})",
                "Drawdown %": drawdown_percent,
                "Equity Allocation %": equity_alloc * 100,
                "Bond Allocation %": bond_alloc * 100,
                "Equity Investment": equity_investment_today,
                "Bond Investment": bond_investment_today,
                "Units Bought": units_bought_today,
                "Total Invested After Action": total_invested,
                "Bond Value After Action": bond_value,
                "Equity Units After Action": equity_units,
            })

        # -------------------------------------------------
        # 6. Calculate daily portfolio value
        # -------------------------------------------------

        equity_value = equity_units * price
        total_asset_value = equity_value + bond_value

        portfolio_peak = max(portfolio_peak, total_asset_value)

        if portfolio_peak > 0:
            portfolio_drawdown_percent = (
                (total_asset_value - portfolio_peak) / portfolio_peak
            ) * 100
        else:
            portfolio_drawdown_percent = 0.0

        if total_invested > 0:
            roi_percent = ((total_asset_value - total_invested) / total_invested) * 100
        else:
            roi_percent = 0.0

        daily_records.append({
            "Date": current_date,
            "Price": price,
            "ATH": ath_price,
            "Drawdown %": -drawdown_percent,

            "Is Investment Day": is_investment_day,

            "Equity Investment Today": equity_investment_today,
            "Bond Investment Today": bond_investment_today,
            "Bond Shifted Today": bond_shifted_today,

            "Equity Units": equity_units,
            "Equity Value": equity_value,
            "Bond Value": bond_value,
            "Total Asset Value": total_asset_value,

            "Total Invested": total_invested,
            "Profit": total_asset_value - total_invested,
            "ROI %": roi_percent,

            "Portfolio Peak": portfolio_peak,
            "Portfolio Drawdown %": portfolio_drawdown_percent,

            "Triggered Levels": ", ".join(
                [f"{x * 100:.0f}%" for x in sorted(triggered_levels)]
            ),
        })

        previous_date = current_date

    daily_df = pd.DataFrame(daily_records)
    actions_df = pd.DataFrame(action_records)

    return daily_df, actions_df


# =========================================================
# SUMMARY
# =========================================================

def calculate_summary(daily_df: pd.DataFrame, config: dict) -> dict:
    """
    Calculate final strategy summary.
    Includes optional metrics based on config.
    Also includes benchmark comparison metrics.
    """

    last_row = daily_df.iloc[-1]
    first_row = daily_df.iloc[0]

    total_invested = last_row["Total Invested"]
    final_value = last_row["Total Asset Value"]
    profit = final_value - total_invested

    metrics = config.get("metrics", {})

    summary = {
        "Start Date": first_row["Date"],
        "End Date": last_row["Date"],
        "Investment Amount": config["monthly_investment"],
        "Investment Frequency": config["investment_frequency"],
        "Investment Day Rule": config["investment_day_rule"],
        "Bond Annual Return %": config["bond_annual_return"] * 100,
        "Bond Compounding": config["bond_compounding"],
        "Trigger Mode": config["trigger_mode"],
        "Total Invested": total_invested,
    }

    if metrics.get("show_equity_bond_split", True):
        summary["Final Equity Value"] = last_row["Equity Value"]
        summary["Final Bond Value"] = last_row["Bond Value"]

    summary["Final Total Asset Value"] = final_value
    summary["Profit"] = profit

    if metrics.get("show_roi", True):
        roi_percent = (profit / total_invested) * 100 if total_invested > 0 else 0.0
        summary["ROI %"] = roi_percent

    if metrics.get("show_cagr", True):
        start_date = first_row["Date"]
        end_date = last_row["Date"]
        years = (end_date - start_date).days / 365.25
        if years > 0 and total_invested > 0:
            # CAGR approximation using final value / total invested
            # (not exact for SIP but gives a rough sense)
            cagr = ((final_value / total_invested) ** (1 / years) - 1) * 100
            summary["Approx CAGR %"] = cagr

    if metrics.get("show_max_drawdown", True):
        max_drawdown_percent = daily_df["Portfolio Drawdown %"].min()
        summary["Max Portfolio Drawdown %"] = max_drawdown_percent

    summary["Final Price"] = last_row["Price"]
    summary["Final ATH"] = last_row["ATH"]
    summary["Final Drawdown %"] = last_row["Drawdown %"]

    # Add benchmark comparison metrics
    if "Benchmark NIFTY Value" in daily_df.columns:
        benefit_summary = calculate_drawdown_benefit_summary(daily_df)
        summary.update(benefit_summary)

    return summary


# =========================================================
# SAVE OUTPUTS
# =========================================================

def save_outputs(
    daily_df: pd.DataFrame,
    actions_df: pd.DataFrame,
    summary: dict,
    config: dict,
    drawdown_comparison_df: pd.DataFrame = None,
    monthly_comparison_df: pd.DataFrame = None,
):
    """
    Save all outputs to Excel with multiple sheets:
        - Summary
        - Daily Portfolio
        - Actions
        - Drawdown Comparison (if benchmark exists)
        - Monthly Comparison (if benchmark exists)
        - Config Used
    """

    output_file = OUTPUT_DIR / config["output_file_name"]

    summary_df = pd.DataFrame([summary])

    # Flatten config into a readable key-value DataFrame for the Config Used sheet
    config_records = []
    for key, value in config.items():
        if isinstance(value, (list, dict)):
            config_records.append({"Parameter": key, "Value": json.dumps(value, indent=2)})
        else:
            config_records.append({"Parameter": key, "Value": value})
    config_df = pd.DataFrame(config_records)

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            daily_df.to_excel(writer, sheet_name="Daily Portfolio", index=False)
            actions_df.to_excel(writer, sheet_name="Actions", index=False)
            
            # Add benchmark comparison sheets if available
            if drawdown_comparison_df is not None:
                drawdown_comparison_df.to_excel(writer, sheet_name="Drawdown Comparison", index=False)
            
            if monthly_comparison_df is not None:
                monthly_comparison_df.to_excel(writer, sheet_name="Monthly Comparison", index=False)
            
            config_df.to_excel(writer, sheet_name="Config Used", index=False)

        print(f"\nOutput saved to: {output_file}")
    except Exception as e:
        print(f"Could not save to Excel: {e}")

        csv_summary = OUTPUT_DIR / "asset_allocation_summary.csv"
        csv_daily = OUTPUT_DIR / "asset_allocation_daily.csv"
        csv_actions = OUTPUT_DIR / "asset_allocation_actions.csv"
        csv_config = OUTPUT_DIR / "asset_allocation_config_used.csv"

        summary_df.to_csv(csv_summary, index=False)
        daily_df.to_csv(csv_daily, index=False)
        actions_df.to_csv(csv_actions, index=False)
        config_df.to_csv(csv_config, index=False)

        if drawdown_comparison_df is not None:
            csv_dd_comp = OUTPUT_DIR / "asset_allocation_drawdown_comparison.csv"
            drawdown_comparison_df.to_csv(csv_dd_comp, index=False)

        if monthly_comparison_df is not None:
            csv_monthly = OUTPUT_DIR / "asset_allocation_monthly_comparison.csv"
            monthly_comparison_df.to_csv(csv_monthly, index=False)

        print(f"CSV files saved instead: {csv_summary}, {csv_daily}, {csv_actions}, {csv_config}")



# =========================================================
# MAIN
# =========================================================

def main():
    print("=" * 60)
    print("DYNAMIC ASSET ALLOCATION STRATEGY")
    print("=" * 60)

    # 1. Load config
    config = load_config()

    # 2. Load data
    print("\nLoading price data...")
    df = load_price_data(config)

    # 3. Mark investment days
    df = mark_investment_days(df, config)

    date_col = config.get("date_column", "Date")
    print(f"\nData loaded successfully.")
    print(f"  Start Date       : {df[date_col].min().date()}")
    print(f"  End Date         : {df[date_col].max().date()}")
    print(f"  Total trading days: {len(df)}")

    investment_days = df["Is_Investment_Day"].sum()
    print(f"  Investment days  : {investment_days}")

    # 4. Run simulation
    print("\nRunning asset allocation strategy...")
    daily_df, actions_df = simulate_asset_allocation(df, config)

    # 5. Create NIFTY benchmark portfolio
    print("\nCreating NIFTY-only benchmark portfolio...")
    daily_df = simulate_nifty_benchmark(daily_df, config)
    
    # 6. Add comparison columns
    print("Calculating comparison metrics...")
    daily_df = calculate_comparison_columns(daily_df)

    # 7. Create comparison tables
    print("Creating comparison tables...")
    drawdown_comparison_df = create_drawdown_comparison_table(daily_df)
    monthly_comparison_df = create_monthly_comparison_table(daily_df, date_col=date_col)

    # 8. Calculate summary
    summary = calculate_summary(daily_df, config)

    # 9. Print summary
    print("\n" + "=" * 60)
    print("STRATEGY SUMMARY")
    print("=" * 60)

    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:,.2f}")
        else:
            print(f"  {key}: {value}")

    # 10. Save outputs
    save_outputs(
        daily_df,
        actions_df,
        summary,
        config,
        drawdown_comparison_df=drawdown_comparison_df,
        monthly_comparison_df=monthly_comparison_df,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
