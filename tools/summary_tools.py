from tools.github_tools import (
    list_repo_files,
    get_file_content
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

    context = ""

    for file_path in important_files:

        try:

            content = get_file_content(
                repo_url=repo_url,
                file_path=file_path
            )

            context += (
                f"\n\n===== FILE: {file_path} =====\n"
            )

            context += content[:5000]

        except Exception:

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