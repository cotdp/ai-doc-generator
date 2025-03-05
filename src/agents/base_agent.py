from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging
import os

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        """Initialize the base agent.
        
        Args:
            model (str): The model to use for the agent
            temperature (float): The temperature for model responses
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary task.
        
        Args:
            task (Dict[str, Any]): The task parameters
            
        Returns:
            Dict[str, Any]: The task results
        """
        pass
    
    async def _call_llm(self, system_prompt: str, user_prompt: str, response_format: str = "text") -> Any:
        """Call the LLM with system and user prompts.
        
        Args:
            system_prompt (str): The system prompt
            user_prompt (str): The user prompt
            response_format (str): Expected response format ("text" or "json")
            
        Returns:
            Any: The model's response (str for text, dict for json)
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            self.logger.debug(f"Calling LLM with system prompt: {system_prompt}")
            self.logger.debug(f"User prompt: {user_prompt}")
            
            response = await self.llm.ainvoke(messages)
            
            self.logger.debug(f"LLM response: {response.content}")
            
            if response_format == "json":
                try:
                    import json
                    return json.loads(response.content)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response: {str(e)}")
                    return {"error": "Invalid JSON response", "content": response.content}
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            raise 