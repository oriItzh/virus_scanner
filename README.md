# Virus Scanner Web Application

A web-based file virus scanner built with FastAPI, SQLAlchemy, and Jinja2. Users can register, log in, upload files for scanning, and view scan results. The app supports user authentication, file scan caching, and statistics, and is ready for deployment with Docker and PostgreSQL.

## Features
- **User Authentication**: Sign up, log in, and log out with secure password hashing.
- **File Upload & Scanning**: Upload files to be scanned for viruses (scanner logic in `scanner_service`).
- **Scan Caching**: Avoids redundant scans for previously checked files.
- **Statistics**: View scan statistics (requires authentication).
- **Responsive UI**: Clean HTML interface for file upload and results (see `templates/upload.html`).
- **Session Management**: Secure sessions using Starlette middleware.
- **Logging**: Key events and errors are logged for monitoring.
- **Dockerized**: Ready for deployment with Docker and Docker Compose.

## Project Structure
```
├── main.py                # FastAPI app, endpoints, and core logic
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Multi-container setup (app + PostgreSQL)
├── templates/
│   └── upload.html        # File upload and scan result UI
└── ... (models.py, scanner_service.py expected but not found in scan)
```

## Requirements
- Python 3.11+
- PostgreSQL (default config: user `postgres`, password `postgres`)
- Docker & Docker Compose (optional, for containerized deployment)

## Installation & Setup Using Docker
1. **Clone the repository**
   ```sh
   git clone https://github.com/oriItzh/virus_scanner.git
   cd virus_scanner
   ```
   
2. **Build and start all services**
   ```sh
   docker-compose up --build
   ```
3. The app will be available at [http://localhost:8000](http://localhost:8000)

## Usage
- Visit `/signup` to create a new account.
- Log in at `/login`.
- Upload files for scanning at `/scan-files`.
- View scan statistics at `/stats` (must be logged in).
- Log out at `/logout`.

## Dependencies
Main dependencies (see `requirements.txt`):
- fastapi
- uvicorn
- jinja2
- python-multipart
- sqlalchemy
- psycopg2-binary
- python-dotenv
- passlib[bcrypt]
- alembic
- pytest, pytest-asyncio (for testing)

---
