import pandas as pd
import sqlite3

# Baca CSV
df_jobs = pd.read_csv("import_data/jobs_skills_1.csv", low_memory=False)

# Bersihkan kolom
df_jobs["search_country"] = df_jobs["search_country"].astype(str).str.strip()
df_jobs["search_city"] = df_jobs["search_city"].astype(str).str.strip()
df_jobs = df_jobs[df_jobs["search_country"].notna() & (df_jobs["search_country"] != "nan")]

# Simpan ke SQLite
conn = sqlite3.connect("jobs.db")
df_jobs.to_sql("jobs", conn, if_exists="replace", index=False)
conn.close()
