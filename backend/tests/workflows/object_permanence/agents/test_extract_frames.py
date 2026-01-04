import pytest
from PIL import Image

from app.workflows.object_permanence.agents.extract_frames import extract_frames
from app.workflows.object_permanence.state import State


@pytest.mark.asyncio
async def test_extract_frames_successfully(dummy_video_path, mock_db_session):
    """
    Tests that extract_frames successfully extracts frames from a valid video.
    """
    initial_state = State(video_path=dummy_video_path, db_session=mock_db_session)
    result = await extract_frames(initial_state)

    assert "frames" in result
    assert isinstance(result["frames"], list)
    # The dummy video is 3 seconds long with 1 fps, so it should have 3 frames.
    assert len(result["frames"]) == 3
    for frame in result["frames"]:
        assert isinstance(frame, Image.Image)


@pytest.mark.asyncio
async def test_extract_frames_file_not_found(mock_db_session):
    """
    Tests that extract_frames handles a non-existent video file gracefully.
    """
    non_existent_path = "/path/to/non_existent_video.mp4"
    initial_state = State(video_path=non_existent_path, db_session=mock_db_session)

    result = await extract_frames(initial_state)

    assert "frames" in result
    assert result["frames"] == []


@pytest.mark.asyncio
async def test_extract_frames_invalid_video(mocker, mock_db_session):
    """
    Tests that extract_frames handles an invalid or corrupted video file.
    """
    # Simulate a video capture that fails to open
    mock_capture = mocker.patch('cv2.VideoCapture')
    mock_instance = mock_capture.return_value
    mock_instance.isOpened.return_value = False

    dummy_path = "/path/to/dummy_video.mp4"
    initial_state = State(video_path=dummy_path, db_session=mock_db_session)

    result = await extract_frames(initial_state)

    assert "frames" in result
    assert result["frames"] == []
