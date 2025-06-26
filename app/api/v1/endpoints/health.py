from fastapi import APIRouter

from app.schemas.chat import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Import here to avoid circular dependency
        from app.services.rag_service import rag_service

        health_status = await rag_service.get_health_status()
        return HealthResponse(**health_status)

    except Exception:
        return HealthResponse(
            status="error",
            weaviate_ready=False,
            model_ready=False,
            document_count=0,
            last_updated=None,
        )
