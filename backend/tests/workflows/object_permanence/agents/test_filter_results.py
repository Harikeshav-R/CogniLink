import pytest

from app.workflows.object_permanence.agents.filter_results import filter_results
from app.workflows.object_permanence.state import StaticAnalysis, DiffAnalysis, FilteredResults, FilteredEntry


@pytest.mark.asyncio
async def test_filter_results_successfully(mocker, populated_state):
    """
    Tests that filter_results correctly calls the agent and returns filtered results.
    """
    # Arrange
    mock_model = mocker.MagicMock()
    mock_init_model_patch = mocker.patch('app.workflows.object_permanence.agents.filter_results.init_pollinations_chat_model', return_value=mock_model)

    expected_filtered_results = FilteredResults(
        entries=[
            FilteredEntry(content="Filtered content", object_name="test_object", log_type="state")
        ]
    )

    mock_agent = mocker.MagicMock()
    
    async def mock_ainvoke(*args, **kwargs):
        return {"structured_response": expected_filtered_results}
        
    mock_agent.ainvoke.side_effect = mock_ainvoke
    mock_create_agent_patch = mocker.patch('app.workflows.object_permanence.agents.filter_results.create_agent', return_value=mock_agent)

    # Act
    result = await filter_results(populated_state)

    # Assert
    mock_init_model_patch.assert_called_once()
    mock_create_agent_patch.assert_called_once()
    mock_agent.ainvoke.assert_called_once()

    assert "filtered_results" in result
    assert result["filtered_results"] == expected_filtered_results

    # Verify that low-confidence objects/events were filtered before calling the agent
    call_args, _ = mock_agent.ainvoke.call_args
    invoked_messages = call_args[0]['messages']
    # The first content part is the prompt, the second is static analysis, the third is diff analysis
    static_analysis_text = invoked_messages[0].content[1]['text']
    diff_analysis_text = invoked_messages[0].content[2]['text']
    assert "'low'" not in static_analysis_text
    assert "'low'" not in diff_analysis_text


@pytest.mark.asyncio
async def test_filter_results_no_analysis(mocker, sample_state):
    """
    Tests that filter_results returns an empty dictionary if analysis is missing.
    """
    # Arrange
    sample_state.static_analysis = None
    sample_state.diff_analysis = DiffAnalysis(events=[])

    # Act
    result = await filter_results(sample_state)

    # Assert
    assert result == {}

    # Arrange
    sample_state.static_analysis = StaticAnalysis(scene_description="", objects=[])
    sample_state.diff_analysis = None

    # Act
    result = await filter_results(sample_state)

    # Assert
    assert result == {}
