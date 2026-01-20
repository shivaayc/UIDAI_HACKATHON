import duckdb, yaml
import plotly.express as px
import warnings

# Silence future warnings from pandas/plotly
warnings.simplefilter(action="ignore", category=FutureWarning)

# Load config
with open("config/config.yaml") as f:
    cfg = yaml.safe_load(f)

# Connect to DuckDB
con = duckdb.connect()

# Load CSVs again (each script must do this)
enrol_glob = cfg["files"]["enrolment_glob"]
demo_glob = cfg["files"]["demographic_glob"]
bio_glob = cfg["files"]["biometric_glob"]

con.execute(f"CREATE OR REPLACE VIEW enrol AS SELECT * FROM read_csv_auto('{enrol_glob}')")
con.execute(f"CREATE OR REPLACE VIEW demo AS SELECT * FROM read_csv_auto('{demo_glob}')")
con.execute(f"CREATE OR REPLACE VIEW bio AS SELECT * FROM read_csv_auto('{bio_glob}')")

# --- Basic counts ---
print("Enrolment rows:", con.execute("SELECT COUNT(*) FROM enrol").fetchone()[0])
print("Demographic rows:", con.execute("SELECT COUNT(*) FROM demo").fetchone()[0])
print("Biometric rows:", con.execute("SELECT COUNT(*) FROM bio").fetchone()[0])

# --- Daily enrolments by district (example: age_0_5 column) ---
try:
    df = con.execute("""
        SELECT district, date, SUM(age_0_5) AS cnt_0_5
        FROM enrol
        GROUP BY district, date
        ORDER BY date
    """).fetchdf()

    fig = px.line(df, x="date", y="cnt_0_5", color="district",
                  title="Daily enrolments (age 0-5) by district")
    fig.write_html("outputs/enrol_daily.html")
except Exception as e:
    print("Skipped enrolment plot:", e)

# --- Demographic age distributions (auto-detect columns) ---
demo_schema = con.execute("DESCRIBE demo").fetchdf()
demo_age_cols = [col for col in demo_schema["column_name"] if col.startswith("demo_age_")]

print("\nDetected demographic age columns:", demo_age_cols)

demo_df = con.execute("SELECT " + ", ".join(demo_age_cols) + " FROM demo").fetchdf()

for col in demo_age_cols:
    fig = px.histogram(demo_df, x=col, nbins=50, title=f"Distribution of {col}")
    fig.write_html(f"outputs/{col}_hist.html")

# --- Biometric age distributions (auto-detect columns) ---
bio_schema = con.execute("DESCRIBE bio").fetchdf()
bio_age_cols = [col for col in bio_schema["column_name"] if col.startswith("bio_age_")]

print("\nDetected biometric age columns:", bio_age_cols)

bio_df = con.execute("SELECT " + ", ".join(bio_age_cols) + " FROM bio").fetchdf()

for col in bio_age_cols:
    fig = px.histogram(bio_df, x=col, nbins=50, title=f"Distribution of {col}")
    fig.write_html(f"outputs/{col}_hist.html")

print("\nEDA outputs saved in outputs/ (HTML files)")