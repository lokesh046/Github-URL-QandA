def format_chunks(chunks):

    context = []

    for i, chunk in enumerate(chunks, start=1):

        context.append(
            f"""
Chunk {i}

File: {chunk["file"]}
Function: {chunk["fn_name"]}
Line: {chunk["start_line"]}

{chunk["text"]}
"""
        )

    return "\n\n".join(context)