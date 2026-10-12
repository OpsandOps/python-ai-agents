# Decorator Pattern vs Original Pattern Comparison

## Side-by-Side: Tool Definition

### **Original (fileExplorerAgent3.py)**
```python
# Step 1: Define function
def list_files() -> List[str]:
    return os.listdir(".")

# Step 2: Wrap in Action object
action = Action(
    name="list_files",
    function=list_files,
    description="Returns a list of files",
    parameters={"type": "object", "properties": {}},
    terminal=False
)

# Step 3: Register
registry = ActionRegistry()
registry.register(action)
```

### **Decorator Pattern (fileExplorer_Decorator.py)**
```python
# All in one step!
@register_tool(
    name="list_files",
    description="Returns a list of files",
    parameters={"type": "object", "properties": {}},
    terminal=False,
    tags=["file_operations"]
)
def list_files(action_context: ActionContext) -> List[str]:
    return os.listdir(".")

# Auto-registered! No manual steps needed.
```

---

## Key Differences

| Aspect | Original | Decorator |
|--------|----------|-----------|
| **Registration** | Manual: `registry.register(action)` | Automatic: decorator registers on import |
| **Boilerplate** | 3 steps: define → wrap → register | 1 step: decorate function |
| **Tool Storage** | ActionRegistry class | Global `_TOOL_REGISTRY` dict |
| **Tool Lookup** | `registry.get_action(name)` | `get_tool(name)` |
| **Context Parameter** | Not used | All tools get `action_context` first |
| **Tags/Metadata** | Not supported | Supported via decorator params |

---

## Architecture Comparison

### **Original Pattern**
```
Function → Action Object → ActionRegistry → Agent
```

### **Decorator Pattern**
```
Function (with decorator) → Global Registry → Agent
```

---

## Code Example: Full Flow

### **Original**
```python
# Define
def list_files():
    return os.listdir(".")

# Wrap
action = Action(name="list_files", function=list_files, ...)

# Register
registry = ActionRegistry()
registry.register(action)

# Build agent
agent = Agent(..., action_registry=registry)

# Execute
action = registry.get_action("list_files")
result = action.execute()
```

### **Decorator**
```python
# Define with decorator
@register_tool(name="list_files", ...)
def list_files(action_context):
    return os.listdir(".")

# Get all tools
tools = get_all_tools()

# Build agent
agent = Agent(..., tools=tools)

# Execute
tool_fn = tools["list_files"]
result = tool_fn(action_context)
```

---

## When to Use Each

### Use Original Pattern When:
- ✅ Need explicit control over registration
- ✅ Want to see Action objects in code
- ✅ Building educational/teaching examples
- ✅ Prefer explicit over implicit
- ✅ Don't need tags/metadata

### Use Decorator Pattern When:
- ✅ Want cleaner, more concise code
- ✅ Need metadata/tags on tools
- ✅ Prefer auto-discovery
- ✅ Building production systems
- ✅ Following invoiceProcessingAgent pattern
