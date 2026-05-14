from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Type, Union
from enums import QueryIntent, ChartType

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    csv_files: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    chart_url: Optional[str] = None
    chart_id: Optional[str] = None
    csv_files_analyzed: List[str]
    query: str
    tools_used: List[str]
    reasoning: str

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    data_types: Dict[str, str]
    sample_data: Dict[str, Any]
    message: str

class IntentAnalysis(BaseModel):
    intent: QueryIntent
    chart_type: Optional[ChartType] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    aggregation_method: Optional[str] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    needs_visualization: bool
    reasoning: str