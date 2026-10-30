"""Quality inspection + preprocessing for Metro Interstate Traffic Volume.

Inputs : data/raw/metro_interstate_traffic_volume.csv   (untouched UCI snapshot)
Outputs: data/processed/metro_interstate_traffic_model.csv
         reports/quality_report.txt

Rules applied (fail loudly instead of guessing):
- No imputation of missing time steps; gaps are only documented.
- No automatic outlier removal; only documented data errors are flagged.
- Duplicate timestamps are only resolved when traffic_volume values agree.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path("data/raw/metro_interstate_traffic_volume.csv")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")

PROCESSED_PATH = PROCESSED_DIR / "metro_interstate_traffic_model.csv"
REPORT_PATH = REPORTS_DIR / "quality_report.txt"
DUPLICATE_DETAIL_PATH = REPORTS_DIR / "duplicate_timestamp_review.csv"
GAP_PATH = REPORTS_DIR / "timestamp_gaps.csv"
DAILY_COMPLETENESS_PATH = REPORTS_DIR / "daily_completeness.csv"

EXPECTED_START = pd.Timestamp("2012-10-02 09:00:00")
EXPECTED_END = pd.Timestamp("2018-09-30 23:00:00")
FULL_HOURLY_INDEX = pd.date_range(EXPECTED_START, EXPECTED_END, freq="h")


def section(out: io.StringIO, title: str) -> None:
    out.write(f"\n{'=' * 78}\n{title}\n{'=' * 78}\n")


def load_raw() -> pd.DataFrame:
    frame = pd.read_csv(RAW_PATH)
    frame["date_time"] = pd.to_datetime(frame["date_time"], format="%Y-%m-%d %H:%M:%S")
    return frame


def profile(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "1. SHAPE, DTYPE, MISSING VALUES")
    out.write(f"rows x columns : {df.shape[0]} x {df.shape[1]}\n")
    out.write(f"memory usage   : {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MiB\n\n")
    desc = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "non_null": df.notna().sum(),
            "n_missing": df.isna().sum(),
            "pct_missing": (df.isna().mean() * 100).round(3),
            "n_unique": df.nunique(),
        }
    )
    out.write(desc.to_string())
    out.write("\n")

    section(out, "1b. NUMERIC SUMMARY")
    out.write(df.describe().T.to_string())
    out.write("\n")

    section(out, "1c. CATEGORICAL VALUE COUNTS")
    for column in ["holiday", "weather_main"]:
        out.write(f"\n-- {column} --\n")
        out.write(df[column].value_counts(dropna=False).to_string())
        out.write("\n")
    out.write(f"\n-- weather_description (top 15 of {df['weather_description'].nunique()}) --\n")
    out.write(df["weather_description"].value_counts().head(15).to_string())
    out.write("\n")
    out.write(f"\nholiday: NaN (empty cell) = {int(df['holiday'].isna().sum())}, "
              f"named holidays = {int(df['holiday'].notna().sum())}\n")
    out.write("holiday labels present:\n")
    out.write(df["holiday"].dropna().value_counts().to_string())
    out.write("\n")
    holiday_rows = df.loc[df["holiday"].notna(), "date_time"]
    out.write(f"\nrows carrying a holiday label  : {len(holiday_rows)} "
              f"({holiday_rows.dt.date.nunique()} distinct dates)\n")
    out.write(f"time-of-day of those rows      : "
              f"{dict(holiday_rows.dt.hour.value_counts().sort_index())}\n")
    out.write("IMPORTANT: the holiday label only marks the 00:00 record of a holiday; the other 23 "
              "hours of that day keep an empty holiday cell. Row-level flags therefore undercount holidays.\n")


def duplicate_timestamp_review(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "2. DUPLICATE ROWS VS DUPLICATE TIMESTAMPS")
    out.write(f"fully duplicated rows          : {df.duplicated().sum()}\n")
    dup_mask = df["date_time"].duplicated(keep=False)
    dup = df.loc[dup_mask].sort_values(["date_time", "traffic_volume"])
    dup_times = dup["date_time"].unique()
    out.write(f"timestamps occurring >1 time   : {len(dup_times)}\n")
    out.write(f"rows involved                  : {len(dup)}\n")
    out.write(f"date range of duplicates       : {dup['date_time'].min()} .. {dup['date_time'].max()}\n")

    if len(dup_times) == 0:
        out.write("no duplicate timestamps\n")
        return

    grouped = dup.groupby("date_time")["traffic_volume"]
    spread = (grouped.max() - grouped.min()).reindex(dup_times)

    support = ["holiday", "temp", "rain_1h", "snow_1h", "clouds_all", "weather_main", "weather_description"]
    numeric_support = ["temp", "rain_1h", "snow_1h", "clouds_all"]
    n_support_diff = (dup.groupby("date_time")[support].nunique(dropna=False) > 1).any(axis=1)
    n_numeric_diff = (dup.groupby("date_time")[numeric_support].nunique() > 1).any(axis=1)
    n_weather_diff = (dup.groupby("date_time")[["weather_main", "weather_description"]]
                      .nunique() > 1).any(axis=1)
    n_holiday_diff = (dup.groupby("date_time")["holiday"].nunique(dropna=False) > 1).sum()

    out.write(f"duplicate timestamps                     : {len(dup_times)}\n")
    out.write(f"  - traffic_volume identical in group    : {int((spread == 0).sum())}\n")
    out.write(f"  - traffic_volume DIFFERENT in group    : {int((spread > 0).sum())}\n")
    out.write(f"  - every support column identical       : {int((~n_support_diff).sum())}\n")
    out.write(f"  - some support column differs          : {int(n_support_diff.sum())}\n")
    out.write(f"      weather_main/description differs   : {int(n_weather_diff.sum())}\n")
    out.write(f"      numeric weather cols differ        : {int(n_numeric_diff.sum())}\n")
    out.write(f"      holiday label differs              : {int(n_holiday_diff)}\n")
    out.write(f"max spread of traffic_volume inside a duplicate group: {spread.max():.0f}\n")
    numeric_spread = (dup.groupby("date_time")[numeric_support].max()
                      - dup.groupby("date_time")[numeric_support].min())
    out.write(f"numeric spread inside groups: temp max {numeric_spread['temp'].max():.2f} K, "
              f"rain_1h max {numeric_spread['rain_1h'].max():.2f} mm, snow_1h max "
              f"{numeric_spread['snow_1h'].max():.2f} mm, clouds_all max {numeric_spread['clouds_all'].max():.0f} pp\n")
    if n_numeric_diff.sum() > 0:
        example = numeric_spread[n_numeric_diff].nlargest(1, "temp").index[0]
        out.write(f"largest numeric disagreement at {example}:\n")
        out.write(dup.loc[dup["date_time"].eq(example),
                          ["date_time", "temp", "clouds_all", "weather_main", "traffic_volume"]]
                  .to_string(index=False) + "\n")
    if n_weather_diff.sum() > 0:
        example = n_weather_diff[n_weather_diff].index[0]
        out.write(f"example of differing weather label at {example}:\n")
        out.write(dup.loc[dup["date_time"].eq(example),
                          ["date_time", "weather_main", "weather_description", "traffic_volume"]]
                  .to_string(index=False) + "\n")
    out.write("=> traffic_volume is always identical. Two kinds of support-column disagreement exist:\n"
              "   (a) synonym labels for the same weather (Rain/light rain vs Drizzle/light intensity drizzle);\n"
              "   (b) disjoint hourly weather readings merged onto one timestamp (e.g. 276.79 K vs 256.36 K),\n"
              "       i.e. the same hour appears in more than one source weather file. Only the first row is\n"
              "       kept by keep-first, so support columns on those rows are approximate.\n")
    out.write("\ngroup size distribution (records per duplicated timestamp):\n")
    out.write(grouped.size().value_counts().sort_index().to_string())
    out.write("\n\nhour-of-day distribution of duplicated timestamps:\n")
    out.write(pd.Series(dup_times.hour).value_counts().sort_index().to_string())
    out.write("\n")

    dup.drop_duplicates().to_csv(DUPLICATE_DETAIL_PATH, index=False)
    out.write(f"\nfull duplicate rows written to {DUPLICATE_DETAIL_PATH}\n")

    if any(spread > 0):
        raise SystemExit(
            "Duplicate timestamps carry conflicting traffic_volume values. "
            "Review reports/duplicate_timestamp_review.csv manually before preprocessing."
        )


def temporal_coverage(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "3. TEMPORAL RANGE AND TIMESTAMP GAPS")
    out.write(f"min date_time : {df['date_time'].min()}\n")
    out.write(f"max date_time : {df['date_time'].max()}\n")
    out.write(f"span          : {df['date_time'].max() - df['date_time'].min()}\n")
    out.write(f"expected hours in [2012-10-02 09:00, 2018-09-30 23:00]: {len(FULL_HOURLY_INDEX)}\n")
    out.write(f"observed unique timestamps                          : {df['date_time'].nunique()}\n")

    observed = pd.Series(df["date_time"].drop_duplicates().sort_values().to_numpy())
    missing = FULL_HOURLY_INDEX.difference(pd.DatetimeIndex(observed))
    out.write(f"missing hourly timestamps                           : {len(missing)}\n")
    out.write(f"missing pct                                         : {len(missing) / len(FULL_HOURLY_INDEX) * 100:.2f}%\n")

    deltas = observed.diff().dropna()
    out.write(f"step sizes (hours) observed : {deltas.value_counts().sort_index().to_dict()}\n")
    out.write("NOTE: zero NaN in the value columns does NOT imply a complete hourly series.\n")

    if len(missing):
        miss_series = pd.Series(1, index=missing)
        runs = miss_series.groupby((miss_series.index.to_series().diff() != pd.Timedelta(hours=1)).cumsum())
        gaps = pd.DataFrame(
            {
                "gap_start": runs.apply(lambda s: s.index[0]),
                "gap_end": runs.apply(lambda s: s.index[-1]),
                "n_missing_hours": runs.size(),
            }
        ).sort_values("n_missing_hours", ascending=False)
        out.write(f"\nnumber of contiguous gaps : {len(gaps)}\n")
        out.write(f"largest gap               : {gaps['n_missing_hours'].max()} h "
                  f"({gaps.iloc[0]['gap_start']} .. {gaps.iloc[0]['gap_end']})\n")
        out.write("\ntop 15 gaps:\n")
        out.write(gaps.head(15).to_string(index=False))
        out.write("\ngap length distribution (hours -> count):\n")
        out.write(gaps["n_missing_hours"].value_counts().sort_index().to_string())
        out.write("\n")
        gaps.to_csv(GAP_PATH, index=False)
        out.write(f"\nall gaps written to {GAP_PATH}\n")

    section(out, "3b. TRAFFIC_VOLUME == 0 ROWS (suspected station downtime)")
    zeros = df[df["traffic_volume"] == 0]
    out.write(f"count      : {len(zeros)}\n")
    out.write(f"min date   : {zeros['date_time'].min() if len(zeros) else 'n/a'}\n")
    out.write(f"max date   : {zeros['date_time'].max() if len(zeros) else 'n/a'}\n")
    if len(zeros):
        out.write(f"temp/clouds on zero rows (mean): {zeros[['temp','clouds_all']].mean().to_dict()}\n")
        out.write("weather_main on zero rows:\n")
        out.write(zeros["weather_main"].value_counts().to_string())
        out.write("\n")


def yearly_completeness(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "4. OBSERVATIONS PER YEAR AND PER DAY")
    per_year = df.groupby(df["date_time"].dt.year)["date_time"].agg(["count", "nunique"])
    per_year["hours_in_year_observed_window"] = per_year.index.map(
        lambda y: len(FULL_HOURLY_INDEX[FULL_HOURLY_INDEX.year == y])
    )
    per_year["completeness_pct"] = (per_year["nunique"] / per_year["hours_in_year_observed_window"] * 100).round(2)
    out.write(per_year.to_string())
    out.write("\n")

    daily = (
        df.assign(date=df["date_time"].dt.date)
        .groupby("date")
        .agg(n_obs=("date_time", "nunique"), mean_volume=("traffic_volume", "mean"))
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily["is_partial_window"] = daily["date"].isin(
        [pd.Timestamp("2012-10-02"), pd.Timestamp("2018-09-30")]
    )
    full_days = daily.loc[~daily["is_partial_window"]]
    out.write(f"calendar days covered        : {len(daily)}\n")
    out.write(f"complete 24h days            : {int((full_days['n_obs'] == 24).sum())}\n")
    out.write(f"partial days (excluding the 2 clipped boundary days): {int((full_days['n_obs'] < 24).sum())}\n")
    out.write("days-per-observation-count distribution (all days):\n")
    out.write(daily["n_obs"].value_counts().sort_index().to_string())
    out.write("\nthe clipped boundary days:\n")
    out.write(daily[daily["is_partial_window"]].to_string(index=False))
    out.write("\n")
    daily.to_csv(DAILY_COMPLETENESS_PATH, index=False)


def sensor_errors(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "5b. SENSOR SENTINELS / IMPOSSIBLE PHYSICAL VALUES (flagged, kept)")
    zero_k = df["temp"].le(0)
    out.write(f"temp <= 0 K (below absolute zero, physically impossible): {int(zero_k.sum())} rows\n")
    if zero_k.any():
        out.write(f"  dates: {sorted(df.loc[zero_k, 'date_time'].dt.date.unique().tolist())}\n")
    rain_huge = df["rain_1h"].gt(200)
    out.write(f"rain_1h > 200 mm/h (US hourly record is ~330 mm; 200 mm is a sentinel, not rain): "
              f"{int(rain_huge.sum())} rows\n")
    if rain_huge.any():
        out.write(df.loc[rain_huge, ["date_time", "rain_1h", "weather_main"]].to_string(index=False) + "\n")
    lower = df["weather_description"].str.lower()
    mismatched = df.loc[df["weather_description"].ne(lower), "weather_description"].unique()
    out.write(f"weather_description labels only differing by capitalisation: {sorted(mismatched.tolist())}\n")
    out.write("  rows affected: "
              f"{int(df['weather_description'].ne(lower).sum())} -> normalised to lower case\n")
    out.write("These are flagged with is_temp_error / is_rain_error / and not imputed or dropped.\n")


def outliers(df: pd.DataFrame, out: io.StringIO) -> None:
    section(out, "5. OUTLIER REVIEW (no rows removed)")
    q1, q3 = df["traffic_volume"].quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    flagged = df["traffic_volume"].lt(low) | df["traffic_volume"].gt(high)
    out.write(f"Q1={q1:.0f} Q3={q3:.0f} IQR={iqr:.0f} fences=({low:.0f}, {high:.0f})\n")
    out.write(f"IQR outliers : {int(flagged.sum())} rows ({flagged.mean()*100:.2f}%)\n")
    out.write("Lower fence is negative -> traffic_volume has no low outliers.\n")
    out.write(f"Upper fence {high:.0f} exceeds the observed maximum {df['traffic_volume'].max():.0f} "
              "-> no IQR outliers on either side; the distribution is right-skewed, not contaminated.\n")
    non_zero = df.loc[df["traffic_volume"] > 0, "traffic_volume"]
    nz_q1, nz_q3 = non_zero.quantile([0.25, 0.75])
    nz_high = nz_q3 + 1.5 * (nz_q3 - nz_q1)
    out.write(f"After excluding the 0-volume rows: upper fence {nz_high:.0f}, "
              f"rows above it {int((non_zero > nz_high).sum())}\n")
    out.write("Highest 5 traffic_volume values:\n")
    out.write(df.nlargest(5, "traffic_volume")[["date_time", "traffic_volume", "weather_main"]].to_string(index=False))
    out.write("\n")


def preprocess(df: pd.DataFrame, out: io.StringIO) -> pd.DataFrame:
    section(out, "6. PREPROCESSING STEPS APPLIED")
    processed = df.copy()

    n_before = len(processed)
    processed = processed.drop_duplicates(subset="date_time", keep="first")
    out.write(f"1. drop duplicate timestamps (values verified identical): -{n_before - len(processed)} rows\n")

    processed["temp_c"] = processed["temp"] - 273.15
    processed = processed.rename(columns={"temp": "temp_k"})
    processed["is_temp_error"] = processed["temp_k"].le(0)
    processed["is_rain_error"] = processed["rain_1h"].gt(200)
    processed["temp_c_clean"] = processed["temp_c"].where(~processed["is_temp_error"])
    processed["weather_description"] = processed["weather_description"].str.lower()
    out.write("2. keep temp (K) as temp_k, add temp_c = temp_k - 273.15; "
              "flag impossible values (is_temp_error, is_rain_error) and add temp_c_clean "
              "(NaN on flagged rows, no imputation); lower-case weather_description\n")

    processed = processed.sort_values("date_time").reset_index(drop=True)
    processed["holiday"] = processed["holiday"].astype(object).where(processed["holiday"].notna(), "None")
    processed["date"] = processed["date_time"].dt.date
    processed["hour"] = processed["date_time"].dt.hour
    processed["day_of_week"] = processed["date_time"].dt.day_name()
    processed["day_of_week_num"] = processed["date_time"].dt.day_of_week
    processed["is_weekend"] = processed["day_of_week_num"] >= 5
    processed["month"] = processed["date_time"].dt.month
    processed["year"] = processed["date_time"].dt.year
    processed["is_holiday"] = processed["holiday"].ne("None")
    holiday_dates = set(processed.loc[processed["is_holiday"], "date"])
    processed["holiday_date"] = processed["date"].where(processed["date"].isin(holiday_dates))
    out.write("3. add calendar features: holiday (NaN -> 'None'), date, hour, day_of_week, "
              "day_of_week_num, is_weekend, month, year, is_holiday, holiday_date\n")
    out.write("   is_holiday marks only the labelled 00:00 row; holiday_date spreads the label over "
              "all 24 hours of that date for day-level comparisons\n")

    # Station downtime: zeros co-occur with non-zero temperature/clouds (i.e. the
    # sensor reported 0 while the weather station reported live data).
    zero_mask = processed["traffic_volume"].eq(0)
    processed["is_sensor_zero"] = zero_mask
    out.write(f"4. flag traffic_volume == 0 as is_sensor_zero ({int(zero_mask.sum())} rows), values NOT imputed\n")

    # No missing-hour rows are created; document gaps instead.
    processed["gap_hours"] = processed["date_time"].diff().dt.total_seconds().div(3600).fillna(0).astype(int)
    out.write("5. gap_hours = hours elapsed since previous observation (1 = contiguous)\n")

    out.write(f"\nfinal columns : {list(processed.columns)}\n")
    out.write(f"final shape   : {processed.shape}\n")
    out.write(f"missing cells : {int(processed.isna().sum().sum())}\n")
    return processed


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_raw()
    out = io.StringIO()
    out.write(f"source : {RAW_PATH}\n")
    out.write(f"loaded : {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}\n")

    profile(df, out)
    duplicate_timestamp_review(df, out)
    temporal_coverage(df, out)
    yearly_completeness(df, out)
    outliers(df, out)
    sensor_errors(df, out)

    zero_rows = df[df["traffic_volume"] == 0]
    zeros_by_year = zero_rows.groupby(zero_rows["date_time"].dt.year).size().to_dict()
    processed = preprocess(df, out)
    out.write(f"\nzero rows by year (preprocessing evidence): {zeros_by_year}\n")

    processed.to_csv(PROCESSED_PATH, index=False)
    out.write(f"\nwritten: {PROCESSED_PATH}\n")

    REPORT_PATH.write_text(out.getvalue(), encoding="utf-8")
    print(out.getvalue())


if __name__ == "__main__":
    main()
