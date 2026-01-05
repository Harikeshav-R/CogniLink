from PIL.Image import Image
from pydantic import BaseModel, Field

from app.workflows.object_permanence.state import ObjectPermanenceAnalysis


class PassiveOrchestratorState(BaseModel):
    # Input
    current_frame: Image = Field(..., description="The current frame to process.")

    # Internal
    object_permanence_subscriber_id: str = Field(
        ...,
        description="The subscriber ID of the object permanence agent subscribed to the state updates."
    )
    object_permanence_results: list[ObjectPermanenceAnalysis] = Field(
        description="A list of object permanence analysis results.",
        default_factory=list
    )
