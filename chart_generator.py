import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from langchain.tools import BaseTool
import json, uuid
import pandas as pd
from typing import Dict, Optional
from logger import logger

class ChartGenerationTool(BaseTool):
    name: str = "chart_generation_tool"
    description: str = """
    Generate interactive charts based on analysis results and intent.
    
    Input should be a JSON string with:
    - file_id: CSV file to use for chart
    - chart_type: Type of chart to generate
    - x_column: Column for x-axis
    - y_column: Column for y-axis (optional)
    - aggregation_method: How to aggregate data
    - title: Chart title
    - filters: Any filters to apply to data
    """
    
    def _run(self, input_str: str) -> str:
        try:
            from app import csv_store

            params = json.loads(input_str)
            file_id = params.get("file_id")
            chart_type = params.get("chart_type")
            x_column = params.get("x_column")
            y_column = params.get("y_column")
            aggregation = params.get("aggregation_method", "count")
            title = params.get("title", "Data Visualization")
            filters = params.get("filters", {})
            
            if file_id not in csv_store:
                return f"Error: File {file_id} not found"
            
            df = csv_store[file_id]
            
            # Apply filters if any
            filtered_df = self._apply_filters(df, filters)
            
            # Generate chart
            chart_id = self._create_chart(
                filtered_df, chart_type, x_column, y_column, aggregation, title
            )
            
            if chart_id:
                return f"Chart generated successfully. Chart ID: {chart_id}, URL: /chart/{chart_id}"
            else:
                return "Error: Could not generate chart"
                
        except Exception as e:
            return f"Error in chart generation: {str(e)}"
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        filtered_df = df.copy()
        for column, condition in filters.items():
            if isinstance(condition, dict):
                op = condition.get("op", "==")
                value = condition.get("value")
                
                if op == "==" and column in df.columns:
                    filtered_df = filtered_df[filtered_df[column] == value]
                elif op == "contains" and column in df.columns:
                    filtered_df = filtered_df[filtered_df[column].str.contains(str(value), na=False)]
        
        return filtered_df
    
    def _create_chart(self, df: pd.DataFrame, chart_type: str, x_col: str, y_col: str, 
                     aggregation: str, title: str) -> Optional[str]:
        try:
            from app import chart_store

            fig = None
            
            if chart_type == "bar":
                if x_col and x_col in df.columns:
                    if y_col and y_col in df.columns:
                        # Aggregate y_col by x_col
                        if aggregation == "count":
                            data = df.groupby(x_col)[y_col].count().reset_index()
                        elif aggregation == "sum":
                            data = df.groupby(x_col)[y_col].sum().reset_index()
                        elif aggregation == "mean":
                            data = df.groupby(x_col)[y_col].mean().reset_index()
                        else:
                            data = df.groupby(x_col)[y_col].agg(aggregation).reset_index()
                        
                        fig = px.bar(data, x=x_col, y=y_col, title=title)
                    else:
                        # Count occurrences of x_col
                        data = df[x_col].value_counts().reset_index()
                        fig = px.bar(data, x='index', y=x_col, title=title)
                        fig.update_xaxes(title=x_col)
                        fig.update_yaxes(title="Count")
            
            elif chart_type == "line":
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    fig = px.line(df, x=x_col, y=y_col, title=title)
            
            elif chart_type == "pie":
                if x_col and x_col in df.columns:
                    data = df[x_col].value_counts().reset_index()
                    fig = px.pie(data, values=x_col, names='index', title=title)
            
            elif chart_type == "scatter":
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    fig = px.scatter(df, x=x_col, y=y_col, title=title)
            
            elif chart_type == "histogram":
                if x_col and x_col in df.columns:
                    fig = px.histogram(df, x=x_col, title=title)
            
            if fig:
                # Store chart
                chart_id = f"chart_{uuid.uuid4().hex[:8]}"
                chart_html = pio.to_html(fig, include_plotlyjs='cdn')
                chart_store[chart_id] = chart_html
                return chart_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating chart: {str(e)}")
            return None
