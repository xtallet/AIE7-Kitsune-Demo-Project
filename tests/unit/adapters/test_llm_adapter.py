# from unittest.mock import MagicMock, patch
#
# from app.adapters.out.llm_adapter import LLMAdapter
#
#
# @patch("app.adapters.out.llm_adapter.AzureOpenAI")  # Mock the AzureOpenAI client
# def test_llm_adapter_generate_sql_query(mock_azure_openai):
#     # Mock the behavior of the AzureOpenAI client
#     mock_client_instance = mock_azure_openai.return_value
#     mock_client_instance.chat.completions.create.return_value.choices = [
#         MagicMock(message=MagicMock(content="SELECT * FROM table;"))
#     ]
#
#     # Initialize the adapter with the mocked client
#     adapter = LLMAdapter(
#         model_name="model",
#         azure_deployment="deployment",
#         azure_endpoint="https://example.com",  # Ensure a valid URL
#         api_version="v1",
#         api_key="key",
#     )
#
#     # Call the method and assert the result
#     result = adapter.generate_sql_query("What is X?", "Context")
#     assert result == "SELECT * FROM table;"
#
#
# @patch("app.adapters.out.llm_adapter.AzureOpenAI")  # Mock the AzureOpenAI client
# def test_llm_adapter_summarize_answer(mock_azure_openai):
#     # Mock the behavior of the AzureOpenAI client
#     mock_client_instance = mock_azure_openai.return_value
#     mock_client_instance.chat.completions.create.return_value.choices = [
#         MagicMock(message=MagicMock(content="This is the summary."))
#     ]
#
#     # Initialize the adapter with the mocked client
#     adapter = LLMAdapter(
#         model_name="model",
#         azure_deployment="deployment",
#         azure_endpoint="https://example.com",  # Ensure a valid URL
#         api_version="v1",
#         api_key="key",
#     )
#
#     # Call the method and assert the result
#     result = adapter.summarize_answer("What is X?", "Query result")
#     assert result == "This is the summary."
