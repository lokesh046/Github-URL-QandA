# graph/graph_tools.py

import os
from typing import List, Dict, Any, Optional
from utils.repo_utils import get_repo_id
from graph.graph_store import load_graph
from graph.graph_builder import build_dependency_graph

def resolve_import(import_path: str, current_file: str, all_files: List[str]) -> Optional[str]:
    """Resolves an import path to an absolute path within the repository."""
    current_file = current_file.replace("\\", "/")
    import_path = import_path.replace("\\", "/")
    
    # If it is a relative import
    if import_path.startswith("."):
        parts = current_file.split("/")
        if len(parts) > 1:
            dir_path = "/".join(parts[:-1])
        else:
            dir_path = ""
            
        resolved_str = os.path.normpath(os.path.join(dir_path, import_path)).replace("\\", "/")
    else:
        resolved_str = import_path
        
    # Check exact match
    if resolved_str in all_files:
        return resolved_str
        
    # Try extensions
    extensions = [".tsx", ".ts", ".jsx", ".js", ".py", ".java", ".go", ".rs", ".cpp", ".c", ".h"]
    for ext in extensions:
        candidate = resolved_str + ext
        if candidate in all_files:
            return candidate
            
    # Try directory index files
    for ext in extensions:
        candidate = resolved_str + "/index" + ext
        if candidate in all_files:
            return candidate
            
    # Fallback: matching basename or trailing path
    for f in all_files:
        if f.endswith("/" + resolved_str) or f == resolved_str:
            return f
            
    return None

def find_imports(repo_url: str, file_path: str) -> List[str]:
    """Returns the imports listed in a specific file."""
    repo_id = get_repo_id(repo_url)
    graph_data = load_graph(repo_id)
    files = graph_data.get("files", {})
    
    normalized = file_path.replace("\\", "/")
    # Try exact or endswith match to resolve the file
    target_file = None
    if normalized in files:
        target_file = normalized
    else:
        for f in files:
            if f.endswith("/" + normalized) or f == normalized:
                target_file = f
                break
                
    if not target_file:
        return []
        
    return files[target_file].get("imports", [])

def find_usages(repo_url: str, symbol: str) -> List[str]:
    """Returns a list of files that import, call, or reference the given symbol."""
    repo_id = get_repo_id(repo_url)
    graph_data = load_graph(repo_id)
    files = graph_data.get("files", {})
    usages = []
    
    for file_path, meta in files.items():
        # Check imports
        imported = False
        for imp in meta.get("imports", []):
            parts = imp.replace("\\", "/").split("/")
            last_part = parts[-1] if parts else ""
            # Strip extension if present
            if "." in last_part:
                last_part = last_part.split(".")[0]
            if last_part == symbol:
                imported = True
                break
                
        # Check calls
        called = False
        for call in meta.get("calls", []):
            callee = call.get("callee", "")
            if callee == symbol or callee.endswith("." + symbol):
                called = True
                break
                
        if imported or called:
            usages.append(file_path)
            
    return usages

def trace_import_chain(repo_url: str, file_path: str) -> str:
    """Traces and formats the import chain starting from the given file path."""
    repo_id = get_repo_id(repo_url)
    graph_data = load_graph(repo_id)
    files = graph_data.get("files", {})
    all_file_paths = list(files.keys())
    
    normalized = file_path.replace("\\", "/")
    target_file = None
    if normalized in files:
        target_file = normalized
    else:
        for f in all_file_paths:
            if f.endswith("/" + normalized) or f == normalized:
                target_file = f
                break
                
    if not target_file:
        return f"File '{file_path}' not found in dependency graph."
        
    visited = set()
    chains = []
    
    def dfs(current_file, current_path):
        if current_file in visited:
            chains.append(current_path + [f"{current_file} (cycle)"])
            return
            
        visited.add(current_file)
        meta = files.get(current_file, {})
        imports = meta.get("imports", [])
        
        resolved_imports = []
        for imp in imports:
            resolved = resolve_import(imp, current_file, all_file_paths)
            if resolved:
                resolved_imports.append(resolved)
                
        if not resolved_imports:
            chains.append(current_path + [current_file])
        else:
            for resolved in resolved_imports:
                dfs(resolved, current_path + [current_file])
                
        visited.remove(current_file)
        
    dfs(target_file, [])
    
    # Format the chains as strings
    result = []
    for chain in chains:
        result.append(" \n  | \n  v \n".join(chain))
        
    if not result:
        return f"No imports found for '{file_path}'."
        
    return "\n\n--- Chain ---\n".join(result)

def trace_call_chain(repo_url: str, function_name: str) -> str:
    """Traces and formats the call graph starting from the given function name."""
    repo_id = get_repo_id(repo_url)
    graph_data = load_graph(repo_id)
    files = graph_data.get("files", {})
    
    # Build caller -> callees mapping
    call_map = {}
    for file_path, meta in files.items():
        for call in meta.get("calls", []):
            caller = call.get("caller")
            callee = call.get("callee")
            if caller and callee:
                if caller not in call_map:
                    call_map[caller] = set()
                call_map[caller].add(callee)
                
    if function_name not in call_map:
        # Check if it is called anywhere at least
        is_called = False
        for caller, callees in call_map.items():
            if function_name in callees:
                is_called = True
                break
        if is_called:
            return f"{function_name}() (leaf node, no outbound calls)"
        return f"Function '{function_name}' has no recorded call activities."
        
    visited = set()
    chains = []
    
    def dfs(current_func, current_path):
        if current_func in visited:
            chains.append(current_path + [f"{current_func}() (cycle)"])
            return
            
        visited.add(current_func)
        callees = list(call_map.get(current_func, []))
        
        if not callees:
            chains.append(current_path + [f"{current_func}()"])
        else:
            for callee in callees:
                dfs(callee, current_path + [f"{current_func}()"])
                
        visited.remove(current_func)
        
    dfs(function_name, [])
    
    result = []
    for chain in chains:
        result.append(" \n  | \n  v \n".join(chain))
        
    return "\n\n--- Call Chain ---\n".join(result)