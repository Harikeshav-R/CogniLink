import cv2
from PIL import Image
from loguru import logger

from app.workflows.object_permanence.state import State


async def extract_frames(state: State) -> dict:
    """
    Extracts frames from a video file at a rate of 1 frame per second.

    This node reads a video from the `video_path` specified in the state,
    calculates the frame rate, and then iterates through the video to
    capture one frame for each second. The extracted frames are converted
    to PIL Images and stored in the `frames` field of the state.

    :param state: The current state of the workflow, which must include `video_path`.
    :type state: State
    :return: A dictionary containing the list of extracted `frames`.
    :rtype: dict
    """
    logger.trace("Entering extract_frames function")
    logger.debug(f"Extracting frames from video at: {state.video_path}")

    frames = []
    cap = cv2.VideoCapture(state.video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video file at: {state.video_path}")
        return {"frames": []}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        logger.warning("Video FPS is 0, cannot extract frames.")
        return {"frames": []}

    frame_interval = int(fps)  # Capture one frame per second
    logger.debug(f"Video FPS: {fps}, Frame interval: {frame_interval}")

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            logger.trace(f"Extracting frame {frame_count}")
            # Convert frame from BGR (OpenCV) to RGB (PIL)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            frames.append(pil_image)
        frame_count += 1
    cap.release()

    logger.debug(f"Extracted {len(frames)} frames from video.")
    logger.trace("Exiting extract_frames function")

    return {"frames": frames}
