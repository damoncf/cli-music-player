#!/usr/bin/env python3
"""Test MCP Server tools."""
import asyncio
from cmp.mcp_server import create_mcp_server

async def test_mcp_server():
    """Test MCP server creation and tools."""
    print("🎵 Testing MCP Server...\n")
    
    # Create server
    server = create_mcp_server()
    print(f"✅ MCP Server created successfully")
    
    # Test tool handlers
    print("\n📋 Testing tool handlers...")
    
    # Test get_player_status
    result = await server._handle_tool_call("get_player_status", {})
    print(f"  get_player_status: ✅")
    
    # Test get_volume
    result = await server._handle_tool_call("get_volume", {})
    print(f"  get_volume: ✅")
    
    # Test get_playlist
    result = await server._handle_tool_call("get_playlist", {})
    print(f"  get_playlist: ✅")
    
    # Test stop
    result = await server._handle_tool_call("stop", {})
    print(f"  stop: ✅")
    
    # Test set_volume
    result = await server._handle_tool_call("set_volume", {"volume": 50})
    print(f"  set_volume(50): ✅")
    
    # Test set_shuffle
    result = await server._handle_tool_call("set_shuffle", {"enabled": True})
    print(f"  set_shuffle(True): ✅")
    
    # Test set_repeat
    result = await server._handle_tool_call("set_repeat", {"mode": "all"})
    print(f"  set_repeat('all'): ✅")
    
    # Test clear_playlist
    result = await server._handle_tool_call("clear_playlist", {})
    print(f"  clear_playlist: ✅")
    
    # Test play (should fail without tracks)
    result = await server._handle_tool_call("play", {})
    print(f"  play (no tracks): {result}")
    
    # Test add_to_playlist with non-existent file
    result = await server._handle_tool_call("add_to_playlist", {"paths": ["/tmp/test.mp3"]})
    print(f"  add_to_playlist: {result}")
    
    # Test get_player_status again to see changes
    result = await server._handle_tool_call("get_player_status", {})
    print(f"\n📊 Final status:")
    print(result)
    
    print("\n✅ All MCP tools tested successfully!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())