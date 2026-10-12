# PATTERN COMPARISON: fileExplorerAgent3.py vs invoiceProcessingAgent.ipynb

## 🎯 THE BIG PICTURE

Both solve the same problem: **How to get structured output from an LLM**

But they use **completely different approaches**:

---

## 📊 SIDE-BY-SIDE COMPARISON

### **fileExplorerAgent3.py: Function-Calling Pattern**
**"Let the LLM choose which function to call"**

### **invoiceProcessingAgent.ipynb: Schema-Based Pattern**
**"Tell the LLM exactly what JSON structure to return"**

---

## 🔍 DETAILED COMPARISON

### **1. GOAL DEFINITION**

#### **fileExplorerAgent3.py:**
```
Uses: Goal objects
Purpose: Tell LLM what objectives to pursue

goals = [
    Goal(1, "Explore Files", "List and read files"),
    Goal(2, "Terminate", "End when done")
]
```

**Simpler terms:** "Here are your missions, LLM. Decide how to accomplish them."

---

#### **invoiceProcessingAgent.ipynb:**
```
Uses: Function parameters + prompt text
Purpose: Tell LLM exactly what to extract

extraction_prompt = """
Extract invoice information:
- Invoice number
- Date
- Amount
- Vendor info
- Line items
"""
```

**Simpler terms:** "Here's exactly what data I need, LLM. Find it."

---

### **2. TOOL/ACTION DEFINITION**

#### **fileExplorerAgent3.py: Explicit Action Objects**
```python
Action(
    name="list_files",
    function=list_files,           # Actual Python function
    description="Lists files...",
    parameters={                    # JSON Schema
        "type": "object",
        "properties": {}
    }
)
```

**Flow:**
```
1. Define Python function: list_files()
2. Wrap in Action object
3. Store in ActionRegistry
4. Convert to tool schema for LLM
5. LLM chooses which tool to call
6. Agent looks up Action and executes
```

**Simpler terms:** 
> "Here are 3 tools you can use. Pick one, tell me which, and I'll run it."

---

#### **invoiceProcessingAgent.ipynb: Decorator Pattern**
```python
@register_tool(tags=["document_processing", "invoices"])
def extract_invoice_data(action_context: ActionContext, document_text: str):
    """Extract invoice data from document text."""
    ...
```

**Flow:**
```
1. Define Python function: extract_invoice_data()
2. Add @register_tool decorator (marks it as a tool)
3. Call function directly (no registry lookup needed)
4. Function internally prompts LLM with schema
5. LLM returns JSON matching schema
```

**Simpler terms:** 
> "Here's one tool. When I call it, it asks the LLM for specific data."

---

### **3. DECORATOR EXPLAINED**

#### **What is `@register_tool`?**

```python
def register_tool(tags=None):
    def decorator(fn):
        fn.tags = tags or []  # Adds .tags attribute to function
        return fn
    return decorator

@register_tool(tags=["invoices"])
def extract_invoice_data(...):
    pass

# After decoration, the function has:
extract_invoice_data.tags  # ["invoices"]
```

**Simpler terms:**
> A decorator is like a sticker you put on a function.
> `@register_tool` adds a `.tags` attribute to the function.
> It's metadata (information ABOUT the function).

**Why use it?**
- You could search for all tools with tag "invoices"
- You could organize tools by category
- In this code, it's mostly for documentation (not actively used)

---

### **4. SCHEMA DEFINITION**

#### **fileExplorerAgent3.py: Schema in Action Object**
```python
Action(
    name="read_file",
    parameters={                     # Schema lives HERE
        "type": "object",
        "properties": {
            "file_name": {"type": "string"}
        },
        "required": ["file_name"]
    }
)

## this means 
def read_file(file_name: str)-> List[str]:
    pass
```

**Purpose:** Tell LLM what parameters the tool accepts

**Simpler terms:** 
> "If you want to call read_file, you must provide a file_name (string)."

---

#### **invoiceProcessingAgent.ipynb: Schema in Function Body**
```python
def extract_invoice_data(...):
    invoice_schema = {               # Schema defined INSIDE function
        "type": "object",
        "required": ["invoice_number", "date", "amount"],
        "properties": {
            "invoice_number": {"type": "string"},
            "date": {"type": "string"},
            "amount": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "currency": {"type": "string"}
                }
            }
        }
    }
    
    return prompt_llm_for_json(schema=invoice_schema, ...)
```

**Purpose:** Tell LLM what JSON structure to return

**Simpler terms:** 
> "Return your answer in this exact format with these fields."

---

### **5. ACTIONCONTEXT EXPLAINED**

```python
@dataclass
class ActionContext:
    metadata: dict = field(default_factory=dict)
```

**What is it?**
A container for passing extra information to tools.

**Example usage:**
```python
context = ActionContext()
context.metadata["user_id"] = "12345"
context.metadata["session_id"] = "abc"

result = extract_invoice_data(context, document_text)
# Function can access: action_context.metadata["user_id"]
```

**Simpler terms:**
> Think of it as a backpack. You can put extra stuff in it (metadata).
> Every tool gets this backpack and can look inside if needed.

**Why use it?**
- Pass user context to tools
- Store session information
- Add logging data
- In this code, it's mostly unused (placeholder for future use)

---

### **6. PROMPT CONSTRUCTION**

#### **fileExplorerAgent3.py: AgentLanguage Class**
```python
class AgentLanguage:
    def construct_prompt(self, actions, goals, memory):
        # 1. Format goals
        # 2. Format memory (conversation history)
        # 3. Format actions as tools
        # 4. Combine into Prompt object
        return Prompt(messages=[...], tools=[...])
```

**Who constructs:** AgentLanguage class  
**When:** Every agent loop iteration  
**Includes:** Goals, memory, available tools  

**Simpler terms:**
> "Build a complete prompt with conversation history + available tools."

---

#### **invoiceProcessingAgent.ipynb: prompt_llm_for_json Function**
```python
def prompt_llm_for_json(action_context, schema, prompt):
    system = f"You are a data extraction engine. Schema:\n{schema}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    return generate_response(messages)
```

**Who constructs:** Helper function  
**When:** Each time you call extract_invoice_data  
**Includes:** Schema + one-time prompt  

**Simpler terms:**
> "Make a simple prompt: system message with schema + user message with task."

---

### **7. LLM INTERACTION**

#### **fileExplorerAgent3.py: Multi-Turn Conversation**

```
Turn 1:
User: "List files"
LLM: {"tool": "list_files", "args": {}}
Agent: Executes → ["test.py", "agent.py"]

Turn 2:
User: (sees previous result in memory)
LLM: {"tool": "read_file", "args": {"file_name": "test.py"}}
Agent: Executes → "file contents..."

Turn 3:
LLM: {"tool": "terminate", "args": {"message": "Done!"}}
Agent: Stops
```

**Pattern:** Iterative loop with memory

---

#### **invoiceProcessingAgent.ipynb: Single-Shot Extraction**

```
Single Call:
User: "Extract data from this invoice text"
LLM: {
  "invoice_number": "INV-2026-0042",
  "date": "2026-10-01",
  "amount": {"value": 435000, "currency": "NGN"},
  "vendor": {...},
  "line_items": [...]
}
Done!
```

**Pattern:** One call, structured output

---

## 📋 SUMMARY TABLE

| Aspect | fileExplorerAgent3.py | invoiceProcessingAgent.ipynb |
|--------|----------------------|------------------------------|
| **Pattern** | Function-calling agent loop | Schema-based extraction |
| **Tools** | Multiple (list_files, read_file, terminate) | Single (extract_invoice_data) |
| **Tool Registration** | Action objects in ActionRegistry | @register_tool decorator |
| **Schema Location** | In Action.parameters | Inside function body |
| **Prompt Building** | AgentLanguage class | prompt_llm_for_json function |
| **Conversation** | Multi-turn with memory | Single-shot |
| **LLM Decides** | Which tool to call | What data to extract |
| **ActionContext** | Not used | Passed to all tools |
| **Complexity** | Higher (full agent system) | Lower (simple extraction) |
| **Use Case** | Interactive tasks | Data extraction |

---

## 💡 WHEN TO USE EACH PATTERN?

### **Use fileExplorerAgent3.py Pattern When:**
- ✅ Multi-step tasks (explore → read → analyze)
- ✅ LLM needs to decide what to do next
- ✅ Need conversation memory
- ✅ Multiple tools to choose from
- ✅ Building an autonomous agent

**Example:** Chatbot, research assistant, file explorer

---

### **Use invoiceProcessingAgent.ipynb Pattern When:**
- ✅ Single-step extraction
- ✅ You know exactly what data you need
- ✅ No conversation needed
- ✅ One tool does the job
- ✅ Processing documents/data

**Example:** Invoice processing, form extraction, data scraping

---

## 🎯 KEY CONCEPTS SIMPLIFIED

### **1. Decorator (@register_tool)**
**Normal explanation:** Adds metadata to a function  
**Simple explanation:** Puts a label on a function saying "this is a tool"

```python
# Without decorator
def my_function():
    pass

# With decorator
@label_as_tool
def my_function():
    pass
# Now: my_function has extra info attached
```

---

### **2. Schema (JSON Schema)**
**Normal explanation:** Defines the structure of expected JSON output  
**Simple explanation:** A template showing what fields the LLM must return

```python
# Like a form:
schema = {
    "name": (must be text),
    "age": (must be number),
    "email": (must be text)
}
# LLM fills in: {"name": "Alice", "age": 30, "email": "alice@example.com"}
```

---

### **3. ActionContext**
**Normal explanation:** Container for passing contextual information  
**Simple explanation:** A box where you can store extra stuff to pass around

```python
# Like a messenger bag
context = ActionContext()
context.metadata["important_info"] = "something"
# Any function that receives this context can peek inside
```

---

## 🔧 WHICH IS BETTER?

**Neither!** They solve different problems:

| **fileExplorerAgent3.py** | **invoiceProcessingAgent.ipynb** |
|---------------------------|----------------------------------|
| 🤖 Full autonomous agent | 📄 Specialized data extraction |
| 🔄 Multi-turn conversation | ⚡ Single API call |
| 🧠 LLM makes decisions | 📋 Structured output only |
| 🏗️ More complex architecture | 🎯 Simpler, focused |

**Use both together:**
You could use invoiceProcessingAgent's pattern INSIDE fileExplorerAgent as one of the actions!

```python
# In fileExplorerAgent3.py
Action(
    name="extract_invoice",
    function=extract_invoice_data,  # From invoiceProcessingAgent!
    description="Extract structured data from invoice"
)
```

---

## ✨ FINAL TAKEAWAY

**fileExplorerAgent3.py:**
> "I'm a full agent system. LLM decides what tools to use and when. I remember conversations."

**invoiceProcessingAgent.ipynb:**
> "I'm a focused extraction tool. Give me text, I'll return structured data. One shot, done."

Both are valid patterns for different use cases! 🎯
