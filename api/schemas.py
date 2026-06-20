from pydantic import BaseModel


class QueryRequest(BaseModel):

    repo_url: str
    question: str
    thread_id: str = "default"


class QueryResponse(BaseModel):

    answer: str





