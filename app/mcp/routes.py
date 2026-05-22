from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from .tools import TOOL_METADATA, TOOL_HANDLERS
from ..auth.service import get_current_user
from ..database import User

router = APIRouter()

class ToolExecutionRequest(BaseModel):
    tool: str
    arguments: dict

@router.get("/tools", response_model=list)
async def list_tools():
    """
    Discovery endpoint to list all available MCP tools and their schemas.
    """
    return TOOL_METADATA

@router.post("/execute-tool", response_model=dict)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Protected endpoint to execute a specific tool dynamically.
    """
    handler = TOOL_HANDLERS.get(request.tool)
    
    if not handler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{request.tool}' not found"
        )
    
    try:
        # Execute the mapped handler with arguments and the authenticated user's ID
        result = handler(request.arguments, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing tool: {str(e)}"
        )
