from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.redis import close_redis, get_redis_client
from app.routers import auth, comments, posts, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis_client()
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="A fully-featured Blog REST API built with FastAPI, PostgreSQL, and Redis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} 🚀",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}

