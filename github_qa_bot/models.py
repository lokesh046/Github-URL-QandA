from pydantic import BaseModel


class QueryRequest(BaseModel):
    repo_url: str
    branch: str = None
    question: str


class QueryResponse(BaseModel):
    answer: str

class SearchIndexInput(BaseModel):
    repo_url: str
    question: str

class ListRepoFilesInput(BaseModel):
    repo_url: str
    branch: str = None

class GetFileContentInput(BaseModel):
    repo_url: str
    file_path: str
    branch: str = None

class SummaryRepoInput(BaseModel):
    repo_url: str


class FindImportsInput(BaseModel):
    repo_url: str
    file_path: str


class FindUsagesInput(BaseModel):
    repo_url: str
    symbol: str


class TraceImportChainInput(BaseModel):
    repo_url: str
    file_path: str


class TraceCallChainInput(BaseModel):
    repo_url: str
    function_name: str