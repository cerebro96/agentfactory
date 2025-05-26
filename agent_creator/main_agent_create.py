from pathlib import Path

def _generate_agent_python_code(agent_config: dict) -> str:
    """Generates the Python code string for an agent.py file based on the agent configuration."""
    agent_name = agent_config.get("name", "UnnamedAgent")
    agent_model = agent_config.get("model", "gemini-2.0-flash") # Default model if not specified
    agent_instruction = agent_config.get("instructions", "You are a helpful assistant.")
    agent_description = agent_config.get("description", "An agent.")

    connected_agents = agent_config.get("connected_agents", [])
    sub_agent_definitions = []
    sub_agent_names_list = []

    for sub_agent_conf in connected_agents:
        sub_name = sub_agent_conf.get("name", "UnnamedSubAgent")
        sub_model = sub_agent_conf.get("model", "gemini-2.0-flash") # Default model
        sub_description = sub_agent_conf.get("description", "A sub-agent.")
        safe_sub_name_var = "".join(c if c.isalnum() else '_' for c in sub_name).lower() + "_agent"
        
        # Escape sub_description for use within a double-quoted string in the generated code
        escaped_sub_description = sub_description.replace('"', '\\"')

        sub_agent_code = f"""{safe_sub_name_var} = LlmAgent(
    name=\"{sub_name}\",
    model=\"{sub_model}\",
    description=\"{escaped_sub_description}\"
)"""
        sub_agent_definitions.append(sub_agent_code)
        sub_agent_names_list.append(safe_sub_name_var)

    sub_agents_list_str = ", ".join(sub_agent_names_list)
    if not sub_agents_list_str: # Handle case with no sub_agents
        sub_agents_list_str = "[]"
    else:
        sub_agents_list_str = f"[{sub_agents_list_str}]"

    # Escape double quotes in instructions and descriptions for the main agent
    escaped_instruction = agent_instruction.replace('"', '\\"')
    escaped_description = agent_description.replace('"', '\\"')

    code = [
        "from google.adk.agents import LlmAgent",
        ""
    ]
    code.extend(sub_agent_definitions)
    if sub_agent_definitions:
        code.append("") # Add a blank line if there were sub_agents
    
    code.extend([
        f'coordinator = LlmAgent(\n'
        f'    name="{agent_name}",\n'
        f'    model="{agent_model}",\n'
        f'    instruction="""{escaped_instruction}""",\n'
        f'    description="""{escaped_description}""",\n'
        f'    sub_agents={sub_agents_list_str}\n'
        f')',
        "",
        "root_agent = coordinator"
    ])
    
    return "\n".join(code) + "\n"

def create_agent_definition_file(agent_config: dict, target_dir_path: Path):
    """Creates the agent.py file with the agent definition in the target directory."""
    agent_py_path = target_dir_path / "agent.py"
    python_code = _generate_agent_python_code(agent_config)
    
    try:
        with open(agent_py_path, "w") as f:
            f.write(python_code)
        print(f"Successfully created agent definition file: {agent_py_path}")
    except IOError as e:
        print(f"Error creating agent definition file {agent_py_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating agent definition file {agent_py_path}: {e}") 