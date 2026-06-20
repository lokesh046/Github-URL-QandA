from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import QueryRequest, QueryResponse
from agent import agent
from tools.index_tools import index_repository


router = APIRouter()


@router.post("/query",response_model=QueryResponse)
def query_repo(
    request: QueryRequest
):
    import time
    from datetime import datetime
    print(f"\n==================================================")
    print(f"[Query Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received query request from user.")
    print(f"  - Repo URL: {request.repo_url}")
    print(f"  - Question: '{request.question}'")
    
    t_start = time.time()
    
    t_idx = time.time()
    try:
        index_repository(request.repo_url)
    except Exception as e:
        print(f"Auto-indexing failed for {request.repo_url}: {e}")
    print(f"[Timing] [Query Flow] Auto-indexing check completed in {time.time() - t_idx:.4f}s")

    print(f"[Timing] [Query Flow] Invoking LangGraph QA Agent...")
    t_agent = time.time()
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
    t_agent_duration = time.time() - t_agent
    print(f"[Timing] [Query Flow] LangGraph Agent completed in {t_agent_duration:.4f}s")
    
    content = response["messages"][-1].content
    
    if isinstance(content, list):
        answer = "\n".join(item["text"] for item in content if item["type"] == "text")
    else:
        answer = content
    
    print("ANSWER:")
    print(answer)
    print(type(answer))
    
    total_flow_time = time.time() - t_start
    print(f"[Query Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Output response returned to user.")
    print(f"[Timing] [Query Flow] Total processing duration: {total_flow_time:.4f}s")
    print(f"==================================================\n")
    
    return QueryResponse(
        answer=answer
    )

@router.post("/stream")
def stream_repo(request: QueryRequest):
    import time
    from datetime import datetime
    print(f"\n==================================================")
    print(f"[Stream Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received streaming request from user.")
    print(f"  - Repo URL: {request.repo_url}")
    print(f"  - Question: '{request.question}'")
    
    t_idx = time.time()
    try:
        index_repository(request.repo_url)
    except Exception as e:
        print(f"Auto-indexing failed for {request.repo_url}: {e}")
    print(f"[Timing] [Stream Flow] Auto-indexing check completed in {time.time() - t_idx:.4f}s")

    def generate():
        t_start = time.time()
        print(f"[Timing] [Stream Flow] Starting Agent Stream...")
        
        first_chunk_received = False
        
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
            },
            stream_mode="values"
        ):
            if not first_chunk_received:
                first_chunk_received = True
                print(f"[Timing] [Stream Flow] First chunk received in {time.time() - t_start:.4f}s")
                
            content = chunk["messages"][-1].content

            if isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        yield item["text"]
            else:
                yield content
                
        total_stream_time = time.time() - t_start
        print(f"[Stream Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Output stream finished.")
        print(f"[Timing] [Stream Flow] Total streaming duration: {total_stream_time:.4f}s")
        print(f"==================================================\n")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )