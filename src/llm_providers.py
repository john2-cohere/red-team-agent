from langchain_cohere import ChatCohere
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

import os

import logging
from logging import getLogger

logger = getLogger(__name__)

class LLMProviders:
    def __init__(self, providers):
        """
        Initialize LLMProviders with a dictionary of provider name -> client mappings.
        
        Args:
            providers (dict): Dictionary mapping provider names to LLM client instances
        """
        self.providers = providers
        # Set default provider to the first one in the dictionary
        self.default_provider = next(iter(providers.keys()))
        self.default_client = providers[self.default_provider]

    def set_default_provider(self, name):
        """
        Set the default provider to the given name.
        """
        self.default_provider = name
        self.default_client = self.providers[name]
    
    def get_client(self, name) -> BaseChatModel:
        """
        Get a specific LLM client by name.
        
        Args:
            name (str): Name of the provider
            
        Returns:
            LLM client instance
            
        Raises:
            KeyError: If provider name not found
        """
        if name == "default":
            return self.default_client

        if name not in self.providers:
            available = list(self.providers.keys())
            raise KeyError(f"Provider '{name}' not found. Available providers: {available}")
        return self.providers[name]
    
    def get(self, key, default=None):
        """
        Dictionary-like get method for LangChain compatibility.
        """
        return getattr(self.default_client, key, default)
    
    def __getattr__(self, name):
        """
        Pass through attribute access to the default client.
        This allows direct access like: llm_providers.invoke() -> default_client.invoke()
        """
        # Check if the default client has this attribute
        if hasattr(self.default_client, name):
            return getattr(self.default_client, name)
        
        # If the default client doesn't have it, raise AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __repr__(self):
        return f"LLMProviders(default='{self.default_provider}', providers={list(self.providers.keys())})"


# Initialize clients
openai_client = ChatOpenAI(
    model="gpt-4.1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

cohere_client = ChatCohere(
    model="command-a-03-2025",
    cohere_api_key=os.getenv("COHERE_API_KEY"),
)

deepseek_client = ChatDeepSeek(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

deepseek_client_reasoner = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

cohere_client_thinking = ChatCohere(
    model="north-reasoning-alpha",
    cohere_api_key=os.getenv("COHERE_API_KEY"),
    model_kwargs={
        'thinking': {
            'type': 'enabled'
        }
    }
)

# Create the providers dictionary
providers_dict = {
    "cohere": cohere_client,
    "deepseek": deepseek_client,
    "deepseek_reasoner": deepseek_client_reasoner,
    "cohere_thinking": cohere_client_thinking,
    "openai": openai_client,
}

llm_providers = LLMProviders(providers_dict)
llm_providers.set_default_provider("cohere")