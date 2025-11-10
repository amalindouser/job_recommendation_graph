import os
import re
import networkx as nx
import numpy as np
from collections import Counter
from difflib import get_close_matches

# Fix kompatibilitas NumPy 2.0
if not hasattr(np, "float_"):
    np.float_ = np.float64
if not hasattr(np, "int_"):
    np.int_ = np.int64

# ------------------------------
# 🔧 Fungsi bantu normalisasi
# ------------------------------
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

# ------------------------------
# 📂 Load knowledge graph
# ------------------------------
def load_graph_from_path(graph_path: str):
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file tidak ditemukan: {graph_path}")
    
    ext = os.path.splitext(graph_path)[1].lower()
    if ext == ".gpickle":
        G = nx.read_gpickle(graph_path)
    elif ext == ".graphml":
        G = nx.read_graphml(graph_path)
    else:
        raise ValueError("Gunakan file .gpickle atau .graphml")

    print(f"✅ Graph berhasil dimuat ({len(G.nodes)} nodes, {len(G.edges)} edges)")
    return G

# ------------------------------
# 🔑 Skill alias
# ------------------------------
SKILL_ALIASES = {
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "cv": "computer vision",
    "cam": "computer aided manufacturing cam software",
    "cics": "customer information control system",
    "deacom": "deacom erp",
    "paloalto advertising plan pro": "paloalto advertising plan pro"
}

def map_alias(skill: str):
    skill = normalize(skill)
    return SKILL_ALIASES.get(skill, skill)

# ------------------------------
# 🗺️ Fungsi bantu location
# ------------------------------
def get_cities_by_country(G, country: str):
    """Mengembalikan list city dari country tertentu di graph"""
    country = country.lower().strip()
    cities = set()
    for n, d in G.nodes(data=True):
        if str(d.get("type", "")).lower() == "location":
            label = d.get("label", "")
            if "," in label:
                city, loc_country = [x.strip() for x in label.split(",", 1)]
                if loc_country.lower() == country:
                    cities.add(city)
    return sorted(list(cities))

# ------------------------------
# 🧠 Rekomendasi jobs dengan filter lokasi
def recommend_jobs(G, user_skills, top_n=10, filter_country=None, filter_city=None):
    if isinstance(user_skills, str):
        user_skills = [user_skills]

    # normalisasi
    user_skills = [map_alias(s) for s in user_skills if s.strip()]
    user_skills_norm = [normalize(s) for s in user_skills]
    print(f"🔍 Input skills: {', '.join(user_skills_norm)}")

    results = []

    # Loop semua job di graph
    for job, data in G.nodes(data=True):
        if str(data.get("type", "")).lower() != "job":
            continue

        # filter lokasi
        job_location = data.get("location", "").lower()
        if filter_country and filter_country.lower() not in job_location:
            continue
        if filter_city and filter_city.lower() not in job_location:
            continue

        # ambil skill job dari atribut node
        job_skills = [normalize(s) for s in data.get("skills", "").split(",") if s.strip()]
        if not job_skills:
            continue

        matched = [s for s in job_skills if s in user_skills_norm]
        missing = [s for s in job_skills if s not in user_skills_norm]

        # Hitung skor kecocokan
        total_job_skills = len(job_skills) or 1
        match_percent = round(len(matched) / total_job_skills * 100, 1)

        if match_percent == 0:
            continue  # skip yang sama sekali tidak cocok

                # Tentukan level kecocokan
        if match_percent >= 80:
            fit_level = "Very Suitable"
            reason_text = (
                f"This job is a strong match for you because you already have most of the required skills "
                f"({', '.join(matched)}) needed for this position."
                f"{' No additional skills are required.' if not missing else f' You may also benefit from learning: {', '.join(missing[:3])}.'}"
            )

        elif match_percent >= 50:
            fit_level = "Suitable"
            reason_text = (
                f"This job matches well with your background in {', '.join(matched)}. "
                f"However, to be more competitive, consider improving your knowledge in: {', '.join(missing[:3]) or 'none'}."
            )

        elif match_percent >= 20:
            fit_level = "Less Suitable"
            reason_text = (
                f"This job shares a few overlapping skills with your profile ({', '.join(matched)}), "
                f"but most required skills are different — for example: {', '.join(missing[:3]) or 'none'}."
            )

        else:
            fit_level = "Not Suitable"
            reason_text = (
                f"This job has very few matching skills with your current profile. "
                f"Main required skills include: {', '.join(job_skills[:5])}."
            )


        results.append({
            "job_title": data.get("label") or data.get("title") or str(job),
            "company": data.get("company", "Unknown Company"),
            "location": data.get("location", "Unknown Location"),
            "job_type": data.get("job_type", "N/A"),
            "date": data.get("date", ""),
            "skills_job": job_skills[:10],
            "matched_skills": matched[:5],
            "missing_skills": missing[:5],
            "match_percent": match_percent,
            "fit_level": fit_level,
            "reason_text": reason_text,  # ✅ gunakan reason_text yang sudah dijelaskan di atas
            "link": data.get("link", "#")
        })

    # urutkan dari yang paling cocok
    results = sorted(results, key=lambda x: x["match_percent"], reverse=True)

    return results[:top_n]


# ------------------------------
# Test singkat
# ------------------------------
if __name__ == "__main__":
    G = load_graph_from_path("knowledge_graph/output/linkedin_kg_contextual.gpickle")
    
    # Contoh: dapatkan semua cities di United States
    us_cities = get_cities_by_country(G, "United States")
    print("Cities in United States:", us_cities)

    test_skills = [
        "data analyst",
        "CNC Mastercam",
        "Computer aided manufacturing CAM software",
        "Customer information control system CICS",
        "Deacom ERP",
        "PaloAlto Advertising Plan Pro"
    ]

    # Contoh rekomendasi dengan filter country/city
    recs = recommend_jobs(G, test_skills, top_n=5, filter_country="United States", filter_city=None)
    for r in recs:
        print(f"{r['job_title']} — {r['company']} ({r['location']})")
        print(f"💼 {r['job_type']} | Posted: {r['date']} | Match: {r['match_percent']}%")
        print(f"🧠 Skills matched: {', '.join(r['matched_skills'])}")
        print(f"💬 {r['reason_text']}")
        print(f"🔗 Link Job: {r['link']}")
        print("-" * 50)
