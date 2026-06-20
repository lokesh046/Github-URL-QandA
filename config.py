from dotenv import load_dotenv
import os

load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")
    
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not fount")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

