#!/usr/bin/env python3
"""
Test script for MCP integration
This script tests the integration of MCP tools with the chat agent.
"""

import requests
import json
import time


def test_mcp_integration():
    """Test the MCP integration by sending a message that should trigger MCP tools."""
    
    # Test data
    url = "http://localhost:8000/chat"
    data = {
        "text": "What is 15 multiplied by 4?",
        "provider": "ollama",
        "model": "qwen3:8b"
    }
    
    print("=== Testing MCP Integration ===")
    print(f"Sending request to: {url}")
    print(f"Request data: {data}")
    
    try:
        # Send POST request with streaming
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        print("\nStreaming response:")
        tool_request_detected = False
        
        # Process streaming response
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    try:
                        json_data = json.loads(decoded_line[6:])  # Remove 'data: ' prefix
                        print(f"  Received: {json_data}")
                        
                        # Check if we get a tool request
                        if json_data.get('type') == 'tool_request':
                            tool_request_detected = True
                            print(f"  Tool request detected: {json_data.get('tool_name')}")
                            
                    except json.JSONDecodeError as e:
                        print(f"  JSON decode error: {e}")
                        continue
        
        if tool_request_detected:
            print("\n✓ MCP integration test PASSED: Tool request was detected")
        else:
            print("\n✗ MCP integration test FAILED: No tool request detected")
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Request error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


def test_tavily_integration():
    """Test the Tavily integration by sending a message that should trigger the search tool."""
    
    # Test data
    url = "http://localhost:8000/chat"
    data = {
        "text": "What is artificial intelligence?",
        "provider": "ollama",
        "model": "qwen3:8b"
    }
    
    print("\n=== Testing Tavily Integration ===")
    print(f"Sending request to: {url}")
    print(f"Request data: {data}")
    
    try:
        # Send POST request with streaming
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        print("\nStreaming response:")
        tool_request_detected = False
        
        # Process streaming response
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    try:
                        json_data = json.loads(decoded_line[6:])  # Remove 'data: ' prefix
                        print(f"  Received: {json_data}")
                        
                        # Check if we get a tool request
                        if json_data.get('type') == 'tool_request':
                            tool_request_detected = True
                            print(f"  Tool request detected: {json_data.get('tool_name')}")
                            
                    except json.JSONDecodeError as e:
                        print(f"  JSON decode error: {e}")
                        continue
        
        if tool_request_detected:
            print("\n✓ Tavily integration test PASSED: Tool request was detected")
        else:
            print("\n✗ Tavily integration test FAILED: No tool request detected")
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Request error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


if __name__ == "__main__":
    # Wait a moment for the server to fully start
    print("Waiting for server to fully start...")
    time.sleep(2)
    
    # Run tests
    test_mcp_integration()
    test_tavily_integration()
    
    print("\n=== Test Complete ===")