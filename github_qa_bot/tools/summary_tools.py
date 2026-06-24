from tools.github_tools import (
    list_repo_files,
    get_file_content,
    download_repo_archive
)

from rag.answer_generator import generate_answer


def summarize_repo(repo_url: str):

    files = list_repo_files(repo_url)

    file_paths = [
        file["path"]
        for file in files
    ]

    planner_prompt = f"""
You are a software architect.

Given these repository files:

{file_paths}

Select at most 10 files that are most useful for understanding:

1. Project purpose
2. Tech stack
3. Folder structure
4. Main modules
5. Architecture

Return ONLY file paths.
One path per line.
"""

    response = generate_answer(planner_prompt)

    important_files = [
        line.strip()
        for line in response.split("\n")
        if line.strip()
    ]

    print("[Timing] Retrieving ZIP archive for summary (loading from cache if available)...")
    try:
        zip_archive, zip_prefix = download_repo_archive(repo_url)
        print(f"[Timing] ZIP archive retrieved successfully. Prefix: {zip_prefix}")
    except Exception as e:
        print(f"Warning: Failed to retrieve archive: {e}. Falling back to sequential HTTP requests.")
        zip_archive, zip_prefix = None, None

    context = ""

    for file_path in important_files:
        print(f"[Timing] Processing file: {file_path}")
        try:
            content = None
            if zip_archive is not None:
                try:
                    content = zip_archive.read(f"{zip_prefix}{file_path}").decode("utf-8")
                    print(f"  -> Read {file_path} from ZIP archive successfully.")
                except KeyError:
                    print(f"  -> {file_path} not found in ZIP. Falling back to HTTP.")
                    pass

            if content is None:
                content = get_file_content(
                    repo_url=repo_url,
                    file_path=file_path
                )
                print(f"  -> Fetched {file_path} from GitHub API successfully.")

            context += (
                f"\n\n===== FILE: {file_path} =====\n"
            )

            context += content[:5000]

        except Exception as e:
            print(f"  -> Error loading {file_path}: {e}")
            continue

    summary_prompt = f"""
Repository contents:

{context}

Generate a report with:

# Purpose

# Tech Stack

# Folder Structure

# Main Components

# Architecture

# Entry Points

# Important Files

Explain clearly.
"""

    return generate_answer(summary_prompt)