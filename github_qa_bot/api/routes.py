from fastapi import APIRouter, Header, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk

from api.schemas import QueryRequest, QueryResponse
from agent import agent
from tools.index_tools import index_repository
from config import GEMINI_API_KEY, OPENROUTER_API_KEY
from utils.auth import get_current_user

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_repo(
    request: QueryRequest,
    x_gemini_api_key: str = Header(default=None),
    x_openrouter_api_key: str = Header(default=None),
    current_user: dict = Depends(get_current_user)
):
    import time
    from datetime import datetime
    
    gemini_key = x_gemini_api_key or GEMINI_API_KEY
    openrouter_key = x_openrouter_api_key or OPENROUTER_API_KEY

    print(f"\n==================================================")
    print(f"[Query Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received query request from user '{current_user['username']}'.")
    print(f"  - Repo URL: {request.repo_url}")
    print(f"  - Question: '{request.question}'")
    
    t_start = time.time()
    
    t_idx = time.time()
    try:
        index_repository(request.repo_url)
    except Exception as e:
        print(f"Auto-indexing failed for {request.repo_url}: {e}")
    print(f"[Timing] [Query Flow] Auto-indexing check completed in {time.time() - t_idx:.4f}s")

    # Isolate conversation thread by prefixing user's username
    user_thread_id = f"{current_user['username']}_{request.thread_id}"

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
                "thread_id": user_thread_id,
                "gemini_api_key": gemini_key,
                "openrouter_api_key": openrouter_key
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
    try:
        print(answer)
    except Exception:
        print(answer.encode("utf-8", errors="ignore").decode("ascii", errors="ignore"))
    
    total_flow_time = time.time() - t_start
    print(f"[Query Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Output response returned to user.")
    print(f"[Timing] [Query Flow] Total processing duration: {total_flow_time:.4f}s")
    print(f"==================================================\n")
    
    return QueryResponse(
        answer=answer
    )


@router.post("/stream")
def stream_repo(
    request: QueryRequest,
    x_gemini_api_key: str = Header(default=None),
    x_openrouter_api_key: str = Header(default=None),
    current_user: dict = Depends(get_current_user)
):
    import time
    from datetime import datetime
    
    gemini_key = x_gemini_api_key or GEMINI_API_KEY
    openrouter_key = x_openrouter_api_key or OPENROUTER_API_KEY

    print(f"\n==================================================")
    print(f"[Stream Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received streaming request from user '{current_user['username']}'.")
    print(f"  - Repo URL: {request.repo_url}")
    print(f"  - Question: '{request.question}'")
    
    t_idx = time.time()
    try:
        index_repository(request.repo_url)
    except Exception as e:
        print(f"Auto-indexing failed for {request.repo_url}: {e}")
    print(f"[Timing] [Stream Flow] Auto-indexing check completed in {time.time() - t_idx:.4f}s")

    # Isolate conversation thread by prefixing user's username
    user_thread_id = f"{current_user['username']}_{request.thread_id}"

    def generate():
        t_start = time.time()
        print(f"[Timing] [Stream Flow] Starting Agent Stream...")
        
        first_chunk_received = False
        
        for item in agent.stream(
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
                    "thread_id": user_thread_id,
                    "gemini_api_key": gemini_key,
                    "openrouter_api_key": openrouter_key
                }
            },
            stream_mode="messages"
        ):
            if not first_chunk_received:
                first_chunk_received = True
                print(f"[Timing] [Stream Flow] First chunk received in {time.time() - t_start:.4f}s")
                
            if isinstance(item, tuple):
                chunk, metadata = item
                if metadata.get("langgraph_node") == "agent" and isinstance(chunk, AIMessageChunk):
                    # Only stream the text generated by the agent, skipping tool calls
                    if not chunk.tool_call_chunks:
                        content = chunk.content
                        if isinstance(content, list):
                            for text_item in content:
                                if isinstance(text_item, dict) and text_item.get("type") == "text":
                                    yield text_item["text"]
                                elif isinstance(text_item, str):
                                    yield text_item
                        elif isinstance(content, str):
                            yield content
                
        total_stream_time = time.time() - t_start
        print(f"[Stream Flow] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Output stream finished.")
        print(f"[Timing] [Stream Flow] Total streaming duration: {total_stream_time:.4f}s")
        print(f"==================================================\n")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/files")
def get_files(
    repo_url: str,
    current_user: dict = Depends(get_current_user)
):
    from tools.github_tools import list_repo_files
    from fastapi import HTTPException
    try:
        files = list_repo_files(repo_url)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/file-content")
def get_file_content_endpoint(
    repo_url: str,
    file_path: str,
    current_user: dict = Depends(get_current_user)
):
    from tools.github_tools import get_file_content
    from fastapi import HTTPException
    try:
        content = get_file_content(repo_url, file_path)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))