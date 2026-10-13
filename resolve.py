
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

class Memory:
    def __init__(self):
        self.items: List[Dict[str, str]]= []

    def add_memory(self, memory: Dict[str, str]) -> None:
        self.items.append(memory)

    def get_memories(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        if limit:
            return self.items[:limit]
        else:
            return list(self.items)
        


@dataclass
class Action:
    name: str
    function: Callable[..., Any]
    description: str
    parameters: Dict[str, Any]
    terminal: bool = False
    memory: Optional['Memory'] = None

    def execute(self, **args):
        return self.function(**args)

    def access_memory(self) -> Optional[List[Dict[str, str]]]:
        if self.memory:
            return self.memory.get_memories()
        return None

memory = Memory()
memory.add_memory({"type": "user", "content": "List all files"})
memory.add_memory({"type": "user", "content": '{"tool_executed": true, "result": ["test.py", "agent.py"]}'})

# get all memories
all_memories = memory.get_memories(limit=2)
# print(all_memories)
# loop over to display memories
# for i, mem in enumerate(all_memories, 1):
#     print(f" {i}. Type: {mem['type']:10s} | Content: {mem['content'][:70]}")


def list_files() -> List[str]:
    import os
    return sorted(os.listdir("."))

# action without memory
action_with_memory = Action(
    name="list_files",
    function=list_files,
    description="list files in the current directory",
    parameters={"type": "object", 
                "properties": {}},
    terminal=False,
    memory=memory
)
# print(action_with_memory.access_memory())
# print(memory.__dict__)





# =========================================
# analyse the tool decorator here: 
# a decorator is a function that wraps another function and adds
# some functionality to it.................
# =========================================
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



print(_TOOL_REGISTRY)

@register_tool(
    name="list files",
)
def list_files() -> List[str]:
    import os
    return sorted(os.listdir('.'))



# =================================
def register_name(
    fname: str = None,
    lname: str = None
):
    """
    decorator function goes here
    """
    def decorator(fn: Callable) -> Callable:
        # create a tool_name variable
        full_name = f"{fname} {lname}" if fname and lname else fn.__name__
        
        # attach metadata to the function
        fn.full_name = full_name
        fn.first_name = fname
        fn.last_name = lname
        
        # Return the function unchanged (but now with metadata)
        return fn
    return decorator


@register_name(fname="prosper", lname="chigozie")
def identify():
    """Identify function"""
    pass


result = identify()
print(f"    Result: {result}")

# 2. Access the metadata attached by the decorator
print("\n[2] Metadata attached by decorator:")
print(f"    identify.full_name = {identify.full_name}")
print(f"    identify.first_name = {identify.first_name}")
print(f"    identify.last_name = {identify.last_name}")

# 3. Check that the function is still the same
print("\n[3] Function properties:")
print(f"    Function name: {identify.__name__}")
print(f"    Function docstring: {identify.__doc__}")
print(f"    Is callable? {callable(identify)}")

# 4. See all attributes on the function
print("\n[4] All attributes added to function:")
function_attrs = [attr for attr in dir(identify) if not attr.startswith('_')]
print(f"    Custom attributes: {[attr for attr in function_attrs if attr in ['full_name', 'first_name', 'last_name']]}")

# # 5. Access metadata dynamically
# print("\n[5] Dynamic access:")
# if hasattr(identify, 'full_name'):
#     print(f"    Has 'full_name' attribute: YES")
#     print(f"    Value: {getattr(identify, 'full_name')}")
# else:
#     print(f"    Has 'full_name' attribute: NO")


# # =========================================
# # QUICK REFERENCE: Accessing Decorator Metadata
# # =========================================

# print("""
# # 1. DIRECT ACCESS
# identify.full_name          # "prosper chigozie"
# identify.first_name         # "prosper"
# identify.last_name          # "chigozie"

# # 2. CHECK IF ATTRIBUTE EXISTS
# hasattr(identify, 'full_name')      # True
# hasattr(identify, 'age')            # False

# # 3. GET WITH DEFAULT VALUE
# getattr(identify, 'full_name', 'Unknown')     # "prosper chigozie"
# getattr(identify, 'age', 'Not set')           # "Not set"

# # 4. LIST ALL CUSTOM ATTRIBUTES
# [attr for attr in dir(identify) 
#  if not attr.startswith('_') 
#  and attr in ['full_name', 'first_name', 'last_name']]

# # 5. INTROSPECTION
# identify.__name__           # "identify" (original function name)
# identify.__doc__            # Function docstring
# callable(identify)          # True (still callable)
# """)

# print("=" * 70)
# print("PRACTICAL EXAMPLE: Using Metadata in Code")
# print("=" * 70)

# def greet_person(func):
#     """Use the metadata attached by decorator."""
#     if hasattr(func, 'full_name'):
#         print(f"Hello, {func.full_name}!")
#     else:
#         print(f"Hello, {func.__name__}!")

# greet_person(identify)  # Uses the decorator metadata!
