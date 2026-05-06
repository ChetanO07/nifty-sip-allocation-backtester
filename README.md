# NIFTY Strategy Suite

A Flask-based NIFTY investment strategy dashboard for SIP backtesting, dynamic asset allocation, portfolio growth analysis, drawdown comparison, and investor-friendly reporting.

## Features

- SIP wealth strategy backtesting across NIFTY market-cap and sector indices.
- Dynamic asset allocation between equity and bonds based on market drawdown.
- Investor-friendly reports with charts, summary cards, plain-English explanations, and risk notes.
- CSV and Excel dataset upload support.
- Configurable investment amount, frequency, bond return, allocation rules, and shift rules.

## Tech Stack

- Python
- Flask
- Pandas
- Matplotlib
- OpenPyXL

## Run Locally

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
flask --app src.main run --host 127.0.0.1 --port 5050
```

Then open:

```text
http://127.0.0.1:5050
```

## Project Structure

```text
config/      Strategy configuration
data/        Historical market datasets
src/         Flask app and strategy logic
outputs/     Generated reports and exports
```

Generated files in `outputs/`, virtual environments, and Python cache files are ignored by Git.
