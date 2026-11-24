from mcp.server.mcpserver import MCPServer

from qauto_mcp.resources.cars import register_car_resources


def register_resources(mcp: MCPServer) -> None:
    register_car_resources(mcp)
