"""Utilities for comparing Zurich air-quality data with DOI datasets.

The notebook uses these functions both in Renku sessions, where data connectors are
mounted under /home/renku/work, and locally, where DOI records can be copied or
mounted with rclone.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd

POLLUTANT_COLUMNS = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone"]

CITY_DATASETS = {
    "New York City": {
        "doi": "10.5281/zenodo.18673876",
        "zip_name": "new-york-city-us-5128581.zip",
        "renku_target": "dataset-air-quality-dataset-fo-doi-10.5281-zenodo.18673876",
    },
    "Delhi": {
        "doi": "10.5281/zenodo.18673773",
        "zip_name": "delhi-in-1273294.zip",
        "renku_target": "dataset-air-quality-dataset-fo-doi-10.5281-zenodo.18673773",
    },
}

PARAMETER_MAP = {
    "pm2.5": "pm2_5",
    "pm2_5": "pm2_5",
    "pm25": "pm2_5",
    "pm2,5": "pm2_5",
    "pm10": "pm10",
    "no2": "nitrogen_dioxide",
    "stickstoffdioxid": "nitrogen_dioxide",
    "o3": "ozone",
    "ozon": "ozone",
}

WHO_DAILY_GUIDELINES = {
    "pm2_5": 15.0,
    "pm10": 45.0,
    "nitrogen_dioxide": 25.0,
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def search_roots(root: Path | None = None) -> list[Path]:
    """Return likely roots where Renku/local data connectors may be mounted."""
    root = root or project_root()
    candidates = [
        Path.cwd(),
        root,
        root.parent,
        Path.home() / "work",
        Path("/home/renku/work"),
        Path("/workspaces"),
        root / ".tmp_doi_explore" / "extracted",
    ]
    return list(dict.fromkeys(candidates))


def existing_paths(paths: Iterable[Path]) -> list[Path]:
    return [p for p in paths if p.exists()]


def find_zurich_data_dir(root: Path | None = None) -> Path:
    roots = search_roots(root)
    candidates = []
    for base in roots:
        candidates.extend(
            [
                base / "zurich-air-quality-data",
                base / "air-quality-data",
                base / "data" / "zurich-air-quality-data",
            ]
        )
    for path in candidates:
        if path.exists() and list(path.glob("ugz_ogd_air_d1_*.csv")):
            return path
    raise FileNotFoundError(
        "Could not find Zurich CSV files. Expected a Renku data connector mounted "
        "at 'zurich-air-quality-data' containing ugz_ogd_air_d1_*.csv."
    )


def load_zurich_daily(root: Path | None = None) -> pd.DataFrame:
    """Load Zurich long-format CSVs and return daily city-level pollutant columns."""
    data_dir = find_zurich_data_dir(root)
    frames = [pd.read_csv(path) for path in sorted(data_dir.glob("ugz_ogd_air_d1_*.csv"))]
    raw = pd.concat(frames, ignore_index=True)

    raw["date"] = pd.to_datetime(raw["Datum"], errors="coerce")
    raw["value"] = pd.to_numeric(raw["Wert"], errors="coerce")
    raw["pollutant"] = raw["Parameter"].astype(str).str.lower().str.strip().map(PARAMETER_MAP)
    raw = raw.dropna(subset=["date", "value", "pollutant"])

    daily = (
        raw.groupby([pd.Grouper(key="date", freq="D"), "pollutant"], as_index=False)["value"]
        .mean()
        .pivot(index="date", columns="pollutant", values="value")
        .reset_index()
    )
    daily.columns.name = None
    daily["city"] = "Zurich"
    daily["source"] = str(data_dir)
    return daily


def _candidate_doi_dirs(city: str, root: Path | None = None) -> list[Path]:
    info = CITY_DATASETS[city]
    slug = city.lower().replace(" ", "-")
    dirs: list[Path] = []
    for base in search_roots(root):
        dirs.extend(
            [
                base / info["renku_target"],
                base / slug,
                base / city.lower().replace(" ", ""),
                base / ".tmp_doi_explore" / "extracted" / ("nyc" if city == "New York City" else "delhi"),
            ]
        )
    return list(dict.fromkeys(dirs))


def _read_csv_from_zip(zip_path: Path, member_name: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member_name) as handle:
            return pd.read_csv(handle)


def load_doi_city(city: str, root: Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Load one DOI city dataset from a mounted/copied DOI connector.

    rclone exposes each Zenodo DOI record as a read-only filesystem containing a
    single zip file. Renku mounts the same filesystem as a data connector.
    """
    info = CITY_DATASETS[city]
    for directory in _candidate_doi_dirs(city, root):
        csv_path = directory / "air_quality_historical.csv"
        metadata_path = directory / "dataset-metadata.json"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
            df["source"] = str(directory)
            return _standardize_open_meteo_city(df, city), metadata

        zip_path = directory / info["zip_name"]
        if zip_path.exists():
            df = _read_csv_from_zip(zip_path, "air_quality_historical.csv")
            try:
                with zipfile.ZipFile(zip_path) as archive:
                    metadata = json.loads(archive.read("dataset-metadata.json"))
            except Exception:
                metadata = {}
            df["source"] = str(zip_path)
            return _standardize_open_meteo_city(df, city), metadata

    searched = "\n".join(str(p) for p in _candidate_doi_dirs(city, root))
    raise FileNotFoundError(
        f"Could not find mounted/copied DOI data for {city}. DOI: {info['doi']}. "
        f"Expected {info['zip_name']} or an extracted air_quality_historical.csv.\nSearched:\n{searched}"
    )


def _standardize_open_meteo_city(df: pd.DataFrame, city: str) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for column in POLLUTANT_COLUMNS + ["carbon_monoxide", "sulphur_dioxide", "us_aqi", "european_aqi"]:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    keep = ["date", "city", "source"] + [c for c in out.columns if c in POLLUTANT_COLUMNS + ["us_aqi", "european_aqi"]]
    out["city"] = city
    return out[keep].dropna(subset=["date"])


def load_all_cities(root: Path | None = None) -> tuple[pd.DataFrame, dict]:
    frames = [load_zurich_daily(root)]
    metadata = {"Zurich": {"title": "City of Zurich open government daily air-quality data"}}
    for city in CITY_DATASETS:
        city_df, city_metadata = load_doi_city(city, root)
        frames.append(city_df)
        metadata[city] = city_metadata
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = combined.sort_values(["city", "date"]).reset_index(drop=True)
    return combined, metadata


def overlapping_period(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    per_city = df.groupby("city")["date"].agg(["min", "max"])
    return per_city["min"].max(), per_city["max"].min()


def comparison_window(df: pd.DataFrame) -> pd.DataFrame:
    start, end = overlapping_period(df)
    return df[(df["date"] >= start) & (df["date"] <= end)].copy()


def pollutant_summary(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for city, city_df in df.groupby("city"):
        for pollutant in POLLUTANT_COLUMNS:
            if pollutant not in city_df:
                continue
            series = city_df[pollutant].dropna()
            if series.empty:
                continue
            record = {
                "city": city,
                "pollutant": pollutant,
                "days_with_data": int(series.shape[0]),
                "mean": series.mean(),
                "median": series.median(),
                "p95": series.quantile(0.95),
                "max": series.max(),
            }
            if pollutant in WHO_DAILY_GUIDELINES:
                limit = WHO_DAILY_GUIDELINES[pollutant]
                record["who_daily_guideline"] = limit
                record["days_above_guideline"] = int((series > limit).sum())
                record["pct_days_above_guideline"] = 100.0 * (series > limit).mean()
            records.append(record)
    return pd.DataFrame.from_records(records)


def add_month(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    return out


def monthly_means(df: pd.DataFrame) -> pd.DataFrame:
    return (
        add_month(df)
        .groupby(["city", "month"], as_index=False)[[c for c in POLLUTANT_COLUMNS if c in df.columns]]
        .mean()
    )
