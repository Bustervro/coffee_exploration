
from pathlib import Path
import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)

FILES = {
    "production": "Coffee_production-1.csv",
    "exports": "Coffee_export-1.csv",
    "imports": "Coffee_import-1.csv",
}


def clean_data(kind, filename):
    df = pd.read_csv(ROOT / filename, encoding="utf-8-sig")
    original_rows = len(df)

    # Clean column names and remove duplicates
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna(how="all").drop_duplicates()

    # Find the country column
    country_col = next(
        (col for col in df.columns if "country" in col.lower()),
        None
    )

    if country_col is None:
        raise ValueError(f"No country column in {filename}")

    df[country_col] = df[country_col].astype("string").str.strip()
    df = df.dropna(subset=[country_col])
    df = df[df[country_col] != ""]

    # Find columns containing years
    year_cols = [
        col for col in df.columns
        if re.match(r"^(19|20)\d{2}", str(col))
    ]

    if year_cols:
        df = df.melt(
            id_vars=[col for col in df.columns if col not in year_cols],
            value_vars=year_cols,
            var_name="year",
            value_name="amount"
        )
    else:
        year_col = next(
            (col for col in df.columns if col.lower() == "year"),
            None
        )
        if year_col is None:
            raise ValueError(f"No year column in {filename}")

        amount_cols = [
            col for col in df.columns
            if col not in [country_col, year_col]
        ]
        if not amount_cols:
            raise ValueError(f"No amount column in {filename}")

        df = df.rename(columns={
            year_col: "year",
            amount_cols[0]: "amount"
        })

    df = df.rename(columns={country_col: "country"})

    # Convert values into numbers
    df["year"] = pd.to_numeric(
        df["year"].astype(str).str.extract(r"((?:19|20)\d{2})")[0],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"].astype("string").str.replace(",", "", regex=False),
        errors="coerce"
    )

    missing_count = df["amount"].isna().sum()

    # Remove invalid entries
    df = df.dropna(subset=["year", "amount"])
    df = df[df["amount"] >= 0].copy()
    df["year"] = df["year"].astype(int)

    # Combine records for each country and year
    df = df.groupby(
        ["country", "year"], as_index=False
    )["amount"].sum()

    df = df.rename(columns={"amount": kind})
    df.to_csv(OUTPUT / f"clean_{kind}.csv", index=False)

    return df, {
        "dataset": kind,
        "original_rows": original_rows,
        "clean_rows": len(df),
        "missing_amounts": int(missing_count)
    }


def create_bar_chart(data, title, filename):
    if data.empty:
        return

    plt.figure(figsize=(10, 6))
    data.sort_values().plot(kind="barh")
    plt.title(title)
    plt.xlabel("Coffee quantity (source dataset units)")
    plt.ylabel("Country")
    plt.tight_layout()
    plt.savefig(OUTPUT / filename)
    plt.close()


def main():
    cleaned = {}
    quality = []
    findings = []

    # Load and clean all three datasets
    for kind, filename in FILES.items():
        data, report = clean_data(kind, filename)
        cleaned[kind] = data
        quality.append(report)
        print(f"Cleaned {kind}: {len(data)} rows")

    pd.DataFrame(quality).to_csv(
        OUTPUT / "data_quality_summary.csv",
        index=False
    )

    # Merge data by country and year
    combined = cleaned["production"]

    for kind in ["exports", "imports"]:
        combined = combined.merge(
            cleaned[kind],
            on=["country", "year"],
            how="outer",
            validate="one_to_one"
        )

    combined = combined.sort_values(["country", "year"])
    combined["trade_balance"] = (
        combined["exports"] - combined["imports"]
    )

    combined.to_csv(
        OUTPUT / "unified_coffee_trade.csv",
        index=False
    )

    # Find top 10 countries for each measurement
    for metric in ["production", "exports", "imports"]:
        available = combined.dropna(subset=[metric])

        if available.empty:
            continue

        latest_year = int(available["year"].max())
        latest = available[available["year"] == latest_year]

        top_10 = (
            latest.groupby("country")[metric]
            .sum()
            .nlargest(10)
        )

        print(f"\nTop 10 coffee {metric} countries:")
        print(top_10)

        create_bar_chart(
            top_10,
            f"Top 10 Coffee {metric.title()} Countries ({latest_year})",
            f"top_10_{metric}.png"
        )

        if not top_10.empty:
            findings.append(
                f"- {metric.title()}: {top_10.index[0]} "
                f"ranked first in {latest_year}."
            )

    # Show global coffee trends
    yearly = combined.groupby("year")[
        ["production", "exports", "imports"]
    ].sum(min_count=1)

    if not yearly.empty:
        yearly.plot(figsize=(11, 6), marker="o")
        plt.title("Global Coffee Production, Exports and Imports")
        plt.xlabel("Year")
        plt.ylabel("Coffee quantity (check source units)")
        plt.tight_layout()
        plt.savefig(OUTPUT / "global_trends.png")
        plt.close()

    # Compare exports and imports where both exist
    trade = combined.dropna(subset=["exports", "imports"])

    if not trade.empty:
        balance = trade.groupby("country")[
            ["exports", "imports"]
        ].sum()

        balance["trade_balance"] = (
            balance["exports"] - balance["imports"]
        )

        balance.to_csv(OUTPUT / "country_trade_balance.csv")

        leader = balance["trade_balance"].idxmax()
        findings.append(
            f"- Largest total export-minus-import balance: {leader}."
        )

    # Save findings
    report_text = "# Coffee Analysis Findings\n\n"
    report_text += "## Main Results\n\n"
    report_text += "\n".join(findings)
    report_text += "\n\n## Limitations\n\n"
    report_text += (
        "Missing values were not treated as zero. "
        "Invalid values and negative quantities were removed. "
        "Source units and country names should be verified "
        "before comparing datasets directly.\n"
    )

    (OUTPUT / "FINDINGS.md").write_text(
        report_text,
        encoding="utf-8"
    )

    print("\n" + report_text)
    print("\nFinished! Check the outputs folder.")


if __name__ == "__main__":
    main()
