#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatAgent Human-in-the-Loop 测试脚本

这个脚本用于测试 ChatAgent 应用中的人机协作功能，特别是工具执行前的中断和用户确认流程。

测试流程：
1. 向聊天代理发送一条会触发工具调用的消息
2. 验证代理是否在工具执行前正确中断
3. 模拟用户批准工具执行
4. 验证工具是否正确执行并返回结果
5. 验证最终的AI响应是否正确生成

作者: Qwen
日期: 2025-09-15
"""

import requests
import json
import time
import uuid
from typing import Optional, Dict, Any


def test_chat_with_interrupt() -> tuple:
    """
    测试聊天功能，验证工具执行前的中断机制
    
    Returns:
        tuple: (thread_id, tool_request) 如果成功中断工具执行，否则返回 (None, None)
    """
    # 定义测试端点和数据
    url = "http://localhost:8000/chat"
    data = {
        "text": "Search for information about artificial intelligence",
        "provider": "ollama",
        "model": "qwen3:8b"
    }
    
    print("=== 开始测试聊天中断功能 ===")
    print(f"发送请求到: {url}")
    print(f"请求数据: {data}")
    
    try:
        # 发送POST请求并启用流式响应
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()  # 检查HTTP错误
        
        thread_id = None
        tool_request = None
        
        print("接收流式响应:")
        # 逐行读取流式响应
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                # 解析SSE格式的数据
                if decoded_line.startswith('data: '):
                    try:
                        json_data = json.loads(decoded_line[6:])  # 移除 'data: ' 前缀
                        print(f"  收到数据: {json_data}")
                        
                        # 提取会话ID
                        if 'thread_id' in json_data:
                            thread_id = json_data['thread_id']
                            print(f"  会话ID: {thread_id}")
                        
                        # 检查是否收到工具请求
                        if json_data.get('type') == 'tool_request':
                            tool_request = json_data
                            print(f"  检测到工具请求: {tool_request}")
                            
                    except json.JSONDecodeError as e:
                        print(f"  JSON解析错误: {e}")
                        continue
        
        # 返回结果
        if thread_id and tool_request:
            print("✓ 测试成功: 工具执行已正确中断")
            return thread_id, tool_request
        else:
            print("✗ 测试失败: 未检测到工具请求或会话ID")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求错误: {e}")
        return None, None
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return None, None


def test_continue_thread(thread_id: str, approved: bool = True) -> Optional[Dict[Any, Any]]:
    """
    测试继续执行被中断的线程
    
    Args:
        thread_id (str): 会话ID
        approved (bool): 是否批准工具执行，默认为True
        
    Returns:
        dict: 服务器响应，如果出错则返回None
    """
    # 定义测试端点和数据
    url = "http://localhost:8000/continue_thread"
    data = {
        "thread_id": thread_id,
        "approved": approved,
        "tool_calls": None  # 在实际应用中，这里会包含工具调用信息
    }
    
    print(f"\n=== 测试继续执行线程 ===")
    print(f"发送请求到: {url}")
    print(f"请求数据: {data}")
    
    try:
        # 发送POST请求
        response = requests.post(url, json=data)
        response.raise_for_status()  # 检查HTTP错误
        
        result = response.json()
        print(f"服务器响应: {result}")
        
        # 检查响应状态
        if result.get('status') == 'success':
            print("✓ 测试成功: 线程继续执行成功")
            return result
        else:
            print(f"✗ 测试失败: {result.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求错误: {e}")
        return None
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return None


def main():
    """
    主测试函数
    """
    print("ChatAgent Human-in-the-Loop 测试脚本")
    print("=" * 50)
    
    # 测试1: 验证工具执行中断
    thread_id, tool_request = test_chat_with_interrupt()
    
    if thread_id and tool_request:
        print(f"\n获得会话ID: {thread_id}")
        print(f"获得工具请求: {tool_request['tool_name']}")
        
        # 等待片刻以确保服务器状态稳定
        print("\n等待2秒...")
        time.sleep(2)
        
        # 测试2: 验证批准工具执行
        print("\n" + "=" * 50)
        result = test_continue_thread(thread_id, approved=True)
        
        if result:
            print("\n测试总结:")
            print("- 工具执行中断: ✓ 通过")
            print("- 用户批准处理: ✓ 通过")
            print("- 工具执行结果: ✓ 成功" if result.get('result') else "- 工具执行结果: ✗ 失败")
            print("- 最终AI响应: ✓ 成功" if result.get('final_response') else "- 最终AI响应: ✗ 失败")
        else:
            print("\n测试总结:")
            print("- 工具执行中断: ✓ 通过")
            print("- 用户批准处理: ✗ 失败")
    else:
        print("\n测试总结:")
        print("- 工具执行中断: ✗ 失败")
        print("- 用户批准处理: 未测试")


if __name__ == "__main__":
    main()