# utils/repo_utils.py

def get_repo_id(repo_url: str) -> str:
    """
    Convert:
    https://github.com/lokesh046/ocr_metric

    into:

    lokesh046_ocr_metric
    """

    repo_url = repo_url.rstrip("/")

    parts = repo_url.split("/")

    owner = parts[-2]
    repo_name = parts[-1]

    return f"{owner}_{repo_name}"