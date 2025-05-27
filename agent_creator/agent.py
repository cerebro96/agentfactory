from google.adk.agents import Agent
from .tools.file_operations import create_agent_directory_structure # Import the function

root_agent = Agent(
    name="agent_creator",
    model="gemini-2.5-pro-preview-05-06",
    description=(
        "An agent that creates directory structures and agent definition files based on a JSON configuration. "
        "Each created main agent directory will include an __init__.py file, a .env file "
        "(if an 'apiKey' is provided in the JSON for that agent), and an agent.py file containing the agent logic."
    ),
    instruction=(
        "You are an agent designed to create directory structures and Python agent definition files for other agents. "
        "Your primary task is to process a JSON string of agent configurations provided by the user. "
        "Each 'Multi Agent' configuration in the JSON should include: 'name', 'model', 'instructions' (can be string or array), 'description', 'apiKey', "
        "and optionally 'connected_agents' (each with 'name', 'model', 'instruction', and optional 'tools' field). "
        "The 'tools' field for sub-agents can include: 'YahooFinanceNewsTool', 'get_price', 'BraveSearchTool', 'ScrapeWebsiteTool', 'EXASearchTool', 'hyperbrowser_tool', 'serper_tool'. "
        "If a sub-agent uses 'BraveSearchTool', it should have a 'BraveSearchAPIKey' field. "
        "If a sub-agent uses 'EXASearchTool', it should have an 'EXA_API_KEY' field. "
        "If a sub-agent uses 'hyperbrowser_tool', it should have a 'HYPERBROWSER_API_KEY' field. "
        "If a sub-agent uses 'serper_tool', it should have a 'SERPER_API_KEY' field. "
        "Upon receiving the JSON, immediately use the 'create_agent_directory_structure' tool. "
        "This tool will create a main directory for each 'Multi Agent'. Inside each of these directories, it will also create: "
        "1. An __init__.py file (containing 'from . import agent'). "
        "2. A .env file containing GOOGLE_GENAI_USE_VERTEXAI=FALSE, GOOGLE_API_KEY=the_value_from_json, BRAVE_API_KEY if BraveSearchTool is used, EXA_API_KEY if EXASearchTool is used, HYPERBROWSER_API_KEY if hyperbrowser_tool is used, and SERPER_API_KEY if serper_tool is used. "
        "3. An agent.py file, which defines the coordinator agent and its sub-agents (if any) with appropriate tools based on the JSON configuration. "
        "Directories will be created in the current working directory by default. "
        "If the user *explicitly* provides a base output directory path alongside the JSON, pass this path to the tool. "
        "Do not ask for the base output directory if it's not provided; proceed with the default. "
        "After the tool has run, confirm the action taken (including the creation of directories and all three types of files) and the outcome to the user using json format."
    ),
    tools=[create_agent_directory_structure], # This now refers to the imported function
)