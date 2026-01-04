from unittest.mock import patch, MagicMock

import pytest
from PIL import Image
from sqlmodel import Session

from app.workflows.object_permanence.agents.analyze_diff_frames import analyze_diff_frames
from app.workflows.object_permanence.agents.analyze_static_frame import analyze_static_frame
from app.workflows.object_permanence.agents.check_frame_similarity import check_frame_similarity
from app.workflows.object_permanence.agents.filter_results import filter_results
from app.workflows.object_permanence.agents.save_analysis import save_analysis
from app.workflows.object_permanence.state import State, StaticAnalysis, DiffAnalysis, FilteredResults, FilteredEntry, Event


@pytest.fixture
def mock_state():
    """Fixture to create a mock state object for agent tests."""
    state = MagicMock(spec=State)
    state.current_frame = Image.new("RGB", (100, 100), color="red")
    state.previous_frame = Image.new("RGB", (100, 100), color="blue")
    state.db_session = MagicMock(spec=Session)
    state.static_analysis = StaticAnalysis(scene_description="A scene")
    state.diff_analysis = DiffAnalysis(events=[Event(event_type="placed", object_name="keys", action_description="keys placed", location_context="table", confidence="high")])
    state.filtered_results = FilteredResults(entries=[FilteredEntry(content="Test", object_name="test", log_type="state")])
    return state


# --- Tests for check_frame_similarity ---

@patch("app.workflows.object_permanence.agents.check_frame_similarity.compare_images")
def test_check_frame_similarity_returns_true(mock_compare, mock_state):
    mock_compare.return_value = True
    result = check_frame_similarity(mock_state)
    assert result == {"should_analyze": True}
    mock_compare.assert_called_once_with(mock_state.current_frame, mock_state.previous_frame)


@patch("app.workflows.object_permanence.agents.check_frame_similarity.compare_images")
def test_check_frame_similarity_returns_false(mock_compare, mock_state):
    mock_compare.return_value = False
    result = check_frame_similarity(mock_state)
    assert result == {"should_analyze": False}


def test_check_frame_similarity_no_frames(mock_state):
    mock_state.previous_frame = None
    assert check_frame_similarity(mock_state) == {}


# --- Tests for analyze_static_frame ---

@patch("app.workflows.object_permanence.agents.analyze_static_frame.init_pollinations_chat_model")
@patch("app.workflows.object_permanence.agents.analyze_static_frame.create_agent")
def test_analyze_static_frame_happy_path(mock_create_agent, mock_init_model, mock_state):
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent
    mock_agent.invoke.return_value = {"structured_response": "test_analysis"}

    result = analyze_static_frame(mock_state)

    mock_init_model.assert_called_once()
    mock_create_agent.assert_called_once()
    mock_agent.invoke.assert_called_once()
    assert result == {"static_analysis": "test_analysis"}


def test_analyze_static_frame_no_frame(mock_state):
    mock_state.current_frame = None
    assert analyze_static_frame(mock_state) == {}


# --- Tests for analyze_diff_frames ---

@patch("app.workflows.object_permanence.agents.analyze_diff_frames.init_pollinations_chat_model")
@patch("app.workflows.object_permanence.agents.analyze_diff_frames.create_agent")
def test_analyze_diff_frames_happy_path(mock_create_agent, mock_init_model, mock_state):
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent
    mock_agent.invoke.return_value = {"structured_response": "diff_analysis"}

    result = analyze_diff_frames(mock_state)

    mock_init_model.assert_called_once()
    mock_create_agent.assert_called_once()
    mock_agent.invoke.assert_called_once()
    assert result == {"diff_analysis": "diff_analysis"}


def test_analyze_diff_frames_no_frames(mock_state):
    mock_state.previous_frame = None
    assert analyze_diff_frames(mock_state) == {}


# --- Tests for filter_results ---

@patch("app.workflows.object_permanence.agents.filter_results.init_pollinations_chat_model")
@patch("app.workflows.object_permanence.agents.filter_results.create_agent")
def test_filter_results_happy_path(mock_create_agent, mock_init_model, mock_state):
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent
    mock_agent.invoke.return_value = {"structured_response": "filtered"}

    result = filter_results(mock_state)

    mock_init_model.assert_called_once()
    mock_create_agent.assert_called_once()
    mock_agent.invoke.assert_called_once()
    assert result == {"filtered_results": "filtered"}


def test_filter_results_no_analysis(mock_state):
    mock_state.static_analysis = None
    assert filter_results(mock_state) == {}


# --- Tests for save_analysis ---

@patch("app.workflows.object_permanence.agents.save_analysis.create_log_entry")
@patch("app.workflows.object_permanence.agents.save_analysis.GoogleGenerativeAIEmbeddings")
def test_save_analysis_happy_path(mock_embeddings, mock_create_log, mock_state):
    mock_embed_instance = MagicMock()
    mock_embeddings.return_value = mock_embed_instance
    mock_embed_instance.embed_documents.return_value = [[0.1]]

    result = save_analysis(mock_state)

    mock_embeddings.assert_called_once()
    mock_embed_instance.embed_documents.assert_called_with(["Test"])
    mock_create_log.assert_called_once()
    assert result == {"save_status": True}


def test_save_analysis_no_results(mock_state):
    mock_state.filtered_results = None
    assert save_analysis(mock_state) == {}

def test_save_analysis_empty_results(mock_state):
    mock_state.filtered_results = FilteredResults(entries=[])
    assert save_analysis(mock_state) == {}
