from typing import Optional

from fastapi import APIRouter, Depends
from minecraft_ai.database.database import get_session
from pydantic import BaseModel
from sqlmodel import Session

# from minecraft_ai.database.models import SavedLocation # Will be used later

router = APIRouter(
    prefix="/minecraft",
    tags=["Minecraft Integration"],
)


class Coordinates(BaseModel):
    x: int
    y: int
    z: int
    dimension: Optional[str] = "overworld"


class MinecraftCommandRequest(BaseModel):
    prompt: str
    player_coordinates: Optional[Coordinates] = None


class MinecraftCommandResponse(BaseModel):
    message: str
    details: Optional[dict] = None


@router.post("/command", response_model=MinecraftCommandResponse)
async def handle_minecraft_command(
    request: MinecraftCommandRequest,
    db: Session = Depends(get_session),
) -> MinecraftCommandResponse:
    """Handles commands sent from the Minecraft Fabric mod."""

    # TODO: Implement command parsing logic
    # - Check if prompt is 'save location NAME'
    # - Check if prompt is 'find location NAME'
    # - Check if prompt is 'list locations'
    # - Otherwise, pass to PydanticAI agent

    # TODO: Implement database interaction
    # - Save location if command matches
    # - Query location if command matches

    # TODO: Implement PydanticAI interaction
    # - Call agent.run(request.prompt)

    # Placeholder response
    return MinecraftCommandResponse(
        message=f"Received command: '{request.prompt}'",
        details={"coordinates": request.player_coordinates.model_dump() if request.player_coordinates else None},
    )
