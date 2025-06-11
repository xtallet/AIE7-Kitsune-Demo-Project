from unittest.mock import MagicMock, patch

import pandas as pd

from app.adapters.out.knowledge_base_lancedb_adapter import KnowledgeLanceDBAdapter


@patch("app.adapters.out.knowledge_base_lancedb_adapter.lancedb.connect")
def test_knowledge_lancedb_adapter_search(mock_connect):
    # 1. Create realistic DataFrame structure
    mock_data = [
        {
            "question": "What is X?",
            "cot": "Reasoning",
            "sql_query": "SELECT * from Y",
            "vector": [0.1],  # Include columns to be dropped
            "chunk_id": 1,
            "_distance": 0.5,
        }
    ]
    mock_df = pd.DataFrame(mock_data)

    # 2. Configure LanceDB mock chain
    mock_table = MagicMock()
    mock_table.search.return_value.limit.return_value.to_pandas.return_value = mock_df
    mock_connect.return_value.open_table.return_value = mock_table

    # 3. Mock embedding client
    mock_embedding_client = MagicMock()
    mock_embedding_client.create.return_value.data = [
        MagicMock(embedding=[0.1, 0.2, 0.3])
    ]

    # 4. Test execution
    adapter = KnowledgeLanceDBAdapter(
        db_path="path",
        table_name="table",
        embedding_model_name="model",
        embedding_client=mock_embedding_client,
    )
    result = adapter.search("query")

    # 5. Verify output
    expected = "question: What is X?\n" "cot: Reasoning\n" "sql_query: SELECT * from Y"
    assert expected in result
