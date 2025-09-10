from langchain_ollama import ChatOllama
from typing import Dict, Any

# Default configuration
DEFAULT_OLLAMA_CONFIG = {
    "model": "qwen3:8b",
    "base_url": "http://192.168.1.128:11434"
}

def init_ollama(config: Dict[str, Any] = None):
    """
    Initialize Ollama model with provided configuration.
    If no config is provided, uses default configuration.
    """
    if config is None:
        config = DEFAULT_OLLAMA_CONFIG
    
    llm = ChatOllama(**config)
    return llm