import os
import hashlib
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

# --- File hash function ---
def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def scan_for_virus(file_bytes: bytes) -> bool:
    try:
        text = file_bytes.decode(errors="ignore")
        return "virus" in text.lower()
    except Exception:
        return False

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request, "result": None})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(request: Request, file: UploadFile = File(...)):
    db = SessionLocal()
    result = None
    filename = file.filename
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Empty file uploaded.")
        file_hash = get_file_hash(file_bytes)

        scan_entry = db.query(FileScan).filter(FileScan.file_hash == file_hash).first()
        if scan_entry:
            result = "File has already been scanned. " + ("Virus detected!!" if scan_entry.scan_result else "File is clean!!")
            logging.info(f"Cache HIT: {filename}, hash: {file_hash}")
        else:
            is_virus = scan_for_virus(file_bytes)
            new_scan = FileScan(
                file_hash=file_hash,
                scan_result=is_virus,
                filename=filename,
                scan_timestamp=datetime.now()
            )
            db.add(new_scan)
            db.commit()
            result = "Virus detected" if is_virus else "File is clean"
            logging.info(f"Scanned {filename}, hash: {file_hash}, result: {result}")
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
        total = db.query(FileScan).count()
        viruses = db.query(FileScan).filter(FileScan.scan_result == True).count()
        cache_size = total
        return {
            "total_files_scanned": total,
            "total_viruses_detected": viruses,
            "cache_size": cache_size
        }
    finally:
        db.close()
