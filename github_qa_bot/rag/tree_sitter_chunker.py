
from pathlib import Path

from tree_sitter_language_pack import get_parser


TARGETS = {
    "function_declaration",
    "method_definition",
    "class_definition",
    "class_declaration",
    "lexical_declaration"
}


LANGUAGE_MAP = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c"
}


def get_node_name(node, text: str):

    # function greetUser(){}
    if node.kind() == "function_declaration":

        for i in range(node.child_count()):

            child = node.child(i)

            if child.kind() == "identifier":

                return text[
                    child.start_byte():
                    child.end_byte()
                ]

    # const Hero = ()=>{}
    # const Hero = ()=>{}
    elif node.kind() == "lexical_declaration":

        for i in range(node.child_count()):

            child = node.child(i)

            if child.kind() != "variable_declarator":
                continue

            identifier = None
            is_function = False

            for j in range(child.child_count()):

                grandchild = child.child(j)

                # Hero
                if grandchild.kind() == "identifier":

                    identifier = text[
                        grandchild.start_byte():
                        grandchild.end_byte()
                    ]

                # ()=>{}
                elif grandchild.kind() in (
                        "arrow_function",
                        "function"
                ):

                    is_function = True

                if identifier is not None and is_function:

                    return identifier
        return None

    # class Foo {}
    elif node.kind() in (
            "class_definition",
            "class_declaration"
    ):

        for i in range(node.child_count()):

            child = node.child(i)

            if child.kind() in (
                    "identifier",
                    "type_identifier"
            ):

                return text[
                    child.start_byte():
                    child.end_byte()
                ]

    return node.kind()
    


def traverse(
        node,
        text: str,
        file_path: str,
        chunks: list
):

    if node.kind() in TARGETS:

        chunk_text = text[
            node.start_byte():
            node.end_byte()
        ]

        fn_name = get_node_name(
            node,
            text
        )

        if fn_name is not None:

            chunks.append(
                {
                    "text": chunk_text,
                    "file": file_path,
                    "fn_name": fn_name,
                    "start_line": node.start_position().row + 1
                }
            )

    for i in range(node.child_count()):

        child = node.child(i)

        traverse(
            child,
            text,
            file_path,
            chunks
        )


def chunk_tree_sitter(
        text: str,
        file_path: str
):

    ext = Path(
        file_path
    ).suffix.lower()

    language = LANGUAGE_MAP.get(ext)

    if language is None:

        return [
            {
                "text": text,
                "file": file_path,
                "fn_name": "full_file",
                "start_line": 1
            }
        ]

    try:

        parser = get_parser(
            language
        )

        tree = parser.parse(
            text
        )

        root = tree.root_node()

        chunks = []

        traverse(
            root,
            text,
            file_path,
            chunks
        )

        if not chunks:

            chunks.append(
                {
                    "text": text,
                    "file": file_path,
                    "fn_name": "full_file",
                    "start_line": 1
                }
            )

        return chunks

    except Exception as e:

        print(
            f"Failed to chunk {file_path}: {e}"
        )

        return [
            {
                "text": text,
                "file": file_path,
                "fn_name": "full_file",
                "start_line": 1
            }
        ]