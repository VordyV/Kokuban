from fastapi import APIRouter, Request, Depends, HTTPException
from .admin_event_type import AdminEventType
from .recipient_param_type import RecipientParamType
from loguru import logger
from typing import Annotated

router = APIRouter(prefix="/api")

async def Token(request: Request):
	core = request.app.state.core
	token = request.headers.get("auth")
	if not token: raise HTTPException(status_code=401, detail="Token not specified")
	srv_name = await core.check_token(token)
	if not srv_name: raise HTTPException(status_code=401, detail="Token is invalid")
	return srv_name

@router.get('/sendadminevent', status_code=202, description="Send adminEvent. The recipient will be shown a dialog with info about the sent event")
async def on_send_admin_event(request: Request, server_name: Annotated[str, Depends(Token)], type: AdminEventType, param: RecipientParamType, text: str = "", recipient: str | None = None):
	core = request.app.state.core
	try:
		await core.sendAdminEvent(type, recipient=recipient, param=param, text=text)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))
	logger.info(f"Server {server_name} sent an adminEvent to recipient {recipient} via parameter {param} with text '{text}'")