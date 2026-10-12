"""
File Explorer Agent - Decorator Pattern Version

This version uses the @register_tool decorator pattern similar to invoiceProcessingAgent.ipynb
instead of explicit Action objects and ActionRegistry.

Key differences from fileExplorerAgent3.py:
1. Uses @register_tool decorator to mark tool functions
2. Auto-discovers tools instead of manual registration
3. Simplified tool definition
4. Still maintains the core agent loop architecture
"""

import json
import os
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# =============================================================================
# 1. PLAIN DATA CONTAINERS
# =============================================================================

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
class ActionContext:
    """Context passed to all tool functions (like invoiceProcessingAgent pattern)."""
    metadata: dict = field(default_factory=dict)


class Memory:
    """An ordered list of {"type": ..., "content": ...} entries."""

    def __init__(self):
        self.items: List[Dict[str, str]] = []

    def add_memory(self, memory: Dict[str, str]) -> None:
        self.items.append(memory)

    def get_memories(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        return self.items[:limit] if limit else list(self.items)


# =============================================================================
# 2. DECORATOR PATTERN - Tool Registration
# =============================================================================

# Global registry to store decorated tools
_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(
    name: str = None,
    description: str = "",
    parameters: Dict[str, Any] = None,
    terminal: bool = False,
    tags: List[str] = None,
):
    """
    Decorator to register a function as a tool.
    
    Usage:
        @register_tool(
            name="list_files",
            description="Lists files in directory",
            parameters={...},
            terminal=False,
            tags=["file_operations"]
        )
        def list_files(action_context: ActionContext) -> List[str]:
            return os.listdir(".")
    """
    def decorator(fn: Callable) -> Callable:
        # Use function name if no name provided
        tool_name = name or fn.__name__
        
        # Attach metadata to the function
        fn.tool_name = tool_name
        fn.tool_description = description or fn.__doc__ or ""
        fn.tool_parameters = parameters or {"type": "object", "properties": {}}
        fn.tool_terminal = terminal
        fn.tool_tags = tags or []
        
        # Register in global registry
        _TOOL_REGISTRY[tool_name] = fn
        
        return fn
    return decorator


def get_all_tools() -> Dict[str, Callable]:
    """Get all registered tools."""
    return _TOOL_REGISTRY.copy()


def get_tool(name: str) -> Optional[Callable]:
    """Get a specific tool by name."""
    return _TOOL_REGISTRY.get(name)


def clear_tools():
    """Clear all registered tools (useful for testing)."""
    _TOOL_REGISTRY.clear()


# =============================================================================
# 3. TOOL DEFINITIONS (Using Decorator Pattern)
# =============================================================================

@register_tool(
    name="list_files",
    description="Returns a list of files in the current directory.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    terminal=False,
    tags=["file_operations", "read"]
)
def list_files(action_context: ActionContext) -> List[str]:
    """List files in the current directory."""
    return sorted(os.listdir("."))


@register_tool(
    name="read_file",
    description="Reads the content of a specified file in the directory.",
    parameters={
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "Name of the file to read"
            }
        },
        "required": ["file_name"]
    },
    terminal=False,
    tags=["file_operations", "read"]
)
def read_file(action_context: ActionContext, file_name: str) -> str:
    """Read a file's contents."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_name} not found."
    except Exception as e:
        return f"Error: {e}"


@register_tool(
    name="terminate",
    description="Terminates the agent loop and provides a summary message.",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Final summary message to display"
            }
        },
        "required": ["message"]
    },
    terminal=True,
    tags=["control"]
)
def terminate(action_context: ActionContext, message: str) -> str:
    """Terminate the agent loop and provide a summary message."""
    return message


# =============================================================================
# 4. AGENT LANGUAGE (Communication Protocol)
# =============================================================================

class AgentLanguage(ABC):
    """Contract: how the agent talks to, and listens to, the LLM."""

    @abstractmethod
    def construct_prompt(
        self,
        tools: Dict[str, Callable],
        environment: "Environment",
        goals: List[Goal],
        memory: Memory,
    ) -> Prompt:
        """Goals + Tools + Memory → a Prompt ready for the LLM."""

    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """LLM reply text → {"tool": <tool name>, "args": {...}}."""

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
    Adapted to work with decorator-registered tools.
    """

    def construct_prompt(self, tools, environment, goals, memory) -> Prompt:
        system_message = {
            "role": "system",
            "content": (
                "You are an agent. Pursue these goals in priority order:\n"
                f"{self.format_goals(goals)}\n\n"
                "Always respond by calling one of the available tools."
            ),
        }
        messages = [system_message] + self.format_memory(memory)
        tool_schemas = self._format_tools(tools)
        return Prompt(messages=messages, tools=tool_schemas)

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(response)
            if "tool" in parsed and "args" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        # LLM answered in plain text instead of calling a tool: treat as final message
        return {"tool": "terminate", "args": {"message": response}}

    def _format_tools(self, tools: Dict[str, Callable]) -> List[Dict[str, Any]]:
        """Convert decorated tool functions to OpenAI tool schema format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": fn.tool_name,
                    "description": fn.tool_description[:1024],
                    "parameters": fn.tool_parameters,
                },
            }
            for fn in tools.values()
        ]


# =============================================================================
# 5. ENVIRONMENT (Execution Runtime)
# =============================================================================

class Environment:
    """Executes tools and returns a uniform result dictionary."""

    def execute_tool(
        self, 
        tool_fn: Callable, 
        args: dict, 
        action_context: ActionContext
    ) -> dict:
        """Run the tool function; always return a dict, never raise."""
        try:
            # All tools receive action_context as first parameter
            result = tool_fn(action_context, **args)
            return self._format_result(result)
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def _format_result(self, result: Any) -> dict:
        """Format a successful result."""
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }


# =============================================================================
# 6. LLM CALL
# =============================================================================

MODEL = os.environ.get("AGENT_MODEL", "openai/gpt-4o")


def generate_response(prompt: Prompt) -> str:
    """Call the LLM. Returns tool calls as JSON text, otherwise plain text."""
    from litellm import completion

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
# 7. AGENT (The Orchestrator)
# =============================================================================

class Agent:
    def __init__(
        self,
        goals: List[Goal],
        agent_language: AgentLanguage,
        tools: Dict[str, Callable],
        generate_response: Callable[[Prompt], str],
        environment: Environment,
    ):
        self.goals = goals
        self.agent_language = agent_language
        self.tools = tools
        self.generate_response = generate_response
        self.environment = environment
        self.action_context = ActionContext()  # Shared context for all tools

    def build_prompt(self, memory: Memory) -> Prompt:
        return self.agent_language.construct_prompt(
            tools=self.tools,
            environment=self.environment,
            goals=self.goals,
            memory=memory,
        )

    def get_tool(self, response: str) -> Tuple[Callable, dict, bool]:
        """Parse response and return (tool_function, args, is_terminal)."""
        invocation = self.agent_language.parse_response(response)
        tool_name = invocation["tool"]
        tool_fn = self.tools.get(tool_name)
        
        if tool_fn is None:
            # Unknown tool - return a dummy function
            def unknown_tool(ctx):
                return f"Error: Unknown tool '{tool_name}'"
            return unknown_tool, invocation, False
        
        is_terminal = getattr(tool_fn, "tool_terminal", False)
        return tool_fn, invocation, is_terminal

    def set_current_task(self, memory: Memory, task: str) -> None:
        memory.add_memory({"type": "user", "content": task})

    def update_memory(self, memory: Memory, response: str, result: dict) -> None:
        memory.add_memory({"type": "assistant", "content": response})
        memory.add_memory({"type": "user", "content": json.dumps(result, default=str)})

    def run(
        self, 
        user_input: str, 
        memory: Optional[Memory] = None,
        max_iterations: int = 50
    ) -> Memory:
        memory = memory or Memory()
        self.set_current_task(memory, user_input)

        for iteration in range(max_iterations):
            prompt = self.build_prompt(memory)
            print(f"\n[Iteration {iteration + 1}] Agent thinking...")
            
            response = self.generate_response(prompt)
            print(f"Agent Decision: {response}")

            tool_fn, invocation, is_terminal = self.get_tool(response)
            result = self.environment.execute_tool(
                tool_fn, 
                invocation["args"], 
                self.action_context
            )
            print(f"Tool Result: {result}")

            self.update_memory(memory, response, result)
            
            if is_terminal:
                print("\n" + "=" * 70)
                print("AGENT TERMINATED")
                print("=" * 70)
                print(f"Final message: {result.get('result', 'Done')}")
                break

        return memory


# =============================================================================
# 8. WIRING IT ALL TOGETHER
# =============================================================================

def build_file_explorer_agent() -> Agent:
    """Build a file explorer agent using decorator-registered tools."""
    goals = [
        Goal(1, "Explore Files",
             "Explore files in the current directory by listing and reading them"),
        Goal(2, "Terminate",
             "Terminate the session when tasks are complete with a helpful summary"),
    ]

    # Get all tools that were registered with @register_tool decorator
    tools = get_all_tools()
    
    print("=" * 70)
    print("REGISTERED TOOLS:")
    print("=" * 70)
    for tool_name, tool_fn in tools.items():
        tags = getattr(tool_fn, "tool_tags", [])
        terminal = getattr(tool_fn, "tool_terminal", False)
        print(f"  • {tool_name}")
        print(f"    Description: {tool_fn.tool_description[:50]}...")
        print(f"    Tags: {tags}")
        print(f"    Terminal: {terminal}")
    print("=" * 70 + "\n")

    return Agent(
        goals=goals,
        agent_language=AgentFunctionCallingActionLanguage(),
        tools=tools,
        generate_response=generate_response,
        environment=Environment(),
    )


def main():
    agent = build_file_explorer_agent()
    user_input = input("What would you like me to do? ")
    final_memory = agent.run(user_input, max_iterations=10)

    print("\n" + "=" * 70)
    print("CONVERSATION HISTORY:")
    print("=" * 70)
    for i, item in enumerate(final_memory.get_memories(), 1):
        print(f"\n[{i}] Type: {item.get('type', 'unknown')}")
        content = item['content']
        if len(content) > 200:
            content = content[:200] + "..."
        print(f"Content: {content}")


if __name__ == "__main__":
    main()


# =============================================================================
# COMPARISON WITH fileExplorerAgent3.py
# =============================================================================
"""
KEY DIFFERENCES:

1. TOOL REGISTRATION:
   OLD: Action objects + ActionRegistry
   NEW: @register_tool decorator + global registry

2. TOOL DEFINITION:
   OLD: 
       def list_files(): ...
       Action(name="list_files", function=list_files, ...)
   NEW:
       @register_tool(name="list_files", ...)
       def list_files(action_context): ...

3. ACTION CONTEXT:
   OLD: Not used
   NEW: ActionContext passed to all tools (like invoiceProcessingAgent)

4. TOOL DISCOVERY:
   OLD: Manual registration with registry.register()
   NEW: Automatic via decorator

5. AGENT INITIALIZATION:
   OLD: Agent(..., action_registry=registry, ...)
   NEW: Agent(..., tools=get_all_tools(), ...)

SIMILARITIES:
- Same AgentLanguage architecture
- Same Agent loop structure
- Same Memory system
- Same Goal system
- Same execution flow

BENEFITS OF DECORATOR PATTERN:
✅ Less boilerplate (no Action objects)
✅ Cleaner syntax (decorators at definition)
✅ Auto-discovery of tools
✅ Metadata attached to functions
✅ Easy to add/remove tools

TRADE-OFFS:
⚠️ Global registry (less explicit)
⚠️ All tools must accept action_context first parameter
⚠️ Slightly less flexible than Action objects
"""
