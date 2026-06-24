# graph/graph_builder.py

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from tree_sitter_language_pack import get_parser

from graph.language_rules import LANGUAGE_RULES

LANGUAGE_MAP = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".py": "python",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "cpp"
}

def extract_import_paths(node, text: str, language: str) -> List[str]:
    node_text = text[node.start_byte():node.end_byte()].strip()
    
    if language in ("javascript", "typescript", "tsx"):
        paths = []
        for i in range(node.child_count()):
            child = node.child(i)
            if child.kind() == "string":
                val = text[child.start_byte():child.end_byte()]
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                paths.append(val)
        return paths
    
    elif language == "python":
        paths = []
        if node.kind() == "import_statement":
            def find_dotted_names(n):
                if n.kind() == "dotted_name":
                    return [text[n.start_byte():n.end_byte()]]
                res = []
                for idx in range(n.child_count()):
                    res.extend(find_dotted_names(n.child(idx)))
                return res
            paths.extend(find_dotted_names(node))
        elif node.kind() == "import_from_statement":
            for idx in range(node.child_count()):
                child = node.child(idx)
                if child.kind() in ("dotted_name", "relative_import"):
                    paths.append(text[child.start_byte():child.end_byte()])
                    break
        return paths

    elif language == "java":
        for idx in range(node.child_count()):
            child = node.child(idx)
            if child.kind() in ("scoped_identifier", "identifier"):
                return [text[child.start_byte():child.end_byte()]]
        return []

    elif language == "go":
        paths = []
        def find_strings(n):
            if n.kind() == "string_literal":
                val = text[n.start_byte():n.end_byte()]
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                return [val]
            res = []
            for idx in range(n.child_count()):
                res.extend(find_strings(n.child(idx)))
            return res
        paths.extend(find_strings(node))
        return paths

    elif language == "rust":
        if node_text.startswith("use "):
            path = node_text[4:].rstrip(";").strip()
            return [path]
        return []

    elif language in ("cpp", "c"):
        for idx in range(node.child_count()):
            child = node.child(idx)
            if child.kind() in ("system_lib_string", "string_literal"):
                val = text[child.start_byte():child.end_byte()]
                if (val.startswith('"') and val.endswith('"')) or (val.startswith('<') and val.endswith('>')):
                    val = val[1:-1]
                return [val]
        return []

    return []

def extract_function_name(node, text: str, language: str) -> Optional[str]:
    if language in ("javascript", "typescript", "tsx"):
        if node.kind() in ("function_declaration", "method_definition"):
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() in ("identifier", "property_identifier"):
                    return text[child.start_byte():child.end_byte()]
        
        elif node.kind() in ("lexical_declaration", "variable_declaration"):
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "variable_declarator":
                    identifier = None
                    is_func = False
                    for j in range(child.child_count()):
                        grandchild = child.child(j)
                        if grandchild.kind() == "identifier":
                            identifier = text[grandchild.start_byte():grandchild.end_byte()]
                        elif grandchild.kind() in ("arrow_function", "function"):
                            is_func = True
                    if identifier and is_func:
                        return identifier
            return None

    elif language == "python":
        if node.kind() == "function_definition":
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "identifier":
                    return text[child.start_byte():child.end_byte()]

    elif language == "java":
        if node.kind() == "method_declaration":
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "identifier":
                    return text[child.start_byte():child.end_byte()]

    elif language == "go":
        if node.kind() in ("function_declaration", "method_declaration"):
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "identifier":
                    return text[child.start_byte():child.end_byte()]

    elif language == "rust":
        if node.kind() == "function_item":
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "identifier":
                    return text[child.start_byte():child.end_byte()]

    elif language in ("cpp", "c"):
        if node.kind() == "function_definition":
            declarator = None
            for i in range(node.child_count()):
                child = node.child(i)
                if child.kind() == "function_declarator":
                    declarator = child
                    break
            if declarator:
                def find_identifier(n):
                    if n.kind() == "identifier":
                        return text[n.start_byte():n.end_byte()]
                    for j in range(n.child_count()):
                        res = find_identifier(n.child(j))
                        if res:
                            return res
                    return None
                return find_identifier(declarator)
                
    return None

def extract_callee_name(node, text: str, language: str) -> Optional[str]:
    if node.child_count() > 0:
        callee_node = node.child(0)
        if callee_node.kind() in ("identifier", "property_identifier", "field_identifier"):
            return text[callee_node.start_byte():callee_node.end_byte()]
        
        curr = callee_node
        while curr.kind() in ("member_expression", "attribute", "selector_expression", "field_expression", "scoped_identifier"):
            if curr.child_count() > 0:
                curr = curr.child(curr.child_count() - 1)
            else:
                break
        if curr.kind() in ("identifier", "property_identifier", "field_identifier"):
            return text[curr.start_byte():curr.end_byte()]
        
        return text[callee_node.start_byte():callee_node.end_byte()].strip()
    return None

def traverse(node, text: str, language: str, rules: dict, state: dict):
    node_kind = node.kind()
    func_name = None
    
    # Extract imports
    if node_kind in rules.get("imports", []):
        imported_paths = extract_import_paths(node, text, language)
        state["imports"].extend(imported_paths)
        
    # Extract function definitions
    if node_kind in rules.get("functions", []):
        func_name = extract_function_name(node, text, language)
        if func_name:
            state["functions"].append(func_name)
            state["caller_stack"].append(func_name)
            
    # Extract calls
    if node_kind in rules.get("calls", []):
        callee = extract_callee_name(node, text, language)
        if callee:
            caller = state["caller_stack"][-1] if state["caller_stack"] else "<global>"
            state["calls"].append({
                "caller": caller,
                "callee": callee
            })
            
    # Recurse to children
    for i in range(node.child_count()):
        traverse(node.child(i), text, language, rules, state)
        
    # Pop caller function name from stack if we pushed it
    if func_name and state["caller_stack"] and state["caller_stack"][-1] == func_name:
        state["caller_stack"].pop()

def build_dependency_graph(text: str, file_path: str) -> Dict[str, Any]:
    """Parses text using Tree-sitter and returns import, function, and call graph meta-information."""
    ext = Path(file_path).suffix.lower()
    language = LANGUAGE_MAP.get(ext)
    
    default_graph = {
        "file": file_path,
        "imports": [],
        "functions": [],
        "calls": []
    }
    
    if not language or language not in LANGUAGE_RULES:
        return default_graph
        
    try:
        parser = get_parser(language)
        tree = parser.parse(text)
        root = tree.root_node()
        
        rules = LANGUAGE_RULES[language]
        state = {
            "imports": [],
            "functions": [],
            "calls": [],
            "caller_stack": []
        }
        
        traverse(root, text, language, rules, state)
        
        return {
            "file": file_path,
            "imports": list(set(state["imports"])),  # deduplicate imports
            "functions": list(set(state["functions"])),
            "calls": state["calls"]
        }
    except Exception as e:
        print(f"Failed to build graph for {file_path}: {e}")
        return default_graph
