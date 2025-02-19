# Zurich Air Quality Analysis (1983-2025)

## Project Description
This repository contains code and analysis for processing and visualizing historical air quality data across multiple city locations. The project focuses on temporal trends and spatial variations in air quality parameters.

## Data Structure
- Time range: 1983-2025
- Frequency: Daily measurements
- Parameters:
  - PM2.5 and PM10
  - NO2, SO2, CO
    
## Key Features
- Data collection and cleaning pipeline
- Temporal trend analysis
- Spatial distribution visualization
- Seasonal pattern identification
- Statistical analysis of air quality trends
- Interactive dashboards

## Technical Stack
- Python 3.9+
- Libraries:
  - pandas for data manipulation
  - numpy for numerical operations
  - matplotlib/seaborn for static visualizations
  - plotly for interactive plots
  - scikit-learn for trend analysis
  - folium for spatial mapping

## Project Structure
```
zurich_air_quality_analysis/
├── air-quality-analysis/
├── personal-storage/
├── air-quality-analysis/
│   ├── notebooks/
│   │   ├── 01_data_cleaning.ipynb
│   │   ├── 02_exploratory_analysis.ipynb
│   │   └── 03_visualization.ipynb
│   └── src/
│       ├── data_processing/
│       ├── analysis/
│       └── visualization/
└── results/
    ├── figures/
    └── reports/
```

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run data processing pipeline
4. Execute analysis notebooks

## Analysis Components
- Time series decomposition
- Spatial correlation analysis
- Pollution hotspot identification
- Trend analysis by location
- Seasonal pattern visualization
- Statistical hypothesis testing

## Visualization Outputs
- Time series plots
- Heatmaps
- Geographic distributions
- Correlation matrices
- Interactive dashboards