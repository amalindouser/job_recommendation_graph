import sqlite3
import networkx as nx

DB_PATH = "knowledge_graph.db"

def save_graph_to_db(G, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Tabel nodes
    c.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, type TEXT, code TEXT, category TEXT, label TEXT, description TEXT
    )""")
    # Tabel edges
    c.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER, target_id INTEGER,
        relation TEXT, reason TEXT, confidence REAL,
        FOREIGN KEY(source_id) REFERENCES nodes(id),
        FOREIGN KEY(target_id) REFERENCES nodes(id)
    )""")

    # Simpan nodes
    node_ids = {}
    for n, d in G.nodes(data=True):
        c.execute("""
        INSERT INTO nodes (name, type, code, category, label, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (n, d.get("type"), d.get("code"), d.get("category"), d.get("label"), d.get("description")))
        node_ids[n] = c.lastrowid

    # Simpan edges
    for u, v, d in G.edges(data=True):
        c.execute("""
        INSERT INTO edges (source_id, target_id, relation, reason, confidence)
        VALUES (?, ?, ?, ?, ?)
        """, (node_ids[u], node_ids[v], d.get("relation"), d.get("reason"), d.get("confidence")))

    conn.commit()
    conn.close()
    print(f"Graph berhasil disimpan ke {db_path}")


def load_graph_from_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    G = nx.Graph()

    c.execute("SELECT id, name, type, code, category, label, description FROM nodes")
    nodes = c.fetchall()
    node_map = {}
    for node_id, name, ntype, code, category, label, desc in nodes:
        G.add_node(name, type=ntype, code=code, category=category, label=label, description=desc)
        node_map[node_id] = name

    c.execute("SELECT source_id, target_id, relation, reason, confidence FROM edges")
    for source_id, target_id, relation, reason, confidence in c.fetchall():
        G.add_edge(node_map[source_id], node_map[target_id],
                   relation=relation, reason=reason, confidence=confidence)

    conn.close()
    return G
