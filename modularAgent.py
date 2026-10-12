# Goal = What and How (instructions)
from dataclasses import dataclass
from typing import Dict, Callable, Any, List
import os

@dataclass(frozen=True)
class Goal:
    priority: int
    name: str
    description: str

file_management_goal = Goal(
    priority=1,
    name="file_management",
    description="""
    manage files in the given directory by
    1. listing files
    2. reading files
    3. searching withing files when information is required
    """
)
# actions - what the agent can do, agent capability
# actions class and the actions registry
class Action:

    def __init__(
        self, 
        name: str,
        function: Callable,
        description: str,
        parameters: Dict,
        terminal: bool = False
    ):
        self.name = name
        self.function = function
        self.description = description
        self.parameters = parameters
        self.terminal = terminal

    def execute(self, **args) -> Any:
        """execute the action function"""
        return self.function(**args)

# create the list_files function
def list_file(full_path: str) -> list:
    return list(os.listdir(full_path))

def read_files(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read()


# list_file = Action(
#     "list_files",
#     list_files,  # Fixed: was read_files, should be list_files
#     """list all files in the current direction""",
#     {"full_path": os.getcwd()}
# )

# read_file = Action(
#     "read_files",
#     read_files,
#     """read a file to display its content""",
#     {"file_name": "..."}
# )

# list = list_file.execute(full_path=os.getcwd())
# print(list)

# read = read_file.execute(file_name="generator.py")
# print(f"Reading file: {read}")

# action registry provides a way of looking up actions in defined Schema for the LLM
class ActionRegistry:
    def __init__(self):
        self.actions = {}

    def register(self, action: Action):
        # recieves an action object of the action class and stores it in the actions dictionary
        self.actions[action.name] = action 

    def get_action(self, name:str) -> [Action, None]:
        return self.actions.get(name)

    def get_all_actions(self) -> List[Action]:
        return list(self.actions.values())
        
    def get_tools(self) -> List[Dict]:
        """
        Convert every registered action into the JSON format the LLM API
        expects for tool/function definitions.
        """
        return [ {
            "name": action.name,
            "desciption": action.description,
            "parameters": actioin.parameters
        }
        for action in self.actions.values()]

registry = ActionRegistry()

# registering actions in a registry 
registry.register(Action(
    name="list_files",
    function=list_file,  # Fixed: was read_files, should be list_files
    description="""list all files in the current direction""",
    parameters={
        "type": "object",
        "properties": {
            "full_path": {
                "type": "string",
                "description": "the full path of the current working directory"
            }},
        "required": [],
        "terminal": False
    }
))

registry.register(Action(
    name="read_file",
    function=read_files,
    description="""read a given file in the current directory""",
    parameters={
        "type": "object",
        "properties": {
            "file_name": {
                "type": "sting",
                "description": "read a given file from the file listed"   
            }},
        "required": ['file_name']},
    terminal=False
))

# Memory is how the agent remembers as it loops through its iterations
# also defined as classes
# One thing to note is that our memory always has to be represented as a list of messages in the prompt

class Memory:
    def __init__(self):
        self.items = []

    def add_memory(self, memory: Dict):
        self.items.append(memory)

    def get_memories(self, limit: int = None) -> List[Dict]:
        return self.items[:limit]

# Environement is the interface between the agent and the outside world
# instead of usin if/else statements we would like to make them more modular

class Environment:
    def execute_action(self, action: Action, args: dict) -> dict:
        """Execute an action and return the result."""
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def format_result(self, result: Any) -> dict:
        """Format the result with metadata."""
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }

    
 



