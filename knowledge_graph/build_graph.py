import os
import time
import re
import pandas as pd
import networkx as nx
from tqdm import tqdm
from datetime import datetime
from rapidfuzz import fuzz


import numpy as np
if not hasattr(np, "float_"):
    np.float_ = np.float64

try:
    import lxml
except ImportError:
    print("⚙️ Menginstal modul lxml otomatis...")
    os.system("pip install lxml")
    import lxml


def extract_keywords(text):
    text = str(text)
    text = re.sub(r"[().,/#+-]", " ", text)
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text)
    return [w.lower() for w in words]



def detect_status(date_str):
    if not date_str or str(date_str).lower() in ["nan", "none", ""]:
        return "unknown"
    try:
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]
        for fmt in date_formats:
            try:
                job_date = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return "unknown"

        return "expired" if (datetime.now() - job_date).days > 90 else "active"
    except:
        return "unknown"


def build_graph(marged_jobs_path="import_data/merged_jobs.csv",
                tech_skills_path="import_data/Technology Skills.xlsx"):
    start_time = time.time()
    print("📂 Membaca dataset jobs dan technology_skills...")

    jobs_df = pd.read_csv(marged_jobs_path)
    tech_df = pd.read_excel(tech_skills_path)

    print(f"✅ Total jobs: {len(jobs_df)}, Total skill teknologi: {len(tech_df)}")

    G = nx.Graph()


    for _, row in tqdm(tech_df.iterrows(), total=len(tech_df), desc="Menambahkan skill nodes"):
        skill = str(row.get("Example", "")).strip()
        if skill and not G.has_node(skill):
            G.add_node(
                skill,
                type="skill",
                label=skill,
                title=row.get("Title_Job", ""),
                hot_technology=row.get("Hot Technology", "N"),
                in_demand=row.get("In Demand", "N")
            )


    for _, row in tqdm(jobs_df.iterrows(), total=len(jobs_df), desc="Memetakan job ke skill"):
        job_title = str(row.get("title", "")).strip()
        if not job_title:
            continue

        company = str(row.get("company", "")).strip()
        link = str(row.get("link", "")).strip()
        location = str(row.get("location", "")).strip()
        date_posted = str(row.get("date", "")).strip() or str(row.get("scrape_date", "")).strip()
        status = detect_status(date_posted)

        job_key = f"{job_title} - {company}"

        G.add_node(
            job_key,
            type="job",
            label=job_title,
            company=company,
            link=link,
            location=location,
            date=date_posted,
            status=status
        )


        combined_text = job_title + " " + str(row.get("description", ""))
        keywords = extract_keywords(combined_text)
        if not keywords:
            continue

        matched_skills = []
        for _, srow in tech_df.iterrows():
            skill_example = str(srow.get("Example", "")).strip()
            if not skill_example:
                continue
            skill_norm = re.sub(r"[^a-z0-9 ]", "", skill_example.lower())

            for kw in keywords:
                kw_norm = re.sub(r"[^a-z0-9 ]", "", kw)
                ratio = max(fuzz.partial_ratio(kw_norm, skill_norm),
                            fuzz.token_sort_ratio(kw_norm, skill_norm))
                if ratio >= 55:
                    if not G.has_node(skill_example):
                        G.add_node(skill_example, type="skill", label=skill_example)
                    G.add_edge(job_key, skill_example,
                               relation="requires",
                               confidence=ratio / 100)
                    matched_skills.append(skill_example)
                    break


    output_dir = os.path.join("knowledge_graph", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "jobs_tech_graph_fuzzy.graphml")

    try:
        nx.write_graphml(G, output_path)
        print(f"\n✅ GraphML berhasil disimpan ke: {output_path}")
    except Exception as e:
        print(f"⚠️ Gagal menyimpan ke GraphML ({e}). Menyimpan versi cadangan .gpickle...")
        fallback_path = os.path.join(output_dir, "jobs_tech_graph_fuzzy.gpickle")
        nx.write_gpickle(G, fallback_path)
        print(f"✅ Disimpan ke: {fallback_path}")

    end_time = time.time()
    print(f"📊 Total Nodes: {len(G.nodes())}, Total Edges: {len(G.edges())}")
    print(f"⏱ Runtime: {end_time - start_time:.2f} detik")

    return G



if __name__ == "__main__":
    G = build_graph()
