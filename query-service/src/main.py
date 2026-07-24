from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import check_db_connection, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_db_connection()
    yield
    await engine.dispose()


app = FastAPI(title="Environmental Data Query API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}
