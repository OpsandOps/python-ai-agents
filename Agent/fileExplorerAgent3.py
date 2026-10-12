
import json
import os
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ========================================
# Game is not a framework but a design philosophy
# 1. PLAIN DATA CONTAINERS
# important to lay out classes for
# Goal(Prompt)
# Actions
# ActionRegistry
# AgentLanguage
# Memory
# Environment
# and use and overall agent class to help organise the structure

@dataclass(frozen=True)
class Goal:
    priority: int
    name: str
    description: str

@dataclass
class Prompt:
    """What gets sent to the LLM: chat messages plus optional tool definitions."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Action:
    """A capability the agent can use: a name, a Python function, and a schema."""
    name: str
    function: Callable[..., Any]
    description: str
    parameters: Dict[str, Any]
    terminal: bool = False

    def execute(self, **args) -> Any:
        return self.function(**args)


class ActionRegistry:
    """A lookup table of Actions, keyed by name."""

    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register(self, action: Action) -> None:
        self.actions[action.name] = action

    def get_action(self, name: str) -> Optional[Action]:
        return self.actions.get(name)

    def get_actions(self) -> List[Action]:
        return list(self.actions.values())


class Memory:
    """An ordered list of {"type": ..., "content": ...} entries."""

    def __init__(self):
        self.items: List[Dict[str, str]] = []

    def add_memory(self, memory: Dict[str, str]) -> None:
        self.items.append(memory)

    def get_memories(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        return self.items[:limit] if limit else list(self.items)


# =============================================================================
# 2. AGENT LANGUAGE  (collaborator #1)
#    Responsible for translating between the agent's data (pythonObjects: Goals, Actions, Memory)
#     and the LLM's text(text prompts, JSON schemas, chat messages) and
#    the execution world(Runtime tools and results).
#
#    The base class defines the CONTRACT (two abstract methods) and offers
#    small reusable helpers. Subclasses decide the actual format.
# =============================================================================

class AgentLanguage(ABC):
    """Contract: how the agent talks to, and listens to, the LLM."""

    # ---- the two methods every language MUST implement ---------------------

    @abstractmethod
    def construct_prompt(
        self,
        actions: List[Action],
        environment: "Environment",
        goals: List[Goal],
        memory: Memory,
    ) -> Prompt:
        """Goals + Actions + Memory  ->  a Prompt with chat messages and tool schema ready for the LLM."""

    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """LLM reply text  ->  {"tool": <action name>, "args": {...}}."""

    # ---- reusable helpers any subclass can call ----------------------------

    def format_goals(self, goals: List[Goal]) -> str:
        """Render goals as text, ordered by priority."""
        ordered = sorted(goals, key=lambda g: g.priority)
        return "\n".join(f"{g.name}: {g.description}" for g in ordered)

    def format_memory(self, memory: Memory) -> List[Dict[str, str]]:
        """Convert memory entries into chat messages."""
        role_map = {"assistant": "assistant", "system": "system"}
        return [
            {"role": role_map.get(m["type"], "user"), "content": m["content"]}
            for m in memory.get_memories()
        ]


class AgentFunctionCallingActionLanguage(AgentLanguage):
    """
    Concrete language that uses the LLM's native function-calling.

    Output of construct_prompt:  system message + memory messages + tool schemas
    Expected LLM reply:          JSON like {"tool": "read_file", "args": {"file_name": "a.txt"}}
    """

    def construct_prompt(self, actions, environment, goals, memory) -> Prompt:
        system_message = {
            "role": "system",
            "content": (
                "You are an agent. Pursue these goals in priority order:\n"
                f"{self.format_goals(goals)}\n\n"
                "Always respond by calling one of the available tools."
            ),
        }
        messages = [system_message] + self.format_memory(memory)
        tools = self._format_tools(actions)
        return Prompt(messages=messages, tools=tools)

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(response)
            if "tool" in parsed and "args" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        # LLM answered in plain text instead of calling a tool: treat as final message
        return {"tool": "terminate", "args": {"message": response}}

    # private: only this subclass cares about the tool-schema format
    def _format_tools(self, actions: List[Action]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": a.name,
                    "description": a.description[:1024],
                    "parameters": a.parameters or {"type": "object", "properties": {}},
                },
            }
            for a in actions
        ]


# =============================================================================
# 3. ENVIRONMENT  (collaborator #2)
#    Responsible for actually running an Action and reporting what happened.
#    It never talks to the LLM and never decides what to do next.
# =============================================================================

class Environment:
    """Executes actions and returns a uniform result dictionary."""

    def execute_action(self, action: Action, args: dict) -> dict:
        """Run the action's function; always return a dict, never raise."""
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def format_result(self, result: Any) -> dict:
        """One place that defines what a successful result looks like."""
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }


# =============================================================================
# 4. LLM CALL  (collaborator #3, injected as a plain function)
# =============================================================================

MODEL = os.environ.get("AGENT_MODEL", "openai/gpt-4o")  # any litellm model string


def generate_response(prompt: Prompt) -> str:
    """Call the LLM. Returns tool calls as JSON text, otherwise plain text."""
    from litellm import completion  # pip install litellm

    kwargs = {"model": MODEL, "messages": prompt.messages, "max_tokens": 1024}
    if prompt.tools:
        kwargs["tools"] = prompt.tools

    message = completion(**kwargs).choices[0].message

    if getattr(message, "tool_calls", None):
        call = message.tool_calls[0]
        return json.dumps(
            {"tool": call.function.name, "args": json.loads(call.function.arguments)}
        )
    return message.content


# =============================================================================
# 5. AGENT  (the orchestrator)
#    Note how each method delegates: the Agent decides WHEN, others decide HOW.
# =============================================================================

class Agent:
    def __init__(
        self,
        goals: List[Goal],
        agent_language: AgentLanguage,
        action_registry: ActionRegistry,
        generate_response: Callable[[Prompt], str],
        environment: Environment,
    ):
        self.goals = goals
        self.agent_language = agent_language
        self.actions = action_registry
        self.generate_response = generate_response
        self.environment = environment

    def build_prompt(self, memory: Memory) -> Prompt:
        # delegates to AgentLanguage (different object, so not recursion)
        return self.agent_language.construct_prompt(
            actions=self.actions.get_actions(),
            environment=self.environment,
            goals=self.goals,
            memory=memory,
        )

    def get_action(self, response: str) -> Tuple[Action, dict]:
        invocation = self.agent_language.parse_response(response)  # AgentLanguage
        action = self.actions.get_action(invocation["tool"])       # ActionRegistry
        return action, invocation

    def set_current_task(self, memory: Memory, task: str) -> None:
        memory.add_memory({"type": "user", "content": task})

    def update_memory(self, memory: Memory, response: str, result: dict) -> None:
        memory.add_memory({"type": "assistant", "content": response})
        memory.add_memory({"type": "user", "content": json.dumps(result, default=str)})

    def run(self, user_input: str, memory: Optional[Memory] = None,
            max_iterations: int = 50) -> Memory:
        memory = memory or Memory()
        self.set_current_task(memory, user_input)

        for _ in range(max_iterations):
            prompt = self.build_prompt(memory)                          # AgentLanguage
            print("Agent thinking...")
            response = self.generate_response(prompt)                   # LLM
            print(f"Agent Decision: {response}")

            action, invocation = self.get_action(response)              # AgentLanguage + Registry
            result = self.environment.execute_action(action, invocation["args"])  # Environment
            print(f"Action Result: {result}")

            self.update_memory(memory, response, result)
            if action.terminal:
                break

        return memory


# =============================================================================
# 6. WIRING IT ALL TOGETHER
# =============================================================================

def build_file_explorer_agent() -> Agent:
    goals = [
        Goal(1, "Explore Files",
             "Explore files in the current directory by listing and reading them"),
        Goal(2, "Terminate",
             "Terminate the session when tasks are complete with a helpful summary"),
    ]

    # ---- tool functions ----
    def list_files() -> List[str]:
        """List files in the current directory."""
        return os.listdir(".")

    def read_file(file_name: str) -> str:
        """Read a file's contents."""
        try:
            with open(file_name, "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: {file_name} not found."
        except Exception as e:
            return f"Error: {e}"

    def terminate(message: str) -> str:
        """Terminate the agent loop and provide a summary message."""
        return message

    # ---- register them as Actions ----
    registry = ActionRegistry()
    registry.register(Action(
        name="list_files", function=list_files,
        description="Returns a list of files in the directory.",
        parameters={}, terminal=False,
    ))
    registry.register(Action(
        name="read_file", function=read_file,
        description="Reads the content of a specified file in the directory.",
        parameters={
            "type": "object",
            "properties": {"file_name": {"type": "string"}},
            "required": ["file_name"],
        },
        terminal=False,
    ))
    registry.register(Action(
        name="terminate", function=terminate,
        description="Terminates the conversation. Prints the provided message for the user.",
        parameters={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        terminal=True,
    ))

    return Agent(
        goals=goals,
        agent_language=AgentFunctionCallingActionLanguage(),
        action_registry=registry,
        generate_response=generate_response,
        environment=Environment(),
    )


def main():
    agent = build_file_explorer_agent()
    user_input = input("What would you like me to do? ")
    final_memory = agent.run(user_input, max_iterations=10)

    for item in final_memory.get_memories():
        print(f"\nMemory: {item['content']}")


if __name__ == "__main__":
    main()