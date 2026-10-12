"""
Converted from fileExplorer.ipynb for command-line execution
"""

import json, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

MODEL = "gemini/gemini-3.6-flash"
MAX_OUTPUT_CHARS = 20_000

# ----------------------------------------------------------------
# GAME Framework Classes
# ----------------------------------------------------------------

@dataclass
class Goal:
    priority: int
    name: str
    description: str


@dataclass
class Action:
    name: str
    function: Callable
    description: str
    parameters: dict = field(default_factory=dict)
    terminal: bool = False


class ActionRegistry:
    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register(self, action: Action):
        self.actions[action.name] = action

    def get(self, name: str) -> Optional[Action]:
        return self.actions.get(name)


class Memory:
    def __init__(self):
        self.items: List[dict] = []

    def add_memory(self, type: str, content: str):
        self.items.append({"type": type, "content": content})

    def get_memories(self) -> List[dict]:
        return self.items


class Environment:
    """Runs actions and reports the outcome; errors go back to the agent instead of crashing the loop."""

    def execute_action(self, action: Action, args: dict) -> dict:
        try:
            return {"tool_executed": True, "result": action.function(**args)}
        except Exception as e:
            return {"tool_executed": False, "error": f"{type(e).__name__}: {e}"}


# ----------------------------------------------------------------
# Agent Language and Loop
# ----------------------------------------------------------------

class AgentFunctionCallingActionLanguage:
    """Turns goals + actions + memory into a Gemini function-calling request, and parses the reply."""

    def construct_prompt(self, actions: ActionRegistry, goals: List[Goal], memory: Memory) -> dict:
        goal_text = "\n".join(f"{g.priority}. {g.name}: {g.description}" for g in sorted(goals, key=lambda g: g.priority))
        messages = [{"role": "system", "content": "You are an AI agent. Your goals, in priority order:\n"
                     f"{goal_text}\n\nOn every turn, call exactly one tool."}]
        for m in memory.get_memories():
            messages.append({"role": "assistant" if m["type"] == "assistant" else "user", "content": m["content"]})
        tools = [{"type": "function", "function": {
                    "name": a.name, "description": a.description,
                    **({{"parameters": a.parameters}} if a.parameters else {})}}
                 for a in actions.actions.values()]
        return {"messages": messages, "tools": tools}

    def parse_response(self, response) -> dict:
        msg = response.choices[0].message
        if msg.tool_calls:
            call = msg.tool_calls[0]
            return {"tool": call.function.name, "args": json.loads(call.function.arguments or "{}")}
        return {"tool": "terminate", "args": {"message": msg.content or ""}}


def generate_response(prompt: dict):
    return completion(model=MODEL, messages=prompt["messages"], tools=prompt["tools"], tool_choice="required")


class Agent:
    def __init__(self, goals, agent_language, action_registry, generate_response, environment):
        self.goals, self.agent_language, self.action_registry = goals, agent_language, action_registry
        self.generate_response, self.environment = generate_response, environment

    def run(self, user_input: str, memory: Optional[Memory] = None, max_iterations: int = 10) -> Memory:
        memory = memory or Memory()
        memory.add_memory("user", user_input)
        for i in range(1, max_iterations + 1):
            prompt = self.agent_language.construct_prompt(self.action_registry, self.goals, memory)
            call = self.agent_language.parse_response(self.generate_response(prompt))
            action = self.action_registry.get(call["tool"])
            result = (self.environment.execute_action(action, call["args"]) if action
                      else {"tool_executed": False, "error": f"Unknown tool: {call['tool']}"})

            memory.add_memory("assistant", json.dumps(call))
            memory.add_memory("environment", json.dumps(result, default=str)[:MAX_OUTPUT_CHARS])
            print(f"[{i}] {call['tool']}({call['args']})")

            if action and action.terminal:
                print("\n" + "="*70)
                print("FINAL RESULT:")
                print("="*70)
                print(str(result.get("result", result)))
                return memory
        print(f"Stopped after {max_iterations} iterations without terminating.")
        return memory


# ----------------------------------------------------------------
# Goals and Actions
# ----------------------------------------------------------------

goals = [
    Goal(priority=1, name="Explore Files",
         description="Explore files in the current directory by listing and reading them"),
    Goal(priority=2, name="Terminate",
         description="Terminate the session when tasks are complete with a helpful summary"),
]


def list_files() -> List[str]:
    """List files in the current directory."""
    return sorted(os.listdir("."))


def read_file(file_name: str) -> str:
    """Read a file's contents (only inside the working directory)."""
    path = Path(file_name).resolve()
    if not path.is_relative_to(Path.cwd()):
        raise PermissionError("can only read files inside the working directory")
    return path.read_text()


def terminate(message: str) -> str:
    """Terminate the agent loop and provide a summary message."""
    return message


action_registry = ActionRegistry()

action_registry.register(Action(
    name="list_files", function=list_files,
    description="Returns a list of files in the directory."))
action_registry.register(Action(
    name="read_file", function=read_file,
    description="Reads the content of a specified file in the directory.",
    parameters={"type": "object", "properties": {"file_name": {"type": "string"}}, "required": ["file_name"]}))
action_registry.register(Action(
    name="terminate", function=terminate, terminal=True,
    description="Terminates the conversation. Prints the provided message for the user.",
    parameters={"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}))


# ----------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------

if __name__ == "__main__":
    print("="*70)
    print("FILE EXPLORER AGENT")
    print("="*70)
    
    file_explorer_agent = Agent(
        goals=goals,
        agent_language=AgentFunctionCallingActionLanguage(),
        action_registry=action_registry,
        generate_response=generate_response,
        environment=Environment(),
    )

    TASK = "List the files here and summarize what each one does."
    print(f"\nTASK: {TASK}\n")
    
    final_memory = file_explorer_agent.run(TASK, max_iterations=10)
    
    print("\n" + "="*70)
    print("MEMORY TRACE:")
    print("="*70)
    for item in final_memory.get_memories():
        print(f"\n{item['type'].upper()}: {item['content'][:500]}")
