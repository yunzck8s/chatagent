# src/models/__init__.py

from typing import Dict, Any, Callable
from . import ollama_provider  # 导入我们的 provider 模块
from . import deepseek_provider

# 1. 定义一个“注册表”，存放所有 provider 的初始化函数和配置
MODEL_PROVIDERS = {
    "ollama": {
        "initializer": ollama_provider.initialize,
        "configs": ollama_provider.PROVIDER_CONFIGS
    },
    # 2. 在这里新增一个字典项来“注册” deepseek
    "deepseek": {
        "initializer": deepseek_provider.initialize,
        "configs": deepseek_provider.PROVIDER_CONFIGS
    }
    # 未来想支持 openai，只需要在这里新增一行
    # "openai": {
    #     "initializer": openai_provider.initialize,
    #     "configs": openai_provider.PROVIDER_CONFIGS
    # }
}


def get_available_models() -> Dict[str, list]:
    """
    从注册表中动态获取所有可用的模型
    """
    return {
        provider: list(details["configs"].keys())
        for provider, details in MODEL_PROVIDERS.items()
    }


def init_model(provider: str, model_name: str) -> Any:
    """
    一个更简洁、更具扩展性的模型初始化工厂函数
    """
    if provider not in MODEL_PROVIDERS:
        raise ValueError(f"Provider '{provider}' is not supported.")

    provider_details = MODEL_PROVIDERS[provider]

    if model_name not in provider_details["configs"]:
        raise ValueError(f"Model '{model_name}' is not supported by {provider}.")

    # 2. 从注册表中查找对应的 provider 配置和初始化函数
    config = provider_details["configs"][model_name]
    initializer_func = provider_details["initializer"]

    # 3. 调用该 provider 自己的初始化函数
    return initializer_func(config)