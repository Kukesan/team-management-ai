from fastapi import APIRouter, Depends

from app.dependencies import RequestContext, get_current_context
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import run_tool_loop

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, ctx: RequestContext = Depends(get_current_context)) -> ChatResponse:
    history = [h.model_dump() for h in request.history]
    result = await run_tool_loop(user_message=request.message, history=history)
    return ChatResponse(**result)
