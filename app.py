from flask import Flask, render_template, request
import networkx as nx
from recommender import recommend_jobs
import os, requests

app = Flask(__name__)

# ===============================
# Google Drive file setup
# ===============================
GRAPH_ID = "1Xz2fETwR50N5JlNnjReZwF4uT8kNWeSv"  # <== GANTI DENGAN FILE ID PUNYAMU
GRAPH_PATH = "knowledge_graph/output/jobs_tech_graph_fuzzy.graphml"
GRAPH_URL = f"https://drive.google.com/uc?export=download&id={GRAPH_ID}"

# Pastikan folder output ada
os.makedirs("knowledge_graph/output", exist_ok=True)

# ===============================
# Download otomatis jika file belum ada
# ===============================
if not os.path.exists(GRAPH_PATH):
    print("🌐 Mengunduh graph dari Google Drive...")
    r = requests.get(GRAPH_URL, allow_redirects=True)
    with open(GRAPH_PATH, "wb") as f:
        f.write(r.content)
    print("✅ File graph berhasil diunduh.")

# ===============================
# Muat graph
# ===============================
print("🔄 Memuat graph jobs_tech_graph_fuzzy.graphml...")
try:
    G = nx.read_graphml(GRAPH_PATH)
    print(f"✅ Graph berhasil dimuat: {len(G.nodes())} nodes, {len(G.edges())} edges")
except Exception as e:
    print(f"❌ Gagal memuat graph: {e}")
    G = None


@app.route("/", methods=["GET", "POST"])
def index():
    results, error = [], None
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
                        error = "Graph belum dimuat. Pastikan file tersedia."
                    else:
                        results = recommend_jobs(user_skills, graph=G, top_n=10)
                        if not results:
                            error = "Tidak ditemukan rekomendasi pekerjaan yang relevan."
                except Exception as e:
                    error = f"Terjadi kesalahan saat menghasilkan rekomendasi: {str(e)}"

    return render_template("index.html", results=results, error=error, nama=nama, skills=skills)

