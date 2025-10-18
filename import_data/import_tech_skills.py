import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_sql import get_connection

def import_tech_skills(excel_path=None):
    if excel_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        excel_path = os.path.join(base_dir, "import_data", "Technology_Skills.xlsx")

    df = pd.read_excel(excel_path)

    # Normalisasi nama kolom
    df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]

    conn = get_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        job_code = str(row.get("O*NET_SOC_Code", "")).strip()
        job_title = str(row.get("Title", "")).strip()
        example = str(row.get("Example", "")).strip()
        commodity_code = str(row.get("Commodity_Code", "")).strip()
        commodity_title = str(row.get("Commodity_Title", "")).strip()

        hot = 1 if str(row.get("Hot_Technology", "")).strip().lower() == "yes" else 0
        in_demand = 1 if str(row.get("In_Demand", "")).strip().lower() == "yes" else 0

        cursor.execute("""
            INSERT INTO tech_skills (job_code, job_title, example, commodity_code, commodity_title, hot_tech, in_demand)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (job_code, job_title, example, commodity_code, commodity_title, hot, in_demand))

    conn.commit()
    conn.close()
    print(f"✅ Imported {len(df)} technology skills into MySQL successfully!")

if __name__ == "__main__":
    import_tech_skills()
