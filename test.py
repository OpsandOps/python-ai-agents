
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import os

@dataclass(frozen=True)
class Goal:
    priority: int
    name: str
    description: str
    
@dataclass
class Prompt:
    """What gets sent to the LLM: chat messages + tool definitions (optionally)"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Action:
    name: str                           # Unique identifier (e.g., "list_files")
    function: Callable[..., Any]        # THE ACTUAL PYTHON FUNCTION to execute
    description: str                    # Human-readable explanation
    parameters: Dict[str, Any]          # JSON Schema describing function arguments
    terminal: bool = False              # Does this action end the agent loop?

    def execute(self, **args) -> Any:
        """Execute the function with given arguments"""
        return self.function(**args)

class ActionRegistry:
    """ a lookup for the agent to use when calling its action: a place of governance"""
    def __init__(self):
        self.actions: Dict = Field(default={}, description="a dictionary of registered actions for the agent tasks")
    
    def __register__(self, action: Action) -> None:
        """register actions by name in the actions __dict__"""
        self.actions[action.name] = action

    def get_Action(self, name: str) -> Optional[Action]:
        return self.actions.get(name)
    
    def get_all_actions(self) -> List[Action]:
        return list(self.actions.values())
    
    
class Memory:
    """an ordered list of {"type": ..., "content}: ...} enteries"""
    def __init__(self):
        self.items: List[Dict[str, str]] = []

    def add_memory(self, memory: Dict[str, str]) -> None:
        self.items.append(memory)

    def get_memories(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        if limit:
            return self.items[:limit]
        else:
            list(self.items)

class AgentLanguage(ABC):
    """The contract of how the agent talks to, and listens to the LLM"""
    @abstractmethod
    def construct_prompt(
        self,
        actions: List[Action],
        environment: "Environment",
        goals: List[Goal],
        memory: Memory,
    ) -> Prompt:
        """
        Goals + Action + Memory -> prompt with a chat massage and tool schema ready for the LLM
        """

    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """LLM reply text -> {"tool": <action name>, "args": {...}"""

        # more helpers that other subclasses can use
    def format_goals(self, goals: List[Goal])-> str:
        """Render goats as text, ordered by priority"""
        ordered = sorted(goals, key=lamda g:g.priority)
        return "\n".join(f"{g.name}: {g.description}" for g in ordered)

    def format_memory(self, memory: Memory) -> List[Dict[str, str]]:
        """convert memory into the chat messges"""
        role_map = {"assistant": "assistant", "system": "system"}
        for m in memory.get_memories():
            # the agent internally labels memory with "type": "...", while the LLM receives it
            # as "role": "..." so we have to translate here
            return  [{"role": role_map.get(m["type"], "user"), "content": m["content"]}]
        
class AgentFunctionCallingActionLanguage(AgentLanguage):
    # a concrete class that implements the abstract methods of the AgentLanguage
    # we deifned a contract for comm between the agent and the LLM in the agent language
    # so we must define the concerte implementations since we cannot create an instance of the AgentLanguage as an ABC
    # so we use the subclass approact to get the implementation 

    def construct_prompt(self, actions, enviroment, goals, memory)-> Prompt:
        system_message = {
            "role": "system",
            "content": (
                "You are an agent. Pursue these goals in the priority order:\n"
                f"{self.format_goals(goals)}\n\n"
                "Always respond by calling one of the available tools"
            ),
        }
        messages = [system_messages] + self.format_memory(memory)
        tools = self._format_tools(actions)

    def _format_tools(self, actions: List[Action]) -> List[Dict[str, Any]]:
        # this function is private to this class bcos languages behave differently with tools
        # since it is exposed within this class, it is private to the class
        # interface segregation principle
        return [
            {
                "type": "function",
                "function": {
                    "name": a.name,
                    "description": a.description[:1024],
                    "parameters": a.parameters or {"type": "object", "properties": {}}
                }
            }
            for a in actions
        ]
# =============================================================================
# 3. ENVIRONMENT  (collaborator #2)
#    Responsible for actually running an Action and reporting what happened.
#    It never talks to the LLM and never decides what to do next.
# =============================================================================

class Environment:
    """Executes actions and returns a uniform result dictionary"""
    def execute_action(self, action: Action, args: dict) -> dict:
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except {
            "tool_executed": False,
            "error": str(e)
            "traceback": tracebook._format_exc()
        }

    def _format_result(self, result:Any)-> dict:
        """one place that defines what a successful result looks like"""
        return {
            "tool_executed" :True,
            "result": result,

        }


# =============================================================================
# 4. LLM CALL  (collaborator #3, injected as a plain function)
# =============================================================================

MODEL = os.environ.get("AGENT_MODEL", "gemini-3.6-flash")


def generate_response(prompt: Prompt) -> str:
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
        enviroment: Environment,
    ):
        self.goals = goals
        self.agent_language = agent_language
        self.actions = action_registry
        self.generate_response = generate_response
        self.environment = environment

    def build_prompt(self, memory: Memory) -> Prompt:
        # delegates to AgentLanguage
        return self.agent_language.construct_prompt(
            actions=self.actions.get_actions(),
            environment=self.environment,
            goals=self.goals,
            memory=memory,
        )

    def get_actions(self, response: str) -> Tuple[Action, dict]:
        invocation = self.agent_language.parse_response(reponse)
        action = self.actions.get_action(invocation["tool"])
        return action, invocation

    def set_current_task(self, memory: Memory, task: str) -> None:
        memory.add_memory({"type": "user", "content": task})

    def update_memory(self, memory: Memory, response: str, result: dict)-> None:
        memory.add_memory({"type": "assistant","content": response})
        memory.add_memory({"type": "user", "content": json.dumps(result, default=str)})


    def run(self, user_input: str, 
            memory: Optional[Memory] = None,
            max_iterations: int = 50) -> Memory: 
            
        memory = memory or Memory()
        self.set_current_task(memory, user_input)

        for _ in range(max_iterations):
            prompt = self.build_prompt(memory)  # AgentLanguage
            print("....Agent is Thinking....")
            response = self.generate_response(prompt) # LLM 
            print(f"Agent Decision: {response}")

            action, invocation = self.get_action(reponse) # AgentLanguage + Registry
            result = self.environment.execute_action(action, invocation["args"])
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
        Goal(1, "Explore Files", "Explore file in the current directory")
        Goal(2, "Terminate", "Terminate the session when tasks are completed")
    ]

    # --tool function--
    # why do we create the function actions as a nested function inside build_file_explorer_agent()
    def list_files() - > List[str]:
        return os.listdir(".")

    def read_file(file_name: str) -> str:
        try:
            with open(file_name, "r") as f:
                return f.read()
            except FileNotFoundError:
                return f"Error: {file_name} not found"
            except Exception as e:
                return f"Error: {e}"
            
    def terminate(message: str)-> str:
        return message

    registry = ActionRegistry()
    registry.register(Action(
        name="",
        function=list_files,
        description="",
        parameters={}, 
        terminal=False
    ))
    registry.register(Action(
        name="read_file",
        function=read_file,
        description="Reads the content of a specific directory.",
        parameters={
            "type": "object",
            "properties": {"message": {"type": "string"}},
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
        action_language=AgentFunctionCallingActionLanguage,
        action_registry=registry,
        generate_reponse=generate_response,
        environment=Environment(),
    )


def main():
    agent = build_file_explorer_agent()
    user_input = input("What should i do")
    final_memory = agent.run(user_input, max_iterations=10)

    for item in final_memory.get_memories():
        print(f"\n Memory: {item['content']}")

if __name__ = "__main__":
    main()
