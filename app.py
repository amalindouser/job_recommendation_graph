from flask import Flask, render_template, request
import networkx as nx
from recommender import recommend_jobs

app = Flask(__name__)

GRAPH_PATH = "knowledge_graph/output/jobs_tech_graph_fuzzy_reduced.graphml"

print("🔄 Memuat graph jobs_tech_graph_fuzzy.graphml...")
try:
    G = nx.read_graphml(GRAPH_PATH)
    print(f"✅ Graph berhasil dimuat: {len(G.nodes())} nodes, {len(G.edges())} edges")
except Exception as e:
    print(f"❌ Gagal memuat graph: {e}")
    G = None 



@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None
    nama = skills = ""

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        skills = request.form.get("skills", "").strip()

        if not skills:
            error = "Silakan masukkan minimal satu skill!"
        else:
           
            user_skills = [s.strip() for s in skills.split(",") if s.strip()]
            if not user_skills:
                error = "Format skill tidak valid."
            else:
                try:
                    if G is None:
                        error = "Graph belum dimuat. Pastikan file .graphml tersedia."
                    else:
                        
                        results = recommend_jobs(user_skills, graph=G, top_n=10)
                        if not results:
                            error = "Tidak ditemukan rekomendasi pekerjaan yang relevan."
                except Exception as e:
                    error = f"Terjadi kesalahan saat menghasilkan rekomendasi: {str(e)}"

    return render_template(
        "index.html",
        results=results,
        error=error,
        nama=nama,
        skills=skills
    )
