# test_dependency_graph.py

import os
import sys
from dotenv import load_dotenv
load_dotenv()

from graph.graph_builder import build_dependency_graph
from graph.graph_store import update_file_graph
from graph.graph_tools import find_imports, find_usages, trace_import_chain, trace_call_chain
from agent import agent

# Set up a mock repo graph
repo_url = "https://github.com/test-user/dependency-test-repo"
repo_id = "test-user_dependency-test-repo"

# Mock file structures
files_to_mock = {
    "index.js": """
        import { initApp } from "./src/app";
        initApp();
    """,
    "src/app.js": """
        import { setupRoutes } from "./router";
        import { startServer } from "./server";
        
        export function initApp() {
            setupRoutes();
            startServer();
        }
    """,
    "src/router.js": """
        import { handleRequest } from "./handler";
        export function setupRoutes() {
            console.log("Setting up routes");
        }
    """,
    "src/server.js": """
        export function startServer() {
            console.log("Server listening");
        }
    """,
    "src/handler.js": """
        export function handleRequest() {
            console.log("Handling request");
        }
    """
}

print("1. Building and saving dependency graph for mock repository...")
for path, content in files_to_mock.items():
    file_graph = build_dependency_graph(content, path)
    update_file_graph(repo_id, path, file_graph)

print("Dependency graph stored successfully.")

print("\n2. Testing direct graph tools:")

print("\n--- find_imports('index.js') ---")
print(find_imports(repo_url, "index.js"))

print("\n--- find_usages('startServer') ---")
print(find_usages(repo_url, "startServer"))

print("\n--- trace_import_chain('index.js') ---")
print(trace_import_chain(repo_url, "index.js"))

print("\n--- trace_call_chain('initApp') ---")
print(trace_call_chain(repo_url, "initApp"))

print("\n3. Testing Agent Integration (mock query):")
try:
    response = agent.invoke(
        {
            "messages": [
                (
                    "user",
                    f"""
                    Repository: {repo_url}
                    Question: Trace the call chain starting from the function 'initApp' and explain what functions are called.
                    """
                )
            ]
        },
        config={
            "configurable": {
                "thread_id": "dependency_test_thread"
            }
        }
    )
    print("\nAgent Response:")
    print(response["messages"][-1].content)
except Exception as e:
    print(f"Agent execution failed: {e}")
