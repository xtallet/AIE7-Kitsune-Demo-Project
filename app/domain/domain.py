from typing import Optional

from pydantic import BaseModel


class CbotState(BaseModel):
    question: str
    user_id: str
    session_id: Optional[str] = None
    context: Optional[str] = None
    sql_query: Optional[str] = None
    sql_result: Optional[str] = None
    answer: Optional[str] = None
