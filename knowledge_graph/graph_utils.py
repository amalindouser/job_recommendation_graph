import networkx as nx
from mongo_connection import get_db

def generate_explanation(job_title, score, matched_skills, missing_skills):
    """
    Membuat kalimat penjelasan otomatis berdasarkan skill yang cocok dan tidak cocok.
    """
    match_percent = min(100, round(score * 10, 2))
    explanation = f"Anda cocok sekitar {match_percent}% untuk pekerjaan ini karena memiliki "

    if matched_skills:
        explanation += f"{len(matched_skills)} keterampilan yang relevan, seperti "
        explanation += ", ".join(matched_skills[:4])
        if len(matched_skills) > 4:
            explanation += ", dan lainnya."
        else:
            explanation += "."
    else:
        explanation += "beberapa kesesuaian dengan deskripsi pekerjaan."

    if missing_skills:
        explanation += f" Disarankan untuk meningkatkan kemampuan di bidang {', '.join(missing_skills[:3])} agar peluang meningkat."

    return explanation


def score_user(G, user_skills, user_education=None, user_experience=None, top_n=5):
    results = []
    user_skills_lower = [s.lower() for s in user_skills]

    for node in G.nodes:
        if G.nodes[node]["type"] == "job":
            job_node = node
            job_title = G.nodes[job_node].get("title", job_node)

            # Ambil semua skill yang berhubungan dengan job
            job_skills = [(u, G.edges[u, job_node]["weight"])
                          for u in G.predecessors(job_node)
                          if G.nodes[u]["type"] in ["skill", "tech_skill"]]

            # Skill yang cocok
            matched = [(s, w) for s, w in job_skills if s.lower() in user_skills_lower]
            matched_skills = [s for s, _ in matched]
            score = sum(w for _, w in matched)

            # Skill yang belum dimiliki
            all_job_skills = {s for s, _ in job_skills}
            missing_skills = list(all_job_skills - set(matched_skills))

            # Tambahan bobot untuk education dan experience
            if user_education and user_education.lower() in job_title.lower():
                score += 1
            if user_experience and user_experience.lower() in job_title.lower():
                score += 1

            if score > 0:
                explanation = generate_explanation(job_title, score, matched_skills, missing_skills)
                match_percent = min(100, round(score * 10, 2))
                
                results.append({
                    "job": job_node,
                    "job_title": job_title,
                    "score": round(score, 2),
                    "match_percent": match_percent,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "explanation": explanation
                })

    # Urutkan berdasarkan skor tertinggi
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
    return results
