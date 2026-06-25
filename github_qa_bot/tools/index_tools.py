# tools/index_tool.py

from config import DATA_DIR

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
        branch: str = None
):
    """
    Index a GitHub repository into Pinecone.
    Only new/changed files are processed.
    """
    import time
    start_total = time.time()

    repo_id = get_repo_id(repo_url)

    import os
    cache_path = os.path.join(DATA_DIR, "sha_cache", f"{repo_id}.json")

    cache = load_cache(cache_path)

    t0 = time.time()
    files = list_repo_files(
        repo_url=repo_url,
        branch=branch,
        use_cache=False
    )
    t_list_files = time.time() - t0
    print(f"[Timing] Listed {len(files)} files via GitHub API in {t_list_files:.4f}s")

    # 1. Check which files need to be reindexed
    files_to_reindex = []
    new_cache = {}
    for file in files:
        path = file["path"]
        sha = file["sha"]
        new_cache[path] = sha
        if needs_reindex(
                path,
                sha,
                cache
        ):
            files_to_reindex.append(file)

    # 2. If no files need reindexing, save cache and return immediately
    if len(files_to_reindex) == 0:
        save_cache(
            new_cache,
            cache_path
        )
        print(f"[Timing] Indexing finished. Total time: {time.time() - start_total:.4f}s (Cache up-to-date)")
        return "Repository already up-to-date."

    # 3. Only download the ZIP archive if files actually need to be indexed
    print(f"[Timing] {len(files_to_reindex)} files need indexing. Downloading ZIP archive...")
    t0 = time.time()
    try:
        from tools.github_tools import download_repo_archive
        zip_archive, zip_prefix = download_repo_archive(repo_url, branch, force_download=True)
        t_zip_download = time.time() - t0
        print(f"[Timing] Downloaded ZIP archive in {t_zip_download:.4f}s")
    except Exception as ae:
        print(f"Warning: Failed to download repository archive, falling back to sequential files API. Error: {ae}")
        zip_archive, zip_prefix = None, None
        t_zip_download = 0.0

    all_chunks = []

    t_content_total = 0.0
    t_chunk_total = 0.0
    t_graph_total = 0.0
    processed_count = 0

    for file in files_to_reindex:

        path = file["path"]
        print(f"Processing {path}")
        processed_count += 1

        try:
            t_start = time.time()
            if zip_archive is not None:
                zip_path = f"{zip_prefix}{path}"
                try:
                    content = zip_archive.read(zip_path).decode("utf-8")
                except KeyError:
                    content = get_file_content(
                        repo_url=repo_url,
                        file_path=path,
                        branch=branch
                    )
            else:
                content = get_file_content(
                    repo_url=repo_url,
                    file_path=path,
                    branch=branch
                )
            t_content_total += (time.time() - t_start)

            if not content:
                continue

            t_start = time.time()
            chunks = chunk_file(
                text=content,
                file_path=path
            )
            all_chunks.extend(
                chunks
            )
            t_chunk_total += (time.time() - t_start)

            # Build and update dependency graph
            t_start = time.time()
            try:
                from graph.graph_builder import build_dependency_graph
                from graph.graph_store import update_file_graph
                file_graph = build_dependency_graph(content, path)
                update_file_graph(repo_id, path, file_graph)
            except Exception as ge:
                print(f"Error building dependency graph for {path}: {ge}")
            t_graph_total += (time.time() - t_start)

        except Exception as e:
            print(
                f"Error processing {path}: {e}"
            )

    print(f"[Timing] File loop finished. Processed {processed_count} files.")
    if processed_count > 0:
        print(f"  - File Content retrieval: {t_content_total:.4f}s")
        print(f"  - File Chunking:          {t_chunk_total:.4f}s")
        print(f"  - Graph Construction:     {t_graph_total:.4f}s")

    # Clean up deleted files from graph
    t0 = time.time()
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
    t_graph_cleanup = time.time() - t0

    if len(all_chunks) == 0:
        save_cache(
            new_cache,
            cache_path
        )
        print(f"[Timing] Indexing finished. Total time: {time.time() - start_total:.4f}s (Cache up-to-date)")
        return "Repository already up-to-date."

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    t0 = time.time()
    embeddings = embed_texts(
        texts
    )
    t_embed = time.time() - t0
    print(f"[Timing] Generated Pinecone embeddings in {t_embed:.4f}s")

    t0 = time.time()
    add_chunk(
        chunks=all_chunks,
        embeddings=embeddings,
        repo_id=repo_id
    )
    t_upsert = time.time() - t0
    print(f"[Timing] Upserted vectors to Pinecone in {t_upsert:.4f}s")

    save_cache(
        new_cache,
        cache_path
    )

    total_time = time.time() - start_total
    print(f"[Timing] Indexing complete! Total time: {total_time:.4f}s")

    return (
        f"Indexed {len(all_chunks)} chunks "
        f"for {repo_id}"
    )