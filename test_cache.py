from cache.sha_cache import load_cache, save_cache, needs_reindex


cache_path = r"C:\Users\lokes\OneDrive\Desktop\github_qa_bot\data\sha_cache.json"

cache = {
    "quality.py": "abc123",
     "metric.py": "defd56"
}

save_cache(cache,cache_path)

loaded_cache = load_cache(cache_path)

print("loaded cache:")
print(loaded_cache)

print()


print(
    needs_reindex(
        "quality.py",
        "abc123",
        loaded_cache
    )
)

print(
    needs_reindex(
        "metrics.py",
        "defd56",
        loaded_cache
    )
)



