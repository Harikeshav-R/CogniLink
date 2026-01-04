import pytest
from PIL import Image

from app.workflows.object_permanence.agents.analyze_frames import analyze_frames
from app.workflows.object_permanence.state import State, VideoAnalysis, StaticAnalysis, DiffAnalysis


@pytest.mark.asyncio
async def test_analyze_frames_successfully(mocker, sample_state):
    """
    Tests that analyze_frames correctly calls the agent and returns the analysis.
    """
    # Arrange
    mock_model = mocker.MagicMock()
    mock_init_model_patch = mocker.patch('app.workflows.object_permanence.agents.analyze_frames.init_pollinations_chat_model', return_value=mock_model)

    mock_agent = mocker.MagicMock()
    
    # Define an async function to be the side effect
    async def mock_ainvoke(*args, **kwargs):
        return {
            "structured_response": VideoAnalysis(
                static_analysis=StaticAnalysis(scene_description="Test scene", objects=[]),
                diff_analysis=DiffAnalysis(events=[])
            )
        }
    
    mock_agent.ainvoke.side_effect = mock_ainvoke
    mock_create_agent_patch = mocker.patch('app.workflows.object_permanence.agents.analyze_frames.create_agent', return_value=mock_agent)

    # Create some dummy frames
    sample_state.frames = [Image.new('RGB', (100, 100), color='red')]

    # Act
    result = await analyze_frames(sample_state)

    # Assert
    mock_init_model_patch.assert_called_once()
    mock_create_agent_patch.assert_called_once()
    mock_agent.ainvoke.assert_called_once()

    assert "static_analysis" in result
    assert "diff_analysis" in result
    assert isinstance(result["static_analysis"], StaticAnalysis)
    assert result["static_analysis"].scene_description == "Test scene"
    assert isinstance(result["diff_analysis"], DiffAnalysis)


@pytest.mark.asyncio
async def test_analyze_frames_no_frames(sample_state):
    """
    Tests that analyze_frames returns an empty dictionary when no frames are provided.
    """
    # Arrange
    sample_state.frames = []

    # Act
    result = await analyze_frames(sample_state)

    # Assert
    assert result == {}
