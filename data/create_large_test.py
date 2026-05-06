import pandas as pd

# Create a larger test dataset with dates from 2018-01-01 to 2020-12-31
dates = pd.date_range(start='2018-01-01', end='2020-12-31', freq='D')
prices = [5000 + i * 0.5 + (i % 50) for i in range(len(dates))]

df = pd.DataFrame({
    'Date': dates,
    'Close': prices
})

df.to_csv('large_test_dataset.csv', index=False)
print(f'Created large_test_dataset.csv with {len(df)} rows')
print(f'Date range: {df["Date"].min()} to {df["Date"].max()}')
