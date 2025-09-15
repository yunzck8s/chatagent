import asyncio
from src.tools.tavily import get_tavily_tool
from langgraph.types import interrupt

# Mock the interrupt function to simulate user approval
def mock_interrupt(requests):
    print("Tool interrupt triggered!")
    print(f"Request: {requests[0]}")
    
    # Simulate user approval
    response = {
        "type": "accept",
        "args": requests[0]["action_request"]["args"]
    }
    print(f"Simulating user approval: {response}")
    return [response]

# Replace the interrupt function with our mock
import langgraph.types
langgraph.types.interrupt = mock_interrupt

async def test_tool_interrupt():
    """Test the tool interrupt functionality"""
    print("=== Testing Tool Interrupt Functionality ===")
    
    # Get the tavily tool
    tool = get_tavily_tool()
    
    # Try to use the tool
    try:
        result = tool.invoke({"query": "latest developments in AI"})
        print(f"Tool result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tool_interrupt())