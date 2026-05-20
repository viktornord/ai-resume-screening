from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.structured_logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.log_level, settings.log_format)
    yield


app = FastAPI(title="AI Resume Screening", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
