# app.py
from flask import Flask, render_template, request
from knowledge_graph.build_graph import build_graph
from recommender import score_user

app = Flask(__name__)

# Build graph once at startup (rebuild periodically or on demand if DB updates frequently)
G = build_graph()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    nama = request.form.get("nama", "").strip()
    skills_raw = request.form.get("skills", "")
    education = request.form.get("education", "")
    experience = request.form.get("experience", "")

    # parse skills by comma
    user_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # get recommendations
    results = score_user(G, user_skills, user_education=education, user_experience=experience, top_n=10)

    # normalize output for template: matched_skills => list of (skill,weight)
    for r in results:
        # r already structured
        pass

    return render_template('results.html', nama=nama or "User", results=results)

if __name__ == '__main__':
    app.run(debug=True)
