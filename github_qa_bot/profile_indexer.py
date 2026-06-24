import os
import time
from dotenv import load_dotenv
load_dotenv()

from tools.github_tools import list_repo_files, get_file_content
from rag.chunker import chunk_file
from rag.embedder import embed_texts
from rag.indexer import add_chunk
from cache.sha_cache import load_cache, save_cache
from utils.repo_utils import get_repo_id

def profile_indexing(repo_url: str, branch: str = None, force_reindex: bool = True):
    print(f"=== Profiling Indexing for {repo_url} ===")
    start_total = time.time()
    
    # 1. Parse URL & Cache Load
    t0 = time.time()
    repo_id = get_repo_id(repo_url)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(current_dir, "data", "sha_cache", f"{repo_id}.json")
    cache = load_cache(cache_path)
    t_cache = time.time() - t0
    print(f"[*] Cache loaded in: {t_cache:.4f}s")

    # 2. List Repository Files (GitHub API call)
    t0 = time.time()
    files = list_repo_files(repo_url=repo_url, branch=branch)
    t_list_files = time.time() - t0
    print(f"[*] Listed {len(files)} files via GitHub API in: {t_list_files:.4f}s")

    # ZIP Archive Download profiling
    t_zip_download = 0.0
    print("[*] Downloading repository archive ZIP...")
    t0 = time.time()
    try:
        from tools.github_tools import download_repo_archive
        zip_archive, zip_prefix = download_repo_archive(repo_url, branch)
        t_zip_download = time.time() - t0
        print(f"[*] Downloaded and parsed ZIP archive in: {t_zip_download:.4f}s")
    except Exception as ae:
        print(f"Warning: Failed to download archive: {ae}")
        zip_archive, zip_prefix = None, None

    all_chunks = []
    new_cache = {}
    
    total_download_time = 0.0
    total_chunk_time = 0.0
    total_graph_time = 0.0
    processed_count = 0

    print(f"\n[*] Processing files (force_reindex={force_reindex})...")
    
    for file in files:
        path = file["path"]
        sha = file["sha"]
        new_cache[path] = sha

        # Bypass cache check if force_reindex is True
        if not force_reindex:
            from cache.sha_cache import needs_reindex
            if not needs_reindex(path, sha, cache):
                continue

        processed_count += 1
        
        # A. Get File Content (Read from ZIP, fallback to API)
        t_a = time.time()
        try:
            if zip_archive is not None:
                zip_path = f"{zip_prefix}{path}"
                try:
                    content = zip_archive.read(zip_path).decode("utf-8")
                except KeyError:
                    content = get_file_content(repo_url=repo_url, file_path=path, branch=branch)
            else:
                content = get_file_content(repo_url=repo_url, file_path=path, branch=branch)
        except Exception as e:
            print(f"    [Error] Fetching content for {path}: {e}")
            continue
        total_download_time += (time.time() - t_a)

        if not content:
            continue

        # B. Chunk File
        t_b = time.time()
        chunks = chunk_file(text=content, file_path=path)
        all_chunks.extend(chunks)
        total_chunk_time += (time.time() - t_b)

        # C. Graph Construction
        t_c = time.time()
        try:
            from graph.graph_builder import build_dependency_graph
            from graph.graph_store import update_file_graph
            file_graph = build_dependency_graph(content, path)
            update_file_graph(repo_id, path, file_graph)
        except Exception:
            pass
        total_graph_time += (time.time() - t_c)

    print(f"\n[*] Processed {processed_count} files:")
    if processed_count > 0:
        print(f"    - Content extraction total: {total_download_time:.4f}s (avg: {total_download_time/processed_count:.4f}s/file)")
        print(f"    - Local chunking total:     {total_chunk_time:.4f}s (avg: {total_chunk_time/processed_count:.4f}s/file)")
        print(f"    - Graph construction total: {total_graph_time:.4f}s (avg: {total_graph_time/processed_count:.4f}s/file)")

    # 3. Clean up deleted files from graph
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
    except Exception:
        pass
    t_graph_cleanup = time.time() - t0
    print(f"[*] Graph cleanup of deleted files in: {t_graph_cleanup:.4f}s")

    # 4. Generate Embeddings (Pinecone Inference API)
    t_embed = 0.0
    t_upsert = 0.0
    if len(all_chunks) > 0:
        texts = [chunk["text"] for chunk in all_chunks]
        print(f"\n[*] Generating Pinecone embeddings for {len(all_chunks)} chunks...")
        t0 = time.time()
        embeddings = embed_texts(texts)
        t_embed = time.time() - t0
        print(f"[*] Pinecone embeddings generated in: {t_embed:.4f}s")

        # 5. Upsert to Pinecone (Pinecone Vector DB)
        print(f"[*] Upserting vectors to Pinecone index...")
        t0 = time.time()
        add_chunk(chunks=all_chunks, embeddings=embeddings, repo_id=repo_id)
        t_upsert = time.time() - t0
        print(f"[*] Pinecone upsert completed in: {t_upsert:.4f}s")
    else:
        print("\n[*] No chunks to index.")

    # 6. Save cache
    t0 = time.time()
    save_cache(new_cache, cache_path)
    t_cache_save = time.time() - t0
    
    total_time = time.time() - start_total
    print(f"\n=== Total Time Taken: {total_time:.4f}s ===")
    
    # Print summary table
    print("\n--- Performance Breakdown ---")
    print(f"{'Indexing Phase':<35} | {'Duration (s)':<15} | {'Percentage (%)':<10}")
    print("-" * 68)
    def print_row(phase, duration):
        pct = (duration / total_time) * 100 if total_time > 0 else 0
        print(f"{phase:<35} | {duration:<15.4f} | {pct:<10.1f}%")
        
    print_row("Cache Load/Save", t_cache + t_cache_save)
    print_row("List Files (GitHub API)", t_list_files)
    print_row("Download ZIP Archive", t_zip_download)
    print_row("Read Files (ZIP Extraction / Fallback)", total_download_time)
    print_row("Local Chunking", total_chunk_time)
    print_row("Graph Construction & Cleanup", total_graph_time + t_graph_cleanup)
    print_row("Pinecone Embedding Generation", t_embed)
    print_row("Pinecone Upsert", t_upsert)

if __name__ == "__main__":
    import sys
    repo_url = "https://github.com/lokesh046/neural-mind"
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    
    profile_indexing(repo_url, force_reindex=True)
