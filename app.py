from flask import Flask, render_template, request
import os
import sqlite3
import pandas as pd
from recommender import load_graph_from_path, recommend_jobs

app = Flask(__name__)

# ============================================================
# 🧩 LOAD KNOWLEDGE GRAPH
# ============================================================
GRAPH_DIR = "knowledge_graph/output"
GRAPH_NAME = "linkedin_kg_contextual_"

graph_path_gz = os.path.join(GRAPH_DIR, GRAPH_NAME + ".gpickle.gz")
graph_path = os.path.join(GRAPH_DIR, GRAPH_NAME + ".gpickle")

if os.path.exists(graph_path_gz):
    GRAPH_PATH = graph_path_gz
elif os.path.exists(graph_path):
    GRAPH_PATH = graph_path
else:
    raise FileNotFoundError("❌ Tidak ditemukan file graph (.gpickle atau .gpickle.gz)")

print(f"📦 Memuat Knowledge Graph dari: {GRAPH_PATH}")
G = load_graph_from_path(GRAPH_PATH)
print("✅ Graph berhasil dimuat!")


DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")


def get_jobs(country=None, city=None):
    """Ambil pekerjaan dari SQLite, bisa filter country & city"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if country:
        query += " AND search_country=?"
        params.append(country)
    if city:
        query += " AND search_city=?"
        params.append(city)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


all_jobs = get_jobs()
countries_cities = {
    country: sorted(all_jobs[all_jobs["search_country"] == country]["search_city"].unique())
    for country in all_jobs["search_country"].unique()
}
countries = sorted(countries_cities.keys())

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    results = []
    skills_input = []
    selected_country = ""
    selected_city = ""
    cities = []

    if request.method == "POST":
        # Ambil input skill
        skills_text = request.form.get("skills", "")
        skills_input = [s.strip() for s in skills_text.split(",") if s.strip()]

        # Ambil lokasi
        selected_country = request.form.get("country", "")
        selected_city = request.form.get("city", "")
        cities = countries_cities.get(selected_country, [])

        
        if not skills_input:
            filtered = get_jobs(selected_country, selected_city)

            if filtered.empty:
                error = "Tidak ditemukan pekerjaan di lokasi tersebut."
            else:
                results = [
                    {
                        "job_title": row.get("job_title", "Unknown Job"),
                        "company": row.get("company", ""),
                        "location": f"{row.get('search_city', '')}, {row.get('search_country', '')}",
                        "job_type": row.get("job_type", ""),
                        "date": row.get("date_posted", ""),
                        "link": row.get("job_link", "#"),
                        "skills_job": [
                            s.strip()
                            for s in str(row.get("job_skills", row.get("skills", ""))).split(",")
                            if s.strip()
                        ],
                        "match_percent": None,
                        "matched_skills": [],
                        "missing_skills": [],
                        "reason_text": "Pekerjaan ini direkomendasikan berdasarkan lokasi.",
                    }
                    for _, row in filtered.head(12).iterrows()
                ]

        
        else:
            try:
                results = recommend_jobs(G, skills_input, top_n=12)
            except Exception as e:
                print(f"⚠️ Error during recommendation: {e}")
                error = "Terjadi kesalahan saat menghasilkan rekomendasi."

    return render_template(
        "index.html",
        results=results,
        skills=skills_input,
        error=error,
        countries=countries,
        countries_cities=countries_cities,
        selected_country=selected_country,
        selected_city=selected_city,
        cities=countries_cities.get(selected_country, []),
    )


# if __name__ == "__main__":
#     app.run(debug=True)
