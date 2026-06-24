# graph/language_rules.py

LANGUAGE_RULES = {
    "javascript": {
        "imports": ["import_statement"],
        "functions": ["function_declaration", "method_definition", "lexical_declaration", "variable_declaration"],
        "calls": ["call_expression"]
    },
    "typescript": {
        "imports": ["import_statement"],
        "functions": ["function_declaration", "method_definition", "lexical_declaration", "variable_declaration"],
        "calls": ["call_expression"]
    },
    "tsx": {
        "imports": ["import_statement"],
        "functions": ["function_declaration", "method_definition", "lexical_declaration", "variable_declaration"],
        "calls": ["call_expression"]
    },
    "python": {
        "imports": ["import_statement", "import_from_statement"],
        "functions": ["function_definition"],
        "calls": ["call"]
    },
    "java": {
        "imports": ["import_declaration"],
        "functions": ["method_declaration"],
        "calls": ["method_invocation"]
    },
    "go": {
        "imports": ["import_declaration"],
        "functions": ["function_declaration", "method_declaration"],
        "calls": ["call_expression"]
    },
    "rust": {
        "imports": ["use_declaration"],
        "functions": ["function_item"],
        "calls": ["call_expression"]
    },
    "cpp": {
        "imports": ["preproc_include"],
        "functions": ["function_definition"],
        "calls": ["call_expression"]
    },
    "c": {
        "imports": ["preproc_include"],
        "functions": ["function_definition"],
        "calls": ["call_expression"]
    }
}
