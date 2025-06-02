import os
import logging
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from models import Base, FileScan
from scanner_service import ScannerService

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/postgres")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Logging setup ---
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO
)

# Initialize scanner service
scanner_service = ScannerService()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request, "result": None})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(request: Request, file: UploadFile = File(...)):
    db = SessionLocal()
    filename = file.filename
    try:
        file_bytes = await file.read()
        result, is_cached = scanner_service.scan_file(db, file_bytes, filename)
        if is_cached:
            logging.info(f"Cache HIT: {filename}")
        else:
            logging.info(f"Scanned {filename}, result: {result}")
        
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "result": result, "filename": filename},
        )
    except Exception as e:
        logging.error(f"Error scanning file: {e}")
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "result": f"Error: {str(e)}", "filename": filename},
        )
    finally:
        db.close()

@app.get("/stats")
def stats():
    db = SessionLocal()
    try:
        return scanner_service.get_stats(db)
    finally:
        db.close()
