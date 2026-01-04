import pytest

from app.workflows.object_permanence.agents.save_analysis import save_analysis


@pytest.mark.asyncio
async def test_save_analysis_successfully(mocker, populated_state):
    """
    Tests that save_analysis correctly processes entries and calls create_log_entry.
    """
    # Arrange
    mock_embeddings_model = mocker.patch('app.workflows.object_permanence.agents.save_analysis.GoogleGenerativeAIEmbeddings')
    mock_embed_instance = mock_embeddings_model.return_value
    
    async def mock_aembed_documents(*args, **kwargs):
        return [[0.1] * 3072, [0.2] * 3072]

    mock_embed_instance.aembed_documents.side_effect = mock_aembed_documents

    mock_create_log_entry = mocker.patch('app.workflows.object_permanence.agents.save_analysis.create_log_entry')
    async def mock_create_log_entry_side_effect(*args, **kwargs):
        return None # The function returns the created log, but we don't need it here

    mock_create_log_entry.side_effect = mock_create_log_entry_side_effect

    # Act
    result = await save_analysis(populated_state)

    # Assert
    assert result == {"save_status": True}

    # Verify embeddings were called with the content from the state
    mock_embeddings_model.assert_called_once()
    contents_to_embed = [entry.content for entry in populated_state.filtered_results.entries]
    mock_embed_instance.aembed_documents.assert_called_with(contents_to_embed)

    # Verify create_log_entry was called for each entry
    assert mock_create_log_entry.call_count == len(populated_state.filtered_results.entries)

    # Check the first call as a sample
    first_entry = populated_state.filtered_results.entries[0]
    first_embedding = (await mock_embed_instance.aembed_documents())[0]
    call_args, _ = mock_create_log_entry.call_args_list[0]
    assert call_args[0] == populated_state.db_session
    assert call_args[1] == first_entry.content
    assert call_args[2] == first_embedding
    # call_args[3] is time.time(), so we can't assert a specific value
    assert call_args[4] == first_entry.object_name
    assert call_args[5] == first_entry.log_type


@pytest.mark.asyncio
async def test_save_analysis_no_results(sample_state):
    """
    Tests that save_analysis returns an empty dictionary if there are no filtered results.
    """
    # Arrange
    sample_state.filtered_results = None

    # Act
    result = await save_analysis(sample_state)

    # Assert
    assert result == {}


@pytest.mark.asyncio
async def test_save_analysis_no_content(mocker, populated_state):
    """
    Tests that save_analysis returns an empty dict if filtered results have no content.
    """
    # Arrange
    populated_state.filtered_results.entries = []
    mock_embeddings_model = mocker.patch('app.workflows.object_permanence.agents.save_analysis.GoogleGenerativeAIEmbeddings')
    mock_embed_instance = mock_embeddings_model.return_value

    # Act
    result = await save_analysis(populated_state)

    # Assert
    assert result == {}
    # Ensure we didn't waste an API call for embeddings
    mock_embed_instance.aembed_documents.assert_not_called()
