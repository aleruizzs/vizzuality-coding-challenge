from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import Base, check_db_connection, engine

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_db_connection()
    yield


app = FastAPI(title="Environmental Data Query API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}
