import os
import re
import duckdb
import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# -----------------------------
# Config
# -----------------------------
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_PATH = "C:/Users/SHIVAAY/Desktop/Uidai/api_data_aadhar_enrolment/api_data_aadhar_enrolment/*.csv"

def safe_filename(name: str) -> str:
    """Replace invalid filename characters with underscores."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', str(name))

print("Loading data...")

# -----------------------------
# Load data (only needed columns)
# -----------------------------
con = duckdb.connect()
con.execute(f"""
    CREATE OR REPLACE TABLE enrolments AS
    SELECT date, district, pincode
    FROM read_csv_auto('{DATA_PATH}', SAMPLE_SIZE=-1)
""")

df = con.execute("SELECT * FROM enrolments").df()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["district"] = df["district"].astype(str)
df["pincode"] = df["pincode"].astype(str)

# -----------------------------
# Weekly aggregation
# -----------------------------
df["week"] = df["date"].dt.to_period("W").dt.start_time
timeline = (
    df.groupby(["week", "district"])
      .size()
      .reset_index(name="total")
      .sort_values("week")
)

# -----------------------------
# Z-score anomaly detection
# -----------------------------
def zscore_anomalies(group):
    vals = group["total"].astype(float)
    mean, std = vals.mean(), vals.std(ddof=0)
    group["zscore"] = 0.0 if std == 0 else (vals - mean) / std
    group["is_anomaly"] = group["zscore"].abs() >= 2.0
    return group

timeline = (
    timeline.groupby("district", group_keys=False)
            .apply(lambda g: zscore_anomalies(g.copy()))
            .reset_index(drop=True)
)

# -----------------------------
# Save anomalies
# -----------------------------
anomaly_weeks = timeline.loc[timeline["is_anomaly"], ["week", "district"]].drop_duplicates()
anomalies_df = df.merge(anomaly_weeks, on=["week", "district"], how="inner")
anomalies_df.to_csv(os.path.join(OUTPUT_DIR, "anomalies.csv"), index=False)

district_rank = (
    anomalies_df.groupby("district")
    .size()
    .reset_index(name="anomaly_count")
    .sort_values("anomaly_count", ascending=False)
)
pincode_rank = (
    anomalies_df.groupby("pincode")
    .size()
    .reset_index(name="anomaly_count")
    .sort_values("anomaly_count", ascending=False)
)

district_rank.to_csv(os.path.join(OUTPUT_DIR, "district_anomaly_rank.csv"), index=False)
pincode_rank.to_csv(os.path.join(OUTPUT_DIR, "pincode_anomaly_rank.csv"), index=False)

# -----------------------------
# Summary metrics
# -----------------------------
summary = {
    "total_anomalies": int(len(anomalies_df)),
    "unique_districts": int(anomalies_df["district"].nunique()),
    "unique_pincodes": int(anomalies_df["pincode"].nunique()),
    "top_district": district_rank.iloc[0]["district"] if not district_rank.empty else None,
    "top_pincode": pincode_rank.iloc[0]["pincode"] if not pincode_rank.empty else None,
}
pd.DataFrame([summary]).to_csv(os.path.join(OUTPUT_DIR, "summary_metrics.csv"), index=False)

# -----------------------------
# Charts
# -----------------------------
fig_overall = px.line(
    timeline,
    x="week",
    y="total",
    color="district",
    title="Weekly Timeline of Enrolments with Anomalies",
    markers=True
)
anomaly_points = timeline[timeline["is_anomaly"]]
if not anomaly_points.empty:
    fig_overall.add_scatter(
        x=anomaly_points["week"],
        y=anomaly_points["total"],
        mode="markers",
        marker=dict(color="red", size=8),
        name="Anomalies",
    )
fig_overall.write_html(os.path.join(OUTPUT_DIR, "anomaly_timeline.html"), include_plotlyjs="cdn")

fig_district = px.bar(
    district_rank.head(10),
    x="district",
    y="anomaly_count",
    title="Top 10 Districts with Most Anomalies",
)
fig_district.write_html(os.path.join(OUTPUT_DIR, "district_anomaly_rank.html"), include_plotlyjs="cdn")

fig_pincode = px.bar(
    pincode_rank.head(10),
    x="pincode",
    y="anomaly_count",
    title="Top 10 Pincodes with Most Anomalies",
)
fig_pincode.write_html(os.path.join(OUTPUT_DIR, "pincode_anomaly_rank.html"), include_plotlyjs="cdn")

# Per-district timelines
os.makedirs(os.path.join(OUTPUT_DIR, "timeline_district"), exist_ok=True)
for d in timeline["district"].dropna().unique():
    subset = timeline[timeline["district"] == d].sort_values("week")
    fig_d = px.line(subset, x="week", y="total", title=f"Weekly Timeline for District: {d}", markers=True)
    sub_anom = subset[subset["is_anomaly"]]
    if not sub_anom.empty:
        fig_d.add_scatter(
            x=sub_anom["week"],
            y=sub_anom["total"],
            mode="markers",
            marker=dict(color="red", size=8),
            name="Anomalies",
        )
    filename = safe_filename(d) + ".html"
    fig_d.write_html(os.path.join(OUTPUT_DIR, "timeline_district", filename), include_plotlyjs="cdn")

# Per-pincode timelines
os.makedirs(os.path.join(OUTPUT_DIR, "timeline_pincode"), exist_ok=True)
for p in anomalies_df["pincode"].dropna().unique():
    pin_subset = (
        df[df["pincode"] == p]
        .groupby("week")
        .size()
        .reset_index(name="total")
        .sort_values("week")
    )
    fig_p = px.line(pin_subset, x="week", y="total", title=f"Weekly Timeline for Pincode: {p}", markers=True)
    pin_anom_weeks = anomalies_df[anomalies_df["pincode"] == p]["week"].drop_duplicates()
    pin_anom_points = pin_subset[pin_subset["week"].isin(pin_anom_weeks)]
    if not pin_anom_points.empty:
        fig_p.add_scatter(
            x=pin_anom_points["week"],
            y=pin_anom_points["total"],
            mode="markers",
            marker=dict(color="red", size=8),
            name="Anomalies",
        )
    filename = safe_filename(p) + ".html"
    fig_p.write_html(os.path.join(OUTPUT_DIR, "timeline_pincode", filename), include_plotlyjs="cdn")

print("Detection complete. Outputs saved in 'outputs/'")