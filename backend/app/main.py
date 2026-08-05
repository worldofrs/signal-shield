import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import router as v1_router
from app.core.adversarial_engine import VALID_ENCODERS, warmup_encoders


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.warmup:
        names = [n for n in settings.warmup_encoders_list if n in VALID_ENCODERS]
        if names:
            print(f"Startup warmup: {', '.join(names)}")
            await asyncio.to_thread(warmup_encoders, names)
            print("Startup warmup complete")
    else:
        print("Startup warmup disabled (SS_WARMUP=false)")
    yield


app = FastAPI(title="Signal Shield", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
