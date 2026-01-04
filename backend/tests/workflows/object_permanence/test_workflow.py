from unittest.mock import patch, MagicMock

import pytest
from PIL import Image
from langgraph.graph.state import CompiledStateGraph
from sqlmodel import Session

from app.workflows.object_permanence.state import State, StaticAnalysis, DiffAnalysis, FilteredResults, FilteredEntry
from app.workflows.object_permanence.workflow import create_compiled_state_graph


@pytest.fixture
def compiled_graph() -> CompiledStateGraph:
    """Fixture to provide a compiled state graph for testing."""
    return create_compiled_state_graph()


@pytest.fixture
def initial_state() -> dict:
    """Fixture to provide a basic initial state for the workflow."""
    mock_session = MagicMock(spec=Session)
    return {
        "current_frame": Image.new("RGB", (100, 100), color="red"),
        "previous_frame": Image.new("RGB", (100, 100), color="blue"),
        "db_session": mock_session,
    }


def test_graph_compilation(compiled_graph):
    """Tests if the graph compiles successfully."""
    assert isinstance(compiled_graph, CompiledStateGraph)
    assert set(compiled_graph.nodes.keys()) == {
        "check_frame_similarity",
        "analyze_static_frame",
        "analyze_diff_frames",
        "filter_results",
        "save_analysis",
        "__start__",
    }


@patch("app.workflows.object_permanence.agents.save_analysis.create_log_entry")
@patch("app.workflows.object_permanence.agents.save_analysis.GoogleGenerativeAIEmbeddings")
@patch("app.workflows.object_permanence.agents.filter_results.create_agent")
@patch("app.workflows.object_permanence.agents.analyze_diff_frames.create_agent")
@patch("app.workflows.object_permanence.agents.analyze_static_frame.create_agent")
@patch("app.workflows.object_permanence.agents.check_frame_similarity.compare_images")
def test_full_workflow_happy_path(
    mock_compare_images,
    mock_static_agent,
    mock_diff_agent,
    mock_filter_agent,
    mock_embeddings,
    mock_create_log_entry,
    compiled_graph,
    initial_state,
):
    """
    Tests the full workflow when images are different and analysis proceeds.
    """
    # --- Mock Setup ---
    mock_compare_images.return_value = True  # Images are different

    # Mock the agent invocations
    mock_static_agent.return_value.invoke.return_value = {"structured_response": StaticAnalysis(scene_description="A test scene")}
    mock_diff_agent.return_value.invoke.return_value = {"structured_response": DiffAnalysis(events=[])}
    mock_filter_agent.return_value.invoke.return_value = {
        "structured_response": FilteredResults(
            entries=[FilteredEntry(content="Test content", object_name="test_object", log_type="state")]
        )
    }

    # Mock embedding and DB
    mock_embeddings.return_value.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    # --- Run Workflow ---
    final_state = compiled_graph.invoke(initial_state)

    # --- Assertions ---
    mock_compare_images.assert_called_once()
    mock_static_agent.assert_called_once()
    mock_diff_agent.assert_called_once()
    mock_filter_agent.assert_called_once()
    mock_embeddings.assert_called_once()
    mock_create_log_entry.assert_called_once()

    assert final_state["should_analyze"] is True
    assert isinstance(final_state["static_analysis"], StaticAnalysis)
    assert isinstance(final_state["diff_analysis"], DiffAnalysis)
    assert isinstance(final_state["filtered_results"], FilteredResults)
    assert final_state["save_status"] is True


@patch("app.workflows.object_permanence.agents.save_analysis.create_log_entry")
@patch("app.workflows.object_permanence.agents.filter_results.create_agent")
@patch("app.workflows.object_permanence.agents.analyze_diff_frames.create_agent")
@patch("app.workflows.object_permanence.agents.analyze_static_frame.create_agent")
@patch("app.workflows.object_permanence.agents.check_frame_similarity.compare_images")
def test_workflow_terminates_on_similar_images(
    mock_compare_images,
    mock_static_agent,
    mock_diff_agent,
    mock_filter_agent,
    mock_create_log_entry,
    compiled_graph,
    initial_state,
):
    """
    Tests that the workflow correctly terminates if the frames are not different.
    """
    # --- Mock Setup ---
    mock_compare_images.return_value = False  # Images are SIMILAR

    # --- Run Workflow ---
    final_state = compiled_graph.invoke(initial_state)

    # --- Assertions ---
    mock_compare_images.assert_called_once()

    # Ensure no other major nodes were called
    mock_static_agent.assert_not_called()
    mock_diff_agent.assert_not_called()
    mock_filter_agent.assert_not_called()
    mock_create_log_entry.assert_not_called()

    # The graph should end, and these values should not be set
    assert final_state["should_analyze"] is False
    assert final_state.get("static_analysis") is None
    assert final_state.get("diff_analysis") is None
    assert final_state.get("save_status") is not True
