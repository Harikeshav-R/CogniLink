import pytest
from langgraph.graph.state import CompiledStateGraph
from PIL import Image

from app.workflows.object_permanence.state import State, StaticAnalysis, DiffAnalysis, FilteredResults
from app.workflows.object_permanence.workflow import create_compiled_state_graph


def test_create_compiled_state_graph():
    """
    Tests that the state graph is created and compiled without errors.
    """
    graph = create_compiled_state_graph()
    assert isinstance(graph, CompiledStateGraph)
    # Check if all nodes are present
    assert "extract_frames" in graph.nodes
    assert "analyze_frames" in graph.nodes
    assert "filter_results" in graph.nodes
    assert "save_analysis" in graph.nodes


@pytest.mark.asyncio
async def test_workflow_execution(mocker, sample_state):
    """
    Tests the full workflow execution by mocking each agent.
    """
    # Arrange Mocks
    mock_frames = [Image.new('RGB', (1, 1)), Image.new('RGB', (1, 1)), Image.new('RGB', (1, 1))]
    mock_extract_patch = mocker.patch('app.workflows.object_permanence.workflow.extract_frames', return_value={"frames": mock_frames})
    mock_analyze_patch = mocker.patch('app.workflows.object_permanence.workflow.analyze_frames', return_value={
        "static_analysis": StaticAnalysis(scene_description="test", objects=[]),
        "diff_analysis": DiffAnalysis(events=[])
    })
    mock_filter_patch = mocker.patch('app.workflows.object_permanence.workflow.filter_results', return_value={"filtered_results": FilteredResults(entries=[])})
    mock_save_patch = mocker.patch('app.workflows.object_permanence.workflow.save_analysis', return_value={"save_status": True})

    # Create and run the graph
    graph = create_compiled_state_graph()
    final_state = await graph.ainvoke(sample_state)

    # Assert
    mock_extract_patch.assert_awaited_once()
    mock_analyze_patch.assert_awaited_once()
    mock_filter_patch.assert_awaited_once()
    mock_save_patch.assert_awaited_once()

    # Check that the state was updated by the mocks
    assert final_state['frames'] == mock_frames
    assert isinstance(final_state['static_analysis'], StaticAnalysis)
    assert isinstance(final_state['filtered_results'], FilteredResults)
    assert final_state['save_status'] is True
