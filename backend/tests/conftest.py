import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.workflows.object_permanence.state import State, StaticAnalysis, DiffAnalysis, Object, Event, FilteredResults, \
    FilteredEntry

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_db_session(mocker):
    """Provides a mock AsyncSession."""
    session = mocker.MagicMock(spec=AsyncSession)
    session.exec.return_value.first.return_value = ("PostgreSQL 13.0",)
    return session


@pytest.fixture(scope="session")
def dummy_video_path():
    """
    Creates a dummy video file for testing and returns its path.
    The video is 3 seconds long, 100x100, with a frame rate of 1 fps.
    It shows a moving square.
    """
    width, height = 100, 100
    fps = 1
    duration_secs = 3
    total_frames = duration_secs * fps

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        video_path = tmp.name

    # Use 'mp4v' for broader compatibility, especially in containerized environments
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, float(fps), (width, height))

    if not out.isOpened():
        raise IOError("Could not open video writer")

    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        square_size = 20
        pos_x = (i * (width - square_size)) // (total_frames - 1) if total_frames > 1 else 0
        cv2.rectangle(frame, (pos_x, 40), (pos_x + square_size, 40 + square_size), (255, 255, 255), -1)
        out.write(frame)

    out.release()

    yield video_path

    os.unlink(video_path)


@pytest.fixture
def sample_state(dummy_video_path, mock_db_session):
    """
    Provides a sample State object for testing.
    """
    return State(video_path=dummy_video_path, db_session=mock_db_session)


@pytest.fixture
def populated_state(sample_state):
    """
    Provides a populated State object with analysis results.
    """
    sample_state.static_analysis = StaticAnalysis(
        scene_description="A test scene.",
        objects=[
            Object(
                object_name="Test Object",
                category="other",
                status="resting",
                location_description="on the test surface",
                supporting_surface="Test Surface",
                visual_details="A test object.",
                confidence="high"
            ),
            Object(
                object_name="Held Object",
                category="other",
                status="held",
                location_description="in hand",
                supporting_surface="Hand",
                visual_details="A held object.",
                confidence="high"
            ),
            Object(
                object_name="Low Confidence Object",
                category="other",
                status="resting",
                location_description="somewhere",
                supporting_surface="Somehwere",
                visual_details="A blurry object.",
                confidence="low"
            )
        ]
    )
    sample_state.diff_analysis = DiffAnalysis(
        events=[
            Event(
                event_type="placed",
                object_name="Test Object",
                action_description="The test object was placed.",
                location_context="The Test Surface",
                confidence="high"
            )
        ]
    )
    sample_state.filtered_results = FilteredResults(
        entries=[
            FilteredEntry(
                content="The test object is resting on the test surface.",
                object_name="test_object",
                log_type="state"
            ),
            FilteredEntry(
                content="ACTION: The test object was placed on The Test Surface.",
                object_name="test_object",
                log_type="action"
            )
        ]
    )
    return sample_state
