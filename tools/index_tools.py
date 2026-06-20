# tools/index_tool.py

from tools.github_tools import (
    list_repo_files,
    get_file_content
)

from rag.chunker import chunk_file
from rag.embedder import embed_texts
from rag.indexer import add_chunk

from cache.sha_cache import (
    load_cache,
    save_cache,
    needs_reindex
)

from utils.repo_utils import get_repo_id


def index_repository(
        repo_url: str,
        branch: str = "main"
):
    """
    Index a GitHub repository into ChromaDB.
    Only new/changed files are processed.
    """

    repo_id = get_repo_id(repo_url)

    cache_path = f"./data/sha_cache/{repo_id}.json"

    cache = load_cache(cache_path)

    files = list_repo_files(
        repo_url=repo_url,
        branch=branch
    )

    all_chunks = []
    new_cache = {}

    for file in files:

        path = file["path"]
        sha = file["sha"]

        new_cache[path] = sha

        # Skip unchanged files
        if not needs_reindex(
                path,
                sha,
                cache
        ):
            continue

        print(f"Processing {path}")

        try:

            content = get_file_content(
                repo_url=repo_url,
                file_path=path,
                branch=branch
            )

            if not content:
                continue

            chunks = chunk_file(
                text=content,
                file_path=path
            )

            all_chunks.extend(
                chunks
            )

            # Build and update dependency graph in parallel
            try:
                from graph.graph_builder import build_dependency_graph
                from graph.graph_store import update_file_graph
                file_graph = build_dependency_graph(content, path)
                update_file_graph(repo_id, path, file_graph)
            except Exception as ge:
                print(f"Error building dependency graph for {path}: {ge}")

        except Exception as e:

            print(
                f"Error processing {path}: {e}"
            )

    # Clean up deleted files from graph
    try:
        from graph.graph_store import load_graph, save_graph
        graph_data = load_graph(repo_id)
        if "files" in graph_data:
            active_paths = {f["path"] for f in files}
            to_delete = [f for f in graph_data["files"] if f not in active_paths]
            if to_delete:
                for f in to_delete:
                    del graph_data["files"][f]
                save_graph(repo_id, graph_data)
    except Exception as e:
        print(f"Error cleaning up deleted files from graph: {e}")

    if len(all_chunks) == 0:

        save_cache(
            new_cache,
            cache_path
        )

        return "Repository already up-to-date."

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    embeddings = embed_texts(
        texts
    )

    add_chunk(
        chunks=all_chunks,
        embeddings=embeddings,
        repo_id=repo_id
    )

    save_cache(
        new_cache,
        cache_path
    )

    return (
        f"Indexed {len(all_chunks)} chunks "
        f"for {repo_id}"
    )