# import_data/import_occupation_data.py
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_sql import get_connection

def import_occupation_data():
    file_path = "import_data/Occupation Data.xlsx"
    df = pd.read_excel(file_path)

    required_cols = ["O*NET-SOC Code", "Title", "Description"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Kolom '{col}' wajib ada di Occupation Data.xlsx")

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        code = str(row["O*NET-SOC Code"]).strip()
        desc = str(row.get("Description", "")).strip()

        cur.execute("""
            UPDATE jobs
            SET description = %s
            WHERE code = %s
        """, (desc, code))

    conn.commit()
    print(f"✅ Berhasil memperbarui {len(df)} deskripsi pekerjaan dari Occupation Data.xlsx")
    cur.close()
    conn.close()

if __name__ == "__main__":
    import_occupation_data()
