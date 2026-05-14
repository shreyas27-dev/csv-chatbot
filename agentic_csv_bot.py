from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from intent_analysis import IntentAnalysisTool
from data_analysis import DataAnalysisTool
from chart_generator import ChartGenerationTool
import os
from fastapi import HTTPException
import io
from langchain.agents import AgentExecutor, create_openai_tools_agent
from typing import Dict, Optional, List, Any
from logger import logger
import pandas as pd
import uuid

class AgenticCSVChatbot:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=os.getenv("LLM_MODEL_NAME"),
            temperature=0.1
        )

        
        # Initialize tools
        self.tools = [
            DataAnalysisTool(),
            IntentAnalysisTool(),
            ChartGenerationTool()
        ]
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent data analysis assistant with access to specialized tools.

            Your workflow should be:
            1. First, analyze the user's query intent using the intent_analysis_tool
            2. Then, perform data analysis using the data_analysis_tool to get the actual data
            3. If visualization is needed, use the chart_generation_tool to create charts
            4. Provide a comprehensive answer combining insights from all tools

            Available tools:
            - intent_analysis_tool: Understand what the user wants and determine chart requirements
            - data_analysis_tool: Perform calculations, aggregations, and data filtering
            - chart_generation_tool: Create interactive visualizations

            Be thorough in your analysis and always explain your reasoning."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)
    
    def process_csv(self, file_content: bytes, filename: str) -> tuple[str, pd.DataFrame]:
        try:
            from app import csv_store

            file_id = f"{filename.replace('.csv', '')}_{uuid.uuid4().hex[:8]}"
            df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
            csv_store[file_id] = df
            logger.info(f"Successfully processed CSV: {file_id}")
            return file_id, df
        except Exception as e:
            logger.error(f"Error processing CSV {filename}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
    
    async def process_query(self, query: str, csv_file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        from app import csv_store

        if not csv_file_ids:
            csv_file_ids = list(csv_store.keys())
        
        if not csv_file_ids:
            raise HTTPException(status_code=400, detail="No CSV files available")
        
        # Prepare context about available data
        data_context = ""
        for file_id in csv_file_ids:
            if file_id in csv_store:
                df = csv_store[file_id]
                data_context += f"\nFile: {file_id}\n"
                data_context += f"Columns: {list(df.columns)}\n"
                data_context += f"Sample data: {df.head(2).to_dict('records')}\n"
        
        # Enhanced query with context
        enhanced_query = f"""
        User Query: {query}
        
        Available Data Context:
        {data_context}
        
        Please analyze this query and provide a comprehensive response using the available tools.
        """
        
        # Execute agent
        result = self.agent_executor.invoke({"input": enhanced_query})
        
        # Extract information from the agent's response
        response_text = result["output"]
        tools_used = []
        chart_url = None
        chart_id = None
        
        # Parse agent steps to find tools used and chart info
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if hasattr(step[0], 'tool'):
                    tools_used.append(step[0].tool)
                tool_output = str(step[1])
                if "Chart ID:" in tool_output:
                    chart_id = tool_output.split("Chart ID: ")[1].split(",")[0].strip()
                    chart_url = f"/chart/{chart_id}"
        
        return {
            "answer": response_text,
            "chart_url": chart_url,
            "chart_id": chart_id,
            "csv_files_analyzed": csv_file_ids,
            "query": query,
            "tools_used": tools_used,
            "reasoning": "Agent used specialized tools for comprehensive analysis"
        }
