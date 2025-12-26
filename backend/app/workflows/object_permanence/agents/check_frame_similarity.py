from app.tools.compare_images import compare_images
from app.workflows.object_permanence.state import State


def check_frame_similarity(state: State) -> dict:
    if state.previous_frame is None or state.current_frame is None:
        return {}

    return {
        "should_analyze": compare_images(state.previous_frame, state.current_frame)
    }
