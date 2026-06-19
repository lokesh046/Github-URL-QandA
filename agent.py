from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate

from models import (
    SearchIndexInput,
    ListRepoFilesInput,
    GetFileContentInput
)

from tools.rag_tool import search_index
from tools.github_tools import (list_repo_files, get_file_content)

from config import GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2
)


SYSTEM_PROMPT = """
You are a GitHub repository assistant.

When answering questions:

1. Prefer search_index() first.
2. Use list_repo_files() if structure is needed.
3. Use get_file_content() if exact implementation details are required.
4. Base answers only on retrieved code.
5. Cite file names and function names.
"""



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

tools = [
    search_tool,
    list_tool,
    file_tool
]


agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT
)

