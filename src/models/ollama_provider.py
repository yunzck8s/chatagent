# src/models/ollama_provider.py

from langchain_ollama import ChatOllama

def initialize(config: dict):
    """
    专门负责初始化 Ollama 模型的函数
    """
    return ChatOllama(**config)

# 可以在这里定义该 provider 支持的模型
# 注意：我们将配置从 __init__.py 移到了这里
PROVIDER_CONFIGS = {
    "qwen3:1.7b": {
        "base_url": "http://192.168.1.128:11434",
        "model": "qwen3:1.7b"
    },
    "qwen3:8b": {
        "base_url": "http://192.168.1.128:11434",
        "model": "qwen3:8b"
    }
}