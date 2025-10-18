# import_data/import_to_sql.py
import pandas as pd
import pymysql
import os

# ============================
# 🔹 Konfigurasi koneksi SQL
# ============================
db_config = {
    "host": "localhost",      # ganti sesuai host-mu
    "user": "root",           # ganti sesuai user-mu
    "password": "", # ganti password
    "database": "job_recommendation"  # nama database
}

conn = pymysql.connect(
    host=db_config["host"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"],
    charset='utf8mb4'
)
cursor = conn.cursor()

# ============================
# 🔹 File CSV/XLSX
# ============================
skills_file = os.path.join("import_data", "Skills.xlsx")
tech_file   = os.path.join("import_data", "Technology_Skills.xlsx")

# ============================
# 🔹 Load data
# ============================
skills_df = pd.read_excel(skills_file)
tech_df   = pd.read_excel(tech_file)

all_records = []

# ============================
# 🔹 Import Skills
# ============================
for _, row in skills_df.iterrows():
    cursor.execute("""
        INSERT INTO skills (job_code, uri, title, description, category, score, type, hot, in_demand)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        title=VALUES(title), description=VALUES(description), score=VALUES(score)
    """, (
        row.get("O*NET-SOC Code", ""),
        row.get("Element ID", ""),
        row.get("Title", ""),
        row.get("Element Name", ""),
        row.get("Domain Source", ""),
        row.get("Data Value", 0),
        "skill",
        False,
        False
    ))

# ============================
# 🔹 Import Technology Skills
# ============================
for _, row in tech_df.iterrows():
    cursor.execute("""
        INSERT INTO skills (job_code, uri, title, description, category, score, type, hot, in_demand)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        title=VALUES(title), description=VALUES(description)
    """, (
        row.get("O*NET-SOC Code", ""),
        row.get("Title", ""),
        row.get("Title", ""),
        row.get("Example", ""),
        row.get("Commodity Title", ""),
        None,
        "tech_skill",
        bool(row.get("Hot Technology", False)),
        bool(row.get("In Demand", False))
    ))

# ============================
# 🔹 Commit & Tutup koneksi
# ============================
conn.commit()
cursor.close()
conn.close()

print(f"✅ Data Skills dan Technology Skills berhasil diimport ke SQL!")
