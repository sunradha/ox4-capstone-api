from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "hello world", "version": "1.0.0"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
