# Data (not included)

The raw data is **not** in this repository, and never will be. The Kaggle
competition rules (7.A non-commercial use, 7.B no redistribution of the
competition data) do not allow publishing it. The `.gitignore` blocks it so it
cannot be committed by accident.

## How to get it

1. Create a free Kaggle account.
2. Go to the competition: **H&M Personalized Fashion Recommendations**.
3. Accept the rules and download these files into the project root:
   - `transactions_train.csv`
   - `customers.csv`
   - `articles.csv`
4. Run the pipeline (see the main README).

## What you can see without the data

Everything in `outputs/` is already here. Those are small grouped aggregates,
no customer level rows, so you can read the full set of results and open the
Tableau dashboard without downloading anything.

## One thing to keep in mind

Prices in this dataset are scrambled by Kaggle. Every money figure in this
project is therefore an **index**, useful for comparison, not real pounds.
