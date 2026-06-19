from agent import agent

response = agent.invoke(
    {
        "messages": [
            (
                "user",
                """
repo_url:
https://github.com/lokesh046/ocr_metric

Question:
What does compute_doc_qual_score do?
"""
            )
        ]
    }
)

print(response["messages"][-1].content)