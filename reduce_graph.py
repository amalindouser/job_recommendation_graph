import networkx as nx
import os
import time
from datetime import datetime
import numpy as np

# ===============================
# Patch NumPy 2.x compatibility
# ===============================
if not hasattr(np, "float_"):
    np.float_ = np.float64
if not hasattr(np, "int_"):
    np.int_ = np.int64
if not hasattr(np, "complex_"):
    np.complex_ = np.complex128

# ===============================
# Input & Output
# ===============================
INPUT_PATH = "knowledge_graph/output/jobs_tech_graph_fuzzy.graphml"
OUTPUT_PATH = "knowledge_graph/output/jobs_tech_graph_fuzzy_reduced.graphml.gz"
TOP_N_JOBS = 200
SKILL_THRESHOLD = 2

# ===============================
# Fungsi parsing tanggal
# ===============================
def parse_date(date_str):
    if not date_str or str(date_str).lower() in ["nan", "none", ""]:
        return datetime(1900, 1, 1)
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return datetime(1900, 1, 1)

# ===============================
# Mulai timer
# ===============================
start_time = time.time()

# ===============================
# Load graph
# ===============================
print("🔄 Memuat graph...")
G = nx.read_graphml(INPUT_PATH)

# Ambil TOP_N_JOBS terbaru
job_nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("type") == "job"]
job_nodes.sort(key=lambda x: parse_date(x[1].get("date", "")), reverse=True)
job_nodes = job_nodes[:TOP_N_JOBS]

# Buat graph baru dengan job + skill
G_reduced = nx.Graph()
for job, data in job_nodes:
    G_reduced.add_node(job, **data)
    for nbr in G.neighbors(job):
        if G.nodes[nbr].get("type") == "skill":
            if not G_reduced.has_node(nbr):
                G_reduced.add_node(nbr, **G.nodes[nbr])
            G_reduced.add_edge(job, nbr, **G.get_edge_data(job, nbr))

# Filter skill jarang muncul
skills_to_keep = [n for n, d in G_reduced.nodes(data=True)
                  if d.get("type") == "skill" and G_reduced.degree(n) >= SKILL_THRESHOLD]
job_nodes_kept = [n for n, d in G_reduced.nodes(data=True) if d.get("type") == "job"]

G_reduced = G_reduced.subgraph(job_nodes_kept + skills_to_keep).copy()

# Simpan graph hasil pangkas
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
nx.write_graphml(G_reduced, OUTPUT_PATH)

# ===============================
# Hitung runtime
# ===============================
end_time = time.time()
print(f"📊 Total Nodes: {len(G_reduced.nodes())}, Total Edges: {len(G_reduced.edges())}")
print(f"⏱ Runtime: {end_time - start_time:.2f} detik")
