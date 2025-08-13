from pathlib import Path
from .string_utils import _break_long_line

def _generate_agent_python_code(agent_config: dict) -> str:
    """Generates the Python code string for an agent.py file based on the agent configuration."""
    agent_name = agent_config.get("name", "UnnamedAgent")
    agent_model = agent_config.get("model", "gemini-2.0-flash")
    agent_provider = agent_config.get("provider", "gemini")
    
    # Handle instructions as either string or array
    agent_instructions = agent_config.get("instructions", "You are a helpful assistant.")
    if isinstance(agent_instructions, list):
        # Keep as list for special formatting later
        agent_instruction_list = agent_instructions
    else:
        agent_instruction_list = [agent_instructions]
    
    agent_description = agent_config.get("description", "An agent.")

    connected_agents = agent_config.get("connected_agents", [])
    sub_agent_definitions = []
    sub_agent_names_list = []
    
    # Track which tools are needed for imports
    tools_needed = set()
    has_get_price = False
    has_mcp_tool = False
    mcp_configs = []  # Store MCP configurations with agent info
    mcp_toolsets = {}  # Map agent names to their MCP toolset variables
    
    # Track if we need ParallelAgent or SequentialAgent
    needs_parallel_agent = False
    needs_sequential_agent = False
    
    # Track if we need LiteLLM
    needs_litellm = agent_provider in ["anthropic", "openai", "deepseek"]
    
    def process_agent_recursive(agent_conf, is_sub_agent=False):
        """Recursively process agents and their connected agents"""
        nonlocal needs_parallel_agent, needs_sequential_agent, needs_litellm, has_mcp_tool, mcp_configs, mcp_toolsets
        
        agent_type = agent_conf.get("type", "LLM Agent")
        sub_name = agent_conf.get("name", "UnnamedSubAgent")
        sub_model = agent_conf.get("model", "gemini-2.0-flash")
        sub_provider = agent_conf.get("provider", "gemini")
        sub_instruction = agent_conf.get("instruction", "You are a helpful sub-agent.")
        sub_tools = agent_conf.get("tools", "")
        sub_description = agent_conf.get("description", "An agent.")
        
        # Check if this sub-agent needs LiteLLM
        if sub_provider in ["anthropic", "openai", "deepseek"]:
            needs_litellm = True
        
        safe_sub_name_var = "".join(c if c.isalnum() else '_' for c in sub_name).lower() + "_agent"
        
        # Escape sub_instruction for use within a double-quoted string
        escaped_sub_instruction = sub_instruction.replace('"', '\\"')
        escaped_sub_description = sub_description.replace('"', '\\"')
        
        # Format model based on provider
        if sub_provider == "anthropic":
            # Add anthropic prefix if not already present
            if not sub_model.startswith("anthropic/"):
                formatted_model = f"anthropic/{sub_model}"
            else:
                formatted_model = sub_model
            model_str = f'LiteLlm(model="{formatted_model}")'
        elif sub_provider == "openai":
            # Add openai prefix if not already present
            if not sub_model.startswith("openai/"):
                formatted_model = f"openai/{sub_model}"
            else:
                formatted_model = sub_model
            model_str = f'LiteLlm(model="{formatted_model}")'
        elif sub_provider == "deepseek":
            # Add deepseek prefix if not already present
            if not sub_model.startswith("deepseek/"):
                formatted_model = f"deepseek/{sub_model}"
            else:
                formatted_model = sub_model
            model_str = f'LiteLlm(model="{formatted_model}")'
        else:
            model_str = f'"{sub_model}"'
        
        if agent_type == "Parallel agent":
            needs_parallel_agent = True
            # Process connected agents first
            nested_sub_agents = []
            for nested_agent in agent_conf.get("connected_agents", []):
                nested_agent_var = process_agent_recursive(nested_agent, True)
                nested_sub_agents.append(nested_agent_var)
            
            nested_sub_agents_str = f"[{', '.join(nested_sub_agents)}]" if nested_sub_agents else "[]"
            
            sub_agent_code = f"""{safe_sub_name_var} = ParallelAgent(
    name="{sub_name}",
    sub_agents={nested_sub_agents_str},
    description="{escaped_sub_description}"
)"""
            sub_agent_definitions.append(sub_agent_code)
            if not is_sub_agent:
                sub_agent_names_list.append(safe_sub_name_var)
            return safe_sub_name_var
            
        elif agent_type == "Sequential agent":
            needs_sequential_agent = True
            # Process connected agents first
            nested_sub_agents = []
            for nested_agent in agent_conf.get("connected_agents", []):
                nested_agent_var = process_agent_recursive(nested_agent, True)
                nested_sub_agents.append(nested_agent_var)
            
            nested_sub_agents_str = f"[{', '.join(nested_sub_agents)}]" if nested_sub_agents else "[]"
            
            sub_agent_code = f"""{safe_sub_name_var} = SequentialAgent(
    name="{sub_name}",
    sub_agents={nested_sub_agents_str},
    description="{escaped_sub_description}"
)"""
            sub_agent_definitions.append(sub_agent_code)
            if not is_sub_agent:
                sub_agent_names_list.append(safe_sub_name_var)
            return safe_sub_name_var
            
        else:  # Regular LLM Agent
            # Determine tools for this sub-agent
            tools_list = []
            if "YahooFinanceNewsTool" in sub_tools:
                tools_needed.add("YahooFinanceNewsTool")
                tools_list.append("news_tool")
            if "get_price" in sub_tools:
                nonlocal has_get_price
                has_get_price = True
                tools_list.append("get_price")
            if "BraveSearchTool" in sub_tools:
                tools_needed.add("BraveSearchTool")
                tools_list.append("search_tool")
            if "ScrapeWebsiteTool" in sub_tools:
                tools_needed.add("ScrapeWebsiteTool")
                tools_list.append("scrape_tool")
            if "EXASearchTool" in sub_tools:
                tools_needed.add("EXASearchTool")
                tools_list.append("EXASearchTool")
            if "hyperbrowser_tool" in sub_tools:
                tools_needed.add("hyperbrowser_tool")
                tools_list.append("hyperbrowser_tool")
            if "serper_tool" in sub_tools:
                tools_needed.add("serper_tool")
                tools_list.append("serper_tool")
            if "mcp_tool" in sub_tools:
                has_mcp_tool = True
                # Store MCP configuration for this agent
                mcp_config = agent_conf.get("mcp_config", {})
                if mcp_config:
                    # Create unique toolset variable name for this agent
                    safe_agent_name = "".join(c if c.isalnum() else '_' for c in sub_name).lower()
                    toolset_var_name = f"mcp_toolset_{safe_agent_name}"
                    mcp_configs.append({
                        "config": mcp_config,
                        "agent_name": sub_name,
                        "toolset_var": toolset_var_name
                    })
                    mcp_toolsets[sub_name] = toolset_var_name
                    tools_list.append(toolset_var_name)
                else:
                    tools_list.append("mcp_toolset")
            
            tools_str = f"[{', '.join(tools_list)}]" if tools_list else "[]"

            sub_agent_code = f"""{safe_sub_name_var} = Agent(
    name="{sub_name}",
    model={model_str},
    instruction="{escaped_sub_instruction}",
    tools={tools_str}
)"""
            sub_agent_definitions.append(sub_agent_code)
            if not is_sub_agent:
                sub_agent_names_list.append(safe_sub_name_var)
            return safe_sub_name_var
    
    # Process all connected agents
    for sub_agent_conf in connected_agents:
        process_agent_recursive(sub_agent_conf)

    sub_agents_list_str = ", ".join(sub_agent_names_list)
    if not sub_agents_list_str:
        sub_agents_list_str = "[]"
    else:
        sub_agents_list_str = f"[{sub_agents_list_str}]"

    # Escape double quotes in description for the main agent
    escaped_description = agent_description.replace('"', '\\"')

    # Build imports section
    imports = ["from google.adk.agents import Agent, LlmAgent"]
    
    # Add ParallelAgent and SequentialAgent imports if needed
    if needs_parallel_agent or needs_sequential_agent:
        additional_imports = []
        if needs_parallel_agent:
            additional_imports.append("ParallelAgent")
        if needs_sequential_agent:
            additional_imports.append("SequentialAgent")
        imports[0] = f"from google.adk.agents import Agent, LlmAgent, {', '.join(additional_imports)}"
    
    # Add LiteLLM import if needed
    if needs_litellm:
        imports.append("from google.adk.models.lite_llm import LiteLlm")
    
    if "YahooFinanceNewsTool" in tools_needed:
        imports.append("from google.adk.tools.langchain_tool import LangchainTool")
        imports.append("from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool")
    
    if "BraveSearchTool" in tools_needed or "ScrapeWebsiteTool" in tools_needed or "EXASearchTool" in tools_needed or "serper_tool" in tools_needed:
        imports.append("from google.adk.tools.crewai_tool import CrewaiTool")
        
    if "BraveSearchTool" in tools_needed:
        imports.append("from crewai_tools import BraveSearchTool")
    
    if "ScrapeWebsiteTool" in tools_needed:
        imports.append("from crewai_tools import ScrapeWebsiteTool")
    
    if "EXASearchTool" in tools_needed:
        imports.append("from crewai_tools import EXASearchTool")
    
    if "serper_tool" in tools_needed:
        imports.append("from crewai_tools import SerperDevTool")
    
    if has_get_price:
        imports.append("import yfinance as yf")
    
    if "hyperbrowser_tool" in tools_needed:
        imports.append("from hyperbrowser import Hyperbrowser")
        imports.append("from hyperbrowser.models import StartBrowserUseTaskParams")
    
    if has_mcp_tool:
        imports.append("from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams,SseConnectionParams")
        imports.append("from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset")
        imports.append("import json")
    
    # Add os and dotenv imports if EXASearchTool, hyperbrowser_tool, serper_tool, or mcp_tool is used
    if "EXASearchTool" in tools_needed or "hyperbrowser_tool" in tools_needed or "serper_tool" in tools_needed or has_mcp_tool:
        imports.insert(0, "import os")
        imports.insert(1, "from dotenv import load_dotenv")

    # Build code
    code = imports
    code.append("")
    
    # Add load_dotenv() call if EXASearchTool, hyperbrowser_tool, serper_tool, or mcp_tool is used
    if "EXASearchTool" in tools_needed or "hyperbrowser_tool" in tools_needed or "serper_tool" in tools_needed or has_mcp_tool:
        code.append("# Load environment variables")
        code.append("load_dotenv()")
        code.append("")
    
    # Add tool definitions if needed
    tool_definitions = []
    
    if has_get_price:
        tool_definitions.extend([
            "# Define custom tool for fetching stock prices",
            "def get_price(tkr: str):",
            '    """Returns the latest close price for a stock ticker."""',
            '    data = yf.Ticker(tkr).history(period="1d")',
            "    return float(data['Close'][-1]) if not data.empty else None",
            ""
        ])
    
    if "YahooFinanceNewsTool" in tools_needed:
        tool_definitions.append("# Define news tool")
        tool_definitions.append("news_tool = LangchainTool(YahooFinanceNewsTool())")
        tool_definitions.append("")
    
    if "BraveSearchTool" in tools_needed:
        tool_definitions.append("# Define search tool")
        tool_definitions.append("BraveSrcTool = BraveSearchTool()")
        tool_definitions.append('search_tool = CrewaiTool(tool=BraveSrcTool, name="web_search", description="A tool for performing web searches using Brave.")')
        tool_definitions.append("")
    
    if "ScrapeWebsiteTool" in tools_needed:
        tool_definitions.append("# Define scrape tool")
        tool_definitions.append("ScrapeSitetool = ScrapeWebsiteTool()")
        tool_definitions.append('scrape_tool = CrewaiTool(tool=ScrapeSitetool, name="scraper", description="Scrape a URL to get its content.")')
        tool_definitions.append("")
    
    if "EXASearchTool" in tools_needed:
        tool_definitions.append("# Define EXA search tool")
        tool_definitions.append("EXASchTool = EXASearchTool(os.getenv('EXA_API_KEY'))")
        tool_definitions.append('EXASearchTool = CrewaiTool(tool=EXASchTool, name="EXA_search", description="A tool for performing EXA searches using EXA.")')
        tool_definitions.append("")
    
    if "hyperbrowser_tool" in tools_needed:
        tool_definitions.extend([
            "# Define Hyperbrowser tool",
            "def hyperbrowser_tool(task: str):",
            '    """Uses Hyperbrowser to perform browser automation tasks and extract information from websites."""',
            "    hb_client = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))",
            "    ",
            "    try:",
            "        resp = hb_client.agents.browser_use.start_and_wait(",
            "            StartBrowserUseTaskParams(task=task)",
            "        )",
            "        return resp.data.final_result",
            "    except Exception as e:",
            '        return f"Error executing browser task: {e}"',
            ""
        ])
    
    if "serper_tool" in tools_needed:
        tool_definitions.append("# Define Serper search tool")
        tool_definitions.append("SerperDevToolInstance = SerperDevTool()")
        tool_definitions.append('serper_tool = CrewaiTool(tool=SerperDevToolInstance, name="serper_search", description="A tool for performing web searches using Serper.")')
        tool_definitions.append("")
    
    if has_mcp_tool:
        tool_definitions.append("# Define MCP tools")
        tool_definitions.append("")
        
        # Add MCPToolset definition for each MCP config with individual API keys
        for mcp_info in mcp_configs:
            mcp_config = mcp_info["config"]
            mcp_agent_name = mcp_info["agent_name"]  # Use different variable name
            toolset_var = mcp_info["toolset_var"]
            mcp_url = mcp_config.get("url", "")
            mcp_name = mcp_config.get("name", "MCP")

            mcp_auth = mcp_config.get("authentication","No Authentication")
            mcp_tr_proto = mcp_config.get("transport_protocol","HTTP")
            # Create safe environment variable name for this agent
            safe_mcp_agent_name = "".join(c.upper() if c.isalnum() else '_' for c in mcp_agent_name)  # Updated variable name
            env_var_name = f"{safe_mcp_agent_name}_MCP_KEY"  # Updated variable name
            headers_var_name = f"{safe_mcp_agent_name}_MCP_HEADERS"  # Updated variable name
            if(mcp_auth == "Bearer Token"):
                tool_definitions.append(f"# Define {mcp_name} toolset for {mcp_agent_name}")  # Updated variable name
                tool_definitions.append(f"{env_var_name} = os.getenv('{env_var_name}')")
                tool_definitions.append(f"{headers_var_name} = json.dumps(")
                tool_definitions.append(f'    {{"Authorization": f"Bearer {{{env_var_name}}}","Content-Type": "application/json"}}')
                tool_definitions.append(")")

            tool_definitions.append("")
            tool_definitions.append(f"{toolset_var} = MCPToolset(")
            if(mcp_tr_proto == "HTTP"):
                tool_definitions.append(f"    connection_params=StreamableHTTPServerParams(")
            elif(mcp_tr_proto == "SSE"):
                tool_definitions.append(f"    connection_params=SseConnectionParams(")

            tool_definitions.append(f"        url='{mcp_url}',")
            if(mcp_auth == "Bearer Token"):
                tool_definitions.append(f"        env={{{headers_var_name}}}")

            tool_definitions.append(f"    ),")
            tool_definitions.append(f")")
            tool_definitions.append("")
    
    code.extend(tool_definitions)
    
    # Add sub-agent definitions
    if sub_agent_definitions:
        code.append("# Define agents")
    code.extend(sub_agent_definitions)
    if sub_agent_definitions:
        code.append("")
    
    # Format main agent model based on provider
    if agent_provider == "anthropic":
        # Add anthropic prefix if not already present
        if not agent_model.startswith("anthropic/"):
            formatted_main_model = f"anthropic/{agent_model}"
        else:
            formatted_main_model = agent_model
        main_model_str = f'LiteLlm(model="{formatted_main_model}")'
    elif agent_provider == "openai":
        # Add openai prefix if not already present
        if not agent_model.startswith("openai/"):
            formatted_main_model = f"openai/{agent_model}"
        else:
            formatted_main_model = agent_model
        main_model_str = f'LiteLlm(model="{formatted_main_model}")'
    elif agent_provider == "deepseek":
        # Add deepseek prefix if not already present
        if not agent_model.startswith("deepseek/"):
            formatted_main_model = f"deepseek/{agent_model}"
        else:
            formatted_main_model = agent_model
        main_model_str = f'LiteLlm(model="{formatted_main_model}")'
    else:
        main_model_str = f'"{agent_model}"'
    
    # Add coordinator definition with properly formatted instruction
    code.extend([
        "# Create the Coordinator Agent",
        f'coordinator = LlmAgent(',
        f'    name="{agent_name}",',
        f'    model={main_model_str},',
        f'    description="{escaped_description}",',
    ])
    
    # Format instruction properly
    instruction_lines_for_code = []
    is_multiline_instruction_output = False

    if len(agent_instruction_list) == 1:
        # Potentially a single line, or a single long line that needs breaking
        escaped_instruction = agent_instruction_list[0].replace('"', '\\"')
        parts = _break_long_line(escaped_instruction, 100) # Max length for instruction="..."
        if len(parts) == 1:
            code.append(f'    instruction="{escaped_instruction}",')
        else:
            is_multiline_instruction_output = True
            code.append('    instruction=(')
            for i, part in enumerate(parts):
                if i < len(parts) - 1 and not part.endswith(' '):
                    # Add space at the end if not already there to ensure proper concatenation
                    instruction_lines_for_code.append(f'        "{part} "')
                else:
                    instruction_lines_for_code.append(f'        "{part}"')
    else:
        # Definitely a multi-line instruction from the JSON list
        is_multiline_instruction_output = True
        code.append('    instruction=(')
        for line_from_json in agent_instruction_list:
            escaped_line = line_from_json.replace('"', '\\"')
            parts = _break_long_line(escaped_line, 120) # Standard max length for lines within parentheses
            for i, part in enumerate(parts):
                if i < len(parts) - 1 and not part.endswith(' '):
                    # Add space at the end if not already there to ensure proper concatenation
                    instruction_lines_for_code.append(f'        "{part} "')
                else:
                    instruction_lines_for_code.append(f'        "{part}"')

    if is_multiline_instruction_output:
        code.extend(instruction_lines_for_code)
        code.append('    ),')
    
    code.extend([
        f'    sub_agents={sub_agents_list_str}',
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
        # Explicitly specify UTF-8 encoding and handle encoding errors
        with open(agent_py_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(python_code)
        print(f"Successfully created agent definition file: {agent_py_path}")
    except IOError as e:
        print(f"Error creating agent definition file {agent_py_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating agent definition file {agent_py_path}: {e}")