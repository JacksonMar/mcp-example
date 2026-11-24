from mcp.server.mcpserver import MCPServer

from qauto_mcp.tools.auth import register_auth_tools
from qauto_mcp.tools.cars import register_car_tools


def register_tools(mcp: MCPServer) -> None:
    register_auth_tools(mcp)
    register_car_tools(mcp)
