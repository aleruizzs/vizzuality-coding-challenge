from fastapi import FastAPI
from src.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Environmental Data Query API")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}
