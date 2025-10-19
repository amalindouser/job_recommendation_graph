import os
from supabase import create_client
import networkx as nx

# ================= Supabase Client =================
SUPABASE_URL = "https://kxivlqmybqpjoiwcrsbf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4aXZscW15YnFwam9pd2Nyc2JmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA4NDIyNTUsImV4cCI6MjA3NjQxODI1NX0.m0dkK7WgSUloc9q_y92ylc4CHP3yaV0JIQQaFRKp81o"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= Bersihkan Tabel =================
def clear_graph_tables():
    try:
        supabase.table("graph_edges").delete().neq("job_title", None).execute()
        supabase.table("graph_nodes").delete().neq("label", None).execute()
        print("✅ Tabel graph_nodes dan graph_edges berhasil dikosongkan.")
    except Exception as e:
        print("⚠️ Gagal menghapus data:", e)

# ================= Simpan Graph ke Supabase =================
def save_graph_to_db(G):
    # ===== Simpan nodes =====
    nodes_to_insert = []
    for node, data in G.nodes(data=True):
        nodes_to_insert.append({
            "name": data.get("name") or node,      # ✅ pastikan name tidak null
            "type": data.get("type", ""),
            "code": data.get("code", ""),
            "category": data.get("category", ""),
            "label": data.get("label", node),
            "description": data.get("description", "")
        })

    batch_size = 500
    for i in range(0, len(nodes_to_insert), batch_size):
        batch = nodes_to_insert[i:i + batch_size]
        supabase.table("graph_nodes").insert(batch).execute()
        print(f"✅ Inserted nodes batch {i//batch_size + 1} ({len(batch)} rows)")

    # ===== Simpan edges =====
    edges_to_insert = []
    for u, v, data in G.edges(data=True):
        edges_to_insert.append({
            "job_title": u,
            "skill_name": v,
            "relation": data.get("relation", "uses_technology"),
            "reason": data.get("reason", ""),
            "confidence": data.get("confidence", 1.0)
        })

    for i in range(0, len(edges_to_insert), batch_size):
        batch = edges_to_insert[i:i + batch_size]
        supabase.table("graph_edges").insert(batch).execute()
        print(f"✅ Inserted edges batch {i//batch_size + 1} ({len(batch)} rows)")

    print(f"✅ Total {len(nodes_to_insert)} nodes dan {len(edges_to_insert)} edges disimpan ke Supabase.")


def load_graph_from_db():
    response = supabase.table("graph_edges").select("*").execute()
    data = response.data

    if not data:
        print("⚠️ Tidak ada data di tabel graph_edges.")
        return nx.Graph()

    G = nx.Graph()
    # insert nodes dulu supaya edge bisa connect
    node_response = supabase.table("graph_nodes").select("*").execute()
    for n in node_response.data:
        label = n.get("label")
        if not label:
            continue
        G.add_node(label,
                   type=n.get("type", "skill"),
                   code=n.get("code", ""),
                   category=n.get("category", ""),
                   description=n.get("description", ""))

    # insert edges
    for row in data:
        job = row.get("job_title")
        skill = row.get("skill_name")
        if not job or not skill:
            continue
        G.add_edge(job, skill,
                   relation=row.get("relation", "uses_technology"),
                   reason=row.get("reason", ""),
                   confidence=row.get("confidence", 1.0))
    print(f"✅ Graph dibangun dari Supabase ({len(G.nodes())} node, {len(G.edges())} edge)")
    return G

