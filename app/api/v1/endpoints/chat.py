from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, get_rag_service
from app.core.logging import setup_logging
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import RefreshDataRequest, RefreshDataResponse
from app.services.rag_service import RAGService

logger = setup_logging()

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: str = Depends(get_current_user),
):
    """Handle chat requests"""
    try:
        logger.info(f"Processing chat request: {request.message[:100]}...")

        conversation_history = []
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        result = await rag_service.query(
            question=request.message,
            conversation_history=conversation_history,
            max_results=request.max_results or 5,
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=RefreshDataResponse)
async def refresh_data(
    request: RefreshDataRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: str = Depends(get_current_user),
):
    """Refresh knowledge base data"""
    try:
        logger.info("Manual data refresh requested")

        result = await rag_service.refresh_knowledge_base(
            force_refresh=request.force_refresh
        )

        return RefreshDataResponse(**result)

    except Exception as e:
        logger.error(f"Error in refresh endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
