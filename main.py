import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import route, health
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Workforce Reskilling APIs")

ALLOWED_ORIGINS = [
    "https://future-proof-workforce-insights.lovable.app",
    "https://future-workforce-navigator.lovable.app",
    "https://lovable.dev",
    "http://localhost:3000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router)
app.include_router(route.router, prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
