from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import CORS_ORIGINS
from app.services.data_kiosk_queue_service import data_kiosk_queue
from app.services.report_queue_service import report_queue


@asynccontextmanager
async def lifespan(_: FastAPI):
    report_queue.start()
    data_kiosk_queue.start()
    yield
    report_queue.stop()
    data_kiosk_queue.stop()


app = FastAPI(title="itrend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
