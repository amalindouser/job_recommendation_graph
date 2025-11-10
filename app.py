from flask import Flask, render_template, request
import pandas as pd
from recommender import load_graph_from_path, recommend_jobs

app = Flask(__name__)

# ===== Load Knowledge Graph =====
GRAPH_PATH = "knowledge_graph/output/linkedin_kg_contextual_.gpickle"
G = load_graph_from_path(GRAPH_PATH)

# ===== Load Jobs Dataset =====
df_jobs = pd.read_csv("import_data/jobs_skills_1.csv", low_memory=False)

# Bersihkan kolom country & city
df_jobs["search_country"] = df_jobs["search_country"].astype(str).str.strip()
df_jobs["search_city"] = df_jobs["search_city"].astype(str).str.strip()

# Buang baris dengan country kosong
df_jobs = df_jobs[df_jobs["search_country"].notna() & (df_jobs["search_country"] != "nan")]

# Generate dictionary country → [cities]
countries_cities = {
    country: sorted(df_jobs[df_jobs["search_country"] == country]["search_city"].unique())
    for country in df_jobs["search_country"].unique()
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
        # Ambil input skills
        skills_text = request.form.get("skills", "")
        skills_input = [s.strip() for s in skills_text.split(",") if s.strip()]

        # Ambil country & city
        selected_country = request.form.get("country", "")
        selected_city = request.form.get("city", "")
        cities = countries_cities.get(selected_country, [])

        # === Jika tidak input skill, tampilkan berdasarkan lokasi ===
        if not skills_input:
            filtered = df_jobs.copy()
            if selected_country:
                filtered = filtered[filtered["search_country"] == selected_country]
            if selected_city:
                filtered = filtered[filtered["search_city"] == selected_city]

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
                        # ambil skill dari kolom job_skills atau skills
                        "skills_job": [
                            s.strip()
                            for s in str(
                                row.get("job_skills", row.get("skills", ""))
                            ).split(",")
                            if s.strip()
                        ],
                        "match_percent": None,
                        "matched_skills": [],
                        "missing_skills": [],
                        "reason_text": "Pekerjaan ini direkomendasikan berdasarkan lokasi.",
                    }
                    for _, row in filtered.head(12).iterrows()
                ]

        # === Jika ada input skill, gunakan rekomendasi berbasis graph ===
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


if __name__ == "__main__":
    app.run(debug=True)
