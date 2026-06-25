from fastapi import FastAPI
from api.routes import router
from api.auth_routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
        from utils.db import close_db_pool
        close_db_pool()
    except Exception as e:
        print(f"Error closing shared database pool: {e}")

from config import ALLOWED_ORIGINS

app = FastAPI(
    title="GITHUB QA Bot",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)

