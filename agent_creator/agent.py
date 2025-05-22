import json
import os
from google.adk.agents import Agent

def create_agent_directory_structure(agent_config_json: str, base_output_dir: str = "."):
    """
    Parses agent configuration JSON and creates a directory structure.
    For each 'Multi Agent' type, creates a main directory and subdirectories 
    for its 'connected_agents'.

    Args:
        agent_config_json: A JSON string containing a list of agent configurations.
        base_output_dir: The base directory where agent folders will be created. 
                         Defaults to the current directory.
    """
    try:
        agent_configs = json.loads(agent_config_json)
        if not isinstance(agent_configs, list):
            print("Error: Expected a list of agent configurations in JSON.")
            return

        for config in agent_configs:
            if config.get("type") == "Multi Agent":
                main_agent_name = config.get("name")
                if not main_agent_name or not isinstance(main_agent_name, str) or not main_agent_name.strip():
                    print(f"Skipping Multi Agent with missing or invalid name (id: {config.get('id')}).")
                    continue
                
                # Basic sanitization for folder names
                safe_main_agent_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in main_agent_name)
                if not safe_main_agent_name: # Handle cases where name becomes empty after sanitization
                    print(f"Skipping Multi Agent due to empty name after sanitization: Original '{main_agent_name}'")
                    continue

                main_agent_dir = os.path.join(base_output_dir, safe_main_agent_name)
                
                try:
                    os.makedirs(main_agent_dir, exist_ok=True)
                    print(f"Ensured directory exists: {main_agent_dir}")

                except OSError as e:
                    print(f"Error creating directory {main_agent_dir}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing agent {safe_main_agent_name}: {e}")
            # else:
            #     # Optionally, handle or log other agent types
            #     # print(f"Configuration for '{config.get('name', 'Unknown')}' is not of type 'Multi Agent'. Skipping.")
            #     pass


    except json.JSONDecodeError:
        print("Error: Invalid JSON provided. Failed to decode.")
    except Exception as e: 
        print(f"An unexpected error occurred at the top level of create_agent_directory_structure: {e}")


root_agent = Agent(
    name="directory_creator_agent",
    model="gemini-2.5-pro-preview-05-06",
    description="An agent that creates directory structures based on a JSON configuration provided by the user.",
    instruction=(
        "You are an agent designed to create directory structures. "
        "Your primary task is to process a JSON string of agent configurations provided by the user. "
        "Upon receiving the JSON, immediately use the 'create_agent_directory_structure' tool. "
        "This tool will create directories in the current working directory by default. "
        "If the user *explicitly* provides a base output directory path alongside the JSON, pass this path to the tool. "
        "Do not ask for the base output directory if it's not provided; proceed with the default. "
        "After the tool has run, confirm the action taken and the outcome to the user."
    ),
    tools=[create_agent_directory_structure],
)