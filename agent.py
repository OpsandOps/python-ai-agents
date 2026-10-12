def list_files() -> list:
    ...

def read_files(file_name: str) -> str:
    ...

def terminate(message: str)-> str:
    ...


# create a dictionary mapping of the tools
tools_list = {
    "listfiles": list_files,
    "readfiles": read_files,
    "terminate": terminate
}

# create a JSON schema for the model to use for tool calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "listfiles",
            "description": "a function to list all files in the directory",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listfiles",
            "description": "a function to read files in the src/ directory",
            "parameters": {
                "type": "object",
                "properties": {"file_name": {"type": "string"},
                               "length": {"type": "number"}},
                "required": ["file_name", "number"]
            }
        }
    }
]