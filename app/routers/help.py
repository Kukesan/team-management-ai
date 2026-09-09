from fastapi import APIRouter, Depends

from app.dependencies import RequestContext, get_any_role_context
from app.schemas.help import HelpRequest, HelpResponse
from app.services.help import answer_help_question
from app.services.knowledge_base import load_knowledge_base

router = APIRouter()


@router.post("/help", response_model=HelpResponse)
async def help_chat(request: HelpRequest, ctx: RequestContext = Depends(get_any_role_context)) -> HelpResponse:
    knowledge_base = load_knowledge_base(ctx.roles)
    history = [h.model_dump() for h in request.history]
    answer = await answer_help_question(user_message=request.message, history=history, knowledge_base=knowledge_base)
    return HelpResponse(answer=answer)
