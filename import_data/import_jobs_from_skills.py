# import_data/import_jobs_from_skills.py
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_sql import get_connection

def import_jobs_from_skills():
    conn = get_connection()
    cur = conn.cursor()

    # === Baca dua file ===
    skills_df = pd.read_excel("import_data/Skills.xlsx")
    tech_df = pd.read_excel("import_data/Technology_Skills.xlsx")

    # Ambil semua O*NET-SOC Code unik
    all_jobs = pd.concat([skills_df[['O*NET-SOC Code', 'Title']],
                          tech_df[['O*NET-SOC Code', 'Title']]]).drop_duplicates()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) UNIQUE,
            title VARCHAR(255)
        )
    """)

    for _, row in all_jobs.iterrows():
        cur.execute("""
            INSERT IGNORE INTO jobs (code, title) VALUES (%s, %s)
        """, (row['O*NET-SOC Code'], row['Title']))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Imported {len(all_jobs)} jobs.")

if __name__ == "__main__":
    import_jobs_from_skills()