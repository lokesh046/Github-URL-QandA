# graph/graph_store.py

import os
import json
from typing import Dict, Any

from config import DATA_DIR, S3_STORAGE_ENABLED
from utils.s3_store import s3_exists, s3_upload, s3_download

DB_DIR = os.path.join(DATA_DIR, "graph_db")

def get_db_path(repo_id: str) -> str:
    return os.path.join(DB_DIR, f"{repo_id}.json")

def load_graph(repo_id: str) -> Dict[str, Any]:
    """Loads the dependency graph for the given repository. Returns empty dict if not found."""
    r2_key = f"graph_db/{repo_id}.json"

    if S3_STORAGE_ENABLED and s3_exists(r2_key):
        try:
            print(f"[R2 Storage] Loading dependency graph: {r2_key}")
            graph_bytes = s3_download(r2_key)
            return json.loads(graph_bytes.decode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to load graph from R2 ({r2_key}): {e}")

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
    r2_key = f"graph_db/{repo_id}.json"
    graph_str = json.dumps(graph_data, indent=2, ensure_ascii=False)

    if S3_STORAGE_ENABLED:
        try:
            s3_upload(graph_str.encode("utf-8"), r2_key)
            return
        except Exception as e:
            print(f"Warning: Failed to upload graph to R2 ({r2_key}): {e}")

    os.makedirs(DB_DIR, exist_ok=True)
    db_path = get_db_path(repo_id)
    try:
        with open(db_path, "w", encoding="utf-8") as f:
            f.write(graph_str)
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
