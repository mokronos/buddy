from unittest.mock import patch
from buddy.llm import call_llm

@patch('litellm.completion')
def test_call_llm_basic(mock_complete):
    """Test basic LLM call with mock response"""
    # Setup mock response
    mock_complete.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    
    # Test basic call
    messages = [{"role": "user", "content": "Hello"}]
    response = call_llm(messages)
    
    # Verify response and mock called correctly
    assert response["choices"][0]["message"]["content"] == "Test response"
    mock_complete.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=None,
        stream=False,
        temperature=0.7
    )
