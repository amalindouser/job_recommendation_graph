# app.py
import os
from flask import Flask, render_template, request
import networkx as nx
from recommender import score_user

app = Flask(__name__)

# ================================
# Load pre-built graph (GraphML)
# ================================
GRAPH_PATH = os.path.join("knowledge_graph", "output", "explainable_skills_graph.graphml")

if not os.path.exists(GRAPH_PATH):
    raise FileNotFoundError(f"Graph file tidak ditemukan: {GRAPH_PATH}. Jalankan build_graph() dulu!")

G = nx.read_graphml(GRAPH_PATH)

# ================================
# Routes
# ================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    nama = request.form.get("nama", "").strip()
    skills_raw = request.form.get("skills", "")
    education = request.form.get("education", "")
    experience = request.form.get("experience", "")

    # parse skills by comma
    user_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # get recommendations
    results = score_user(
        G,
        user_skills,
        user_education=education,
        user_experience=experience,
        top_n=10
    )

    # results sudah siap, kirim ke template
    return render_template('results.html', nama=nama or "User", results=results)
