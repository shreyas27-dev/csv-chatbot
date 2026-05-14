from langchain.tools import BaseTool
import pandas as pd
import json
from typing import Dict, Optional, List
from schemas import IntentAnalysis
from logger import logger
from enums import QueryIntent, ChartType

class IntentAnalysisTool(BaseTool):
    name: str = "intent_analysis_tool"
    description: str = """
    Analyze user query to understand intent and determine what type of analysis or visualization is needed.
    This tool will:
    - Identify if visualization is needed
    - Determine the best chart type
    - Extract column names and operations
    - Identify aggregation methods
    - Understand filtering requirements
    
    Input should be a JSON string with:
    - query: The user's question
    - available_columns: List of available columns in the dataset
    - sample_data: Sample rows to understand data structure
    """
    
    def _run(self, input_str: str) -> str:
        try:
            logger.info(f"Input str: {input_str}, {type(input_str)}")
            params = json.loads(input_str)
            logger.info(f"Parmas: {params}, {type(params)}")
            query = params.get("query", "").lower()
            available_columns = params.get("available_columns", [])
            
            # Analyze intent using LLM-based reasoning
            intent = self._analyze_intent(query)
            chart_type = self._determine_chart_type(query, intent)
            columns = self._extract_relevant_columns(query, available_columns)
            aggregation = self._determine_aggregation(query)
            
            analysis = IntentAnalysis(
                intent=intent,
                chart_type=chart_type,
                x_column=columns.get("x_column"),
                y_column=columns.get("y_column"),
                aggregation_method=aggregation,
                needs_visualization=self._needs_visualization(query),
                reasoning=self._generate_reasoning(query, intent, chart_type, columns)
            )
            
            return analysis.json()
            
        except Exception as e:
            return f"Error in intent analysis: {str(e)}"
    
    def _analyze_intent(self, query: str) -> QueryIntent:
        if any(word in query for word in ["show", "display", "plot", "chart", "graph", "visualize"]):
            return QueryIntent.VISUALIZATION
        elif any(word in query for word in ["compare", "vs", "versus", "difference"]):
            return QueryIntent.COMPARISON
        elif any(word in query for word in ["trend", "over time", "change", "progression"]):
            return QueryIntent.TREND_ANALYSIS
        elif any(word in query for word in ["summary", "describe", "overview"]):
            return QueryIntent.SUMMARY
        else:
            return QueryIntent.DATA_ANALYSIS
    
    def _determine_chart_type(self, query: str, intent: QueryIntent) -> Optional[ChartType]:
        # Chart type keywords
        if "bar" in query or "bar chart" in query:
            return ChartType.BAR
        elif "line" in query or "line chart" in query or "trend" in query:
            return ChartType.LINE
        elif "pie" in query or "pie chart" in query:
            return ChartType.PIE
        elif "scatter" in query or "scatter plot" in query:
            return ChartType.SCATTER
        elif "histogram" in query:
            return ChartType.HISTOGRAM
        elif "heatmap" in query:
            return ChartType.HEATMAP
        
        # Intent-based defaults
        if intent == QueryIntent.COMPARISON:
            return ChartType.BAR
        elif intent == QueryIntent.TREND_ANALYSIS:
            return ChartType.LINE
        elif intent in [QueryIntent.VISUALIZATION, QueryIntent.DATA_ANALYSIS]:
            return ChartType.BAR  # Safe default
        
        return None
    
    def _extract_relevant_columns(self, query: str, available_columns: List[str]) -> Dict[str, Optional[str]]:
        columns = {"x_column": None, "y_column": None}
        
        # Simple keyword matching - in production, you'd want more sophisticated NLP
        query_words = query.lower().split()
        
        for col in available_columns:
            col_words = col.lower().replace('_', ' ').split()
            if any(word in query_words for word in col_words):
                if not columns["x_column"]:
                    columns["x_column"] = col
                elif not columns["y_column"]:
                    columns["y_column"] = col
        
        return columns
    
    def _determine_aggregation(self, query: str) -> Optional[str]:
        if "count" in query or "number of" in query:
            return "count"
        elif "sum" in query or "total" in query:
            return "sum"
        elif "average" in query or "mean" in query:
            return "mean"
        elif "max" in query or "maximum" in query:
            return "max"
        elif "min" in query or "minimum" in query:
            return "min"
        return "count"  # Default
    
    def _needs_visualization(self, query: str) -> bool:
        viz_keywords = ["show", "display", "plot", "chart", "graph", "visualize", "bar", "line", "pie"]
        return any(keyword in query.lower() for keyword in viz_keywords)
    
    def _generate_reasoning(self, query: str, intent: QueryIntent, chart_type: Optional[ChartType], columns: Dict) -> str:
        reasoning = f"Query analysis: Intent identified as {intent.value}."
        if chart_type:
            reasoning += f" Best visualization: {chart_type.value} chart."
        if columns["x_column"]:
            reasoning += f" X-axis: {columns['x_column']}."
        if columns["y_column"]:
            reasoning += f" Y-axis: {columns['y_column']}."
        return reasoning