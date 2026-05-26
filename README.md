# Comparative Air Quality Analysis across European Cities

## Project Description
This repository contains code and analysis for processing and visualizing historical air quality data across European cities. It combines the original Zurich open-government monitoring data with two Zenodo DOI datasets exposed through Renku/rclone data connectors: London (`10.5281/zenodo.18673871`) and Berlin (`10.5281/zenodo.18677070`). The project focuses on temporal trends, cross-city contrasts, and guideline exceedances.

## Data Structure
- Zurich: daily station-level CSV files, 1983-2025, mounted at `zurich-air-quality-data`.
- London DOI connector: Zenodo record `10.5281/zenodo.18673871`, mounted as a read-only rclone DOI filesystem.
- Berlin DOI connector: Zenodo record `10.5281/zenodo.18677070`, mounted as a read-only rclone DOI filesystem.
- Common comparison period: automatically inferred from the overlap across all cities.
- Harmonized parameters:
  - PM2.5 and PM10
  - NO2 / nitrogen dioxide
  - O3 / ozone

## Key Features
- Robust data discovery for Renku-mounted connectors and local rclone DOI copies
- Harmonization of Zurich long-format data and Open-Meteo DOI wide-format data
- Common-window comparison across Zurich, London, and Berlin
- Monthly and annual trend plots
- Distribution plots and WHO daily guideline exceedance summaries
- Exported summary tables and figures under `results/`

## Technical Stack
- Python 3.9+
- Libraries:
  - pandas for data manipulation
  - matplotlib for static visualizations

## Project Structure
```
renku-demo-air-quality-analysis/
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   └── exploratory_analysis.py
├── src/
│   └── air_quality_comparison.py
├── results/
│   ├── figures/
│   └── tables/
├── requirements.txt
└── project.toml
```

## Getting Started
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. In Renku, attach the Zurich, London DOI, and Berlin DOI data connectors.
4. Execute `notebooks/exploratory_analysis.ipynb`.

### Local DOI exploration with rclone

The rclone DOI backend can list or copy Zenodo DOI contents locally by passing the DOI directly:

```bash
rclone config create london doi doi 10.5281/zenodo.18673871
rclone backend metadata london:
rclone lsf london:
rclone copy london: .tmp_doi_explore/downloads/london
```

The same pattern works for Berlin with DOI `10.5281/zenodo.18677070`.

## Analysis Components

## Visualization Outputs
- Time series plots