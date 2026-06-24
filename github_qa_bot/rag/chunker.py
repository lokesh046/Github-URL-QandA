
import ast
import re
import tiktoken
from rag.tree_sitter_chunker import chunk_tree_sitter
from pathlib import Path
from utils.language_map import LANGUAGE_MAP

ENCODER = tiktoken.get_encoding("cl100k_base")




def chunk_python_file(text: str, file_path: str):

    chunks = []

    try:
        tree = ast.parse(text,filename=file_path)
        lines = text.splitlines()

        for node in tree.body:
            
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):

                start = node.lineno

                end = node.end_lineno

                source = "\n".join(lines[start -1:end])

                chunks.append({
                    "text": source,
                    "file":file_path,
                    "fn_name": node.name,
                    "start_line": start
                })

    except Exception as e:
        print(f"Failed to chunk {file_path}: {e}")
        chunks.append({
            "text":text,
            "file":file_path,
            "fn_name":"full_file",
            "start_line":1
        })

    return chunks


def chunk_text_file(
    text:str,
    file_path:str,
    chunk_size:int=512,
    overlap:int=50
):

    chunks = []
    
    tokens = ENCODER.encode(text)

    step =  chunk_size - overlap

    for i  in range(0, len(tokens), step):

        chunk_token = tokens[i:i+ chunk_size]

        chunk_text = ENCODER.decode(chunk_token)

        chunks.append({
            "text":chunk_text,
            "file":file_path,
            "fn_name":"full_file",
            "start_line":1
        })
    return chunks


def chunk_file(
    text: str,
    file_path: str
):

    if file_path.endswith(".py"):
        return chunk_python_file(text,file_path)


    else:
        return chunk_text_file(text,file_path,chunk_size=1024,overlap=100)


    return []




def chunk_file(
        text: str,
        file_path: str
):

    ext = Path(
        file_path
    ).suffix.lower()

    if ext == ".py":

        return chunk_python_file(
            text,
            file_path
        )

    elif ext in LANGUAGE_MAP:

        return chunk_tree_sitter(
            text,
            file_path
        )

    else:

        return chunk_text_file(
            text,
            file_path,
            chunk_size=1024,
            overlap=100
        )