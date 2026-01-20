import os
import pandas as pd

OUTPUT_DIR = "outputs"
DASHBOARD_PATH = os.path.join(OUTPUT_DIR, "fraud_radar_dashboard.html")

def read_csv_safe(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def main():
    # Load core artifacts
    anomalies = read_csv_safe(os.path.join(OUTPUT_DIR, "anomalies.csv"))
    district_rank = read_csv_safe(os.path.join(OUTPUT_DIR, "district_anomaly_rank.csv"))
    pincode_rank = read_csv_safe(os.path.join(OUTPUT_DIR, "pincode_anomaly_rank.csv"))
    summary = read_csv_safe(os.path.join(OUTPUT_DIR, "summary_metrics.csv"))

    # Headline metrics
    total_anomalies = int(summary["total_anomalies"].iloc[0]) if not summary.empty else 0
    unique_districts = int(summary["unique_districts"].iloc[0]) if not summary.empty else 0
    unique_pincodes = int(summary["unique_pincodes"].iloc[0]) if not summary.empty else 0
    top_district = summary["top_district"].iloc[0] if not summary.empty else "N/A"
    top_pincode = summary["top_pincode"].iloc[0] if not summary.empty else "N/A"

    # Dropdown options
    districts = sorted(anomalies["district"].dropna().unique().tolist()) if not anomalies.empty else []
    pincodes = sorted(anomalies["pincode"].dropna().unique().tolist()) if not anomalies.empty else []

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Fraud Radar Dashboard</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <header class="header">
    <div class="title">
      <h1>Fraud Radar Dashboard</h1>
      <p>Team Tech Developers — Shri Ram Institute of Technology, Jabalpur</p>
    </div>
  </header>

  <section class="banner">
    <h2>🔥 Current hotspot</h2>
    <p><strong>District:</strong> {top_district} &nbsp; | &nbsp; <strong>Pincode:</strong> {top_pincode}</p>
  </section>

  <section class="summary">
    <div class="card">
      <h3>Total anomalies</h3>
      <p class="metric">{total_anomalies}</p>
    </div>
    <div class="card">
      <h3>Districts affected</h3>
      <p class="metric">{unique_districts}</p>
    </div>
    <div class="card">
      <h3>Pincodes affected</h3>
      <p class="metric">{unique_pincodes}</p>
    </div>
  </section>

  <section class="filters">
    <div class="filter-group">
      <label for="districtSelect"><strong>District</strong></label>
      <select id="districtSelect">
        <option value="">-- Select district --</option>
        {"".join([f'<option value="{d}">{d}</option>' for d in districts])}
      </select>
    </div>
    <div class="filter-group">
      <label for="pincodeSelect"><strong>Pincode</strong></label>
      <select id="pincodeSelect">
        <option value="">-- Select pincode --</option>
        {"".join([f'<option value="{p}">{p}</option>' for p in pincodes])}
      </select>
    </div>
  </section>

  <section class="charts">
    <div class="chart">
      <h2>Overall timeline</h2>
      <iframe id="overallFrame" src="anomaly_timeline.html"></iframe>
    </div>

    <div class="chart">
      <h2>Top 10 districts</h2>
      <iframe src="district_anomaly_rank.html"></iframe>
    </div>

    <div class="chart">
      <h2>Top 10 pincodes</h2>
      <iframe src="pincode_anomaly_rank.html"></iframe>
    </div>

    <div class="chart">
      <h2>Drill‑down timeline</h2>
      <iframe id="drillFrame" src=""></iframe>
    </div>
  </section>

  <section class="downloads">
    <h2>⬇️ Evidence downloads</h2>
    <a class="button" href="anomalies.csv" download>Anomalies CSV</a>
    <a class="button" href="district_anomaly_rank.csv" download>District ranking CSV</a>
    <a class="button" href="pincode_anomaly_rank.csv" download>Pincode ranking CSV</a>
  </section>

  <footer class="footer">
    <p>UIDAI Data Hackathon 2026 — Prototype build</p>
  </footer>

  <script>
    const districtSelect = document.getElementById('districtSelect');
    const pincodeSelect = document.getElementById('pincodeSelect');
    const drillFrame = document.getElementById('drillFrame');

    districtSelect.addEventListener('change', () => {{
      const d = districtSelect.value;
      if (d) {{
        const safe = d.replace(/[^A-Za-z0-9_-]/g, '_');
        drillFrame.src = 'timeline_district/' + safe + '.html';
      }} else {{
        drillFrame.src = '';
      }}
      pincodeSelect.value = '';
    }});

    pincodeSelect.addEventListener('change', () => {{
      const p = pincodeSelect.value;
      if (p) {{
        const safe = p.replace(/[^A-Za-z0-9_-]/g, '_');
        drillFrame.src = 'timeline_pincode/' + safe + '.html';
      }} else {{
        drillFrame.src = '';
      }}
      districtSelect.value = '';
    }});
  </script>
</body>
</html>
"""
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] Dashboard built: {DASHBOARD_PATH}")

if __name__ == "__main__":
    main()