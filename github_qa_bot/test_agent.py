from agent import agent

import uuid
response = agent.invoke(
    {
        "messages": [
            (
                "user",
                """
repo_url:
https://github.com/lokesh046/neural-mind

Question:
give me a summary about this repo
"""
            )
        ]
    },
    config={
        "configurable": {
            "thread_id": f"test_thread_{uuid.uuid4().hex[:8]}"
        }
    }
)

print(response["messages"][-1].content)