from enum import Enum

# Enums for better type safety
class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"
    VIOLIN = "violin"

class QueryIntent(str, Enum):
    VISUALIZATION = "visualization"
    DATA_ANALYSIS = "data_analysis"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    TREND_ANALYSIS = "trend_analysis"