import pandas as pd
from mongo_connection import get_db
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db = get_db()
collection = db["skills"]

# Paths file
skills_file = os.path.join("import_data", "data", "Skills.xlsx")       # kalau ini CSV asli
tech_file   = os.path.join("import_data", "data", "Technology_Skills.xlsx")  # Excel

# Load dataset
skills_df = pd.read_excel(skills_file)
tech_df   = pd.read_excel(tech_file)  # pakai read_excel untuk .xlsx

all_records = []

# Dataset Skills
for _, row in skills_df.iterrows():
    record = {
        "uri": row.get("Element ID", ""),
        "title": row.get("Title", ""),
        "type": "skill",
        "job_code": row.get("O*NET-SOC Code", ""),
        "description": row.get("Element Name", ""),
        "category": row.get("Domain Source", ""),
        "score": row.get("Data Value", 0),
        "hot": False,
        "in_demand": False
    }
    all_records.append(record)

# Dataset Tech Skills
for _, row in tech_df.iterrows():
    record = {
        "uri": row.get("Title", ""),
        "title": row.get("Title", ""),
        "type": "tech_skill",
        "job_code": row.get("O*NET-SOC Code", ""),
        "description": row.get("Example", ""),
        "category": row.get("Commodity Title", ""),
        "score": None,
        "hot": row.get("Hot Technology", False),
        "in_demand": row.get("In Demand", False)
    }
    all_records.append(record)

# Simpan ke MongoDB
collection.drop()
collection.insert_many(all_records)
print(f"✅ Total {len(all_records)} skill & tech_skill tersimpan di MongoDB!")
