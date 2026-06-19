from pydantic import BaseModel


class QueryRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    question: str


class QueryResponse(BaseModel):
    answer: str

class SearchIndexInput(BaseModel):
    repo_url: str
    question: str

class ListRepoFilesInput(BaseModel):
    repo_url: str
    branch: str = "main"

class GetFileContentInput(BaseModel):
    repo_url: str
    file_path: str
    branch: str = "main"