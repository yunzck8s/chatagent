from typing import Dict, Any
from langchain_ollama import ChatOllama

MODEL_CONFIGS = {
    "ollama": {
        "qwen3:8b": {
            "base_url": "http://192.168.1.128:11434",
            "model": "qwen3:8b"
        },
        "llama3:8b": {
            "base_url": "http://192.168.1.128:11434",
            "model": "llama3:8b"
        }
    },
    # Add configurations for other providers
    # "openai": {
    #     "gpt-3.5-turbo": {
    #         "model": "gpt-3.5-turbo"
    #     },
    #     "gpt-4": {
    #         "model": "gpt-4"
    #     }
    # },
    # "anthropic": {
    #     "claude-3-haiku": {
    #         "model": "claude-3-haiku-20240307"
    #     },
    #     "claude-3-sonnet": {
    #         "model": "claude-3-sonnet-20240229"
    #     }
    # }
}


def get_available_models() -> Dict[str, list]:
    """Return a dictionary of available models grouped by provider"""
    return {
        provider: list(models.keys())
        for provider, models in MODEL_CONFIGS.items()
    }

def init_model(provider: str, model_name: str) -> Any:
    """Initialize a model from the given provider and model name"""
    if provider not in MODEL_CONFIGS:
        raise ValueError(f"Provider {provider} is not supported")
    
    if model_name not in MODEL_CONFIGS[provider]:
        raise ValueError(f"Model {model_name} is not supported by {provider}")
    
    config = MODEL_CONFIGS[provider][model_name]

    if provider == "ollama":
        return ChatOllama(**config)
    else:
        raise ValueError(f"Provider {provider} is not supported")