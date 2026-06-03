# Expense Monthly Report

Generate a monthly expense report from an expense CSV.

## Input

The CSV must include these columns:

- `date`
- `amount`
- `category`

Extra columns are allowed.

## Run

```powershell
python expense_report.py sample_expenses.csv --output monthly_report.csv
```

## Output

The report CSV contains:

- `month`
- `category`
- `total_amount`
- `count`
