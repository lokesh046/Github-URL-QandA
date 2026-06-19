from tools.github_tools import list_repo_files,get_file_content

repo_url = "https://github.com/lokesh046/portfolio"

files = list_repo_files(repo_url)

print(files[:10])


content = get_file_content(
    repo_url,
    "README.md"
)

print(content)
