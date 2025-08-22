from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the crew module to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'aws-expert', 'src', 'crew'))

from src.crew.awscrew import AWSCrew

# Create FastAPI app
app = FastAPI(
    title="AWS Expert API",
    description="API for AWS Expert Crew AI system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    topic: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None

# Global crew instance
crew_instance = None

def get_crew_instance():
    """Get or create crew instance"""
    global crew_instance
    if crew_instance is None:
        crew_instance = AWSCrew()
    return crew_instance

def run_crew_sync(inputs: dict):
    """Run crew synchronously in a separate thread"""
    try:
        crew_instance = get_crew_instance()
        
        # Try different approaches to access the crew
        if hasattr(crew_instance, 'crew'):
            # If crew is a property
            result = crew_instance.crew().kickoff(inputs=inputs)
        else:
            # Alternative: manually create the crew
            from crewai import Crew, Process
            manual_crew = Crew(
                agents=[
                    crew_instance.aws_query_agent(),
                    crew_instance.search_agent(), 
                    crew_instance.report_agent()
                ],
                tasks=[
                    crew_instance.aws_query_task(),
                    crew_instance.search_task(),
                    crew_instance.report_task()
                ],
                process=Process.sequential,
                verbose=True
            )
            result = manual_crew.kickoff(inputs=inputs)
        
        return str(result)
    except Exception as e:
        raise Exception(f"Error running crew: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AWS Expert API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Submit AWS related queries",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AWS Expert API is running"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process AWS related queries using the crew system
    
    Args:
        request: QueryRequest containing the user's query
        
    Returns:
        QueryResponse with the crew's response or error
    """
    try:
        # Prepare inputs for the crew
        inputs = {
            'topic': request.topic or request.query,
            'query': request.query
        }
        
        # Run crew in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, run_crew_sync, inputs)
        
        return QueryResponse(
            success=True,
            result=result
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            result="",
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
