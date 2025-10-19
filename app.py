import os
from flask import Flask, render_template, request
import networkx as nx
from recommender import score_user

# =====================================================
# 🔧 Inisialisasi Aplikasi Flask
# =====================================================
app = Flask(__name__)

# =====================================================
# 📦 Muat Knowledge Graph
# =====================================================
GRAPH_PATH = os.path.join("knowledge_graph", "output", "explainable_skills_graph.graphml")

if not os.path.exists(GRAPH_PATH):
    raise FileNotFoundError(
        f"❌ Graph file tidak ditemukan: {GRAPH_PATH}\n"
        "Pastikan kamu sudah menjalankan fungsi build_graph() terlebih dahulu."
    )

# Membaca graph dari file GraphML
G = nx.read_graphml(GRAPH_PATH)


# =====================================================
# 🌐 ROUTES
# =====================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Halaman utama: form input dan hasil rekomendasi ditampilkan bersama.
    """
    results = []
    nama = ""
    
    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get("nama", "").strip()
        skills_raw = request.form.get("skills", "").strip()
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "").strip()

        # Parsing skills (pisahkan berdasarkan koma)
        user_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        # 🔍 Hitung hasil rekomendasi
        try:
            results = score_user(
                G,
                user_skills,
                user_education=education,
                user_experience=experience,
                top_n=10
            )
        except Exception as e:
            print(f"Terjadi error saat memproses rekomendasi: {e}")
            results = []

    # Render ke index.html (form + hasil rekomendasi)
    return render_template('index.html', nama=nama or "User", results=results)


# =====================================================
# 🚀 Jalankan Server Flask
# =====================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
