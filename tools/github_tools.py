from dotenv import main
from github import Github
from config import GITHUB_TOKEN


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

    return owner,repo_name


def list_repo_files(repo_url: str, branch: str = "main"):
    """
    Return list of .py .md .json .yaml files with SHA.
    """

    try:
        owner, repo_name = parse_repo_url(repo_url)

        repo = g.get_repo(f"{owner}/{repo_name}")

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

            try:
                blob = repo.get_contents(item.path, ref=branch)

                # Skip files >100 KB
                if isinstance(blob, list):
                    continue

                if blob.size > 100 * 1024:
                    continue

                if item.type == "blob" and item.path.endswith(ALLOWED_EXTENSIONS):
                    file_details.append({
                        "path":item.path,
                        "sha":item.sha
                    })
            except Exception as e:
                print(f"Error processing file {item.path}: {e}")

        return file_details

    except Exception as e:
        raise RuntimeError(f"Failed to list files : {str(e)}")


def get_file_content(repo_url: str, file_path: str, branch: str = "main"):
    """
    Return content of a specific file.
    """
    try:
        owner, repo_name = parse_repo_url(repo_url)

        repo = g.get_repo(f"{owner}/{repo_name}")

        file = repo.get_contents(file_path, ref=branch)

        return file.decoded_content.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to get file content : {str(e)}")
