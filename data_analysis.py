import json
from langchain.tools import BaseTool
import pandas as pd
from typing import Dict

class DataAnalysisTool(BaseTool):
    name: str = "data_analysis_tool"
    description: str = """
    Analyze CSV data to answer questions and perform calculations.
    Use this tool to:
    - Filter data based on conditions
    - Perform aggregations (count, sum, average, etc.)
    - Find specific data points
    - Compare different segments of data
    
    Input should be a JSON string with:
    - file_id: The CSV file to analyze
    - operation: The operation to perform (filter, aggregate, compare, etc.)
    - parameters: Specific parameters for the operation
    """
    
    def _run(self, query: str) -> str:
        try:
            from app import csv_store
            
            params = json.loads(query)
            file_id = params.get("file_id")
            operation = params.get("operation")
            parameters = params.get("parameters", {})
            
            if file_id not in csv_store:
                return f"Error: File {file_id} not found"
            
            df = csv_store[file_id]
            
            if operation == "aggregate":
                return self._perform_aggregation(df, parameters)
            elif operation == "filter":
                return self._perform_filter(df, parameters)
            elif operation == "compare":
                return self._perform_comparison(df, parameters)
            elif operation == "describe":
                return self._describe_data(df, parameters)
            else:
                return f"Unknown operation: {operation}"
                
        except Exception as e:
            return f"Error in data analysis: {str(e)}"
    
    def _perform_aggregation(self, df: pd.DataFrame, params: Dict) -> str:
        try:
            group_by = params.get("group_by")
            agg_column = params.get("agg_column")
            agg_method = params.get("agg_method", "count")
            
            if group_by and agg_column:
                if agg_method == "count":
                    result = df.groupby(group_by)[agg_column].count()
                elif agg_method == "sum":
                    result = df.groupby(group_by)[agg_column].sum()
                elif agg_method == "mean":
                    result = df.groupby(group_by)[agg_column].mean()
                else:
                    result = df.groupby(group_by)[agg_column].agg(agg_method)
            elif group_by:
                result = df[group_by].value_counts()
            else:
                return "Error: group_by parameter required for aggregation"
            
            return f"Aggregation result:\n{result.to_string()}"
        except Exception as e:
            return f"Error in aggregation: {str(e)}"
    
    def _perform_filter(self, df: pd.DataFrame, params: Dict) -> str:
        try:
            conditions = params.get("conditions", {})
            filtered_df = df.copy()
            
            for column, condition in conditions.items():
                if isinstance(condition, dict):
                    op = condition.get("op", "==")
                    value = condition.get("value")
                    
                    if op == "==":
                        filtered_df = filtered_df[filtered_df[column] == value]
                    elif op == "!=":
                        filtered_df = filtered_df[filtered_df[column] != value]
                    elif op == ">":
                        filtered_df = filtered_df[filtered_df[column] > value]
                    elif op == "<":
                        filtered_df = filtered_df[filtered_df[column] < value]
                    elif op == "contains":
                        filtered_df = filtered_df[filtered_df[column].str.contains(value, na=False)]
                
            return f"Filtered data ({len(filtered_df)} rows):\n{filtered_df.head().to_string()}"
        except Exception as e:
            return f"Error in filtering: {str(e)}"
    
    def _perform_comparison(self, df: pd.DataFrame, params: Dict) -> str:
        try:
            compare_column = params.get("compare_column")
            metric_column = params.get("metric_column", None)
            
            if metric_column:
                result = df.groupby(compare_column)[metric_column].agg(['count', 'mean', 'sum'])
            else:
                result = df[compare_column].value_counts()
            
            return f"Comparison result:\n{result.to_string()}"
        except Exception as e:
            return f"Error in comparison: {str(e)}"
    
    def _describe_data(self, df: pd.DataFrame, params: Dict) -> str:
        try:
            columns = params.get("columns", df.columns.tolist())
            description = df[columns].describe(include='all').to_string()
            return f"Data description:\n{description}"
        except Exception as e:
            return f"Error in description: {str(e)}"

