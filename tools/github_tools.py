from dotenv import main
from github import Github
from config import GITHUB_TOKEN
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


def list_repo_files(repo_url: str, branch: str = None):
    """
    Return list of .py .md .json .yaml files with SHA.
    """

    try:
        owner, repo_name = parse_repo_url(repo_url)

        repo = g.get_repo(f"{owner}/{repo_name}")

        if not branch:
            branch = repo.default_branch

        tree = repo.get_git_tree(branch, recursive=True)

        ALLOWED_EXTENSIONS = (
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".c",
            ".cs",
            ".md",
            ".json",
            ".yaml",
            ".yml"
        )

        file_details = []

        for item in tree.tree:
            if item.type == "blob" and item.path.endswith(ALLOWED_EXTENSIONS):
                # GitTree objects contain the size field directly (in bytes)
                size = getattr(item, "size", 0) or 0
                if size > 100 * 1024:
                    continue

                file_details.append({
                    "path": item.path,
                    "sha": item.sha
                })

        return file_details

    except Exception as e:
        raise RuntimeError(f"Failed to list files : {str(e)}")


def get_file_content(repo_url: str, file_path: str, branch: str = None):
    """
    Return content of a specific file.
    """
    try:
        owner, repo_name = parse_repo_url(repo_url)

        repo = g.get_repo(f"{owner}/{repo_name}")

        if not branch:
            branch = repo.default_branch

        file = repo.get_contents(file_path, ref=branch)

        return file.decoded_content.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to get file content : {str(e)}")


def download_repo_archive(repo_url: str, branch: str = None) -> tuple[zipfile.ZipFile, str]:
    """
    Download the repository archive as a ZIP file.
    Returns the ZipFile object and the top-level directory prefix inside the archive.
    """
    try:
        owner, repo_name = parse_repo_url(repo_url)
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        if not branch:
            branch = repo.default_branch
            
        # Get archive link (Redirect URL to S3)
        archive_url = repo.get_archive_link("zipball", ref=branch)
        
        # Download archive
        response = requests.get(archive_url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download archive: status code {response.status_code}")
            
        z = zipfile.ZipFile(io.BytesIO(response.content))
        prefix = z.namelist()[0]
        
        return z, prefix
    except Exception as e:
        raise RuntimeError(f"Failed to download repository archive: {str(e)}")
