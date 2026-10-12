# This class will encapsulate the GAME components and provide a simple interface for running the agent loop. ]
# The agent will be responsible for constructing prompts, executing actions, and managing memory. 
# We can create different agents simply by changing the goals, actions, and environment without modifying the core loop.
from modularAgent import Goal, ActionRegistry, Environment
from typing import Callable, List, str

class Agent:

    def __init__(self,
                goals: List[Goals],
                agent_language: AgentLanguage,
                action_registry: ActionRegistry,
                generate_response: Callable [[prompt], str],
                environment: Environment,
    ):
        self.goals = goals
        self.agent_language = agent_language
        self.action_registry = action_registry
        self.generate_response = generate_response
        self.environment = environment

    def construct_prompt(self, goals: List[Goal], memory: Memory, actions: ActionRegistry) -> prompt:
        
