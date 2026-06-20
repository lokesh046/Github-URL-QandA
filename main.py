from fastapi import FastAPI
from api.routes import router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="GITHUB QA Bot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)