import duckdb, yaml

with open("config/config.yaml") as f:
    cfg = yaml.safe_load(f)

enrol_glob = cfg["files"]["enrolment_glob"]
demo_glob = cfg["files"]["demographic_glob"]
bio_glob = cfg["files"]["biometric_glob"]

con = duckdb.connect()

con.execute(f"CREATE OR REPLACE VIEW enrol AS SELECT * FROM read_csv_auto('{enrol_glob}')")
con.execute(f"CREATE OR REPLACE VIEW demo AS SELECT * FROM read_csv_auto('{demo_glob}')")
con.execute(f"CREATE OR REPLACE VIEW bio AS SELECT * FROM read_csv_auto('{bio_glob}')")

print("Enrolment rows:", con.execute("SELECT COUNT(*) FROM enrol").fetchone()[0])
print("Demographic rows:", con.execute("SELECT COUNT(*) FROM demo").fetchone()[0])
print("Biometric rows:", con.execute("SELECT COUNT(*) FROM bio").fetchone()[0])

print("\n--- Enrolment schema ---")
print(con.execute("DESCRIBE enrol").fetchdf().head())

print("\n--- Demographic schema ---")
print(con.execute("DESCRIBE demo").fetchdf().head())

print("\n--- Biometric schema ---")
print(con.execute("DESCRIBE bio").fetchdf().head())