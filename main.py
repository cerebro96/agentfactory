import os
import shutil
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Response, Request
from google.adk.cli.fast_api import get_fast_api_app
from agent_creator.tools.file_operations import create_agent_directory_structure
import json
from dotenv import load_dotenv

load_dotenv()

# Get the directory where main.py is located
# AGENT_DIR = Path(__file__).parent.absolute()
AGENT_DIR = os.getenv("AGENT_DIR")
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

# POST endpoint for agent creation
@app.post("/agent_creator")
async def agent_creator(request: Request):
    try:
        # Get JSON payload from request
        payload = await request.json()
        
        agent_config_text = None
        
        # Try to extract the agent config text from various nested structures
        if isinstance(payload, dict):
            # Check for the new nested structure: new_message.parts[0].text
            if "new_message" in payload and isinstance(payload["new_message"], dict):
                new_message = payload["new_message"]
                if "parts" in new_message and isinstance(new_message["parts"], list) and len(new_message["parts"]) > 0:
                    if isinstance(new_message["parts"][0], dict) and "text" in new_message["parts"][0]:
                        agent_config_text = new_message["parts"][0]["text"]
                        print(f"Extracted from new_message.parts[0].text: {agent_config_text}")
            
            # Check for the simpler structure: payload.text
            elif "text" in payload:
                agent_config_text = payload["text"]
                # print(f"Extracted from payload.text: {agent_config_text}")
        
        # If we found agent config text, parse it
        if agent_config_text:
            try:
                agent_configs = json.loads(agent_config_text)
                print(f"Parsed agent configs: {agent_configs}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON in text field: {str(e)}"
                )
        else:
            # Handle the original format for backward compatibility
            if isinstance(payload, dict):
                agent_configs = [payload]
            elif isinstance(payload, list):
                agent_configs = payload
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Payload must contain agent configuration in 'text' field or 'new_message.parts[0].text' field"
                )
        
        # Ensure agent_configs is a list
        if not isinstance(agent_configs, list):
            agent_configs = [agent_configs]
        
        # Ensure each config has the required structure
        for config in agent_configs:
            if not isinstance(config, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Each agent configuration must be an object"
                )
            
            # Set default type if not provided
            if "type" not in config:
                config["type"] = "Multi Agent"
        
        # Convert to JSON string for the function
        json_payload = json.dumps(agent_configs)
        # print(f"Final JSON payload to function: {json_payload}")
        
        # Call the create_agent_directory_structure function with JSON string
        result = create_agent_directory_structure(json_payload, str(AGENT_DIR))
        
        # If the operation is successful, return 200
        return {
            "message": "Agent directory structure created successfully", 
            "agents_processed": len(agent_configs),
            "result": result
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # If there's an error, return appropriate HTTP status
        raise HTTPException(
            status_code=500,
            detail=f"Error creating agent directory structure: {str(e)}"
        )
    
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
    
    folder_path = Path(AGENT_DIR) / safe_folder_name
    
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
    return Response(content="OK", status_code=200, media_type="text/plain")

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))