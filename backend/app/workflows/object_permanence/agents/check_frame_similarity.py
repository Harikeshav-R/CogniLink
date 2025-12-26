from loguru import logger

from app.workflows.object_permanence.state import State
from app.workflows.object_permanence.tools.compare_images import compare_images


def check_frame_similarity(state: State) -> dict:
    """
    Analyze the similarity between the previous and current frames and determine if
    analysis should be conducted based on the comparison result.

    :param state: A State object that contains the previous and current frames to
        be analyzed. Must include `previous_frame` and `current_frame` attributes.
    :type state: State
    :return: A dictionary containing the result of whether further analysis is
        required, with the key `should_analyze`.
    :rtype: dict
    """
    logger.trace("Entering check_frame_similarity function")
    if state.previous_frame is None or state.current_frame is None:
        logger.debug("Previous frame or current frame is None, returning empty dict")
        return {}

    logger.debug("Comparing previous and current frames")
    should_analyze = compare_images(state.current_frame, state.previous_frame)
    logger.debug(f"Comparison result: {should_analyze}")

    logger.trace("Exiting check_frame_similarity function")
    return {
        "should_analyze": should_analyze
    }
