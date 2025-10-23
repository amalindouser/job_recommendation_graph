import networkx as nx
import os
import pandas as pd
from datetime import datetime

# ===============================
# Patch NumPy 2.x compatibility
# ===============================
import numpy as np
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
OUTPUT_PATH = "knowledge_graph/output/jobs_tech_graph_fuzzy_reduced.graphml"
TOP_N_JOBS = 1000  # ambil 2000 job terbaru

def parse_date(date_str):
    if not date_str or str(date_str).lower() in ["nan", "none", ""]:
        return datetime(1900, 1, 1)
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return datetime(1900, 1, 1)

print("🔄 Memuat graph...")
G = nx.read_graphml(INPUT_PATH)
print(f"✅ Graph asli: {len(G.nodes())} nodes, {len(G.edges())} edges")

# ===============================
# Ambil job nodes dengan tanggal terbaru
# ===============================
job_nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("type") == "job"]
# sort by date descending
job_nodes.sort(key=lambda x: parse_date(x[1].get("date", "")), reverse=True)
job_nodes = job_nodes[:TOP_N_JOBS]

# ===============================
# Buat graph baru hanya dengan job + skill terhubung
# ===============================
G_reduced = nx.Graph()
for job, data in job_nodes:
    G_reduced.add_node(job, **data)
    # ambil skill yang terhubung
    for nbr in G.neighbors(job):
        if G.nodes[nbr].get("type") == "skill":
            if not G_reduced.has_node(nbr):
                G_reduced.add_node(nbr, **G.nodes[nbr])
            # tambahkan edge
            G_reduced.add_edge(job, nbr, **G.get_edge_data(job, nbr))

# ===============================
# Simpan graph yang dipangkas
# ===============================
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
nx.write_graphml(G_reduced, OUTPUT_PATH)
print(f"✅ GraphML dipangkas berhasil disimpan: {OUTPUT_PATH}")
print(f"📊 Nodes: {len(G_reduced.nodes())}, Edges: {len(G_reduced.edges())}")
