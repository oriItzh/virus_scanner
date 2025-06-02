import uvicorn
from main import app

if __name__ == "__main__":
    # Host '0.0.0.0' makes the server accessible from any IP
    # Port 8000 is the default, but you can change it
    # Workers=1 is good for development, increase for production
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=80,
        reload=True  # Enable auto-reload on code changes
    ) 