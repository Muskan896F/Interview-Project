import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config.settings import settings
from app.database.database import engine, Base
from app.database import models
from app.api.routes import router as api_router
from app.utils.logger import logger

# Initialize database schemas
logger.info("Initializing SQLite database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database schemas compiled successfully.")

app = FastAPI(
    title="Real Estate Voice Agent API",
    description="Conversational Outbound Voice Assistant driving qualifications and bookings.",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include APIs
app.include_router(api_router, prefix="/api")

# Mount frontend static folder
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_dashboard():
    """Serves the central outbound dialing board client."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Voice Agent API Online. Static files index.html missing."}

if __name__ == "__main__":
    logger.info(f"Starting developer server on {settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
