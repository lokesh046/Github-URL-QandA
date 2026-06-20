# graph/graph_store.py

import os
import json
from typing import Dict, Any

DB_DIR = "./data/graph_db"

def get_db_path(repo_id: str) -> str:
    return os.path.join(DB_DIR, f"{repo_id}.json")

def load_graph(repo_id: str) -> Dict[str, Any]:
    """Loads the dependency graph for the given repository. Returns empty dict if not found."""
    db_path = get_db_path(repo_id)
    if not os.path.exists(db_path):
        return {"files": {}}
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading graph for {repo_id}: {e}")
        return {"files": {}}

def save_graph(repo_id: str, graph_data: Dict[str, Any]):
    """Saves the dependency graph for the given repository."""
    os.makedirs(DB_DIR, exist_ok=True)
    db_path = get_db_path(repo_id)
    try:
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving graph for {repo_id}: {e}")

def update_file_graph(repo_id: str, file_path: str, file_graph: Dict[str, Any]):
    """Updates the graph for a specific file in the repository's dependency graph."""
    graph_data = load_graph(repo_id)
    if "files" not in graph_data:
        graph_data["files"] = {}
    
    graph_data["files"][file_path] = file_graph
    save_graph(repo_id, graph_data)

def remove_file_graph(repo_id: str, file_path: str):
    """Removes the graph metadata of a file from the repository graph."""
    graph_data = load_graph(repo_id)
    if "files" in graph_data and file_path in graph_data["files"]:
        del graph_data["files"][file_path]
        save_graph(repo_id, graph_data)
