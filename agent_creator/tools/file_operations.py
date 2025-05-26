import json
import os
from pathlib import Path
from .main_agent_create import create_agent_definition_file

def create_init_py_file(target_dir_path: Path):
    """Creates an __init__.py file in the target directory with 'from . import agent'."""
    init_file_path = target_dir_path / "__init__.py"
    try:
        with open(init_file_path, "w") as f:
            f.write("from . import agent\n")
        print(f"Successfully created {init_file_path}")
    except IOError as e:
        print(f"Error creating {init_file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating {init_file_path}: {e}")

def create_env_file(api_key_value: str, target_dir_path: Path, brave_api_key: str = None, exa_api_key: str = None):
    """Creates a .env file in the target directory with the provided API keys."""
    env_file_path = target_dir_path / ".env"
    content = f"GOOGLE_GENAI_USE_VERTEXAI=FALSE\nGOOGLE_API_KEY={api_key_value}\n"
    
    if brave_api_key:
        content += f"BRAVE_API_KEY={brave_api_key}\n"
    
    if exa_api_key:
        content += f"EXA_API_KEY={exa_api_key}\n"
    
    try:
        with open(env_file_path, "w") as f:
            f.write(content)
        print(f"Successfully created {env_file_path} with API key(s).")
    except IOError as e:
        print(f"Error creating {env_file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating {env_file_path}: {e}")

def create_agent_directory_structure(agent_config_json: str, base_output_dir: str = "."):
    """
    Parses agent configuration JSON. For each 'Multi Agent' type, creates:
    1. A main directory.
    2. An __init__.py file within it.
    3. A .env file within it (if 'apiKey' is provided).
    4. An agent.py file with the agent definitions within it.

    Args:
        agent_config_json: A JSON string containing agent configurations.
                           Each 'Multi Agent' config should have 'name' and 'apiKey' fields.
        base_output_dir: The base directory for new agent folders. Defaults to current directory.
    """
    try:
        agent_configs = json.loads(agent_config_json)
        if not isinstance(agent_configs, list):
            print("Error: Expected a list of agent configurations in JSON.")
            return

        for config in agent_configs:
            if config.get("type") == "Multi Agent":
                main_agent_name = config.get("name")
                api_key = config.get("apiKey")
                
                # Check for BraveSearchAPIKey and EXAAPIKey in connected_agents
                brave_api_key = None
                exa_api_key = None
                connected_agents = config.get("connected_agents", [])
                for sub_agent in connected_agents:
                    if "BraveSearchTool" in sub_agent.get("tools", ""):
                        brave_api_key = sub_agent.get("BraveSearchAPIKey")
                    if "EXASearchTool" in sub_agent.get("tools", ""):
                        exa_api_key = sub_agent.get("EXA_API_KEY")

                if not main_agent_name or not isinstance(main_agent_name, str) or not main_agent_name.strip():
                    print(f"Skipping Multi Agent with missing or invalid name (id: {config.get('id')}).")
                    continue
                
                safe_main_agent_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in main_agent_name)
                if not safe_main_agent_name:
                    print(f"Skipping Multi Agent due to empty name after sanitization: Original '{main_agent_name}'")
                    continue

                main_agent_dir = Path(base_output_dir) / safe_main_agent_name
                
                try:
                    os.makedirs(main_agent_dir, exist_ok=True)
                    print(f"Ensured directory exists: {main_agent_dir}")
                    
                    create_init_py_file(main_agent_dir)
                    
                    if api_key and isinstance(api_key, str) and api_key.strip():
                        create_env_file(api_key, main_agent_dir, brave_api_key, exa_api_key)
                    else:
                        print(f"Warning: 'apiKey' not found or invalid for agent '{safe_main_agent_name}'. Skipping .env file creation.")
                    
                    # Create the agent.py definition file
                    create_agent_definition_file(config, main_agent_dir)

                except OSError as e:
                    print(f"Error during directory/file creation for {safe_main_agent_name}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing agent {safe_main_agent_name}: {e}")

    except json.JSONDecodeError:
        print("Error: Invalid JSON provided. Failed to decode.")
    except Exception as e: 
        print(f"An unexpected error occurred at the top level of create_agent_directory_structure: {e}") 