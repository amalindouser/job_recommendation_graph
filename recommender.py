# recommender.py
import networkx as nx
from collections import defaultdict
import random
import re


def random_phrase(options):
    """Pilih satu kalimat acak untuk variasi narasi."""
    return random.choice(options)


def clean_skill_name(skill):
    """Hilangkan kata yang aneh atau tidak relevan dari nama skill."""
    # Hilangkan teks terlalu teknis / merek / software product
    if any(bad in skill.lower() for bad in [
        "app", "tool", "product", "system", "application", "platform", "package"
    ]):
        return None
    # Hilangkan simbol atau teks tidak jelas
    skill = re.sub(r"[^a-zA-Z0-9+\-#., ]", "", skill).strip()
    return skill if skill else None


def score_user(G, user_skills, user_education=None, user_experience=None, top_n=10):
    recommendations = []
    job_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "job"]

    for job in job_nodes:
        job_data = G.nodes[job]
        job_title = job_data.get("label", job)
        neighbors = list(G.neighbors(job))

        matched = []
        score = 0
        category_match = defaultdict(list)

        for skill in user_skills:
            for neighbor in neighbors:
                if skill.lower() in neighbor.lower():
                    edge_data = G[job][neighbor]
                    w = edge_data.get("weight", 1.0)
                    skill_cat = G.nodes[neighbor].get("category", "Uncategorized")

                    matched.append((neighbor, w))
                    category_match[skill_cat].append(neighbor)
                    score += w

        # Tambahkan bonus pendidikan & pengalaman
        if user_education:
            score += 0.05
        if user_experience:
            score += 0.05

        if score <= 0:
            continue

        # Hitung kecocokan
        match_percent = min(100, round(score * 10, 1))
        if match_percent >= 75:
            fit_level = "Sangat Cocok"
        elif match_percent >= 50:
            fit_level = "Cocok"
        elif match_percent >= 25:
            fit_level = "Kurang Cocok"
        else:
            fit_level = "Tidak Cocok"

        # =============================
        # 🔍 Penjelasan Dinamis
        # =============================
        explain_parts = []

        # 🧠 Skill relevan
        if matched:
            skill_highlights = []
            for cat, skills in category_match.items():
                clean_skills = [clean_skill_name(s) for s in skills]
                clean_skills = [s for s in clean_skills if s]
                if clean_skills and cat != "Uncategorized":
                    example = ", ".join(clean_skills[:3])
                    skill_highlights.append(f"{cat.lower()} seperti {example}")

            if skill_highlights:
                skill_sentence = random_phrase([
                    f"Kemampuanmu di bidang {', '.join(skill_highlights)} menunjukkan arah yang selaras dengan pekerjaan {job_title}.",
                    f"Kamu punya dasar kuat di {', '.join(skill_highlights)}, yang relevan untuk peran ini.",
                    f"Skill yang kamu kuasai — {', '.join(skill_highlights)} — memberi pondasi kuat untuk posisi ini."
                ])
            else:
                skill_sentence = random_phrase([
                    f"Kamu memiliki beberapa skill yang relevan dengan pekerjaan {job_title}, walau belum mendalam.",
                    f"Ada sedikit kecocokan antara skill-mu dan kebutuhan posisi ini."
                ])
            explain_parts.append(skill_sentence)
        else:
            explain_parts.append(random_phrase([
                f"Tampaknya belum ada skill utama yang cocok dengan kebutuhan {job_title}.",
                f"Belum ada kecocokan signifikan antara skill kamu dengan pekerjaan ini."
            ]))

        # 🎓 Pendidikan
        if user_education:
            edu_lower = user_education.lower()
            if any(x in edu_lower for x in ["computer", "informatics", "it", "engineering", "data", "software"]):
                explain_parts.append(random_phrase([
                    "Latar belakang pendidikanmu sudah sangat relevan dengan bidang teknologi.",
                    "Pendidikanmu memberikan fondasi teori yang kuat untuk posisi ini."
                ]))
            elif fit_level in ["Kurang Cocok", "Tidak Cocok"]:
                explain_parts.append(random_phrase([
                    f"Pendidikanmu ({user_education}) memang berbeda bidang, tapi bisa jadi nilai tambah unik bila digabungkan dengan pelatihan teknis.",
                    f"Meskipun bidang studimu ({user_education}) tidak sejalan, kemampuan adaptasimu tetap bisa jadi keunggulan."
                ]))
            else:
                explain_parts.append(random_phrase([
                    f"Pendidikanmu ({user_education}) memberikan perspektif yang menarik untuk posisi ini.",
                    f"Bidang studimu ({user_education}) mungkin tidak sepenuhnya terkait, namun tetap memberi kontribusi positif."
                ]))

        # 💼 Pengalaman kerja
        if user_experience:
            exp_lower = user_experience.lower()
            if any(x in exp_lower for x in ["developer", "engineer", "programmer", "data", "it", "software"]):
                explain_parts.append(random_phrase([
                    "Pengalaman kerjamu sudah searah dengan tantangan di posisi ini.",
                    "Dari sisi pengalaman, kamu tampak sudah terbiasa dengan lingkungan kerja serupa."
                ]))
            elif fit_level in ["Kurang Cocok", "Tidak Cocok"]:
                explain_parts.append(random_phrase([
                    f"Pengalamanmu ({user_experience}) belum banyak bersinggungan dengan bidang ini, tapi bisa jadi titik awal untuk berkembang.",
                    f"Tampaknya pengalaman kerjamu ({user_experience}) masih di luar bidang ini, namun tetap memberi nilai tambah dalam hal analisis dan manajemen."
                ]))
            else:
                explain_parts.append(random_phrase([
                    f"Pengalamanmu ({user_experience}) memberi dasar kerja yang relevan untuk posisi ini.",
                    f"Walau tidak sepenuhnya sejalan, pengalamanmu ({user_experience}) bisa memperkaya pendekatanmu dalam pekerjaan ini."
                ]))

        # 💡 Saran pengembangan (jika kurang cocok)
        if fit_level in ["Kurang Cocok", "Tidak Cocok"]:
            missing = [
                clean_skill_name(s) for s in neighbors
                if s not in [m[0] for m in matched]
            ]
            missing = [s for s in missing if s][:4]
            if missing:
                explain_parts.append(random_phrase([
                    f"Untuk meningkatkan peluang, coba pelajari skill seperti {', '.join(missing)}.",
                    f"Kamu bisa mulai memperluas kemampuan di area {', '.join(missing)} untuk memperkuat profilmu.",
                    f"Mendalami topik seperti {', '.join(missing)} akan sangat membantu menyesuaikan diri dengan bidang ini."
                ]))

        explanation_text = " ".join(explain_parts)

        recommendations.append({
            "job": job,
            "job_title": job_title,
            "match_percent": match_percent,
            "fit_level": fit_level,
            "matched_skills": matched,
            "explanation": explanation_text
        })

    # Urutkan hasil
    recommendations.sort(key=lambda x: x["match_percent"], reverse=True)
    return recommendations[:top_n]
