import os
import re
from typing import List, Dict, Union, Optional
import networkx as nx
from rapidfuzz import fuzz
import numpy as np
from datetime import datetime, timedelta

if not hasattr(np, "float_"):
    np.float_ = np.float64
if not hasattr(np, "int_"):
    np.int_ = np.int64
if not hasattr(np, "complex_"):
    np.complex_ = np.complex128


def normalize(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9+# ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date_fuzzy(date_str):
    if not date_str or str(date_str).strip() == "":
        return datetime(1900, 1, 1)

    s = str(date_str).lower().strip()
    now = datetime.now()
    try:
        if "day" in s:
            num = int(re.findall(r'\d+', s)[0]) if re.findall(r'\d+', s) else 0
            return now - timedelta(days=num)
        elif "hour" in s:
            return now
        elif "week" in s:
            num = int(re.findall(r'\d+', s)[0]) if re.findall(r'\d+', s) else 0
            return now - timedelta(weeks=num)
        elif "month" in s:
            num = int(re.findall(r'\d+', s)[0]) if re.findall(r'\d+', s) else 0
            return now - timedelta(days=num * 30)
        elif "year" in s:
            num = int(re.findall(r'\d+', s)[0]) if re.findall(r'\d+', s) else 0
            return now - timedelta(days=num * 365)

        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
    except Exception:
        pass
    return datetime(1900, 1, 1)


def load_graph_from_path(graph_path: str) -> nx.Graph:
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"File graph tidak ditemukan: {graph_path}")
    G = nx.read_graphml(graph_path)
    return G


def recommend_jobs(
    user_skills: Union[str, List[str]],
    graph: Optional[nx.Graph] = None,
    graph_path: str = "knowledge_graph/output/jobs_tech_graph_fuzzy_reduced.graphml.gz",
    top_n: int = 10,
    similarity_threshold: int = 55
) -> List[Dict]:
    # Normalisasi input
    if isinstance(user_skills, str):
        user_skills = [user_skills]
    user_skills = [normalize(s) for s in user_skills if str(s).strip()]
    if not user_skills:
        raise ValueError("Tidak ada skill yang diberikan.")

    if graph is None:
        graph = load_graph_from_path(graph_path)

    recommendations = []
    now = datetime.now()

   
    job_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "job"]

    for job in job_nodes:
        data = graph.nodes[job]

        job_title = data.get("label", job)
        company = data.get("company", "Perusahaan tidak diketahui")
        location = data.get("location", "")
        link = data.get("link", "")
        date_posted = data.get("date", "")
        parsed_date = parse_date_fuzzy(date_posted)
        status = data.get("status", "active")

       
        if (now - parsed_date).days > 90:
            status = "expired"
        if status != "active":
            continue

      
        job_skills = [n for n in graph.neighbors(job) if graph.nodes[n].get("type") == "skill"]
        if not job_skills:
            continue

        matched, missing = [], []
        total_score = 0

        for js in job_skills:
            js_norm = normalize(js)
            best_ratio = 0
            for us in user_skills:
                ratio = fuzz.partial_ratio(us, js_norm)
                if ratio > best_ratio:
                    best_ratio = ratio
            if best_ratio >= similarity_threshold:
                matched.append(js)
                total_score += best_ratio / 100
            else:
                missing.append(js)

        if not matched:
            continue

    
        normalized_score = total_score / max(len(job_skills), 1)
        match_percent = round(normalized_score * 100, 1)

        # Level kecocokan
        if match_percent >= 85:
            fit_level = "Sangat Cocok"
        elif match_percent >= 70:
            fit_level = "Cocok"
        elif match_percent >= 50:
            fit_level = "Cukup Cocok"
        elif match_percent >= 30:
            fit_level = "Kurang Cocok"
        else:
            fit_level = "Tidak Cocok"

        matched_display = ", ".join(matched[:7])
        missing_display = ", ".join(missing[:5])
        explanation_parts = [
            f"Kamu memiliki skill relevan seperti {matched_display}."
        ]
        if match_percent < 60 and missing:
            explanation_parts.append(f"Pertimbangkan untuk mempelajari skill seperti {missing_display}.")
        explanation = " ".join(explanation_parts)

        recommendations.append({
            "job_title": job_title,
            "company": company,
            "location": location,
            "link": link,
            "status": status,
            "date_posted": date_posted,
            "match_percent": match_percent,
            "fit_level": fit_level,
            "matched_skills": matched[:7],
            "missing_skills": missing[:5],
            "explanation": explanation,
            "date_sort": parsed_date
        })

    
    recommendations.sort(key=lambda x: (x["match_percent"], x["date_sort"]), reverse=True)
    return recommendations[:top_n]



if __name__ == "__main__":
    print("🔍 Testing recommender with explainable output...")
    skills = ["Python", "Machine Learning", "SQL", "AWS"]
    res = recommend_jobs(skills)
    for r in res[:5]:
        print(f"{r['job_title']} ({r['match_percent']}%) - {r['fit_level']}")
        print(f"  👉 {r['explanation']}\n")
