# %% [markdown]
# # Comparative Air Quality Analysis across European Cities
#
# This notebook compares the original Zurich daily monitoring dataset with two
# additional European Zenodo DOI data connectors:
#
# - London: `10.5281/zenodo.18673871`
# - Berlin: `10.5281/zenodo.18677070`
#
# The DOI records are exposed in Renku through rclone's read-only DOI backend. In
# a Renku session they are mounted as data connectors; locally they can be
# explored with commands such as:
#
# ```bash
# rclone config create london doi doi 10.5281/zenodo.18673871
# rclone lsf london:
# rclone backend metadata london:
# ```

# %%
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "src").exists():
    PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from air_quality_comparison import (  # noqa: E402
    POLLUTANT_COLUMNS,
    WHO_DAILY_GUIDELINES,
    CITY_DATASETS,
    comparison_window,
    load_all_cities,
    monthly_means,
    overlapping_period,
    pollutant_summary,
)

plt.style.use("default")
FIG_DIR = PROJECT_ROOT / "results" / "figures"
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ## Load and harmonize data
#
# Zurich data is stored as one CSV per year in long form (`Datum`, `Parameter`,
# `Wert`, `Standort`). The DOI city datasets contain one `air_quality_historical.csv`
# file in wide form. The loader normalizes these into one daily table with common
# pollutant columns.

# %%
air, metadata = load_all_cities(PROJECT_ROOT)
print(f"Loaded {len(air):,} city-day rows")
display(air.head())

# %%
coverage = air.groupby("city")["date"].agg(["min", "max", "count"])
coverage

# %%
for city, meta in metadata.items():
    print(f"\n{city}")
    if city in CITY_DATASETS:
        print(f"DOI: {CITY_DATASETS[city]['doi']}")
    print(meta.get("title", ""))

# %% [markdown]
# ## Restrict to the common time window
#
# The London and Berlin DOI datasets start in 2013, while Zurich has its own
# monitoring record. For fair comparison, most summaries below use the period
# where all cities overlap.

# %%
start, end = overlapping_period(air)
common = comparison_window(air)
print(f"Common comparison window: {start.date()} to {end.date()}")
common.groupby("city")[POLLUTANT_COLUMNS].count()

# %% [markdown]
# ## Summary statistics and guideline exceedances
#
# All pollutant units are micrograms per cubic metre (µg/m³) except AQI columns.
# For a simple public-health-oriented comparison, daily values are compared with
# WHO 2021 daily guideline levels where directly applicable:
#
# - PM2.5: 15 µg/m³
# - PM10: 45 µg/m³
# - NO2: 25 µg/m³

# %%
summary = pollutant_summary(common)
summary.to_csv(TABLE_DIR / "city_pollutant_summary_common_period.csv", index=False)
summary.sort_values(["pollutant", "mean"])

# %%
wide_mean = summary.pivot(index="city", columns="pollutant", values="mean")
wide_mean.to_csv(TABLE_DIR / "city_pollutant_mean_common_period.csv")
wide_mean

# %% [markdown]
# ## Monthly trends

# %%
monthly = monthly_means(common)
monthly.to_csv(TABLE_DIR / "monthly_city_pollutants_common_period.csv", index=False)

for pollutant in [c for c in POLLUTANT_COLUMNS if c in monthly.columns]:
    fig, ax = plt.subplots(figsize=(10, 5))
    for city, city_df in monthly.groupby("city"):
        ax.plot(city_df["month"], city_df[pollutant], marker="o", linewidth=1.5, label=city)
    if pollutant in WHO_DAILY_GUIDELINES:
        ax.axhline(WHO_DAILY_GUIDELINES[pollutant], color="black", linestyle="--", linewidth=1, label="WHO daily guideline")
    ax.set_title(f"Monthly mean {pollutant.replace('_', '.').upper()}")
    ax.set_xlabel("Month")
    ax.set_ylabel("µg/m³")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"monthly_{pollutant}_comparison.png", dpi=150)
    plt.show()

# %% [markdown]
# ## Distribution comparison

# %%
for pollutant in [c for c in POLLUTANT_COLUMNS if c in common.columns]:
    plot_df = common[["city", pollutant]].dropna()
    if plot_df.empty:
        continue
    cities = sorted(plot_df["city"].unique())
    data = [plot_df.loc[plot_df["city"] == city, pollutant] for city in cities]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, labels=cities, showfliers=False)
    if pollutant in WHO_DAILY_GUIDELINES:
        ax.axhline(WHO_DAILY_GUIDELINES[pollutant], color="black", linestyle="--", linewidth=1, label="WHO daily guideline")
        ax.legend()
    ax.set_title(f"Daily {pollutant.replace('_', '.').upper()} distribution")
    ax.set_ylabel("µg/m³")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"boxplot_{pollutant}_comparison.png", dpi=150)
    plt.show()

# %% [markdown]
# ## Annual means over the common period

# %%
annual = common.copy()
annual["year"] = annual["date"].dt.year
annual_means = annual.groupby(["city", "year"], as_index=False)[POLLUTANT_COLUMNS].mean()
annual_means.to_csv(TABLE_DIR / "annual_city_pollutants_common_period.csv", index=False)

for pollutant in [c for c in POLLUTANT_COLUMNS if c in annual_means.columns]:
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot = annual_means.pivot(index="year", columns="city", values=pollutant)
    pivot.plot(kind="bar", ax=ax)
    ax.set_title(f"Annual mean {pollutant.replace('_', '.').upper()}")
    ax.set_xlabel("Year")
    ax.set_ylabel("µg/m³")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"annual_{pollutant}_comparison.png", dpi=150)
    plt.show()

# %% [markdown]
# ## Key takeaways
#
# Run the notebook to populate these tables and figures. In general, this layout
# is intended to answer:
#
# 1. Which city has the highest average and peak concentrations during the common
#    period?
# 2. How often does each city exceed WHO daily guideline values?
# 3. Are seasonal/monthly patterns similar across Zurich, London, and Berlin?

# %%
for pollutant in ["pm2_5", "pm10", "nitrogen_dioxide"]:
    if pollutant not in summary["pollutant"].unique():
        continue
    part = summary[summary["pollutant"] == pollutant].sort_values("mean", ascending=False)
    highest = part.iloc[0]
    print(
        f"{pollutant}: highest mean is {highest['city']} "
        f"({highest['mean']:.1f} µg/m³; {highest.get('pct_days_above_guideline', float('nan')):.0f}% "
        "of days above the WHO daily guideline)."
    )
