from tools.summary_tools import summarize_repo
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from models import (
    SearchIndexInput,
    ListRepoFilesInput,
    GetFileContentInput,
    SummaryRepoInput,
    FindImportsInput,
    FindUsagesInput,
    TraceImportChainInput,
    TraceCallChainInput
)

from llm.fallback_llm import  FallbackLLM
from tools.rag_tool import search_index
from tools.github_tools import (list_repo_files, get_file_content)
from graph.graph_tools import (
    find_imports,
    find_usages,
    trace_import_chain,
    trace_call_chain
)

llm = FallbackLLM()

from config import DATABASE_URL
from langgraph.checkpoint.memory import MemorySaver

pool = None
checkpointer = None

if DATABASE_URL:
    try:
        from psycopg_pool import ConnectionPool
        from psycopg.rows import dict_row
        from langgraph.checkpoint.postgres import PostgresSaver

        def check_conn(conn):
            conn.execute("SELECT 1;")

        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            max_size=10,
            timeout=5.0,
            check=check_conn,
            kwargs={
                "autocommit": True, 
                "row_factory": dict_row,
                "connect_timeout": 5
            }
        )
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        print("[Database] PostgresSaver checkpointer initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize PostgresSaver: {e}. Falling back to MemorySaver.")
        checkpointer = MemorySaver()
else:
    checkpointer = MemorySaver()

SYSTEM_PROMPT = """
You are an expert software engineer and GitHub repository assistant.

Guidelines:

1. Always begin with search_index().
2. If search results are insufficient, use list_repo_files().
3. Use get_file_content() only when exact code details are needed.
4. Never hallucinate.
5. Use summarize_repo() for overview questions.
6. Cite files and function names.
7. Base answers only on tool outputs.
8. Mention file names and function names.
9. Explain code step by step when asked.
10. If information is unavailable, say so.
11. Prefer minimal tool calls.
12. Use find_imports(), find_usages(), trace_import_chain(), or trace_call_chain() to understand repository structures, trace dependencies, find symbol references/usages, or walk function call chains.
"""


summary_tool = StructuredTool.from_function(
    func=summarize_repo,
    args_schema=SummaryRepoInput,
    description="""
Useful for summarizing an entire repository.

Input:
repo_url

Returns:
Project purpose, architecture,
folder structure and tech stack.
"""
)

search_tool = StructuredTool.from_function(
    func=search_index,
    args_schema=SearchIndexInput,
    description="""
Useful for answering questions about code.

Input:
repo_url : GitHub repository URL
question : User question

Returns relevant code chunks.
"""
)

list_tool = StructuredTool.from_function(
    func=list_repo_files,
    args_schema=ListRepoFilesInput,
    description="""
Lists all repository files.

Input:
repo_url : GitHub repository URL
branch : branch name

Returns file paths.
"""
)

file_tool = StructuredTool.from_function(
    func=get_file_content,
    args_schema=GetFileContentInput,
    description="""
Fetches the contents of a file.

Input:
repo_url : GitHub repository URL
file_path : file path
branch : branch name

Returns file contents.
"""
)

find_imports_tool = StructuredTool.from_function(
    func=find_imports,
    args_schema=FindImportsInput,
    description="""
    Useful for finding all import statements listed in a specific file.

    Input:
    repo_url : GitHub repository URL
    file_path : Relative path to the file in the repository
    """
)

find_usages_tool = StructuredTool.from_function(
    func=find_usages,
    args_schema=FindUsagesInput,
    description="""
    Useful for finding files in the repository that use, call, or import a specific symbol/function.

    Input:
    repo_url : GitHub repository URL
    symbol : Name of the function, class, or variable to find usages of
    """
)

trace_import_chain_tool = StructuredTool.from_function(
    func=trace_import_chain,
    args_schema=TraceImportChainInput,
    description="""
    Useful for tracing the import dependency chain starting from a specific file path.

    Input:
    repo_url : GitHub repository URL
    file_path : Relative path to the starting file
    """
)

trace_call_chain_tool = StructuredTool.from_function(
    func=trace_call_chain,
    args_schema=TraceCallChainInput,
    description="""
    Useful for tracing the call graph/chain of calls starting from a specific function name.

    Input:
    repo_url : GitHub repository URL
    function_name : Name of the function to trace call chains from
    """
)

tools = [
    search_tool,
    list_tool,
    file_tool,
    summary_tool,
    find_imports_tool,
    find_usages_tool,
    trace_import_chain_tool,
    trace_call_chain_tool
]


agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
    checkpointer = checkpointer
)

