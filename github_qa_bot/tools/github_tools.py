from dotenv import main
from github import Github
from config import GITHUB_TOKEN, DATA_DIR, S3_STORAGE_ENABLED
from utils.s3_store import s3_exists, s3_upload, s3_download
import requests
import zipfile
import io


g = Github(GITHUB_TOKEN)


def parse_repo_url(repo_url: str):
    """
    Extract owner and repo name from GitHub URL.
    Example:
    https://github.com/langchain-ai/langchain
    =>
    ('langchain-ai', 'langchain')
    """
    parts = repo_url.rstrip("/").split("/")

    if len(parts) <= 2 or parts[2] != "github.com":
        raise ValueError(f"Invalie Github url{parts} please use the format  :https://github.com/<owner>/<repo>")


    owner = parts[-2]
    repo_name = parts[-1]

    return owner, repo_name


def list_repo_files(repo_url: str, branch: str = None, use_cache: bool = True):
    """
    Return list of source files (e.g., .py, .js, .jsx, etc.).
    Tries to read from the locally cached ZIP archive first for maximum efficiency if use_cache is True.
    If not cached or use_cache is False, falls back to the remote GitHub API to get real Git SHAs.
    """
    import os
    import zipfile
    
    ALLOWED_EXTENSIONS = (
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go",
        ".rs", ".cpp", ".c", ".cs", ".md", ".json", ".yaml", ".yml"
    )

    try:
        owner, repo_name = parse_repo_url(repo_url)
        repo_id = f"{owner}_{repo_name}"

        # Define project root and local cache path
        archive_path = os.path.join(DATA_DIR, "archives", f"{repo_id}.zip")

        # Try Cloudflare R2 / S3 first if enabled
        r2_key = f"archives/{repo_id}.zip"
        if use_cache and S3_STORAGE_ENABLED and s3_exists(r2_key):
            print(f"[Cache Hit] Listing files from R2 ZIP archive: {r2_key}")
            zip_bytes = s3_download(r2_key)
            file_details = []
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                prefix = z.namelist()[0]
                for name in z.namelist():
                    if name.endswith("/") or not name.startswith(prefix):
                        continue
                    rel_path = name[len(prefix):]
                    if not rel_path:
                        continue
                    if rel_path.endswith(ALLOWED_EXTENSIONS):
                        file_details.append({
                            "path": rel_path,
                            "sha": ""
                        })
            return file_details

        # Try local ZIP archive second
        if use_cache and os.path.exists(archive_path):
            print(f"[Cache Hit] Listing files from local ZIP archive: {archive_path}")
            file_details = []
            with zipfile.ZipFile(archive_path) as z:
                prefix = z.namelist()[0]
                for name in z.namelist():
                    if name.endswith("/") or not name.startswith(prefix):
                        continue
                    rel_path = name[len(prefix):]
                    if not rel_path:
                        continue
                    if rel_path.endswith(ALLOWED_EXTENSIONS):
                        file_details.append({
                            "path": rel_path,
                            "sha": "" # SHA not needed for visual tree rendering
                        })
            return file_details

        # Fallback to GitHub API
        print(f"[Cache Miss] Listing files from remote GitHub API for {owner}/{repo_name}...")
        repo = g.get_repo(f"{owner}/{repo_name}")
        if not branch:
            branch = repo.default_branch

        tree = repo.get_git_tree(branch, recursive=True)
        file_details = []

        for item in tree.tree:
            if item.type == "blob" and item.path.endswith(ALLOWED_EXTENSIONS):
                size = getattr(item, "size", 0) or 0
                if size > 100 * 1024:
                    continue

                file_details.append({
                    "path": item.path,
                    "sha": item.sha
                })

        return file_details

    except Exception as e:
        raise RuntimeError(f"Failed to list files: {str(e)}")


def get_file_content(repo_url: str, file_path: str, branch: str = None):
    """
    Return content of a specific file.
    Tries to read from the locally cached ZIP archive first for maximum efficiency.
    If not cached, falls back to the remote GitHub API.
    """
    import os
    import zipfile
    try:
        owner, repo_name = parse_repo_url(repo_url)
        repo_id = f"{owner}_{repo_name}"

        # Define project root and local cache path
        archive_path = os.path.join(DATA_DIR, "archives", f"{repo_id}.zip")

        # Try Cloudflare R2 / S3 first if enabled
        r2_key = f"archives/{repo_id}.zip"
        if S3_STORAGE_ENABLED and s3_exists(r2_key):
            print(f"[Cache Hit] Reading content of '{file_path}' from R2 ZIP archive: {r2_key}")
            zip_bytes = s3_download(r2_key)
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                prefix = z.namelist()[0]
                zip_file_path = prefix + file_path
                if zip_file_path in z.namelist():
                    with z.open(zip_file_path) as f:
                        return f.read().decode("utf-8")

        # Try local ZIP archive second
        if os.path.exists(archive_path):
            print(f"[Cache Hit] Reading content of '{file_path}' from local ZIP archive: {archive_path}")
            with zipfile.ZipFile(archive_path) as z:
                prefix = z.namelist()[0]
                zip_file_path = prefix + file_path
                if zip_file_path in z.namelist():
                    with z.open(zip_file_path) as f:
                        return f.read().decode("utf-8")

        # Fallback to GitHub API
        print(f"[Cache Miss] Fetching content of '{file_path}' from remote GitHub API...")
        repo = g.get_repo(f"{owner}/{repo_name}")
        if not branch:
            branch = repo.default_branch

        file = repo.get_contents(file_path, ref=branch)
        return file.decoded_content.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to get file content: {str(e)}")


def download_repo_archive(repo_url: str, branch: str = None, force_download: bool = False) -> tuple[zipfile.ZipFile, str]:
    """
    Download the repository archive as a ZIP file and cache it locally or upload to cloud.
    Returns the ZipFile object and the top-level directory prefix inside the archive.
    """
    import os
    try:
        owner, repo_name = parse_repo_url(repo_url)
        repo_id = f"{owner}_{repo_name}"
        r2_key = f"archives/{repo_id}.zip"

        # Try R2 cache first
        if not force_download and S3_STORAGE_ENABLED and s3_exists(r2_key):
            print(f"[Timing] Loading ZIP archive from R2 cache: {r2_key}")
            zip_bytes = s3_download(r2_key)
            z = zipfile.ZipFile(io.BytesIO(zip_bytes))
            prefix = z.namelist()[0]
            return z, prefix

        # Define project root and local cache path
        archive_dir = os.path.join(DATA_DIR, "archives")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, f"{repo_id}.zip")

        # If cache exists and we aren't forcing a download, read from local disk
        if not force_download and os.path.exists(archive_path):
            print(f"[Timing] Loading ZIP archive from local cache: {archive_path}")
            z = zipfile.ZipFile(archive_path)
            prefix = z.namelist()[0]
            return z, prefix

        repo = g.get_repo(f"{owner}/{repo_name}")
        
        if not branch:
            branch = repo.default_branch
            
        # Get archive link (Redirect URL to S3)
        archive_url = repo.get_archive_link("zipball", ref=branch)
        
        # Download archive
        print(f"[Timing] Downloading remote ZIP archive from GitHub...")
        response = requests.get(archive_url, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download archive: status code {response.status_code}")
            
        # Upload to R2 if enabled
        if S3_STORAGE_ENABLED:
            s3_upload(response.content, r2_key)
            z = zipfile.ZipFile(io.BytesIO(response.content))
        else:
            # Save to local cache
            with open(archive_path, "wb") as f:
                f.write(response.content)
            print(f"[Timing] ZIP archive saved to local cache: {archive_path}")
            z = zipfile.ZipFile(archive_path)
            
        prefix = z.namelist()[0]
        return z, prefix
    except Exception as e:
        raise RuntimeError(f"Failed to download repository archive: {str(e)}")
