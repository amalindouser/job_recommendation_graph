from flask import Flask, render_template, request
import os
import pandas as pd
import psycopg2
import networkx as nx
from recommender import recommend_jobs
from dotenv import load_dotenv
import gzip

# ==============================
# ⚙️ Inisialisasi Flask
# ==============================
app = Flask(__name__)

# ==============================
# ⚙️ Load environment variables
# ==============================
load_dotenv()
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("❌ Environment variable DB_URL tidak ditemukan. Pastikan ada di Vercel Environment Variables atau .env")

# ==============================
# ☁️ Load Knowledge Graph dari file lokal (.gpickle.gz)
# ==============================
OUTPUT_FILE = os.path.join("knowledge_graph", "output", "linkedin_kg_contextual_.gpickle.gz")

if not os.path.exists(OUTPUT_FILE):
    raise FileNotFoundError(f"❌ File graph tidak ditemukan: {OUTPUT_FILE}")

try:
    with gzip.open(OUTPUT_FILE, 'rb') as f:
        G = nx.read_gpickle(f)
    print("✅ Graph berhasil dimuat dari lokal!")
except Exception as e:
    raise RuntimeError(f"❌ Gagal memuat graph: {e}")

# ==============================
# 🔗 Fungsi koneksi ke Neon PostgreSQL
# ==============================
def get_jobs(country=None, city=None):
    """Ambil data dari tabel jobs_skills di NeonDB"""
    conn = psycopg2.connect(DB_URL)
    query = "SELECT * FROM jobs_skills WHERE 1=1"
    params = []

    if country:
        query += " AND search_country = %s"
        params.append(country)
    if city:
        query += " AND search_city = %s"
        params.append(city)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# ==============================
# 🗺️ Siapkan data lokasi
# ==============================
print("📡 Mengambil semua data lokasi dari NeonDB...")
all_jobs = get_jobs()
print("📊 Kolom di tabel jobs:", all_jobs.columns.tolist())
print("📈 Jumlah data:", len(all_jobs))

# fallback jika kolom berbeda nama
if not all_jobs.empty:
    columns = [c.lower() for c in all_jobs.columns]
    if "search_country" not in columns and "country" in columns:
        all_jobs.rename(columns={"country": "search_country"}, inplace=True)
    if "search_city" not in columns and "city" in columns:
        all_jobs.rename(columns={"city": "search_city"}, inplace=True)

if "search_country" not in all_jobs.columns:
    all_jobs["search_country"] = ""
if "search_city" not in all_jobs.columns:
    all_jobs["search_city"] = ""

countries_cities = {
    country: sorted(all_jobs[all_jobs["search_country"] == country]["search_city"].dropna().unique())
    for country in all_jobs["search_country"].dropna().unique()
} if not all_jobs.empty else {}

countries = sorted(countries_cities.keys())

# ==============================
# 🌍 ROUTES
# ==============================
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    results = []
    skills_input = []
    selected_country = ""
    selected_city = ""

    if request.method == "POST":
        skills_text = request.form.get("skills", "")
        skills_input = [s.strip() for s in skills_text.split(",") if s.strip()]
        selected_country = request.form.get("country", "")
        selected_city = request.form.get("city", "")

        if not skills_input:
            # rekomendasi berdasarkan lokasi
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
                        "date": row.get("first_seen", ""),
                        "link": row.get("job_link", "#"),
                        "skills_job": [s.strip() for s in str(row.get("skills", "")).split(",") if s.strip()],
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

# ==============================
# 🔹 Jalankan server (untuk lokal)
# ==============================
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True)
