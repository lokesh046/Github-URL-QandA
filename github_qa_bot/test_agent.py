from agent import agent

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
            "thread_id": "test_thread_fresh"
        }
    }
)

print(response["messages"][-1].content)