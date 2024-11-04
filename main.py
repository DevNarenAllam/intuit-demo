from fastapi import FastAPI
from Common import get_service_logger

logger = get_service_logger(__name__)
app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}