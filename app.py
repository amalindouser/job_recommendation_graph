from flask import Flask, render_template, request
import os
import networkx as nx
import requests
from recommender import recommend_jobs

app = Flask(__name__)

GRAPH_PATH = "knowledge_graph/output/jobs_tech_graph_small.graphml"
GRAPH_URL = "https://raw.githubusercontent.com/amalindouser/REPO/main/knowledge_graph/output/jobs_tech_graph_small.graphml"

# ============================
# LOAD GRAPH (auto download)
# ============================
def load_graph():
    if not os.path.exists(GRAPH_PATH):
        os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
        print("📥 Mengunduh graph dari GitHub...")
        try:
            r = requests.get(GRAPH_URL)
            r.raise_for_status()
            with open(GRAPH_PATH, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"❌ Gagal mengunduh graph: {e}")
            return None

    try:
        G = nx.read_graphml(GRAPH_PATH)
        print(f"✅ Graph berhasil dimuat: {len(G.nodes())} nodes, {len(G.edges())} edges")
        return G
    except Exception as e:
        print(f"❌ Gagal memuat graph: {e}")
        return None

print("🔄 Memuat graph...")
G = load_graph()
