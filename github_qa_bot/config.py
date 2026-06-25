from dotenv import load_dotenv
import os

load_dotenv()

# Base directory for local file storage (caches, zip files, and SQLite if used)
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Restrict allowed origins for CORS in production
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_raw:
    ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
else:
    # Fallback to local development endpoints and wildcard
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"]

# Ensure JWT_SECRET_KEY is specified in production
if ENVIRONMENT == "production":
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is required in production mode")
    if JWT_SECRET_KEY == "your_jwt_secret_key_change_me_in_production":
        raise ValueError("JWT_SECRET_KEY cannot be set to the default placeholder in production mode")
else:
    # Use fallback secret for development if not provided
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = "your_jwt_secret_key_change_me_in_production"

# Cloudflare R2 / S3 Storage Settings (Optional, enables stateless cloud storage)
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

# Auto-construct R2 endpoint if Account ID is provided but custom endpoint is not
if not S3_ENDPOINT_URL and R2_ACCOUNT_ID:
    S3_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Ensure endpoint has a scheme prefix (http:// or https://)
if S3_ENDPOINT_URL and not (S3_ENDPOINT_URL.startswith("http://") or S3_ENDPOINT_URL.startswith("https://")):
    S3_ENDPOINT_URL = f"https://{S3_ENDPOINT_URL}"

S3_STORAGE_ENABLED = bool(
    S3_ENDPOINT_URL and 
    R2_ACCESS_KEY_ID and 
    R2_SECRET_ACCESS_KEY and 
    R2_BUCKET_NAME
)

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

