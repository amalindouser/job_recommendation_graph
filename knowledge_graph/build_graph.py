import os
import pandas as pd
import networkx as nx
from db_utils import save_graph_to_db

def build_graph():
    file_path = os.path.join("import_data", "Technology_Skills.xlsx")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

    df = pd.read_excel(file_path)
    required_cols = ["O*NET-SOC Code", "Title", "Example", "Commodity Title"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Kolom '{col}' tidak ditemukan.")

    G = nx.Graph()
    for _, row in df.iterrows():
        job_title = str(row["Title"]).strip()
        skill_name = str(row["Example"]).strip()
        job_code = str(row["O*NET-SOC Code"]).strip()
        category = str(row["Commodity Title"]).strip()
        if not job_title or not skill_name:
            continue

        # Node
        G.add_node(job_title, type="job", code=job_code, label=job_title, description=f"Job {job_title}")
        G.add_node(skill_name, type="skill", category=category, label=skill_name, description=f"Skill {skill_name}")

        # Edge
        reason = f"{skill_name} umumnya digunakan oleh {job_title}"
        G.add_edge(job_title, skill_name, relation="uses_technology", reason=reason, confidence=0.9)

    # Simpan ke database
    save_graph_to_db(G)
    return G

if __name__ == "__main__":
    g = build_graph()
    print(f"Total Nodes: {len(g.nodes())}")
    print(f"Total Edges: {len(g.edges())}")
