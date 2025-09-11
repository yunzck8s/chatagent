from langchain_deepseek import ChatDeepSeek
import os

def initialize(config: dict):
    """
    专门负责初始化 DeepSeek 模型的函数。
    ChatDeepSeek 会自动在环境变量中查找 DEEPSEEK_API_KEY，
    因为这个函数在 load_dotenv() 之后被调用，所以能正确找到密钥。
    """
    # 为了调试，我们可以加一个检查
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("警告: 在 .env 文件中未找到 DEEPSEEK_API_KEY")

    return ChatDeepSeek(model=config.get("model"))

# 定义 DeepSeek provider 支持的模型及其配置
PROVIDER_CONFIGS = {
    "deepseek-chat": {
        "model": "deepseek-chat",
    },
    "deepseek-coder": {
        "model": "deepseek-coder",
    }
}