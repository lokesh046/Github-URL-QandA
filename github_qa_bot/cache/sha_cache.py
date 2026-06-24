import os
import json

def load_cache(cache_path: str):
    """
    Load SHA cache from disk

    returns:
    dict:
    """
    if not os.path.exists(cache_path):
        return {}

    with open(cache_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_cache(cache: dict, cache_path: str):


    os.makedirs(os.path.dirname(cache_path), exist_ok= True)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)

def needs_reindex(file_name:str,current_sha: str, cache: dict):

    old_sha = cache.get(file_name)

    if old_sha == current_sha:
        return False

    return True

    