from langchain_deepseek import ChatDeepSeek
import os


deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "default_api_key_if_not_found")

def initialize(config: dict):
    """
    专门负责初始化 Ollama 模型的函数
    """
    return ChatDeepSeek(model=config.get("model"))

# 定义 DeepSeek provider 支持的模型及其配置
PROVIDER_CONFIGS = {
    "deepseek-chat": {
        "model": "deepseek-chat",
        # temperature, max_tokens 等参数也可以在这里加
    },
    "deepseek-coder": {
        "model": "deepseek-coder",
    }
}