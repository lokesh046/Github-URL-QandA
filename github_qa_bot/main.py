from fastapi import FastAPI
from api.routes import router
from api.auth_routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from utils.db import init_db
        init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
    yield
    # Shutdown
    try:
        from agent import pool
        if pool:
            print("[Database] Closing Postgres connection pool...")
            pool.close()
    except Exception as e:
        print(f"Error closing Agent Postgres pool: {e}")
        
    try:
        from utils.db import close_db_pool
        close_db_pool()
    except Exception as e:
        print(f"Error closing Users database pool: {e}")

app = FastAPI(
    title="GITHUB QA Bot",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)

# Serve the frontend built files if the 'dist' directory is present (Production)
dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")