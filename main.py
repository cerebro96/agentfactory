import os
import shutil
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory where main.py is located
AGENT_DIR = Path(__file__).parent.absolute()
# Example session DB URL (e.g., SQLite)
SESSION_DB_URL = "sqlite:///./sessions.db"
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = False

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agent_dir=AGENT_DIR,
    session_db_url=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# # You can add more FastAPI routes or configurations below if needed
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

@app.delete("/delete_folder/{folder_name}")
async def delete_folder(folder_name: str):
    # Protect against path traversal attacks by only using the name component
    safe_folder_name = Path(folder_name).name
    
    # Never allow deletion of agent_creator folder
    if safe_folder_name.lower() == "agent_creator":
        raise HTTPException(
            status_code=403,
            detail="Cannot delete the protected agent_creator folder"
        )
    
    folder_path = AGENT_DIR / safe_folder_name
    
    # Check if folder exists
    if not folder_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Folder '{safe_folder_name}' not found"
        )
    
    # Check if it's actually a directory
    if not folder_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"'{safe_folder_name}' is not a directory"
        )
    
    try:
        # Delete the folder and all its contents
        shutil.rmtree(folder_path)
        return {"message": f"Folder '{safe_folder_name}' has been deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting folder: {str(e)}"
        )

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))