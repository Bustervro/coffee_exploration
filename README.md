# coffee_exploration

# Coffee Production, Export, and Import Analysis

## Project Overview
This project uses Python and Pandas to clean and explore
historical coffee production, export, and import data.

## Tools Used
- Python
- Pandas
- Matplotlib
- uv

## Datasets
1. Coffee_production-1.csv
2. Coffee_export-1.csv
3. Coffee_import-1.csv

## Data Cleaning
I used Pandas to:
- Remove duplicate rows
- Handle missing values
- Clean country names
- Convert data into numbers
- Organize data by country and year
- Combine the three datasets

## Data Analysis
The program examines:
- Top 10 coffee-producing countries
- Top 10 coffee-exporting countries
- Top 10 coffee-importing countries
- Global coffee trends over time
- Coffee export and import balances

## Visualizations
Matplotlib creates bar charts and a line graph
to show coffee trade patterns.

## Run the Project
uv sync
uv run python coffee_exploration.py

## Results
The program saves cleaned datasets, charts,
and findings in the outputs folder.

The results depend on the original CSV data.
Measurement units must be checked before
comparing production, exports, and imports.
