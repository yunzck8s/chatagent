# ChatAgent

ChatAgent 是一个轻量级的对话式 AI 应用程序，旨在与各种语言模型提供商和外部工具集成。它提供了一个灵活且可扩展的框架，用于构建具有人类参与环路功能的基于代理的交互。

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [先决条件](#先决条件)
- [安装](#安装)
- [配置](#配置)
- [使用方法](#使用方法)
- [API 端点](#api-端点)
- [项目结构](#项目结构)
- [人类参与环路工作流](#人类参与环路工作流)
- [测试](#测试)
- [贡献](#贡献)
- [许可证](#许可证)

## 功能特性

- 通过 FastAPI 提供 REST API 接口
- 支持多种 LLM 提供商（Ollama，具有扩展到 OpenAI、Anthropic 等其他提供商的架构）
- 集成 Tavily 搜索工具
- 模块化代理架构（实现 ReAct 模式）
- 具有确认对话框的工具执行人类参与环路工作流
- 使用服务器发送事件 (SSE) 的实时流式响应
- 具有模型切换功能的基于 Web 的聊天界面
- 集成 MCP (Model Connection Protocol) 工具支持

## 技术栈

- **后端**: Python, FastAPI, LangChain, LangGraph
- **前端**: HTML, CSS, Vanilla JavaScript
- **AI/ML**: Ollama (主要), 支持扩展到其他提供商
- **工具**: Tavily 搜索 API, MCP 工具
- **部署**: Uvicorn
- **依赖管理**: uv

## 先决条件

- Python 3.12 或更高版本
- uv (Python 包管理器)
- Ollama (用于本地 LLM 支持)
- Tavily API 密钥 (用于搜索功能)

## 安装

1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd chatagent
   ```

2. 使用 uv 安装依赖：
   ```bash
   uv sync
   ```

## 配置

1. 在项目根目录创建一个 `.env` 文件，包含以下变量：
   ```env
   TAVILY_API_KEY=your_tavily_api_key_here
   OLLAMA_BASE_URL=http://localhost:11434  # 默认 Ollama URL
   DEEPSEEK_API_KEY=your_deepseek_api_key_here  # 可选，用于 DeepSeek 模型
   ```

2. 确保 Ollama 正在运行并且已拉取所需模型：
   ```bash
   ollama pull qwen3:8b  # 或任何你想使用的其他模型
   ```

3. 如需使用 MCP 工具，请确保相应的 MCP 服务器正在运行

## 使用方法

### 开发服务器

使用热重载启动开发服务器：
```bash
uv run python -m uvicorn main:app --reload
```

### 生产服务器

启动生产服务器：
```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

应用程序将在 `http://localhost:8000` 上可用。

## API 端点

### `GET /`

提供主聊天界面 (HTML 页面)。

### `GET /models`

返回按提供商分组的可用模型列表。

**响应：**
```json
{
  "ollama": ["qwen3:8b", "llama3:8b", ...],
  "deepseek": ["deepseek-chat", ...]
}
```

### `POST /chat`

处理聊天消息并流式传输响应。

**请求体：**
```json
{
  "text": "Your message here",
  "provider": "ollama",
  "model": "qwen3:8b",
  "thread_id": "optional-uuid"
}
```

**响应：**
流式传输具有不同类型消息的服务器发送事件：
- `thought`: 处理状态更新
- `content`: AI 生成的内容
- `tool_request`: 需要人类确认的工具执行请求
- `tool_result`: 已执行工具的结果

### `POST /continue_thread`

在人类批准工具请求后继续执行。

**请求体：**
```json
{
  "thread_id": "uuid",
  "approved": true,
  "tool_calls": [
    {
      "name": "tool_name",
      "args": { "param1": "value1" }
    }
  ]
}
```

## 项目结构

```
chatagent/
├── main.py                 # FastAPI 应用程序入口点
├── pyproject.toml          # Python 依赖配置 (uv)
├── uv.lock                 # uv 锁文件
├── .env                    # 环境变量 (不在版本控制中)
├── .gitignore              # Git 忽略文件
├── README.md               # 本文件
├── src/
│   ├── index.html          # 聊天界面
│   ├── models/             # 语言模型提供商实现
│   │   ├── __init__.py
│   │   ├── ollama_provider.py
│   │   └── deepseek_provider.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tavily.py       # Tavily 搜索工具集成
│   │   └── math_server.py  # MCP 数学工具服务器
│   └── agent/
│       ├── __init__.py
│       └── react.py        # ReAct 代理模式实现
└── test/
    ├── test_interrupt.py   # 人类参与环路工作流测试脚本
    └── test_mcp_integration.py  # MCP 集成测试脚本
```

## 人类参与环路工作流

ChatAgent 实现了工具执行的人类参与环路工作流，以确保安全性和用户控制：

1. **代理处理**: 当 AI 代理确定需要执行工具时，它会在实际执行前中断。

2. **工具请求**: 系统向前端发送包含以下内容的 `tool_request` 消息：
   - 工具名称
   - 工具参数

3. **用户确认**: 前端显示一个确认对话框，显示：
   - 工具名称
   - 工具参数 (可编辑)
   - 批准/拒绝按钮

4. **用户操作**: 用户可以：
   - 批准工具执行 (可选择编辑参数)
   - 拒绝工具执行

5. **执行继续**: 
   - 如果批准，执行工具并处理结果
   - 如果拒绝，代理在不执行工具的情况下继续

6. **结果处理**: 工具结果被整合到代理的响应生成中。

此工作流确保潜在的敏感或昂贵的工具操作在执行前需要明确的用户批准。

## 测试

### 自动化测试

运行测试脚本以验证人类参与环路工作流：
```bash
uv run python test/test_interrupt.py
```

此脚本：
1. 发送触发工具调用的聊天消息
2. 验证工具请求是否正确发送
3. 模拟用户批准
4. 验证工具执行和结果处理

运行 MCP 集成测试：
```bash
uv run python test/test_mcp_integration.py
```

### 手动测试

1. 启动服务器：`uv run python -m uvicorn main:app --reload`
2. 在浏览器中打开 `http://localhost:8000`
3. 发送会触发工具调用的消息 (例如，"What is 15 multiplied by 4?" 或 "Search for information about artificial intelligence")
4. 观察工具确认对话框
5. 批准或拒绝工具执行
6. 验证响应行为

## 贡献

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature-name`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin feature-name`
5. 创建拉取请求

## 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## 故障排除

### 常见问题

1. **"Module not found" 错误**: 确保已激活虚拟环境并安装了所有依赖项。

2. **Ollama 连接错误**: 验证 Ollama 是否正在运行并且在配置的 URL 上可访问。

3. **Tavily API 错误**: 检查 `.env` 文件中的 TAVILY_API_KEY 是否正确设置。

4. **工具执行未中断**: 确保使用带有 `interrupt_before=["tools"]` 参数的 `create_react_agent`。

5. **MCP 工具未加载**: 确保 MCP 服务器正在运行并且配置正确。

### 调试技巧

1. 检查终端输出中的错误消息
2. 使用浏览器开发者工具检查网络请求
3. 添加日志语句以跟踪执行流程
4. 验证请求之间 thread_id 的一致性

## 架构说明

### 后端架构

后端遵循模块化单体模式，具有以下关键组件：

1. **FastAPI 层**: 处理 HTTP 请求和响应
2. **模型提供商**: 抽象不同的 LLM 提供商 (Ollama, DeepSeek 等)
3. **工具**: 外部集成 (Tavily 搜索, MCP 工具)
4. **代理逻辑**: 使用 LangGraph 编排交互
5. **状态管理**: 使用 LangGraph 的检查点进行对话状态管理

### 前端架构

前端是一个单页应用程序，具有：

1. **聊天界面**: 具有流式响应的实时消息传递
2. **模型选择**: 动态提供商和模型切换
3. **工具确认**: 人类参与环路工作流的模态对话框
4. **状态管理**: 客户端会话状态跟踪

### 数据流

1. 用户通过前端发送消息
2. 前端 POST 到 `/chat` 端点
3. 后端使用选定模型初始化代理
4. 代理处理消息，可能请求工具执行
5. 如果需要工具执行，代理中断并发送工具请求
6. 后端将工具请求流式传输到前端
7. 前端显示确认对话框
8. 用户批准/拒绝工具执行
9. 前端将用户决定 POST 到 `/continue_thread`
10. 后端根据用户输入恢复代理执行
11. 代理完成处理并生成最终响应
12. 后端将最终响应流式传输到前端
13. 前端向用户显示响应

此架构确保了响应迅速的用户体验，同时保持了组件之间的适当关注点分离。