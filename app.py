import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict
from dotenv import load_dotenv
from agentic_csv_bot import AgenticCSVChatbot
from schemas import UploadResponse, ChatRequest, ChatResponse
from logger import logger

load_dotenv()

app = FastAPI(
    title="Agentic CSV Intelligence API",
    description="AI agent with specialized tools for CSV analysis and visualization",
    version="2.0.0"
)

# Global storage
csv_store: Dict[str, pd.DataFrame] = {}
chart_store: Dict[str, str] = {}

# Initialize chatbot
chatbot = None

@app.on_event("startup")
async def startup_event():
    global chatbot
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning("GROQ_API_KEY environment variable not set")
    else:
        chatbot = AgenticCSVChatbot(groq_api_key)
        logger.info("Agentic CSV Chatbot initialized successfully")

@app.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized. Please set GROQ_API_KEY")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        content = await file.read()
        file_id, df = chatbot.process_csv(content, file.filename)
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            rows=len(df),
            columns=len(df.columns),
            column_names=list(df.columns),
            data_types={str(k): str(v) for k, v in df.dtypes.to_dict().items()},
            sample_data=df.head(3).to_dict('records')[0] if len(df) > 0 else {},
            message=f"Successfully uploaded and processed {file.filename}"
        )
    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized. Please set GROQ_API_KEY")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = await chatbot.process_query(request.query, request.csv_files)
        
        return ChatResponse(
            answer=result["answer"],
            chart_url=result["chart_url"],
            chart_id=result["chart_id"],
            csv_files_analyzed=result["csv_files_analyzed"],
            query=result["query"],
            tools_used=result["tools_used"],
            reasoning=result["reasoning"]
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chart/{chart_id}")
async def get_chart(chart_id: str):
    if chart_id not in chart_store:
        raise HTTPException(status_code=404, detail="Chart not found")
    return HTMLResponse(content=chart_store[chart_id])

@app.get("/files")
async def list_files():
    files_info = []
    for file_id, df in csv_store.items():
        files_info.append({
            "file_id": file_id,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "data_types": {str(k): str(v) for k, v in df.dtypes.to_dict().items()}
        })
    return {"files": files_info}

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    if file_id not in csv_store:
        raise HTTPException(status_code=404, detail="File not found")
    del csv_store[file_id]
    return {"message": f"File {file_id} deleted successfully"}

@app.get("/")
async def root():
    return {
        "message": "Agentic CSV Intelligence API",
        "version": "2.0.0",
        "description": "AI agent with specialized tools for intelligent CSV analysis",
        "features": [
            "Intent analysis with LLM reasoning",
            "Specialized tools for data analysis and visualization", 
            "Automatic chart generation based on query context",
            "Multi-step agentic workflow"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7999)