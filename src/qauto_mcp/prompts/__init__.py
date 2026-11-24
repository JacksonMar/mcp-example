from mcp.server.mcpserver import MCPServer

from qauto_mcp.prompts.cars import register_car_prompts


def register_prompts(mcp: MCPServer) -> None:
    register_car_prompts(mcp)
