# utils/hash_utils.py

import hashlib


def generate_chunk_id(
        repo_id: str,
        file_path: str,
        fn_name: str,
        text: str
) -> str:
    """
    Generate deterministic chunk IDs.
    """

    key = (
        repo_id
        + file_path
        + str(fn_name)
        + text
    )

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()