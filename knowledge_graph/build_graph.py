import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
import os

# Fix kompatibilitas NumPy 2.0
if not hasattr(np, "float_"):
    np.float_ = np.float64
if not hasattr(np, "int_"):
    np.int_ = np.int64

# Load dataset
print("📂 Membaca dataset jobs_skills_1.csv...")
df = pd.read_csv("import_data/jobs_skills_1.csv")
df = df.fillna("")
print(f"✅ Data dimuat: {len(df):,} baris\n")

# Siapkan Graph kosong
G = nx.Graph()
print("🧠 Membuat graph kosong...\n")

progress = tqdm(df.iterrows(), total=len(df), desc="🧩 Membangun Knowledge Graph", ncols=100)

for idx, row in progress:
    job_id = str(row["job_link"]).strip()
    job_title = str(row["job_title"]).strip()
    company = str(row["company"]).strip()
    location = str(row["job_location"]).strip()
    city = str(row["search_city"]).strip()
    country = str(row["search_country"]).strip()
    position = str(row["search_position"]).strip()
    job_level = str(row["job_level"]).strip()
    job_type = str(row["job_type"]).strip()
    skills = [s.strip().lower() for s in str(row["skills"]).split(",") if s.strip()]
    first_seen = str(row["first_seen"]).strip()

    full_location = city or location
    if country:
        full_location = f"{full_location}, {country}" if full_location else country

    # Tambahkan node JOB
    G.add_node(
        job_id,
        type="job",
        label=job_title or job_id,
        title=job_title,
        company=company or "Unknown Company",
        location=full_location or "Unknown Location",
        position=position or "Unknown Position",
        job_level=job_level or "N/A",
        job_type=job_type or "N/A",
        skills=", ".join(skills) if skills else "",
        date=first_seen or "",
        link=job_id
    )

    # COMPANY
    if company and company not in G:
        G.add_node(company, label=company, type="company")
    if company:
        G.add_edge(company, job_id, relation="offers")

    # LOCATION
    if full_location and full_location not in G:
        G.add_node(full_location, label=full_location, type="location")
    if full_location:
        G.add_edge(job_id, full_location, relation="based_in")

    # POSITION
    if position and position not in G:
        G.add_node(position, label=position, type="position")
    if position:
        G.add_edge(job_id, position, relation="belongs_to_field")

    # JOB LEVEL & TYPE
    if job_level and job_level not in G:
        G.add_node(job_level, label=job_level, type="level")
    if job_level:
        G.add_edge(job_id, job_level, relation="has_level")

    if job_type and job_type not in G:
        G.add_node(job_type, label=job_type, type="type")
    if job_type:
        G.add_edge(job_id, job_type, relation="has_type")

    # SKILLS
    for skill in skills:
        if skill and skill.lower() != "nan":
            if skill not in G:
                G.add_node(skill, label=skill, type="skill")
            G.add_edge(job_id, skill, relation="requires")

progress.close()

# Konversi semua atribut ke string
for node, attrs in G.nodes(data=True):
    for k, v in attrs.items():
        G.nodes[node][k] = str(v)

for u, v, attrs in G.edges(data=True):
    for k, v2 in attrs.items():
        G.edges[u, v][k] = str(v2)

# Simpan Graph
os.makedirs("knowledge_graph/output", exist_ok=True)
output_path_graphml = "knowledge_graph/output/linkedin_kg_contextual_.graphml"
output_path_pickle = "knowledge_graph/output/linkedin_kg_contextual_.gpickle"

print("\n💾 Menyimpan Knowledge Graph ke file (GraphML & GPickle)...")
nx.write_graphml(G, output_path_graphml)
nx.write_gpickle(G, output_path_pickle)

print("✅ Knowledge Graph berhasil dibuat!")
print(f"📊 Total Node : {len(G.nodes):,}")
print(f"📎 Total Edge : {len(G.edges):,}")
print(f"📁 Disimpan di : {output_path_graphml}")
