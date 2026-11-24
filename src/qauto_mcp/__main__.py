"""Entrypoint: python -m qauto_mcp.

MCP_TRANSPORT=streamable-http (default) → HTTP on http://MCP_HOST:MCP_PORT/MCP_HTTP_PATH.
MCP_TRANSPORT=stdio → the old mode, the Host starts the process.
"""

from qauto_mcp.config import settings
from qauto_mcp.server import mcp


def main() -> None:
    if settings.mcp_transport == "stdio":
        mcp.run(transport="stdio")
        return
    # In this SDK (MCPServer, mcp 2.x) host/port/path are arguments of run(), not of the constructor.
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path=settings.mcp_http_path,
    )


if __name__ == "__main__":
    main()
