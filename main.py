import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import route, health
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Workforce Reskilling APIs")

ALLOWED_ORIGINS = [
    "https://future-proof-workforce-insights.lovable.app",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://2.220.53.210:8080"
]


def print_env_var(name, mask=True):
    value = os.getenv(name)
    if value:
        if mask:
            # Show only first 4 characters and mask the rest
            display_value = value[:4] + "****"
        else:
            display_value = value
        print(f"{name} is set: {display_value}")
    else:
        print(f"{name} is NOT set!")


# Safe printing (masking sensitive values)
print_env_var("OPENAI_API_KEY")
print_env_var("SUPABASE_URL", mask=False)  # URL is not as sensitive
print_env_var("SUPABASE_KEY")
print_env_var("DB_HOST", mask=False)
print_env_var("DB_NAME", mask=False)
print_env_var("DB_USER", mask=False)
print_env_var("DB_PASS")
print_env_var("DB_PORT", mask=False)

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


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
