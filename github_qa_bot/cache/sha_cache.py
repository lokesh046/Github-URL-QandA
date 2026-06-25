import os
import json
from config import S3_STORAGE_ENABLED
from utils.s3_store import s3_exists, s3_upload, s3_download

def load_cache(cache_path: str):
    """
    Load SHA cache from R2 or local disk
    """
    filename = os.path.basename(cache_path)
    r2_key = f"sha_cache/{filename}"

    if S3_STORAGE_ENABLED and s3_exists(r2_key):
        try:
            print(f"[R2 Storage] Loading SHA cache: {r2_key}")
            cache_bytes = s3_download(r2_key)
            return json.loads(cache_bytes.decode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to load SHA cache from R2 ({r2_key}): {e}")

    if not os.path.exists(cache_path):
        return {}

    with open(cache_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_cache(cache: dict, cache_path: str):
    """
    Save SHA cache to R2 or local disk
    """
    filename = os.path.basename(cache_path)
    r2_key = f"sha_cache/{filename}"
    cache_str = json.dumps(cache, indent=4)

    if S3_STORAGE_ENABLED:
        try:
            s3_upload(cache_str.encode("utf-8"), r2_key)
            return
        except Exception as e:
            print(f"Warning: Failed to upload SHA cache to R2 ({r2_key}): {e}")

    os.makedirs(os.path.dirname(cache_path), exist_ok= True)

    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(cache_str)

def needs_reindex(file_name:str,current_sha: str, cache: dict):

    old_sha = cache.get(file_name)

    if old_sha == current_sha:
        return False

    return True

    