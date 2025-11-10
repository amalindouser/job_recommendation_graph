import numpy as np

if not hasattr(np, "float_"):
    np.float_ = np.float64
if not hasattr(np, "int_"):
    np.int_ = np.int64

import pandas as pd
import networkx as nx
from tqdm import tqdm
import os

print("📂 Membaca dataset jobs_skills_1.csv...")
df = pd.read_csv("import_data/jobs_skills_1.csv")
df = df.fillna("")
print(f"✅ Data dimuat: {len(df):,} baris\n")

G = nx.Graph()
print("🧠 Membuat graph kosong...\n")

progress = tqdm(df.iterrows(), total=len(df), desc="🧩 Membangun Knowledge Graph", ncols=100)

for idx, row in progress:
    job_id = str(row["job_link"]).strip() or f"job_{idx}"
    job_title = str(row["job_title"]).strip()
    company = str(row["company"]).strip()
    location = str(row["job_location"]).strip()
    city = str(row["search_city"]).strip()
    country = str(row["search_country"]).strip()
    position = str(row["search_position"]).strip()
    job_level = str(row["job_level"]).strip()
    job_type = str(row["job_type"]).strip()
    skills = [s.strip() for s in str(row["skills"]).split(",") if s.strip()]
    first_seen = str(row["first_seen"]).strip()

    # Gabung lokasi
    full_location = city or location
    if country:
        full_location = f"{full_location}, {country}" if full_location else country

    # === JOB node utama (pastikan semua atribut cocok dengan recommender.py) ===
    G.add_node(
        job_id,
        type="job",
        label=job_title or job_id,
        title=job_title or "Unknown Job",
        company=company or "Unknown Company",
        job_location=full_location or "Unknown Location",
        job_link=job_id if job_id.startswith("http") else "#",
        job_type=job_type or "N/A",
        job_level=job_level or "N/A",
        skills=", ".join(skills),
        date=first_seen or "",
    )

    # === Hubungan ===
    if company:
        G.add_node(company, label=company, type="company")
        G.add_edge(company, job_id, relation="offers")

    if full_location:
        G.add_node(full_location, label=full_location, type="location")
        G.add_edge(job_id, full_location, relation="based_in")

    if position:
        G.add_node(position, label=position, type="position")
        G.add_edge(job_id, position, relation="belongs_to_field")

    if job_level:
        G.add_node(job_level, label=job_level, type="level")
        G.add_edge(job_id, job_level, relation="has_level")

    if job_type:
        G.add_node(job_type, label=job_type, type="type")
        G.add_edge(job_id, job_type, relation="has_type")

    for skill in skills:
        if skill and skill.lower() != "nan":
            G.add_node(skill, label=skill, type="skill")
            G.add_edge(job_id, skill, relation="requires")

progress.close()

# Konversi agar aman disimpan
for n, attrs in G.nodes(data=True):
    for k, v in attrs.items():
        G.nodes[n][k] = str(v)
for u, v, attrs in G.edges(data=True):
    for k, v2 in attrs.items():
        G.edges[u, v][k] = str(v2)

# Simpan
os.makedirs("knowledge_graph/output", exist_ok=True)
output_path = "knowledge_graph/output/linkedin_kg_contextual.graphml"

print("\n💾 Menyimpan Knowledge Graph ke file (GraphML)...")
nx.write_graphml(G, output_path)

print("✅ Knowledge Graph berhasil dibuat!")
print(f"📊 Total Node : {len(G.nodes):,}")
print(f"📎 Total Edge : {len(G.edges):,}")
print(f"📁 Disimpan di : {output_path}")
