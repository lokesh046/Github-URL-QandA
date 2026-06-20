from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import QueryRequest, QueryResponse
from agent import agent


router = APIRouter()


@router.post("/query",response_model=QueryResponse)
def query_repo(
    request: QueryRequest
):
    response = agent.invoke(
    {
        "messages": [
            (
                "user",
                f"""
Repository:

{request.repo_url}

Question:

{request.question}
"""
            )
        ]
    },
    config={
        "configurable": {
            "thread_id": request.thread_id
        }
    }
)
    
    content = response["messages"][-1].content
    
    if isinstance(content, list):
        answer = "\n".join(item["text"] for item in content if item["type"] == "text")
    else:
        answer = content
    
    print("ANSWER:")
    print(answer)
    print(type(answer))
    return QueryResponse(
        answer=answer
    )

@router.post("/stream")
def stream_repo(request: QueryRequest):

    def generate():

        for chunk in agent.stream(
            {
                "messages": [
                    (
                        "user",
                        f"""
Repository:

{request.repo_url}

Question:

{request.question}
"""
                    )
                ]
            },
            config={
                "configurable": {
                    "thread_id": "default"
                }
            }
        ,stream_mode="values"):
            print("chunk",chunk)

            content = chunk["messages"][-1].content

            if isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        yield item["text"]
            else:
                yield content

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )