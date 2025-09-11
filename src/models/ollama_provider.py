# src/models/ollama_provider.py

from langchain_ollama import ChatOllama

def initialize(config: dict):
    """
    专门负责初始化 Ollama 模型的函数
    """
    return ChatOllama(**config)

# 将 base_url 修改为 localhost，使其更具通用性
PROVIDER_CONFIGS = {
    "qwen3:8b": {
        "base_url": "http://192.168.1.128:11434",
        "model": "qwen3:8b"
    },
    "llama3:8b": {
        "base_url": "http://192.168.1.128:11434",
        "model": "llama3:8b"
    }
}