from rag.tree_sitter_chunker import chunk_tree_sitter

text = """
const Hero = () => {

    const handleIncrement = () => {

    }

    function greetUser() {

    }

}
"""

chunks = chunk_tree_sitter(
    text,
    "Hero.tsx"
)

for chunk in chunks:

    print("-" * 50)

    print("Name :", chunk["fn_name"])

    print("Line :", chunk["start_line"])

    print(chunk["text"])
    