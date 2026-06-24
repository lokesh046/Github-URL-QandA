from dotenv import load_dotenv
import os

load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")
    
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME not found")
