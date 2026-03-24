from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import initialize_connection_pool, close_connection_pool
from app.logging_config import setup_logging
from app.utils.update_parking import fetch_and_update_spots
from app.versions.v1 import router as v1_router

setup_logging()
settings = get_settings()
jobstores = {
    'default': SQLAlchemyJobStore(url=f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}")
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_connection_pool()
    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.add_job(
        fetch_and_update_spots,
        trigger=CronTrigger(day='1', hour='0', minute='0'),  # Run on the 1st of every month at midnight
        id='update_parking_spots',
        replace_existing=True
    )
    scheduler.start()

    yield

    scheduler.shutdown()
    close_connection_pool()

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router=v1_router)


@app.get('/health', tags=['Health'])
def health_check():
    return JSONResponse(
        content={"message": f"{settings.APP_TITLE} is running"},
        status_code=status.HTTP_200_OK
    )
