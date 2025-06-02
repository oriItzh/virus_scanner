import os
import logging
import time
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.engine.base import Engine

from models import Base, FileScan, User
from scanner_service import ScannerService
from passlib.context import CryptContext

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/postgres")
SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_secret_key")

def wait_for_db(engine: Engine, max_retries: int = 5, retry_interval: int = 5) -> bool:
    """Wait for database to become available."""
    for i in range(max_retries):
        try:
            # Try to connect to the database
            with engine.connect() as connection:
                return True
        except OperationalError as e:
            if i < max_retries - 1:
                logging.warning(f"Database not ready, retrying in {retry_interval} seconds... ({i + 1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                logging.error("Could not connect to database after maximum retries")
                raise e
    return False

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Wait for database and create tables
wait_for_db(engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Logging setup ---
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize scanner service
scanner_service = ScannerService()

def get_current_user(request: Request):
    return request.session.get("user")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("upload.html", {"request": request, "result": None, "user": get_current_user(request)})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(request: Request, file: UploadFile = File(...)):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    db = SessionLocal()
    filename = file.filename
    try:
        file_bytes = await file.read()
        result, is_cached = scanner_service.scan_file(
            db, file_bytes, filename, user_id=get_current_user(request)["user_id"]
        )
        if is_cached:
            logging.info(f"Cache HIT: {filename}")
        else:
            logging.info(f"Scanned {filename}, result: {result['message']}")
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "result": result['message'],
                "result_color": result['color'],
                "filename": filename,
                "user": get_current_user(request)
            },
        )
    except Exception as e:
        logging.error(f"Error scanning file: {e}")
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "result": f"Error: {str(e)}",
                "result_color": "red",
                "filename": filename,
                "user": get_current_user(request)
            },
        )
    finally:
        db.close()

@app.get("/stats")
def stats(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    db = SessionLocal()
    try:
        return scanner_service.get_stats(db)
    finally:
        db.close()

@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "errors": [], "form_data": {}})

@app.post("/signup", response_class=HTMLResponse)
def signup(request: Request,
           first_name: str = Form(...),
           last_name: str = Form(...),
           username: str = Form(...),
           password: str = Form(...),
           confirm_password: str = Form(...)):
    db = SessionLocal()
    errors = []
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username
    }
    # Validate
    if not all([first_name, last_name, username, password, confirm_password]):
        errors.append("All fields are required.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if db.query(User).filter(User.username == username).first():
        errors.append("Username already exists.")

    if errors:
        return templates.TemplateResponse("signup.html", {"request": request, "errors": errors, "form_data": form_data})

    # Create user
    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        password_hash=pwd_context.hash(password)
    )
    db.add(user)
    db.commit()
    db.close()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "errors": [], "form_data": {}})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    errors = []
    form_data = {"username": username}
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        errors.append("Invalid username or password.")
        db.close()
        return templates.TemplateResponse("login.html", {"request": request, "errors": errors, "form_data": form_data})

    # Login successful: set session
    request.session["user"] = {
        "user_id": user.user_id,
        "username": user.username,
        "first_name": user.first_name
    }
    db.close()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
